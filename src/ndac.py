#-------------------------------------------------------------------------------
# Name:        ndac.py
# Purpose:     Security Aspects, Licensing components and ProfJ
#
# Created:     10/07/2017
# Copyright:   (c) vishvas.a 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
import os
import json
import requests
import subprocess
import sqlite3
from datetime import datetime, timedelta
import time
import uuid
import redis
import flask
from flask import Flask, request, jsonify, Response
from bson.objectid import ObjectId
from waitress import serve
import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
from pymongo import MongoClient
from nltk.stem import PorterStemmer
from threading import Timer
import calendar
import argparse
import base64
from Crypto.Cipher import AES
import codecs
app = Flask(__name__)

parser = argparse.ArgumentParser()
log_group = parser.add_mutually_exclusive_group()
log_group.add_argument("-T", "--test", action="store_true", help="Set logger level to Test Environment")
log_group.add_argument("-D", "--debug", action="store_true", help="Set logger level to Debug")
log_group.add_argument("-I", "--info", action="store_true", help="Set logger level to Info")
log_group.add_argument("-W", "--warn", action="store_true", help="Set logger level to Warning")
log_group.add_argument("-E", "--error", action="store_true", help="Set logger level to Error")
log_group.add_argument("-C", "--critical", action="store_true", help="Set logger level to Critical")
parserArgs = parser.parse_args()

ice_ndac_key = "".join(['a','j','k','d','f','i','H','F','E','o','w','#','D','j',
    'g','L','I','q','o','c','n','^','8','s','j','p','2','h','f','Y','&','d'])
db_keys = "".join(['N','i','n','E','t','e','E','n','6','8','d','A','t','a','B',
    'A','s','3','e','N','c','R','y','p','T','1','0','n','k','3','y','S'])
mine = "".join(['\x4e','\x36','\x38','\x53','\x51','\x4c','\x69','\x74','\x65','\x44','\x61','\x74','\x61','\x53','\x65',
    '\x63','\x72','\x65','\x74','\x4b','\x65','\x79','\x43','\x6f','\x6d','\x70','\x4f','\x4e','\x65','\x6e','\x74','\x73'])
omgall = "".join(['\x4e','\x69','\x6e','\x65','\x74','\x65','\x65','\x6e','\x36','\x38','\x6e','\x64','\x61','\x74','\x63',
    '\x6c','\x69','\x63','\x65','\x6e','\x73','\x69','\x6e','\x67'])
ldap_key = "".join(['l','!','g','#','t','W','3','l','g','G','h','1','3','@','(',
    'c','E','s','$','T','p','R','0','T','c','O','I','-','k','3','y','S'])
activeicesessions={}
latest_access_time=datetime.now()

currexc = sys.executable
try: currfiledir = os.path.dirname(os.path.abspath(__file__))
except: currfiledir = os.path.dirname(currexc)
currdir = os.getcwd()
if os.path.basename(currexc).startswith("ndac"):
    currdir = os.path.dirname(currexc)
elif os.path.basename(currexc).startswith("python"):
    currdir = currfiledir
    needdir = "ndac_internals"
    parent_currdir = os.path.abspath(os.path.join(currdir,".."))
    if os.path.isdir(os.path.abspath(os.path.join(parent_currdir,"..",needdir))):
        currdir = os.path.dirname(parent_currdir)
    elif os.path.isdir(parent_currdir + os.sep + needdir):
        currdir = parent_currdir
config_path = currdir+'/server_config.json'
assistpath = currdir + "/ndac_internals/assist"
logspath = currdir + "/ndac_internals/logs"

lsip = "127.0.0.1"
lsport = "5000"
ndacport = "1990"
redis_dbup = False
mongo_dbup = False
onlineuser = False
gracePeriodTimer=None
twoDayTimer=None
licensedata=None
grace_period = 172800
LS_CRITICAL_ERR_CODE=['199','120','121','123','124','125']
lsRetryCount=0
sysMAC=None
chronographTimer=None
n68session=redissession=None

#counters for License
debugcounter = 0
scenarioscounter = 0
gtestsuiteid = []
suitescounter = 0

#Variables for ProfJ
questions=[] # to store the questions
pages=[] # to store the pages
keywords=[] # to store the keywords
weights=[] # to store the weights
answers=[] # to store the answers
pquestions=[] #preprocessed questions
newQuesInfo=[] #list to store relevant info about new questions
savedQueries = None #A variable to save every single relevant query asked by user
updateW = [[]]
weightUpdateTime = 60
chatbot = None
profj_db_path=assistpath+"/ProfJ.db"
profj_log_conf_path = assistpath + "/logging_config.conf"
profj_syn_path = assistpath + "/SYNONYMS.json"
profj_keywords_path = assistpath+"/keywords_db.txt"
profj_sqlitedb=None

def _jsonencoder_default(self, obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return flask.json.JSONEncoder._default(self, obj)
flask.json.JSONEncoder._default = flask.json.JSONEncoder.default
flask.json.JSONEncoder.default = _jsonencoder_default
# json.JSONEncoder._default = flask.json.JSONEncoder.default
# json.JSONEncoder.default = _jsonencoder_default

#server check
@app.route('/')
def server_ready():
    msg = 'Data Server Stopped!!!'
    if onlineuser:
        msg = 'Data Server Ready!!!'
    return msg


################################################################################
# BEGIN OF SERVICES IMPORT
################################################################################

from utils import *
setenv(flaskapp=app)
sys.path.append(currfiledir+os.sep+"routes")

def addroutes():
    app.logger.debug("Loading services")
    import loginservice
    loginservice.LoadServices(app, redissession, n68session, licensedata)

    import adminservice
    adminservice.LoadServices(app, redissession, n68session, licensedata,ice_ndac_key)

    import mindmapservice
    mindmapservice.LoadServices(app, redissession, n68session)

    import designscreenservice
    designscreenservice.LoadServices(app, redissession, n68session)

    import designtestcaseservice
    designtestcaseservice.LoadServices(app, redissession, n68session)

    import executionservice
    executionservice.LoadServices(app, redissession, n68session)

    import thirdpartyservice
    thirdpartyservice.LoadServices(app, redissession, n68session)

    import reportsservice
    reportsservice.LoadServices(app, redissession, n68session)

    import utilitiesservice
    utilitiesservice.LoadServices(app, redissession, n68session)

    import neurongraphsservice
    neurongraphsservice.LoadServices(app, redissession, n68session)

    #Prof J First Service: Getting Best Matches
    @app.route('/chatbot/getTopMatches_ProfJ',methods=['POST'])
    def getTopMatches_ProfJ():
        app.logger.debug("Inside getTopMatches_ProfJ")
        global newQuesInfo, savedQueries
        res={'rows':'fail'}
        try:
            if ( type(request.data) == bytes ): query = str(request.data.decode('utf-8'))
            else: query = str(request.data)
            profj = ProfJ(pages,questions,answers,keywords,weights,pquestions,newQuesInfo,savedQueries)
            response,newQuesInfo,savedQueries = profj.start(query)
            #if response[0][1] == "Please be relevant..I work soulfully for Nineteen68":
                #response[0][1] = str(chatbot.get_response(query))
            profj_sqlitedb.updateCaptureTable()
            res={'rows':response}
        except Exception as e:
            servicesException("getTopMatches_ProfJ",e)
        return jsonify(res)

    #Prof J Second Service: Updating the Question's Frequency
    @app.route('/chatbot/updateFrequency_ProfJ',methods=['POST'])
    def updateFrequency_ProfJ():
        app.logger.debug("Inside updateFrequency_ProfJ")
        res={'rows':'fail'}
        try:
            qid = request.data
            weights[int(qid)] += 1
            temp = []
            temp.append(qid)
            temp.append(weights[int(qid)])
            res={'rows': True}
        except Exception as e:
            servicesException("updateFrequency_ProfJ",e)
        return jsonify(res)

################################################################################
# END OF SERVICES IMPORT
################################################################################

@app.route('/server',methods=['POST'])
def checkServer():
    app.logger.debug("Inside checkServer")
    response = "fail"
    status = 500
    try:
        if (onlineuser == True):
            response = "pass"
            status = 200
    except Exception as exc:
        servicesException("checkServer",exc)
    return Response(response, status, mimetype='text/plain')

@app.route('/server/updateActiveIceSessions',methods=['POST'])
def updateActiveIceSessions():
    global activeicesessions
    global latest_access_time
    ice_plugins_list = []
    for keys in licensedata['platforms']:
        if(licensedata['platforms'][keys] == True):
            ice_plugins_list.append(keys)
    res={"id":"","res":"fail","ts_now":str(datetime.now()),"connect_time":str(datetime.now()),"plugins":str(ice_plugins_list)}
    response = {"node_check":False,"ice_check":wrap(json.dumps(res),ice_ndac_key)}
    ice_uuid=None
    ice_ts=None
    try:
        requestdata=json.loads(request.data)
        app.logger.debug("Inside updateActiveIceSessions. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            sess = redissession.get('icesessions')
            if sess == '' or sess is None:
                redissession.set('icesessions',wrap('{}',db_keys))
            activeicesessions=json.loads(unwrap(redissession.get('icesessions'),db_keys))
            if(requestdata['query']=='disconnect'):
                username=requestdata['username'].lower()
                if(username in activeicesessions):
                    del activeicesessions[username]
                    redissession.set('icesessions',wrap(json.dumps(activeicesessions),db_keys))
                res['res']="success"

            elif(requestdata['query']=='connect' and 'icesession' in requestdata):
                icesession = unwrap(requestdata['icesession'],ice_ndac_key)
                icesession = json.loads(icesession)
                hostname=icesession["hostname"]
                ice_action=icesession["iceaction"]
                ice_token_dec = unwrap(requestdata['icetoken'],ice_ndac_key).split("@")
                ice_token=ice_token_dec[0]
                ice_name=ice_token_dec[1]
                ice_uuid=icesession['ice_id']
                ice_ts=icesession['connect_time']
                if('.' not in ice_ts):
                    ice_ts = ice_ts + '.000000'
                username=icesession['username'].lower()
                latest_access_time=datetime.strptime(ice_ts, '%Y-%m-%d %H:%M:%S.%f')
                res['id']=ice_uuid
                res['connect_time']=ice_ts
                app.logger.debug("Connected clients: "+str(list(activeicesessions.keys())))
                #ICE which are "deregistered" are eleminated for the Registartion and Connection
                queryresult = n68session.icetokens.find_one({"token":ice_token,"icename":ice_name,"status":{"$ne": DEREGISTER_STATUS}})
                if queryresult is None:
                    res['err_msg'] = "Unauthorized: Access denied due to Invalid Token, ICE is not registered with Nineteen68"
                    response = {"node_check":"InvalidToken","icename":ice_name,"ice_check":wrap(json.dumps(res),ice_ndac_key)}
                else:
                    #To reject connection with same ice_tokens
                    if ice_action==REGISTER:
                        if queryresult["status"]==REGISTER_STATUS:
                            res['err_msg'] = "Access denied: Multiple registartions Restrcited! ICE name: "+queryresult["icename"]+", Hostname: "+queryresult["hostname"]+" is already registered."
                            response = {"node_check":"InvalidICE","ice_check":wrap(json.dumps(res),ice_ndac_key)}
                        else:
                            n68session.icetokens.update_one({"token":ice_token},{"$set":{"hostname":hostname,"registeredon":datetime.now(),"status":REGISTER_STATUS}})
                            res['res']="validICE"
                            res['icename']=ice_name
                            response = {"node_check":"validICE","icename":ice_name,"ice_check":wrap(json.dumps(res),ice_ndac_key)}
                    else:
                        ice_name=queryresult["icename"]
                        username=n68session.users.find_one({"_id":queryresult["provisionedto"]},{"name":1})
                        user_channel=redissession.pubsub_numsub("ICE1_normal_"+ice_name,"ICE1_scheduling_"+ice_name)
                        user_channel_cnt=int(user_channel[0][1]+user_channel[1][1])
                        if(user_channel_cnt == 0 and ice_name in activeicesessions):
                            del activeicesessions[ice_name]
                        if(ice_name in activeicesessions and activeicesessions[ice_name] != ice_uuid):
                            res['err_msg'] = "Connection exists with same token"
                            response["ice_check"]=wrap(json.dumps(res),ice_ndac_key)
                        #To check if license is available
                        elif(len(activeicesessions)>=int(licensedata['allowedIceSessions'])):
                            res['err_msg'] = "All ice sessions are in use"
                            response["ice_check"]=wrap(json.dumps(res),ice_ndac_key)
                        #To add in active ice sessions
                        else:
                            # random_string=get_random_string()
                            # ct=wrap(ice_token+random_string+hostname,ice_ndac_key)
                            # res['ct']=ct
                            activeicesessions=json.loads(unwrap(redissession.get('icesessions'),db_keys))
                            activeicesessions[ice_token] = ice_uuid
                            redissession.set('icesessions',wrap(json.dumps(activeicesessions),db_keys))
                            res['res']="success"
                            response = {"node_check":"allow","ice_name":ice_name,"username":username["name"],"ice_check":wrap(json.dumps(res),ice_ndac_key)}
        else:
            app.logger.warn('Empty data received. updateActiveIceSessions.')
    except redis.ConnectionError as exc:
        app.logger.critical(printErrorCodes('217'))
        servicesException("updateActiveIceSessions",exc)
    except Exception as exc:
        servicesException("updateActiveIceSessions",exc)
    return jsonify(response)

################################################################################
# BEGIN OF INTERNAL COMPONENTS
################################################################################

################################################################################
# BEGIN OF COUNTERS
################################################################################
def counterupdator(updatortype,userid,count):
    status=False
    try:
        n68session.counters.find_one_and_update({"countertype":updatortype, "userid":ObjectId(userid)},{"$set":{"counter":count},"$currentDate":{"counterdate":True}})
        status = True
    except Exception as counterupdatorexc:
        servicesException("counterupdator",counterupdatorexc)
    return status

def getreports_in_day(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(n68session.reports.find({'executedtime':{'$gt': bgnts, '$lte': endts}}))
        res = {'rows':queryresult}
    except Exception as getreports_in_dayexc:
        servicesException("getreports_in_day",getreports_in_dayexc)
    return res

def getsuites_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(n68session.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testsuites'}))
        res = {"rows":queryresult}
    except Exception as getsuites_inititatedexc:
        servicesException("getsuites_inititated",getsuites_inititatedexc)
    return res

def getscenario_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(n68session.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testscenarios'}))
        res = {"rows":queryresult}
    except Exception as getscenario_inititatedexc:
        servicesException("getscenario_inititated",getscenario_inititatedexc)
    return res

def gettestcases_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(n68session.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testcases'}))
        res = {"rows":queryresult}
    except Exception as gettestcases_inititatedexc:
        servicesException("gettestcases_inititated",gettestcases_inititatedexc)
    return res

def getbgntime(requiredday,*args):
    currentday = ''
    day = ''
    if len(args)==0:
        currentday=datetime.utcnow() + timedelta(seconds = 19800)
    else:
        currentday=args[0]
    if requiredday == 'time_at_nine':
        day=datetime(currentday.year, currentday.month, currentday.day,9,0,0,0)
    elif requiredday == 'yest':
        yesterday=currentday - timedelta(1)
        day=datetime(yesterday.year, yesterday.month, yesterday.day,18,30,0,0)
    elif requiredday == 'time_at_six_thirty':
        day=datetime(currentday.year, currentday.month, currentday.day,18,30,0,0)
    elif requiredday == 'indate':
        day=datetime(currentday.year, currentday.month, currentday.day,0,0,0,0)
    elif requiredday == 'now':
        day=currentday.replace(microsecond=0)
    return day

# def gettimestamp(date):
#     timestampdata=''
#     date= datetime.strptime(str(date),"%Y-%m-%d %H:%M:%S")
#     timestampdata = calendar.timegm(date.utctimetuple()) * 1000
#     return timestampdata

def modelinfoprocessor():
    modelinfo=[]
    try:
        bgnyesday = None
        bgnoftday = None
        x = getbgntime('now')
        if(x.hour <= 9):
            bgnyesday = getbgntime('yest')
            bgnoftday = getbgntime('time_at_nine')
        elif(x.hour > 9 and x.hour <= 18):
            bgnyesday = getbgntime('time_at_nine')
            bgnoftday = getbgntime('time_at_six_thirty')
        else:
            bgnyesday = getbgntime('time_at_six_thirty')
            bgnoftday = x
        dailydata={}
        allusers = []
        dailydata['day'] = str(x)
        bgnts=bgnyesday#gettimestamp(bgnyesday)
        endts=bgnoftday#gettimestamp(bgnoftday)
        resultset=getreports_in_day(bgnts,endts)
        reportobj=reportdataprocessor(resultset,bgnyesday,bgnoftday)
        dailydata['r_exec_cnt'] = str(reportobj['reprt_cnt'])
        suiteobj = dataprocessor('testsuites',bgnts,endts)
        dailydata['su_exec_cnt'] = str(suiteobj['suite_cnt'])
        allusers = allusers + suiteobj['active_usrs']
        scenariosobj = dataprocessor('testscenarios',bgnts,endts)
        dailydata['s_exec_cnt'] = str(scenariosobj['cnario_cnt'])
        allusers = allusers + scenariosobj['active_usrs']
        testcasesobj = dataprocessor('testcases',bgnts,endts)
        dailydata['t_exec_cnt'] = str(testcasesobj['tcases_cnt'])
        allusers = allusers + testcasesobj['active_usrs']
        dailydata['license_usd'] = str(len(set(allusers)))
        modelinfo.append(dailydata)
    except Exception as e:
        servicesException("modelinfoprocessor",e)
    return modelinfo

def dataprocessor(datatofetch,fromdate,todate):
    respobj={}
    usr_list=[]
    total_cnt=0
    dataresp=''
    try:
        if datatofetch == 'testsuites':
            dataresp=getsuites_inititated(fromdate,todate)
            for eachrow in dataresp['rows']:
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
            respobj['suite_cnt'] = str(total_cnt)
        elif datatofetch == 'testscenarios':
            dataresp=getscenario_inititated(fromdate,todate)
            for eachrow in dataresp['rows']:
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
            respobj['cnario_cnt'] = str(total_cnt)
        elif datatofetch == 'testcases':
            dataresp=gettestcases_inititated(fromdate,todate)
            for eachrow in dataresp['rows']:
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
            respobj['tcases_cnt'] = str(total_cnt)
        respobj['active_usrs'] = usr_list
    except Exception as dataprocessorexc:
        servicesException("dataprocessor",dataprocessorexc)
    return respobj

def reportdataprocessor(resultset,fromdate,todate):
    count = 0
    eachreports_in_day={"reprt_cnt":"","day":""}
    try:
        if resultset['rows'] != 'fail':
            for eachrow in resultset['rows']:
                exectime=eachrow['executedtime']
                if exectime != None:
                    if (exectime >= fromdate and exectime < todate):
                        count = count + 1
        eachreports_in_day['day'] = str(todate)
        eachreports_in_day['reprt_cnt'] = str(count)
    except Exception as reportdataprocessorexc:
        servicesException("reportdataprocessor",reportdataprocessorexc)
    return eachreports_in_day

################################################################################
# END OF COUNTERS
################################################################################

################################################################################
# START OF LICENSING COMPONENTS
################################################################################
def getMacAddress():
    app.logger.debug("Inside getMacAddress")
    mac=""
    if sys.platform == 'win32':
        for line in os.popen("ipconfig /all"):
            if line.lstrip().startswith('Physical Address'):
##                mac = line.split(':')[1].strip().replace('-',':')
                mac = line.split(':')[1].strip()
                mac = mac+'    '
                break
    else:
        for line in os.popen("/sbin/ifconfig"):
            if line.find('Ether') > -1:
                mac = line.split()[4]
                mac = mac+'    '
                break
    return mac


def basecheckonls():
    app.logger.debug("Inside basecheckonls")
    basecheckstatus = False
    try:
        dbdata = dataholder('select')
        token=dbdata['tkn']
        EXPECTING_RESPONSE=str(int(time.time()*24150))
        baserequest= {
            "action": "register",
            "token": token,
            "lCheck": str(latest_access_time),
            "ts": EXPECTING_RESPONSE
        }
        baserequest=wrap(json.dumps(baserequest),omgall)
        connectresponse = connectingls(baserequest)
        if connectresponse != False:
            actresp = unwrap(connectresponse,omgall)
            actresp = json.loads(actresp)
            if actresp['ots']==EXPECTING_RESPONSE:
                EXPECTING_RESPONSE=''
                if actresp['res'] == 'F':
                    emsg="[ECODE: "+actresp['ecode']+"] "+actresp['message']
                    if (actresp['ecode'] in LS_CRITICAL_ERR_CODE):
                        app.logger.critical(emsg)
                        stopserver()
                    else:
                        app.logger.error(emsg)
                elif actresp['res'] == 'S':
                    global onlineuser,licensedata
                    licensedata=actresp['ldata']
                    if token==actresp['token']:
                        basecheckstatus = True
                    else:
                        dbdata['tkn']=actresp['token']
                        basecheckstatus=dataholder('update',dbdata)
                    onlineuser = True
                    setenv(licactive=onlineuser)
        else:
            if lsRetryCount<3:
                app.logger.info(printErrorCodes('215'))
                time.sleep(10)
                basecheckstatus=basecheckonls()
            else:
                app.logger.critical(printErrorCodes('216'))
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('201'))
    return basecheckstatus

def updateonls():
    app.logger.debug("Inside updateonls")
    try:
        global licensedata
        dbdata=dataholder('select')
        EXPECTING_RESPONSE=str(int(time.time()*24150))
        modelinfores = modelinfoprocessor()
        if('mdlinfo' in dbdata):
            modelinfores.extend(dbdata['mdlinfo'])
            del dbdata['mdlinfo']
            dataholder('update',dbdata)
        datatols={
            "token": dbdata['tkn'],
            "action": "update",
            "ts": EXPECTING_RESPONSE,
            "lCheck": str(latest_access_time),
            "modelinfo": modelinfores
        }
        datatols=wrap(json.dumps(datatols),omgall)
        updateresponse = connectingls(datatols)
        if updateresponse != False:
            chronograph()
            res = json.loads(unwrap(updateresponse,omgall))
            if res['res'] == 'F':
                emsg="[ECODE: "+res['ecode']+"] "+res['message']
                if (res['ecode'] in LS_CRITICAL_ERR_CODE):
                    app.logger.critical(emsg)
                    dbdata['mdlinfo']=modelinfores
                    dataholder('update',dbdata)
                    stopserver()
                else:
                    app.logger.error(emsg)
            elif res['res'] == 'S':
                if('ldata' in res):
                    licensedata = res['ldata']
        else:
            if lsRetryCount<3:
                app.logger.info(printErrorCodes('215'))
                time.sleep(10)
                updateonls()
            else:
                dbdata['mdlinfo']=modelinfores
                dataholder('update',dbdata)
                app.logger.critical(printErrorCodes('216'))
                startTwoDaysTimer()
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('202'))

def getupdatetime():
    x = datetime.utcnow() + timedelta(seconds = 19800)
    day = None
    datetime_at_twelve = datetime.strptime(str(x.year)+'-'+str(x.month)+'-'+str(x.day)+' 00:00:00', '%Y-%m-%d %H:%M:%S')
    datetime_at_nine = datetime.strptime(str(x.year)+'-'+str(x.month)+'-'+str(x.day)+' 9:00:00', '%Y-%m-%d %H:%M:%S')
    datetime_at_six_thirty = datetime.strptime(str(x.year)+'-'+str(x.month)+'-'+str(x.day)+' 18:30:00', '%Y-%m-%d %H:%M:%S')
    datetime_at_next_nine = datetime.strptime(str((x + timedelta(days=1)).year)+'-'+str((x + timedelta(days=1)).month)+'-'+str((x + timedelta(days=1)).day)+' 9:00:00', '%Y-%m-%d %H:%M:%S')
    if(x >= datetime_at_nine and x < datetime_at_six_thirty):
        #For update at 6:30 PM
        day = datetime_at_six_thirty
    elif((x >= datetime_at_six_thirty and x < datetime_at_next_nine) or (x >=datetime_at_twelve and x < datetime_at_nine)):
        #For update at 9:00 AM
        day = datetime_at_next_nine
    return day

def connectingls(data):
    global lsRetryCount,twoDayTimer,grace_period
    lsRetryCount+=1
    connectionstatus=False
    try:
        lsresponse = requests.post('http://'+lsip+":"+lsport+"/ndacrequest",data=data)
        if lsresponse.status_code == 200:
            dbdata=dataholder('select')
            if('grace_period' in dbdata):
                del dbdata['grace_period']
                dataholder('update',dbdata)
            lsRetryCount=0
            grace_period = 172800
            connectionstatus = lsresponse.content
            if (twoDayTimer != None and twoDayTimer.isAlive()):
                twoDayTimer.cancel()
                twoDayTimer=None
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('208'))
    return connectionstatus

def chronograph():
    app.logger.debug("Chronograph triggred")
    try:
        secs=None
        if chronographTimer is not None:
            secs=chronographTimer
        else:
            x = datetime.utcnow() + timedelta(seconds = 19800)
            secs = (getupdatetime() - x).total_seconds()
        t = Timer(secs, updateonls)
        t.start()
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('210'))

def dataholder(ops,*args):
    data = False
    try:
        if ops=='check':
            if os.access(logspath+"/data.db",os.R_OK):
                data = True
        else:
            # CREATE DATABASE CONNECTION
            conn = sqlite3.connect(logspath+"/data.db")
            if ops=='select':
                #Retrieve the data from db and decrypt it
                cursor1 = conn.execute("SELECT intrtkndt FROM clndls WHERE sysid='ndackey'")
                for row in cursor1:
                    data = row[0]
                data=unwrap(data,mine)
                data=json.loads(data)
            elif ops=='update':
                #Encrypt data and update in db
                datatodb=json.dumps(args[0])
                datatodb=wrap(datatodb,mine)
                cursor1 = conn.execute("UPDATE clndls SET intrtkndt = ? WHERE sysid = 'ndackey'",[datatodb])
                data=True
            conn.commit()
            conn.close()
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('213'))
    return data

def dataholder_profj(ops,*args):
    data = False
    try:
        if ops=='check':
            if os.access(profj_db_path,os.R_OK):
                data = True
        else:
            # CREATE DATABASE CONNECTION
            conn = sqlite3.connect(profj_db_path)
            if ops=='getMainDB':
                cursor1 = conn.execute("SELECT * FROM mainDB")
                data = []
                for row in cursor1:
                    data.append(row)
            elif ops=='getQues':
                cursor1 = conn.execute("SELECT * FROM NewQuestions")
                data = []
                for row in cursor1:
                    data.append(row)
            elif ops=='insertCapQuery':
                cursor1 = conn.executemany('INSERT INTO CapturedQueries VALUES (?,?)', [args[0]])
                data=True
            elif ops=='updateWeight':
                for i in range(len(weights)):
                    cursor1 = conn.execute('UPDATE mainDB SET Weightage= ? WHERE qid = ?',(weights[i],i))
                data=True
            conn.commit()
            conn.close()
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('223'))
    return data

def checkSetup():
    app.logger.debug("Inside Setup Check")
    global grace_period
    enndac=False
    errCode=0
    #checks if the db is already existing,
        #if exists, verifies the MAC address, if present allows further,
        #else considers the Patch is replaced in another Machine
    #else considers patch db is modified/deleted
    dbexists=dataholder('check')
    profj_dbexists=dataholder_profj('check')
    if dbexists:
        dbdata=dataholder('select')
        if dbdata:
            if('grace_period' in dbdata):
                grace_period = dbdata['grace_period']
            dbmacid=dbdata['macid']
            sysmacid=sysMAC
            if len(dbmacid)==0:
                enndac=True
                dbdata['macid']=sysmacid
                dataholder('update',dbdata)
            elif dbmacid!=sysmacid and dbmacid!="PoC".lower():
                enndac=False
                errCode='211'
            else:
                enndac=True
        else:
            enndac=False
            errCode='213'
    else:
        enndac=False
        errCode='212'

    if not profj_dbexists:
        enndac=False
        errCode='222'

    if errCode!=0:
        app.logger.error(printErrorCodes(errCode))
    return enndac

def beginserver():
    global profj_sqlitedb
    if redis_dbup and mongo_dbup:
        profj_sqlitedb = SQLite_DataSetup()
        updateWeightages() # ProfJ component
        serve(app,host='127.0.0.1',port=int(ndacport))
    else:
        app.logger.critical(printErrorCodes('207'))

def stopserver():
    global onlineuser, gracePeriodTimer
    if(gracePeriodTimer != None and gracePeriodTimer.isAlive()):
        gracePeriodTimer.cancel()
        gracePeriodTimer = None
        dbdata = dataholder('select')
        dbdata['grace_period']=0
        dataholder('update',dbdata)
    onlineuser = False
    app.logger.error(printErrorCodes('205'))

def startTwoDaysTimer():
    global twoDayTimer,gracePeriodTimer
    twoDayTimer = Timer(grace_period, stopserver)
    twoDayTimer.start()
    gracePeriodTimer = Timer(3600,saveGracePeriod)
    gracePeriodTimer.start()
    app.logger.critical("Two day timer begins...")

def saveGracePeriod():
    global gracePeriodTimer,twoDayTimer
    if (twoDayTimer.isAlive()):
        dbdata = dataholder('select')
        if('grace_period' in dbdata):
            dbdata['grace_period']=dbdata['grace_period'] - 3600
        else:
            dbdata['grace_period']=169200
        dataholder('update',dbdata)
        gracePeriodTimer = Timer(3600,saveGracePeriod)
        gracePeriodTimer.start()

################################################################################
# END OF LICENSING SERVER COMPONENTS
################################################################################

################################################################################
# BEGIN OF GENERIC FUNCTIONS
################################################################################

def initLoggers(level):
    logLevel = logging.INFO
    consoleFormat = "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s"
    if level.debug:
        logLevel = logging.DEBUG
    elif level.info:
        logLevel = logging.INFO
    elif level.warn:
        logLevel = logging.WARNING
    elif level.error:
        logLevel = logging.ERROR
    elif level.critical:
        logLevel = logging.CRITICAL
    app.debug = True
    consoleFormatter = logging.Formatter(consoleFormat)
    consoleHandler = app.logger.handlers[0]
    consoleHandler.setFormatter(consoleFormatter)
    fileFormatter = logging.Formatter('''{"timestamp": "%(asctime)s", "file": "%(module)s", "lineno.": %(lineno)d, "level": "%(levelname)s", "message": "%(message)s"}''')
    fileHandler = TimedRotatingFileHandler(logspath+'/ndac/ndac'+datetime.now().strftime("_%Y%m%d-%H%M%S")+'.log',when='d', encoding='utf-8', backupCount=1)
    fileHandler.setFormatter(fileFormatter)
    app.logger.addHandler(fileHandler)
    if level.test:
        consoleHandler.setLevel(logging.WARNING)
        fileHandler.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logLevel)
    app.logger.propagate = False
    app.logger.debug("Inside initLoggers")

def getcurrentdate():
    currentdate= datetime.now()
    beginingoftime = datetime.utcfromtimestamp(0)
    differencedate= currentdate - beginingoftime
    return int(differencedate.total_seconds() * 1000.0)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID): return str(obj)
        if isinstance(obj, datetime): return str(obj)
        if isinstance(obj, ObjectId): return str(obj)
        return json.JSONEncoder.default(self, obj)

def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')

def unpad(data):
    return data[0:-ord(data[-1])]

def unwrap(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data, 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def wrap(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex').decode('utf-8')

################################################################################
# END OF GENERIC FUNCTIONS
################################################################################

################################################################################
# Begining of ProfJ assist Components
################################################################################

class SQLite_DataSetup():
    def __init__(self):
        global questions,pages,weights,answers,keywords,pquestions,newQuesInfo
        app.logger.debug("Inside SQLite_DataSetup")
        mainDB_data=dataholder_profj("getMainDB")
        for row in mainDB_data:
            weights.append(int(row[1]))
            questions.append(row[2])
            answers.append(row[3])
            keywords.append(row[4])
            pages.append(row[5])
            pquestions.append(row[6])

        ques_data=dataholder_profj("getQues")
        for col in ques_data:
            info =[col[1],col[2],col[3]]
            newQuesInfo.append(info)

    # Function to update the captured Queries.
    def updateCaptureTable(self):
        app.logger.debug("Inside updateCaptureTable")
        status=False
        try:
            if savedQueries is not None:
                data = tuple(savedQueries)
                status=dataholder_profj("insertCapQuery",data)
        except Exception as e:
            app.logger.debug(e)
            app.logger.error(printErrorCodes("221"))
        return status


###Training the Bot
##def trainProfJ():
##    global chatbot
##    try:
##        from chatterbot import ChatBot
##        import threading
##        app.logger.debug("Starting ProfJ training")
##        chatbot = ChatBot(
##            'Prof J',
##            trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
##        )
##        #Train based on the english corpus
##        chatbot.train("chatterbot.corpus.english")
##        app.logger.debug("ProfJ training successfully completed")
##
##        #Starting chatbot training Parallely
##        threading.Thread(target = trainProfJ).start()
##    except Exception as e:
##        app.logger.debug(e)
##        app.logger.critical('Chatterbot module missing portable python')


#Updating the sqlite database
def updateWeightages():
    t=Timer(weightUpdateTime,updateWeightages)
    status=[]
    try:
        status=dataholder_profj("updateWeight")
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('220'))
    t.start()
    return status


class ProfJ():

    def __init__(self,pages,questions,answers,keywords,weights,pquestions, newQuesInfo, savedQueries):
        self.questions = questions
        self.pages = pages
        self.weights = weights
        self.answers = answers
        self.keywords = keywords
        self.pquestions = pquestions
        self.newQuesInfo = newQuesInfo
        self.topX = 5
        self.userQuery=""
        # Captures all the "Relevant" queries asked by User
        # It is list of list[[query1,page1],[query2,page2]]
        self.savedQueries = savedQueries

    def Preprocess(self,query_string):
        logging.config.fileConfig(profj_log_conf_path,disable_existing_loggers=False)
        logger = logging.getLogger("ProfJ")
        logger.info("Question asked is "+query_string)

        #Step 1: Punctuations Removal
        query1_str = "".join(c for c in query_string if c not in ('@','!','.',':','>','<','"','\'','?','*','/','&','(',')','-'))

        #Step 2: Converting string into lowercase
        query2 = [w.lower() for w in query1_str.split()]
        query2_str = " ".join(query2)

        #Step 3: Correcting appostropes.. Need this dictionary to be quite large
        APPOSTOPHES = {"s" : "is", "'re" : "are","m":"am"}
        words = (' '.join(query2_str.split("'"))).split()
        query5 = [ APPOSTOPHES[word] if word in APPOSTOPHES else word for word in words]

        #Step 4: Normalizing words
        data_file=open(profj_syn_path,"r")
        SYNONYMS = json.loads(data_file.read())
        data_file.close()
        query6 = [ SYNONYMS[word] if word in SYNONYMS else word for word in query5]

        #Step 5: Stemming
        ps = PorterStemmer()
        query_final=set([ps.stem(i) for i in query6])
        return query_final

    def matcher(self,query_final):
        intersection = []
        for q in self.pquestions:
            q1 = set (q.split(" "))
            intersection.append (len(query_final & q1))
        return intersection

    def getTopX(self,intersection):
        relevance=[]
        cnt = 0
        for i in intersection:
            relevance.append(10**(i+2) + self.weights[cnt])
            cnt+=1

        max_index = [i[0] for i in sorted(enumerate(relevance), key=lambda x:x[1],reverse=True)]
        ans = []
        for i in range(self.topX):
            if(intersection[max_index[i]]==0):
                break
            ans.append(self.questions[max_index[i]])
        return ans

    def calculateRel(self,query_final):
        f = open(profj_keywords_path ,"r")
        key = f.read()
        keywords = set(key.split())
        f.close()

        if (len(query_final)==0):
            match=0
        else:
            match=len(query_final & keywords)/float(len(query_final))
        return match

    def setState(self,state):
        self.state = state

    def start(self,userQuery):
        response = []
        query_string = userQuery
        self.userQuery = userQuery
        if query_string is not None:
            #when all the plugins will be activeted
            currPage = "mindmaps"
            query_final = self.Preprocess(query_string)
            rel = self.calculateRel(query_final)
            if (rel > 0):
                self.savedQueries=[query_string,currPage]
                intersection = self.matcher(query_final)
                ques = self.getTopX(intersection)
                if ques:
                    for i in range(len(ques)):
                        temp = []
                        temp.append(self.questions.index(ques[i]))
                        temp.append(self.questions[self.questions.index(ques[i])])
                        temp.append(self.answers[self.questions.index(ques[i])])
                        response.append(temp)
                else:
                    response = [[-1,"Sometimes, I may not have the information you need...We recorded your query..will get back to you soon",-1]]
                    flag = True
                    for nques in self.newQuesInfo:
                        if(str(query_final) is nques[1]):
                            nques[2] = nques[2] + 1
                            flag = False
                    if (flag):
                        temp1 =[str(query_string),str(query_final),0]
                        self.newQuesInfo.append(temp1)
                    #self.newKeys.append(query_string)
            else:
                response = [[-1, "Please be relevant..I work soulfully for Nineteen68", -1]]
        else:
            response = [-1, "Invalid Input...Please try again", -1]
        return response, self.newQuesInfo, self.savedQueries

################################################################################
# End of ProfJ assist components
################################################################################

################################################################################
# END OF INTERNAL COMPONENTS
################################################################################

def main():
    global lsip,lsport,ndacport,mongo_dbup,redis_dbup,chronographTimer
    global redissession,n68session
    cleanndac = checkSetup()
    if not cleanndac:
        app.logger.critical(printErrorCodes('214'))
        return False

    try:
        ndac_conf_obj = open(config_path, 'r')
        ndac_conf = json.load(ndac_conf_obj)
        ndac_conf_obj.close()
        lsip = ndac_conf['licenseserverip']
        if 'licenseserverport' in ndac_conf:
            lsport = ndac_conf['licenseserverport']
        if 'ndacserverport' in ndac_conf:
            ndacport = ndac_conf['ndacserverport']
            ERR_CODE["225"] = "Port "+ndacport+" already in use"
        if 'custChronographTimer' in ndac_conf:
            chronographTimer = int(ndac_conf['custChronographTimer'])
            app.logger.debug("'custChronographTimer' detected.")
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('218'))
        return False

    try:
        redisdb_conf = ndac_conf['cachedb']
        redisdb_pass = unwrap(redisdb_conf['password'],db_keys)
        redissession = redis.StrictRedis(host=redisdb_conf['host'], port=int(redisdb_conf['port']), password=redisdb_pass, db=3)
        if redissession.get('icesessions') is None:
            redissession.set('icesessions',wrap('{}',db_keys))
        redis_dbup = True
    except Exception as e:
        redis_dbup = False
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('217'))
        return False

    try:
        mongodb_conf = ndac_conf['nineteen68db']
        mongo_user=unwrap(mongodb_conf["username"],db_keys)
        mongo_pass=unwrap(mongodb_conf['password'],db_keys)
        client = MongoClient('mongodb://%s:%s/' % (mongodb_conf["host"],mongodb_conf["port"]),
            username = mongo_user, password = mongo_pass, authSource = 'Nineteen68',
            authMechanism = 'SCRAM-SHA-1')
        if client.server_info():
            mongo_dbup = True
        n68session = client.Nineteen68
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('206'))
        return False

    if (basecheckonls()):
        addroutes()
        err_msg = None
        try:
            resp = requests.get("http://127.0.0.1:"+ndacport)
            err_msg = printErrorCodes('225')
            if resp.content == ['Data Server Ready!!!', 'Data Server Stopped!!!']:
                err_msg = printErrorCodes('224')
            app.logger.critical(err_msg)
        except:
            pass
        if err_msg is None:
            chronograph()
            beginserver()
    else:
        app.logger.critical(printErrorCodes('218'))

if __name__ == '__main__':
    initLoggers(parserArgs)
    sysMAC = str(getMacAddress()).strip()
    main()
