from flask import jsonify, request, make_response
from bson.objectid import ObjectId
import flask
import json
import traceback
import statistics 
import numpy as np 
from datetime import datetime, timedelta
import time
import uuid
import string
import random

NORMAL="normal"
CICD="ci-cd"
REGISTER_CONNECT="guestconnect"
REGISTER="register"
DEREGISTER="deregister"
PROVISION="provision"
REGISTER_STATUS="registered"
PROVISION_STATUS="provisioned"
DEREGISTER_STATUS="deregistered"

dasport = "1990"

ui_plugins = {"alm":"Integration","apg":"APG","dashboard":"Dashboard",
    "mindmap":"Mindmap","neurongraphs":"Neuron Graphs","performancetesting":"Performance Testing",
    "reports":"Reports","utility":"Utility","weboccular":"Webocular","seleniumtoavo":"Selenium To Avo", "avodiscover": "Avo Discover", "iTDM" : "iTDM"}

projecttype_names={}

ERR_CODE={
    "201":"Error while registration with LS",
    "202":"Error while pushing update to LS",
    "203":"Avo Assure DAS is stopped. Issue - Licensing Server is offline",
    "204":"Avo Assure DAS is stopped. Issue - Offline license expired",
    "205":"Avo Assure DAS is stopped due to license expiry or loss of connectivity",
    "206":"Error while establishing connection to Avo Assure Database",
    "207":"Database connectivity Unavailable",
    "208":"License server must be running",
    "209":"Critical Internal Exception occurred",
    "210":"Critical Internal Exception occurred: updateData",
    "211":"Another instance of Avo Assure DAS is already registered with the License server",
    "212":"Unable to contact storage areas",
    "213":"Critical error in storage areas",
    "214":"Please contact Team - Avo Assure. Setup is corrupted",
    "215":"Error while establishing connection to Licensing Server. Retrying to establish connection",
    "216":"Connection to Licensing Server failed. Maximum retries exceeded. Hence, Shutting down server",
    "217":"Error while establishing connection to Redis",
    "218":"Invalid configuration file",
    "219":"Please contact Team - Avo Assure. Error while starting Avo Assure DAS",
    "220":"Error occured in assist module: Update weights",
    "221":"Error occured in assist module: Update queries",
    "222":"Unable to contact storage areas: Assist Components",
    "223":"Critical error in storage areas: Assist Components",
    "224":"Another instance of Avo Assure DAS is already running",
    "225":"Port "+dasport+" already in use",
    "226":"Invalid database credentials. Re-enter database credentials using commands. Please refer help command using -h/--help"
}


ecodeServices = {
    "loadUser": "300",
    "loadPermission": "301",
    "loadUserInfo": "304",
    "getReleaseIDs": "305",
    "getCycleIDs": "306",
    "getProjectType": "307",
    "getProjectIDs": "308",
    "getAllNames_ICE": "309",
    "testsuiteid_exists_ICE": "310",
    "testscenariosid_exists_ICE": "311",
    "testscreenid_exists_ICE": "312",
    "testcaseid_exists_ICE": "313",
    "get_node_details_ICE": "314",
    "delete_node_ICE": "315",
    "insertInSuite_ICE": "316",
    "insertInScenarios_ICE": "317",
    "insertInScreen_ICE": "318",
    "insertInTestcase_ICE": "319",
    "updateTestScenario_ICE": "320",
    "updateModule_ICE": "321",
    "updateModulename_ICE": "322",
    "updateTestscenarioname_ICE": "323",
    "updateScreenname_ICE": "324",
    "updateTestcasename_ICE": "325",
    "submitTask": "326",
    "getKeywordDetails": "327",
    "readTestCase_ICE": "328",
    "getScrapeDataScreenLevel_ICE": "329",
    "debugTestCase_ICE": "330",
    "updateScreen_ICE": "331",
    "updateTestCase_ICE": "332",
    "getTestcaseDetailsForScenario_ICE": "333",
    "getTestcasesByScenarioId_ICE": "334",
    "readTestSuite_ICE": "335",
    "updateTestSuite_ICE": "336",
    "ExecuteTestSuite_ICE": "337",
    "ScheduleTestSuite_ICE": "338",
    "qcProjectDetails_ICE": "339",
    "saveQcDetails_ICE": "340",
    "viewQcMappedList_ICE": "341",
    "getUserRoles": "342",
    "getDetails_ICE": "343",
    "getNames_ICE": "344",
    "getDomains_ICE": "345",
    "getAssignedProjects_ICE": "346",
    "manageUserDetails": "347",
    "getUserDetails": "348",
    "manageLDAPConfig": "349",
    "createProject_ICE": "350",
    "updateProject_ICE": "351",
    "getUsers": "352",
    "assignProjects_ICE": "353",
    "getLDAPConfig": "354",
    "getAvailablePlugins": "355",
    "getAllSuites_ICE": "356",
    "getSuiteDetailsInExecution_ICE": "357",
    "reportStatusScenarios_ICE": "358",
    "getReport": "359",
    "exportToJson_ICE": "360",
    "createHistory": "361",
    "encrypt_ICE": "362",
    "dataUpdator_ICE": "363",
    "userAccess": "364",
    "checkServer": "365",
    "updateActiveIceSessions": "366",
    "counterupdator": "367",
    "getreports_in_day": "368",
    "getsuites_inititated": "369",
    "getscenario_inititated": "370",
    "gettestcases_inititated": "371",
    "modelinfoprocessor": "372",
    "dataprocessor": "373",
    "reportdataprocessor": "374",
    "getTopMatches_ProfJ": "375",
    "updateFrequency_ProfJ": "376",
    "updateReportData": "377",
    "updateIrisObjectType": "378",
    "authenticateUser_CI": "379",
    "generateCIusertokens": "380",
    "getCIUsersDetails": "381",
    "deactivateCIUser": "382",
    "saveMindmap": "383",
    "getModules": "384",
    "manageTaskDetails": "385",
    "fetchICE": "386",
    "provisionICE": "387",
    "getSAMLConfig": "388",
    "manageSAMLConfig": "389",
    "getOIDCConfig": "390",
    "manageOIDCConfig": "391",
    "update_execution_times": "392",
    "write_execution_times": "393",
    "fetchICEUser": "394",
    "getPreferences": "395",
    "getReport_API": "396",
    "manageNotificationChannels": "397",
    "getNotificationChannels": "398",
    "exportProject": "399",
    "exportMindmap": "400",
    "importMindmap": "401",
    "checkTandC": "402",
    "updateMapDetails_ICE": "403",
    "getReport_NG": "405",
    "getReportExecutionStatus_NG": "406",
    "updatePool_ICE":"407",
    "getPools":"408",
    "getICE_userid":"409",
    "getICE_pools":"410",
    "getAvailable_ICE":"411",
    "deleteICE_pools":"412",
    "getAll_projects":"413",
    "getUnassgined_ICE":"414",
    "createPool_ICE":"415",
    "updateScenario":"416",
    "getAccessibilityReports_API":"417",
    "getAccessibilityTestingData_ICE":"418",
    "invalidCredCounter": "419",
    "passtimeout": "420",
    "forgotPasswordEmail": "421",
    "unlockAccountEmail": "422",
    "fetchLockedUsers": "423",
    "unlockUser": "424",
    "getExecution_metrics_API":"425",
    "importFromGit_ICE":"426",
    "exportToGit":"427",
    "gitSaveConfig":"428",
    "gitEditConfig":"429",
    "importGitMindmap":"430",
    "manageDataTable":"431",
    "getDatatableDetails":"432",
    "importDtFromExcel":"433",
    "importDtFromCSV":"434",
    "importDtFromXML":"435",
    "exportToDtExcel":"436",
    "exportToDtCSV":"437",
    "exportToDtXML":"438",
    "getDetails_JIRA":"439",
    "manageJiraDetails":"440",
    "getNotificationGroups":"441",
    "updateNotificationGroups":"442",
    "getNotificationRules":"443",
    "updateNotificationConfiguration":"444",
    "getNotificationConfiguration":"445",
    "updateTaskRules":"446",
    "avoDiscoverMap":"447",
    "avoDiscoverReset":"448",
    "fetchAvoDiscoverMap":"449",
    "getMappedDiscoverUser":"450",
    "fetchReplacedKeywords_ICE":"451",
    "manageZephyrDetails":"452",
    "getDetails_Zephyr":"453",
    "configureKey" : "454",
    "getTestSuite": "455",
    "getAgents": "456",
    "executionList":'457',
    "agentDetails":'458',
    "getExecScenario":'459',
    "getScenariosForDevops":'460',
    "getConfigureList":'461',
    "saveAvoGrid": '462',
    "saveAvoAgent":'463',
    "deleteConfigureKey": '464',
    "getAvoAgentAndAvoGridList": '465',
    "fetchModuleListDevopsReport": '466',
    "deleteAvoGrid": '467',
    "verifyUser":"468",
    "deleteScenario": "469",
    "getDetails_SAUCELABS":"470",
    "manageSaucelabsDetails":"471",
    "getDetails_Azure":"472",
    "manageAzureDetails":"473"
}


EXEMPTED_SERVICES = ["checkUser", "validateUserState", "loadUserInfo", "logoutUser",
  "ExecuteTestSuite_ICE_SVN", "getReport_API", "ICE_provisioning_register", "verifyUser"]


def setenv(flaskapp=None):
    global app
    if flaskapp is not None: app = flaskapp

def printErrorCodes(ecode):
    msg = "[ECODE: " + ecode + "] " + ERR_CODE[ecode]
    return msg

def servicesException(srv, exc, trace=False):
    app.logger.debug("Exception occured in "+srv)
    app.logger.error(exc)
    if trace: app.logger.debug(traceback.format_exc())
    app.logger.error("[ECODE: " + ecodeServices[srv] + "] Internal error occured in api")

def isemptyrequest(requestdata):
    flag = False
    for key in requestdata:
        if (key not in ['additionalroles', 'getparampaths', 'testcasesteps'] and
            requestdata[key] in ['undefined', '', 'null', None]):
            app.logger.warn(str(key)+" is empty")
            flag = True
    return flag

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

def counterupdator(dbsession,updatortype,userid,count):
    status=False
    try:
        filter_query = {"counterdate":getupdatetime(), "countertype":updatortype, "userid":userid} 
        result = dbsession.counters.update_one(filter_query, {"$inc":{"counter":count}}, upsert= True)
        status = result.modified_count != 0 or result.upserted_id is not None
    except Exception as counterupdatorexc:
        servicesException("counterupdator",counterupdatorexc)
    return status

def get_random_string():
    chargroup = string.ascii_letters + string.digits 
    random_string = [random.choice(chargroup) for _ in range(8)]
    return "".join(random_string)

def update_execution_times(dbsession,app):
    app.logger.info("Updating Execution Times")
    resultdict = {}
    try:
        result = dbsession.reports.aggregate([
                    { '$lookup':{
                            'from': 'reportitems',
                            'let': { 'pid': '$reportitems' },
                            'pipeline': [
                                { '$match': { '$expr': { '$in': ['$_id','$$pid']}}},
                                {'$unwind':'$rows'},
                                { '$group': { "_id": None, 'rows': { '$push': '$rows' } } } ,
                                { '$project': {  'rows': { '$size': "$rows" } } }
                            ],
                            'as':'rowitems'
                        }
                    },
                    { '$project': {"testscenarioid":1,"overallstatus":1,"status":1,"rowlen":{'$arrayElemAt':['$rowitems.rows',0]} }}
                ])
        for res in result:
            try:
                key = str(res['testscenarioid'])
                if key in resultdict:
                    if 'overallstatus' in res:
                        ostatus = res['overallstatus']
                        statuskey = 'overallstatus'
                        if(res['status'].lower() == 'pass' or res['status'].lower() == 'fail'  ):
                            etime = ostatus['EllapsedTime']
                            if "days" in etime:
                                etime = etime.replace(" days, ",":").split(':')
                                time_sec = float((etime[0]))*86400 + float((etime[1]))*3600 + float((etime[2]))*60 + float((etime[3]))
                            elif "day" in etime:
                                etime = etime.replace(" day, ",":").split(":")
                                time_sec = float((etime[0]))*86400 + float((etime[1]))*3600 + float((etime[2]))*60 + float((etime[3]))
                            else:
                                etime = etime.strip("~").split(":")
                                time_sec = float((etime[0]))*3600 + float((etime[1]))*60 + float((etime[2]))
                            if time_sec >= resultdict[key]['max']:
                                resultdict[key]['max'] = time_sec
                                resultdict[key]['max_status'] = ostatus[statuskey]
                            if time_sec <= resultdict[key]['min']:
                                resultdict[key]['min'] = time_sec
                                resultdict[key]['min_status'] = ostatus[statuskey]
                            resultdict[key]['timearr'].append(time_sec)
                            resultdict[key]['steps'] = res['rowlen']
                else:
                    if "overallstatus" in res:
                        ostatus = res['overallstatus']
                        statuskey = 'overallstatus'
                        if(res['status'].lower() == 'pass' or res['status'].lower() == 'fail'):
                            etime = ostatus['EllapsedTime']
                            if "days" in etime:
                                etime = etime.replace(" days, ",":").split(':')
                                time_sec = float((etime[0]))*86400 + float((etime[1]))*3600 + float((etime[2]))*60 + float((etime[3]))
                            elif "day" in etime:
                                etime = etime.replace(" day, ",":").split(':')
                                time_sec = float((etime[0]))*86400 + float((etime[1]))*3600 + float((etime[2]))*60 + float((etime[3]))
                            else:
                                etime = etime.strip("~").split(":")
                                time_sec = float((etime[0]))*3600 + float((etime[1]))*60 + float((etime[2]))
                            resultdict[key] = {}
                            resultdict[key]['max_status'] = ostatus[statuskey]
                            resultdict[key]['min_status'] = ostatus[statuskey]
                            resultdict[key]['timearr'] = []
                            resultdict[key]['min'] = time_sec
                            resultdict[key]['max'] = time_sec
                            resultdict[key]['timearr'].append(time_sec)
                            resultdict[key]['steps'] = res['rowlen']
            except Exception as e:
                servicesException("update_execution_times",e,True)
                continue
        app.logger.debug("Updating Database for Execution times")
        write_execution_times(resultdict,dbsession)
        app.logger.debug("Update Execution times completed")
        return
    except Exception as e:
        servicesException("update_execution_times",e,True)
        return

def write_execution_times(resultdict,dbsession):
    try:
        i = 0
        for key in resultdict:
            i = i + 1
            data = resultdict[key]
            if len(data['timearr']) > 3:
                data['timearr'].sort()
                minVal = data['timearr'][0]
                maxVal = data['timearr'][len(data['timearr'])-1]
                data['timearr'] = list(filter((maxVal).__ne__, data['timearr']))
                data['timearr'] = list(filter((minVal).__ne__, data['timearr']))  
                if data['timearr'] is not None:
                    if len(data['timearr']) > 1:
                        median_data = statistics.median(data['timearr'])
                        tfive = np.percentile(data['timearr'], 25)
                        sfive = np.percentile(data['timearr'], 75)
                        data['timearr'].sort()
                        minVal = data['timearr'][0]
                        maxVal = data['timearr'][len(data['timearr'])-1]
                        minCount = data['timearr'].count(data['timearr'][0])
                        maxCount = data['timearr'].count(data['timearr'][len(data['timearr'])-1])
                        avg = statistics.mean(data['timearr'])
                        count = len(data['timearr'])
                    elif len(data['timearr']) == 1:
                        median_data = "N/A"
                        tfive = "N/A"
                        sfive = "N/A"
                        count = 1
                        avg = data['timearr'][0]
                        minVal = data['timearr'][0]
                        maxVal = data['timearr'][0]
                    else:
                        continue
                else:
                    median_data = "N/A"
                    tfive = "N/A"
                    sfive = "N/A"
                    data['max'] = "N/A"
                    data['min'] = "N/A"
                    data['count'] = 0
            else:
                continue 
            try:
                sd = statistics.stdev(data['timearr'])
            except Exception as e:
                sd = "N/A"
            resdata = {"testscnearioid":key,"mean":avg,"median":median_data,"count":count,"standarDeviation":sd,"min":minVal,"minCount":minCount,"max":maxVal,"maxCount":maxCount,"25th Percentile":tfive,"75th Percentile":sfive,"time":datetime.utcnow()}
            result = dbsession.executiontimes.find({"testscenarioid": key})
            if result and result.count() > 0:
                dbsession.executiontimes.update_one({"_id":result[0]["_id"]},{"$set":{"testscnearioid":key,"mean":avg,"median":median_data,"count":count,"standarDeviation":sd,"min":minVal,"minCount":minCount,"max":maxVal,"maxCount":maxCount,"25th Percentile":tfive,"75th Percentile":sfive,"time":datetime.utcnow()}})
            else:
                dbsession.executiontimes.insert_one(resdata)

        return
    except Exception as e:
        servicesException("write_execution_times",e,True)
        return

def valid_objectid(oid):
    try:
        ObjectId(oid)
        return True
    except Exception as e:
        return False