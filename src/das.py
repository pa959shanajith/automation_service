#-------------------------------------------------------------------------------
# Name:        das.py
# Purpose:     Security Aspects, Licensing components and ProfJ
#
# Created:     10/07/2017
# Copyright:   (c) vishvas.a 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
import os
import re
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

currexc = sys.executable
try: currfiledir = os.path.dirname(os.path.abspath(__file__))
except: currfiledir = os.path.dirname(currexc)
currdir = os.getcwd()
if os.path.basename(currexc).startswith("AvoAssureDAS"):
    currdir = os.path.dirname(currexc)
elif os.path.basename(currexc).startswith("python"):
    currdir = currfiledir
    needdir = "das_internals"
    parent_currdir = os.path.abspath(os.path.join(currdir,".."))
    if os.path.isdir(os.path.abspath(os.path.join(parent_currdir,"..",needdir))):
        currdir = os.path.dirname(parent_currdir)
    elif os.path.isdir(parent_currdir + os.sep + needdir):
        currdir = parent_currdir
internalspath = currdir + os.sep + "das_internals"
config_path = currdir + os.sep + "server_config.json"
assistpath = internalspath + os.sep + "assist"
logspath = internalspath + os.sep + "logs"
verpath = internalspath + os.sep + "version.txt"
credspath = internalspath + os.sep + ".tokens"
gitpath = os.path.normpath(currdir + "/Lib/portableGit/cmd/git.exe")

das_ver = "3.0"
if os.path.isfile(verpath):
    with open(verpath) as vo:
        das_ver = vo.read().replace("\n", "").replace("\r", "")
        vo.close()

parser = argparse.ArgumentParser(description="Avo Assure Data Access Server - Help")
parser.add_argument("-v", "--version", action="version", version="Avo Assure DAS "+das_ver, help="Show Avo Assure DAS version information")
# dbcred_group = parser.add_argument_group("Arguments to store database credentials")
# dbcred_group.add_argument("-db", "--database", type=str, choices=["avoassuredb", "cachedb"], help="Database name")
# dbcred_group.add_argument("--username", type=str, help="Username for database")
# dbcred_group.add_argument("--password", type=str, help="Password for database")
subparsers = parser.add_subparsers(title="Arguments to store database credentials", dest="database",
    help="Available databases. Run `%(prog)s <database> -h` for more database specific options")
parser_dbmain = subparsers.add_parser('avoassuredb', description="Avo Assure Data Access Server - Primary Database Credential Store - Help")
parser_dbmain.add_argument("--username", type=str, required=True, metavar="username", help="Username for Avo Assure database")
parser_dbmain.add_argument("--password", type=str, required=True, metavar="password", help="Password for Avo Assure database")
parser_dbcache = subparsers.add_parser('cachedb', description="Avo Assure Data Access Server - Cache Database Credential Store - Help")
parser_dbcache.add_argument("--password", type=str, required=True, metavar="password", help="Password for Cache database")
log_group = parser.add_mutually_exclusive_group()
log_group.add_argument("-T", "--test", action="store_true", help="Set logger level to Test Environment")
log_group.add_argument("-D", "--debug", action="store_true", help="Set logger level to Debug")
log_group.add_argument("-I", "--info", action="store_true", help="Set logger level to Info")
log_group.add_argument("-W", "--warn", action="store_true", help="Set logger level to Warning")
log_group.add_argument("-E", "--error", action="store_true", help="Set logger level to Error")
log_group.add_argument("-C", "--critical", action="store_true", help="Set logger level to Critical")
parserArgs = parser.parse_args()

ice_das_key = "".join(['a','j','k','d','f','i','H','F','E','o','w','#','D','j',
    'g','L','I','q','o','c','n','^','8','s','j','p','2','h','f','Y','&','d'])
db_keys = "".join(['N','i','n','E','t','e','E','n','6','8','d','A','t','a','B',
    'A','s','3','e','N','c','R','y','p','T','1','0','n','k','3','y','S'])
ldap_key = "".join(['l','!','g','#','t','W','3','l','g','G','h','1','3','@','(',
    'c','E','s','$','T','p','R','0','T','c','O','I','-','k','3','y','S'])
activeicesessions={}
latest_access_time=datetime.now()
ip_regex = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"


lsport = "5000"
dasport = "1990"
redis_dbup = False
mongo_dbup = False
expiryTime=None
licenseServer=None
licensedata=None
LS_CRITICAL_ERR_CODE=['199','120','121','123','124','125']
webPluginList = {
				"MR":"reports","MD":"dashboard","ALMDMT":"integration","STAVO":"seleniumtoavo",
				"DE":"utility","WEBT":"web","APIT":"webservice","MOBT":"mobileapp","ETOAP":"oebs",
				"DAPP":"desktop","MF":"mainframe","ETSAP":"sap","MOBWT":"mobileweb"
			}
dbsession=redissession=redissession_db2=redissession_db0=client=None


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
    msg = 'Data Server Ready!!!'
    return msg

@app.route('/version')
def version_info():
    msg = 'Avo Assure Data Access Service v'+das_ver
    return msg


################################################################################
# BEGIN OF SERVICES IMPORT
################################################################################

from utils import *
setenv(flaskapp=app)
sys.path.append(currfiledir+os.sep+"routes")
sys.path.append(currfiledir+os.sep+"utility")

def addroutes():
    app.logger.debug("Loading services")

    import licenseManager
    licenseManager.LoadServices(app, redissession_db0, client,getClientName,licensedata)

    import loginservice
    loginservice.LoadServices(app, redissession, client, licensedata,basecheckonls,getClientName)

    import adminservice
    adminservice.LoadServices(app, redissession, client, getClientName,licensedata, ice_das_key, ldap_key)

    import mindmapservice
    mindmapservice.LoadServices(app, redissession, client,getClientName)

    import devopsservice
    devopsservice.LoadServices(app, redissession, client,getClientName)
    
    if os.path.exists(gitpath):
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = gitpath
        import gitservice
        gitservice.LoadServices(app, redissession, client ,getClientName , ldap_key)

    import designscreenservice
    designscreenservice.LoadServices(app, redissession, client,getClientName)

    import designtestcaseservice
    designtestcaseservice.LoadServices(app, redissession, client,getClientName)

    import executionservice
    executionservice.LoadServices(app, redissession, client,getClientName)

    import thirdpartyservice
    thirdpartyservice.LoadServices(app, redissession, client ,getClientName, ldap_key)

    import reportsservice
    reportsservice.LoadServices(app, redissession, client,getClientName)

    import utilitiesservice
    utilitiesservice.LoadServices(app, redissession, client,getClientName)

    import neurongraphsservice
    neurongraphsservice.LoadServices(app, redissession, client,getClientName)
    
    import benchmarkservice
    benchmarkservice.LoadServices(app,redissession,client,getClientName)

    import partitionservice
    partitionservice.LoadServices(app,redissession,client,getClientName)

    import notificationservice
    notificationservice.LoadServices(app,redissession,client,getClientName)

################################################################################
# END OF SERVICES IMPORT
################################################################################

@app.route('/server',methods=['POST'])
def checkServer():
    app.logger.debug("Inside checkServer")
    response = "fail"
    status = 500
    try:
        response = json.dumps({"st":"pass"})
        status = 200
    except Exception as exc:
        servicesException("checkServer",exc)
    return Response(response, status, mimetype='text/plain')

@app.route('/server/updateActiveIceSessions',methods=['POST'])
def updateActiveIceSessions():
    global activeicesessions
    global latest_access_time
    global webPluginList
    res = {"id":"","res":"fail","ts_now":str(datetime.now()),"connect_time":str(datetime.now()),
        "plugins":"","data":random.random()*100000000000000}
    response = {"node_check":False,"ice_check":wrap(json.dumps(res),ice_das_key)}
    ice_uuid = None
    ice_ts = None
    try:
        requestdata = json.loads(request.data)
        app.logger.debug("Inside updateActiveIceSessions. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            clientName=getClientName(requestdata)      
            dbsession=client[clientName]
            sess = redissession.get('icesessions')
            if sess == '' or sess is None:
                redissession.set('icesessions',wrap('{}',db_keys))
            r_lock = redissession.lock('icesessions_lock')
            if(requestdata['query'] == 'disconnect'):
                icename=requestdata['icename'].lower()
                with r_lock:
                    activeicesessions=json.loads(unwrap(redissession.get('icesessions'),db_keys))
                    if icename in activeicesessions:
                        del activeicesessions[icename]
                        redissession.set('icesessions',wrap(json.dumps(activeicesessions),db_keys))
                res['res'] = "success"

            elif(requestdata['query']=='connect' and 'icesession' in requestdata):
                icesession = unwrap(requestdata['icesession'],ice_das_key)
                icesession = json.loads(icesession)
                ice_action = icesession["iceaction"]
                ice_token_dec = icesession["icetoken"]
                hostname = ice_token_dec["hostname"]
                ice_token = ice_token_dec["token"]
                ice_name = ice_token_dec["icename"]
                ice_type = ice_token_dec["icetype"]
                ice_uuid = icesession['ice_id']
                ice_ts = icesession['connect_time']
                if('.' not in ice_ts): ice_ts = ice_ts + '.000000'
                latest_access_time = datetime.strptime(ice_ts, '%Y-%m-%d %H:%M:%S.%f')
                app.logger.debug("icename: "+ice_name+" / time: "+str(latest_access_time))
                res['id']=ice_uuid
                res['connect_time'] = icesession['connect_time']
                # ICE which are in "deregistered" status are eliminated for the Registration and Connection
                queryresult = dbsession.icetokens.find_one({"icename":ice_name,"token":ice_token,"icetype":ice_type})
                if queryresult is None:
                    res['err_msg'] = "Unauthorized: Access denied due to Invalid Token"
                    response["node_check"] = res['status'] = "InvalidToken"
                else:
                    ice_status = queryresult["status"]
                    # Register Phase
                    if ice_action == REGISTER:
                        if ice_status != PROVISION_STATUS:
                            response["node_check"] = res['status'] = "InvalidICE"
                            if ice_status == REGISTER_STATUS:
                                res['err_msg'] = "Access denied: Token already used!"
                            else:
                                res['err_msg'] = "Access denied: Token is expired!"
                        else:
                            dbsession.icetokens.update_one({"token":ice_token},{"$set":{"hostname":hostname,"registeredon":datetime.now(),"status":REGISTER_STATUS}})
                            response["node_check"] = res['status'] = "validICE"
                    # Connection Phase
                    else:
                        if ice_action == REGISTER_CONNECT:   # Guest mode connection
                            if ice_status == PROVISION_STATUS: ice_status = REGISTER_STATUS

                        username = None
                        # To allow the connection, check for registered state of ICE
                        if ice_status == REGISTER_STATUS:
                            lsData=dbsession.licenseManager.find_one({"client":clientName})['data']
                            #If icetype=="normal" , map username-->icename , else if icetype=="ci-cd" map icetoken-->icename
                            if ice_type == "normal": 
                                username = dbsession.users.find_one({"_id":queryresult["provisionedto"]},{"name":1})
                                if username is not None: username = username['name']
                            elif ice_type == "ci-cd":
                                username = ice_name
                            if username:
                                res['status'] = "allow"
                                f_allow = False
                                with r_lock:
                                    activeicesessions=json.loads(unwrap(redissession.get('icesessions'),db_keys))
                                    # Remove stale sessions
                                    ice_statuses = json.loads(redissession_db2.get("ICE_status"))
                                    for ice in list(activeicesessions.keys()):
                                        if ice not in ice_statuses or ice_statuses[ice]['connected'] == False: activeicesessions.pop(ice)
                                    # To ensure another ICE with same name is not connected already
                                    if ice_name in activeicesessions and activeicesessions[ice_name] != ice_uuid:
                                        res['err_msg'] = "Connection exists with same token"
                                    # To check if license is available
                                    elif str(lsData['USER']) != "Unlimited":
                                        if len(activeicesessions) >= int(lsData['USER']):
                                            res['err_msg'] = "All ice sessions are in use"
                                    # To add in active ice sessions
                                    else:
                                        activeicesessions[ice_name] = ice_uuid
                                        redissession.set('icesessions', wrap(json.dumps(activeicesessions),db_keys))
                                        f_allow = True
                                if f_allow:
                                    res['res'] = "success"
                                    response["node_check"] = "allow"
                                    response["username"] = username
                                    ice_plugins_list = []
                                    for key in lsData:
                                        if key in webPluginList:
                                            ice_plugins_list.append(webPluginList[key])
                                    res["plugins"] = ice_plugins_list
                                    res["license_data"] = lsData
                            else:
                                res['err_msg'] = ice_name+" is not Registered with a valid Avo Assure User"
                                response["node_check"] = res['status'] = "InvalidICE"
                                app.logger.error(res['err_msg'])
                        else:
                            if ice_status == DEREGISTER_STATUS:
                                res['err_msg'] = "Access denied: Token is expired! Re-register to connect again."
                            else:
                                res['err_msg'] = "Access denied: ICE is not in Registered state"
                            response["node_check"] = res['status'] = "InvalidICE"
                            app.logger.error("%s : ICE is not in Registered state ", ice_name)
                response["ice_check"] = wrap(json.dumps(res),ice_das_key)
            app.logger.debug("Connected clients: "+str(list(activeicesessions.keys())))
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

def getreports_in_day(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(dbsession.reports.find({'executedtime':{'$gt': bgnts, '$lte': endts}}))
        res = {'rows':queryresult}
    except Exception as getreports_in_dayexc:
        servicesException("getreports_in_day",getreports_in_dayexc)
    return res

def getsuites_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(dbsession.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testsuites'}))
        res = {"rows":queryresult}
    except Exception as getsuites_inititatedexc:
        servicesException("getsuites_inititated",getsuites_inititatedexc)
    return res

def getscenario_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(dbsession.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testscenarios'}))
        res = {"rows":queryresult}
    except Exception as getscenario_inititatedexc:
        servicesException("getscenario_inititated",getscenario_inititatedexc)
    return res

def gettestcases_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        queryresult = list(dbsession.counters.find({'counterdate':{'$gt': bgnts, '$lte': endts}, 'countertype':'testcases'}))
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

def getClientName(requestdata):
    global licenseServer
    clientName="avoassure"
    try:
        if ('DB_NAME' in os.environ):
            clientName=os.environ['DB_NAME']
    except Exception as e:
        app.logger.error(e)
        app.logger.error('Error while fetching client name')

    return clientName


def basecheckonls():
    app.logger.debug("Inside basecheckonls")
    global licensedata,expiryTime,licenseServer
    basecheckstatus = False
    try:
        if not licenseServer["enable"] :
            from licenseManager import getLSData
            licensedata=getLSData(licenseServer["path"])
            if licensedata != False:
                basecheckstatus = True
            else:
                basecheckstatus = False
            expiryDate=licensedata["ExpiresOn"].split('/')
            expiryDate=datetime(int(expiryDate[2]), int(expiryDate[0]), int(expiryDate[1]))
            if expiryTime == None:
                expiryTime=expiryDate
                basecheckstatus = True
            basecheckstatus = True    
        else:
            licensedata={"licenseServer":licenseServer["url"]}
            basecheckstatus = True
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('201'))
    return basecheckstatus



def beginserver(host = '127.0.0.1', **kwargs):
    if redis_dbup and mongo_dbup:
        serve(app,host=host,port=int(dasport),**kwargs)
    else:
        app.logger.critical(printErrorCodes('207'))

def stopserver():
    app.logger.error(printErrorCodes('205'))


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
    fileHandler = TimedRotatingFileHandler(logspath+'/das/das'+datetime.now().strftime("_%Y%m%d-%H%M%S")+'.log',when='d', encoding='utf-8', backupCount=1)
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
# END OF INTERNAL COMPONENTS
################################################################################

def main():
    global lsport,dasport,mongo_dbup,redis_dbup,licenseServer,client
    global redissession,dbsession,redissession_db2,redissession_db0
    das_conf_obj = open(config_path, 'r')
    das_conf = json.load(das_conf_obj)
    das_conf_obj.close()
    licenseServer=das_conf['licenseServer']
    creds = {}
    kwargs = {}

    # Save default database credentials if not intitalized
    if not os.path.isfile(credspath):
        with open(credspath, 'w') as creds_file:
            creds_file.write("4d402de9a971543fa56214f3ca955efc4938f277bbb1293"+
                "9108f140928ec4be44c68b05587ee183b92a885febacafc2ac4f70f42ffe"+
                "f002fa21a2a0efa7d0dbdb54e1bf8e98e4a07aae7ea8b3c92f7f2b2cc620"+
                "de26a00869fbc83a6202f685fb5756d9bbb987bb884f20e51f4d4966b160"+
                "c958afbc11e3f1b1a60ba57d17394d4984b5a0b76ddedb17dbf14811126d"+
                "93d288ebdd863231592eee2107b7d4cd37bbdae25684b5ee4e02e07f9ef7"+
                "4ff4b")

    # Load database credentials
    try:
        with open(credspath) as creds_file:
            creds = json.loads(unwrap(creds_file.read(),db_keys))
        _ = creds['cachedb']['password'] + creds['avoassuredb']['username'] + creds['avoassuredb']['password']
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('226'))
        os.remove(credspath)
        return False

    # Set database credentials and exit program
    if parserArgs.database is not None:
        db = parserArgs.database
        if db == 'avoassuredb':
            username = parserArgs.username
            password = parserArgs.password
            if username is None or len(username) == 0:
                parser.error('--username cannot be empty')
            else:
                creds[db]['username'] = username
            if password is None or len(password) == 0:
                parser.error('--password cannot be empty')
            else:
                creds[db]['password'] = password
        elif db == 'cachedb':
            password = parserArgs.password
            if password is None or len(password) == 0:
                parser.error('--password cannot be empty')
            else:
                creds[db]['password'] = password
        else:
            parser.error("Database name has to be 'avoassuredb' or 'cachedb'")
        creds_file = open(credspath, 'w')
        creds_file.write(wrap(json.dumps(creds), db_keys))
        creds_file.close()
        app.logger.info("Credentials stored for "+db+" database")
        return True

    try:
        if 'licenseserverport' in das_conf:
            lsport = das_conf['licenseserverport']
        if 'dasserverip' in das_conf:
            host = das_conf['dasserverip']
            if not re.match(ip_regex, host):
                kwargs['host'] = host
        if 'dasserverport' in das_conf:
            dasport = das_conf['dasserverport']
            ERR_CODE["225"] = "Port "+dasport+" already in use"
        if 'processthreads' in das_conf:
            kwargs['threads'] = int(das_conf['processthreads'])
        if 'connectionlimit' in das_conf:
            kwargs['backlog'] = int(das_conf['connectionlimit'])
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('218'))
        return False

    try:
        redisdb_conf = das_conf['cachedb']
        redisdb_pass = creds['cachedb']['password']
        redissession = redis.StrictRedis(host=redisdb_conf['host'], port=int(redisdb_conf['port']), password=redisdb_pass, db=3)
        redissession_db2 = redis.StrictRedis(host=redisdb_conf['host'], port=int(redisdb_conf['port']), password=redisdb_pass, db=2)
        redissession_db0 = redis.StrictRedis(host=redisdb_conf['host'], port=int(redisdb_conf['port']), password=redisdb_pass, db=0)

        if redissession.get('icesessions') is None:
            redissession.set('icesessions',wrap('{}',db_keys))
        if redissession_db2.get("ICE_status") is None:
            redissession_db2.set("ICE_status", '{}')
        redis_dbup = True
    except Exception as e:
        redis_dbup = False
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('217'))
        return False

    try:
        mongodb_conf = das_conf['avoassuredb']
        mongo_user= unwrap(mongodb_conf['username'],db_keys)
        mongo_pass= unwrap(mongodb_conf['password'],db_keys)
        if ('DB_IP' in os.environ and 'DB_PORT' in os.environ):
            hosts = [str(os.environ['DB_IP']) + ':' + str(os.environ['DB_PORT'])]
        else:
            hosts = [mongodb_conf["host"] + ':' + str(mongodb_conf["port"])]
        client = MongoClient(hosts, username = mongo_user, password = mongo_pass,authSource = 'admin', 
            appname = 'AvoAssureDAS', authMechanism = 'SCRAM-SHA-1')
        if client.server_info():
            mongo_dbup = True
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('206'))
        return False

    if (basecheckonls()):
        addroutes()
        err_msg = None
        try:
            resp = requests.get("http://127.0.0.1:"+dasport)
            err_msg = printErrorCodes('225')
            if resp.content == ['Data Server Ready!!!', 'Data Server Stopped!!!']:
                err_msg = printErrorCodes('224')
            app.logger.critical(err_msg)
        except:
            pass
        if err_msg is None:
            beginserver(**kwargs)
    else:
        app.logger.critical(printErrorCodes('218'))

if __name__ == '__main__':
    initLoggers(parserArgs)
    main()
