from flask import jsonify, request, make_response
from bson.objectid import ObjectId
import json
import traceback
onlineuser = False
ndacport = "1990"

ui_plugins = {"alm":"ALM","apg":"APG","dashboard":"Dashboard",
    "mindmap":"Mindmap","neurongraphs":"Neuron Graphs","performancetesting":"Performance Testing",
    "reports":"Reports","utility":"Utility","weboccular":"Webocular"}

ERR_CODE={
    "201":"Error while registration with LS",
    "202":"Error while pushing update to LS",
    "203":"NDAC is stopped. Issue - Licensing Server is offline",
    "204":"NDAC is stopped. Issue - Offline license expired",
    "205":"NDAC is stopped due to license expiry or loss of connectivity",
    "206":"Error while establishing connection to Nineteen68 Secondary Database",
    "207":"Database connectivity Unavailable",
    "208":"License server must be running",
    "209":"Critical Internal Exception occurred",
    "210":"Critical Internal Exception occurred: updateData",
    "211":"Another instance of NDAC is already registered with the License server",
    "212":"Unable to contact storage areas",
    "213":"Critical error in storage areas",
    "214":"Please contact Team - Nineteen68. Setup is corrupted",
    "215":"Error while establishing connection to Licensing Server. Retrying to establish connection",
    "216":"Connection to Licensing Server failed. Maximum retries exceeded. Hence, Shutting down server",
    "217":"Error while establishing connection to Redis",
    "218":"Invalid configuration file",
    "219":"Please contact Team - Nineteen68. Error while starting NDAC",
    "220":"Error occured in assist module: Update weights",
    "221":"Error occured in assist module: Update queries",
    "222":"Unable to contact storage areas: Assist Components",
    "223":"Critical error in storage areas: Assist Components",
    "224":"Another instance of NDAC is already running",
    "225":"Port "+ndacport+" already in use",
    "226":"Error while establishing connection to Nineteen68 Database"
}


ecodeServices = {
    "authenticateUser_Nineteen68": "300",
    "authenticateUser_Nineteen68_ldap": "301",
    "getRoleNameByRoleId_Nineteen68": "302",
    "authenticateUser_Nineteen68_projassigned": "303",
    "loadUserInfo_Nineteen68": "304",
    "getReleaseIDs_Nineteen68": "305",
    "getCycleIDs_Nineteen68": "306",
    "getProjectType_Nineteen68": "307",
    "getProjectIDs_Nineteen68": "308",
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
    "getUsers_Nineteen68": "352",
    "assignProjects_ICE": "353",
    "getLDAPConfig": "354",
    "getAvailablePlugins": "355",
    "getAllSuites_ICE": "356",
    "getSuiteDetailsInExecution_ICE": "357",
    "reportStatusScenarios_ICE": "358",
    "getReport_Nineteen68": "359",
    "exportToJson_ICE": "360",
    "createHistory": "361",
    "encrypt_ICE": "362",
    "dataUpdator_ICE": "363",
    "userAccess_Nineteen68": "364",
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
    "authenticateUser_Nineteen68_CI": "379",
    "generateCIusertokens": "380",
    "getCIUsersDetails": "381",
    "deactivateCIUser": "382",
    "saveMindmap":"383",
    "getModules":"384",
    "manageTaskDetails":"385"
}


def setenv(flaskapp=None, licactive=None):
    global app, onlineuser
    if flaskapp is not None: app = flaskapp
    if licactive is not None: onlineuser = licactive

def printErrorCodes(ecode):
    msg = "[ECODE: " + ecode + "] " + ERR_CODE[ecode]
    return msg

def servicesException(srv, exc):
    app.logger.debug("Exception occured in "+srv)
    app.logger.debug(exc)
    app.logger.error("[ECODE: " + ecodeServices[srv] + "] Internal error occured in api")

def isemptyrequest(requestdata):
    flag = False
    if (onlineuser == True):
        for key in requestdata:
            value = requestdata[key]
            if (key != 'additionalroles'
                and key != 'getparampaths' and key != 'testcasesteps'):
                if value == 'undefined' or value == '' or value == 'null' or value == None:
                    app.logger.warn(str(key)+" is empty")
                    flag = True
    else:
        flag = 0
        app.logger.critical(printErrorCodes('203'))
    return flag
