import os
import json
import sqlite3
from Crypto.Cipher import AES
import codecs
from datetime import datetime, timedelta
from utils import *
import requests

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
        app.logger.error(e)
        return False
    
def LoadServices(app, redissession, client,getClientName,licensedata):
    setenv(app)        
        # Get count of users logged in

    @app.route('/hooks/validateStatus',methods=['POST'])
    def validateStatus():
        app.logger.debug("Inside validateStatus.")
        res={'status':'fail','message':'','data':None}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                if lsData['Status'] != 'Active':
                    res = {'status':'fail','message':'License is not active '}
                else:
                    res = {'status':'pass','data':lsData['Status']}
        except Exception as e:
            app.logger.error(e)
            res = {'status':'fail','message':'License is not active '}
            return jsonify(res)
        return jsonify(res)
    
    @app.route('/hooks/validateLicenceType',methods=['POST'])
    def validateLicenceType():
        app.logger.debug("Inside validateLicenceType.")
        res={'status':'fail'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                res = {'status':lsData['LicenseTypes']}
        except Exception as e:
            app.logger.error(e)
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
            app.logger.error(e)
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)
    
    @app.route('/hooks/validateUser',methods=['POST'])
    def validateUser():
        app.logger.debug("Inside validateUser.")
        res={'status':'pass','message':'','data':None}
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
                        res = {'status':"fail",'message':"Max Users Already loggedin"}
                        app.logger.error(res)
                        return res
        except Exception as e:
            app.logger.error(e)
            res = {'message':"Max Users Already loggedin",'status':"fail"}
            return jsonify(res)
        return jsonify(res)

    @app.route('/hooks/validateProject',methods=['POST'])
    def validateProject():
        app.logger.debug("Inside validateProject.")
        res={'status':'pass','message':'','data':None}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                licensedata = dbsession.licenseManager.find_one({"client":clientName})["data"]
                if licensedata['PA'] != "Unlimited":
                    projectsCount=0 
                    projects_list=list(dbsession.projects.find({}))
                    for project in projects_list:
                        if not(project['name'].startswith('Sample_')):
                            projectsCount=projectsCount+1
                    if projectsCount >= int(licensedata['PA']):
                        res = {'status':'fail','message':'Max Allowed Projects Created'}
                return res
        except Exception as e:
            app.logger.error(e)
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
                    res = {'status':'pass'}
        except Exception as e:
            app.logger.error(e)
            res = {'fail':'Failed to fetch License Details'}
            return jsonify(res)
        return jsonify(res)

    @app.route('/hooks/validateExecutionSteps',methods=['POST'])
    def validateExecutionSteps():
        app.logger.debug("Inside validateExecutionSteps.")
        res={'status':'fail','message':'Execution Not allowed due to max steps count exceed','data':0}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                totalSteps=0
                maxExec=dbsession.licenseManager.find_one({"client": clientName})['data']['TE']
                if maxExec == "Unlimited":
                    res={'status':'pass','data':totalSteps}
                    return res
                if len(list(dbsession.reports.find({}))) > 0:
                    reportitems=list(dbsession.reports.aggregate([{"$match":{"executedtime" :{'$gte' : datetime(datetime.now().year, datetime.now().month, 1, 00, 00, 00)}}},{"$lookup":{
                        "from":"reportitems",
                        "localField":"reportitems",
                        "foreignField":"_id",
                        "as":"reportitem"}},{"$unwind":"$reportitem"}
                        ]))
                    
                    for reportitem in reportitems:
                        for step in reportitem["reportitem"]["rows"]:
                            if "Step" in step:
                                totalSteps= totalSteps + 1   
                for exec in requestdata["executionData"]["batchInfo"]:
                    suites=exec["suiteDetails"]
                    scenarioIds=list(map(lambda suite:suite["scenarioId"],suites))
                    currentExecSteps = list(dbsession.testscenarios.aggregate([
                        {"$match":{"_id" :{"$in":list(map(lambda x:ObjectId(x),scenarioIds))}}},
                        {"$lookup":{
                        "from":"testcases",
                        "localField":"testcaseids",
                        "foreignField":"_id",
                        "as":"testcases"}
                        },{"$unwind":"$testcases"},
                        {"$group":{"_id":"null","stepcount":{"$sum":{"$size":"$testcases.steps"}}}}
                    ]))
                    if len(currentExecSteps)>0:
                        totalSteps= totalSteps + currentExecSteps[0]["stepcount"]  
                if int(maxExec) >= totalSteps:
                    res={'status':'pass','data':totalSteps}
                elif totalSteps>0:
                    res['data']=totalSteps
                
        except Exception as e:
            app.logger.error(e)
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
                maxPE=dbsession.licenseManager.find_one({"client": clientName})['data']['PE']
                if maxPE == "Unlimited":
                    res={'status':'pass'}
                    return res
                executionsList=list(dbsession.executions.find({}))
                executionCount=0
                for exec in executionsList:
                    if exec['status'] == "inprogress":
                        executionCount = executionCount +1
                if int(maxPE) > executionCount:
                    res={'status':'pass'}
        except Exception as e:
            app.logger.error(e)
            return jsonify(res)
        
        return jsonify(res)
    
    @app.route('/hooks/upgradeLicense',methods=['POST'])
    def upgradeLicense():
        app.logger.debug("Inside upgradeLicense.")
        res={'False':'Unable to reach License Manager'}
        requestdata=json.loads(request.data)
        try:
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)
                dbsession=client[clientName]
                testManagerID=dbsession.permissions.find_one({"name" : "Test Manager"})
                dbsession.users.update_one({ "name" : requestdata["username"]},{"$set":{"defaultrole" :  testManagerID['_id']}})
                projects_list=list(dbsession.projects.find())
                user=dbsession.users.find_one({"name":requestdata["username"]})
                user_project=list(user['projects'])
                for project in projects_list:
                    if project['name'].startswith('Sample_'):
                        if project['_id'] not in user_project:
                            user_project.append(project["_id"])
                dbsession.users.update_one({"name":requestdata["username"]},{"$set":{"projects":user_project}})
                lsData=dbsession.licenseManager.find_one({"client": clientName})
                CustomerGUID=lsData['guid']
                res={'True':'updated users & projects'}
                if "licenseServer" in licensedata:
                    resp = requests.get(licensedata["licenseServer"]+f"/api/UpgradeLicense?CustomerGUID={CustomerGUID}&CurrentLicenseType&NewLicenseType")
                    if resp.status_code == 200:
                        res={'True':'License Upgraded'}
        except Exception as e:
            app.logger.error(e)
            return jsonify(res)
        app.logger.debug(res)
        return jsonify(res)