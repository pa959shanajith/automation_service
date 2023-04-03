import os
import json
import sqlite3
from Crypto.Cipher import AES
import codecs
from datetime import datetime, timedelta
from utils import *

db_keys = "".join(['N','i','n','E','t','e','E','n','6','8','d','A','t','a','B',
    'A','s','3','e','N','c','R','y','p','T','1','0','n','k','3','y','S'])
KEY_SERVER = "".join(['n','I','N','3','t','3','e','n','6','8','l','I','(','e','N','s','!','n','G','S','3','R','^','e','R','s','E','r','V','e','Rr'])


def unwrap(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data, 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')
    
def unpad(data):
    return data[0:-ord(data[-1])]

def decrypt_node(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data.strip(), 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def encrypt_node(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex').decode('utf-8')

def dbConnector(ops,*args):
    data = False
    if ops=='check':
        if os.access(db_path,os.R_OK):
            data = True
    else:
        # CREATE DATABASE CONNECTION
        conn = sqlite3.connect(db_path)
        if ops=='select':
            #Retrieve the data from db and decrypt it
            cursor = conn.cursor()
            result = cursor.execute("SELECT info from lsdetails WHERE lsid = 'LS001'")
            data = list(result)
            if len(data) >= 0:
                data = data[0][0]
            data = decrypt_node(data, KEY_SERVER)
            data = json.loads(data)
            # Backward compatibility
            old_key = "nd"+"ac"
            if old_key in data:
                data["das"] = data[old_key]
                del data[old_key]
                datatodb = encrypt_node(json.dumps(data), KEY_SERVER)
                cursor.execute("UPDATE lsdetails SET info = ? WHERE lsid = 'LS001'",[datatodb])
        elif ops=='update':
            #Encrypt data and update in db
            datatodb = json.dumps(args[0])
            datatodb = encrypt_node(datatodb, KEY_SERVER)
            cursor1 = conn.execute("UPDATE lsdetails SET info = ? WHERE lsid = 'LS001'",[datatodb])
            data=True
        conn.commit()
        conn.close()
    return data

def getLSData(LS_Path):
    try:
        global db_path
        db_path=LS_Path
        if os.path.isfile(db_path):
            dbdata=dbConnector('select')
            msg=dbdata
            
            if dbdata:
                return msg
        else:
            return False  
        
    except Exception as e:
        return False
    
def LoadServices(app, redissession, client,getClientName):
    setenv(app)        
        # Get count of users logged in

    @app.route('/hooks/validateStatus',methods=['POST'])
    def validateStatus():
        app.logger.debug("Inside validateStatus.")
        res={'status':'Fail'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                res = {'status':lsData['Status']}
        except Exception as e:
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)
    
    @app.route('/hooks/validateLicenceType',methods=['POST'])
    def validateLicenceType():
        app.logger.debug("Inside validateLicenceType.")
        res={'status':'Fail'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                res = {'status':lsData['LicenseTypes']}
        except Exception as e:
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)
    
    @app.route('/hooks/getLicenseDetails',methods=['POST'])
    def getLicenseDetails():
        app.logger.debug("Inside getLicenseDetails.")
        res={'status':'Fail'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                res = {'status':lsData}
        except Exception as e:
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)
    
    @app.route('/hooks/validateUser',methods=['POST'])
    def validateUser():
        app.logger.debug("Inside validateUser.")
        res={'status':'sucess'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                loggedInCount=0
                usersList=list(dbsession.users.find({},{"email":1}))
                usersList=[key['email'] for key in usersList]
                lsData=dbsession.licenseManager.find_one({"client":clientName})
                for key in redissession.keys():
                    sess=json.loads(redissession[key].decode('utf-8'))
                    if 'emailid' in sess:
                        if sess['activeRole'] != 'Admin':
                            if sess['emailid'] in usersList:
                                loggedInCount=loggedInCount+1
                if str(lsData['data']['USER']) != "Unlimited":
                    if loggedInCount >= int(lsData['data']['USER']):
                        res = {'fail':"Max Users Already loggedin"}
                        app.logger.error(res)
                        return res
        except Exception as e:
            res = {'fail':"Max Users Already loggedin"}
            return jsonify(res)
        return jsonify(res)

    @app.route('/hooks/validateProject',methods=['POST'])
    def validateProject():
        app.logger.debug("Inside validateProject.")
        res={'status':'sucess'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                licensedata = dbsession.licenseManager.find_one({"client":clientName})["data"]
                if licensedata['PA'] != "Unlimited":
                    projectsCount=len(list(dbsession.projects.find({})))
                    if projectsCount >= int(licensedata['PA']):
                        res = {'fail':'Max Allowed Projects Created'}
                return res
        except Exception as e:
            return jsonify(res)
        
        return jsonify(res)


    @app.route('/hooks/validateE2E',methods=['POST'])
    def validateE2E():
        app.logger.debug("Inside validateE2E.")
        res={'status':'Fail'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                if 'ETT' in lsData:
                    res = {'status':'sucess'}
        except Exception as e:
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)

    @app.route('/hooks/validateExecutionSteps',methods=['POST'])
    def validateExecutionSteps():
        app.logger.debug("Inside validateExecutionSteps.")
        res={'fail':'Execution Not allowed due to max setps count exceed'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                totalSteps=0
                maxExec=dbsession.licenseManager.find_one({"client": clientName})['data']['TE']
                executionsList=list(dbsession.executions.find({"starttime" :{'$gte' : datetime(datetime.now().year, datetime.now().month, 1, 00, 00, 00)}}))
                for exec in executionsList:
                    for ts in exec["parent"]:
                        tsc=list(dbsession.testsuites.find({"_id" :ts}))
                        for tscenerio in tsc:
                            tsids=list()
                            for i in tscenerio["testscenarioids"]:
                                temp=list(map(lambda x: x["testcaseids"], list(dbsession.testscenarios.find({"_id" :i}))))
                                for y in temp:
                                    for z in y:
                                        tsids.append(z)
                            for testCase in tsids:
                                testData=dbsession.testcases.find_one({"_id" :testCase})
                                totalSteps = totalSteps + len(testData["steps"])

                if int(maxExec) > totalSteps:
                    res={'status':'sucess'}
        except Exception as e:
            return jsonify(res)
        
        return jsonify(res)


    @app.route('/hooks/validateParallelExecutions',methods=['POST'])
    def validateParallelExecutions():
        app.logger.debug("Inside validateParallelExecutions.")
        res={'fail':'Execution Not allowed due to max execution count exceed'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                totalSteps=0
                maxExec=dbsession.licenseManager.find_one({"client": clientName})['data']['TE']
                executionsList=list(dbsession.executions.find({"starttime" :{'$gte' : datetime(datetime.now().year, datetime.now().month, 1, 00, 00, 00)}}))
                for exec in executionsList:
                    for ts in exec["parent"]:
                        tsc=list(dbsession.testsuites.find({"_id" :ts}))
                        for tscenerio in tsc:
                            tsids=list()
                            for i in tscenerio["testscenarioids"]:
                                temp=list(map(lambda x: x["testcaseids"], list(dbsession.testscenarios.find({"_id" :i}))))
                                for y in temp:
                                    for z in y:
                                        tsids.append(z)
                            for testCase in tsids:
                                testData=dbsession.testcases.find_one({"_id" :testCase})
                                totalSteps = totalSteps + len(testData["steps"])

                maxPE=dbsession.licenseManager.find_one({"client": clientName})['data']['PE']
                executionsList=list(dbsession.executions.find({}))
                executionCount=0
                for exec in executionsList:
                    if exec['status'] == "inprogress":
                        executionCount = executionCount +1
                if (int(maxPE) > executionCount) and (int(maxExec) > totalSteps):
                    res={'status':'sucess'}
        except Exception as e:
            return jsonify(res)
        
        return jsonify(res)