#-------------------------------------------------------------------------------
# Name:        ndac.py
# Purpose:     Security Aspects, Licensing components and ProfJ
#
# Author:      vishvas.a
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
import ast
import redis
from flask import Flask, request , jsonify
from waitress import serve
import logging
from logging.handlers import TimedRotatingFileHandler
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
app = Flask(__name__)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-k", type=str, dest='offlinemode', metavar='filename',
    help="Home user registration. Provide the offline registration file")
log_group = parser.add_mutually_exclusive_group()
log_group.add_argument("-T", "--test", action="store_true", help="Set logger level to Test Environment")
log_group.add_argument("-D", "--debug", action="store_true", help="Set logger level to Debug")
log_group.add_argument("-I", "--info", action="store_true", help="Set logger level to Info")
log_group.add_argument("-W", "--warn", action="store_true", help="Set logger level to Warning")
log_group.add_argument("-E", "--error", action="store_true", help="Set logger level to Error")
log_group.add_argument("-C", "--critical", action="store_true", help="Set logger level to Critical")
args = parser.parse_args()

ice_ndac_key = 'ajkdfiHFEow#DjgLIqocn^8sjp2hfY&d'
db_keys = "NinEteEn68dAtaBAs3eNcRypT10nk3yS"
activeicesessions={}
latest_access_time=datetime.now()

##os.chdir("..")
#nineteen68 folder location is parent directory
currdir=os.getcwd()
config_path = currdir+'/server_config.json'
assistpath = currdir + "/ndac_internals/assist"
logspath= currdir + "/ndac_internals/logs"

lsip="127.0.0.1"
cass_dbup = False
redis_dbup = False
offlinestarttime=''
offlineendtime=''
offlineuser = False
onlineuser = False
usersession = False
gracePeriodTimer=None
twoDayTimer=None
licensedata=""
grace_period = 172800
LS_CRITICAL_ERR_CODE=['199','120','121','123','124','125']
lsRetryCount=0
sysMAC=None
chronographTimer=None
ERR_CODE={
    "201":"Error while registration with LS",
    "202":"Error while pushing update to LS",
    "203":"NDAC is stopped. Issue - Licensing Server is offline",
    "204":"NDAC is stopped. Issue - Offline license expired",
    "205":"NDAC is stopped due to license expiry or loss of connectivity",
    "206":"Error while establishing connection to Database",
    "207":"Database connection Unavailable",
    "208":"License server must be running",
    "209":"Critical Internal Exception occurred",
    "210":"Critical Internal Exception occurred: updateData",
    "211":"Another instance of NDAC is already registered with the License server",
    "212":"Unable to contact storage areas",
    "213":"Critical error in storage areas",
    "214":"Please contact Team - Nineteen68. Setup is corrupted",
    "215":"Error establishing connection to Licensing Server. Retrying to establish connection",
    "216":"Connection to Licensing Server failed. Maximum retries exceeded. Hence, Shutting down server",
    "217":"Error while establishing connection to Redis",
    "218":"Invalid configuration file",
    "219":"Please contact Team - Nineteen68. Error while starting NDAC"
}

#counters for License
debugcounter = 0
scenarioscounter = 0
gtestsuiteid = []
suitescounter = 0

#server check
@app.route('/')
def server_ready():
    return 'Data Server Ready!!!'


################################################################################
# BEGIN OF LOGIN SCREEN
# INCLUDES : Login components
################################################################################

#service for login to Nineteen68
@app.route('/login/authenticateUser_Nineteen68',methods=['POST'])
def authenticateUser_Nineteen68():
    app.logger.info("Inside authenticateUser_Nineteen68")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            authenticateuser = ("select password,userid from users where username = '"
                +requestdata["username"]+"' "+" ALLOW FILTERING")
            queryresult = n68session.execute(authenticateuser)
            res= {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. authentication')
    except Exception as authenticateuserexc:
        servicesException('authenticateUser_Nineteen68',authenticateuserexc)
    return jsonify(res)

#service for user ldap validation
@app.route('/login/authenticateUser_Nineteen68/ldap',methods=['POST'])
def authenticateUser_Nineteen68_ldap():
    app.logger.info("Inside authenticateUser_Nineteen68_ldap")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            authenticateuserldap = ("select ldapuser,userid from users where "
                +"username = '"+requestdata["username"]+"'"+"allow filtering")
            queryresult = n68session.execute(authenticateuserldap)
            res= {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. authentication')
    except Exception as authenticateuserldapexc:
        servicesException("authenticateUser_Nineteen68_ldap",authenticateuserldapexc)
    return jsonify(res)

#service for getting rolename by roleid
@app.route('/login/getRoleNameByRoleId_Nineteen68',methods=['POST'])
def getRoleNameByRoleId_Nineteen68():
    app.logger.info("Inside getRoleNameByRoleId_Nineteen68")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            rolename = ("select rolename from roles where "
                        +"roleid = "+requestdata["roleid"]
                        +" allow filtering;")
            queryresult = n68session.execute(rolename)
            res = {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. authentication')

            return jsonify(res)
    except Exception as rolenameexc:
        servicesException("getRoleNameByRoleId_Nineteen68",rolenameexc)
        return jsonify(res)

#utility checks whether user is having projects assigned
@app.route('/login/authenticateUser_Nineteen68/projassigned',methods=['POST'])
def authenticateUser_Nineteen68_projassigned():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside authenticateUser_Nineteen68_projassigned."
            +"Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'getUserId'):
                authenticateuserprojassigned1= ("select userid,defaultrole "
                    +"from users where username = '"+requestdata["username"]
                    +"' allow filtering;")
                queryresult = n68session.execute(authenticateuserprojassigned1)
            elif(requestdata["query"] == 'getUserRole'):
                authenticateuserprojassigned2= ("select rolename from roles "
                    +"where roleid = "+requestdata["roleid"]+" allow filtering")
                queryresult = n68session.execute(authenticateuserprojassigned2)
            elif(requestdata["query"] == 'getAssignedProjects'):
                authenticateuserprojassigned3= ("select projectids from"
                    +" icepermissions where userid = "+requestdata["userid"]
                    +" allow filtering")
                queryresult = icesession.execute(authenticateuserprojassigned3)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. authentication')
            return jsonify(res)
    except Exception as e:
        servicesException("authenticateUser_Nineteen68_projassigned",e)
        return jsonify(res)

#service for loading user information
@app.route('/login/loadUserInfo_Nineteen68',methods=['POST'])
def loadUserInfo_Nineteen68():
    res={'rows':'fail'}
    try:
        ui_plugins_list = []
        requestdata=json.loads(request.data)
        app.logger.info("Inside loadUserInfo_Nineteen68. Query: "
            +str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'userInfo'):
                global latest_access_time
                latest_access_time=datetime.now()
                loaduserinfo1 = ("select userid, emailid, firstname, lastname, "
                                +"defaultrole, ldapuser, additionalroles, username "
                                +"from users where username = "+
                                "'"+requestdata["username"]+"' allow filtering")
                queryresult = n68session.execute(loaduserinfo1)
                rows=[]
                for eachkey in queryresult.current_rows:
                    additionalroles=[]
                    userid = eachkey['userid']
                    emailid = eachkey['emailid']
                    firstname = eachkey['firstname']
                    lastname = eachkey['lastname']
                    defaultrole = eachkey['defaultrole']
                    ldapuser = eachkey['ldapuser']
                    username = eachkey['username']
                    if eachkey['additionalroles'] != None:
                        for eachrole in eachkey['additionalroles']:
                            additionalroles.append(eachrole)
                    eachobject={'userid':userid,'emailid':emailid,'firstname':firstname,
                'lastname':lastname,'defaultrole':defaultrole,'ldapuser':ldapuser,
                'username':username,'additionalroles':additionalroles}
                    rows.append(eachobject)
                res={'rows':rows}
                return jsonify(res)
            elif(requestdata["query"] == 'loggedinRole'):
                loaduserinfo2 = ("select rolename from roles where "
                                    +"roleid = "+requestdata["roleid"]
                                    +" allow filtering")
                queryresult = n68session.execute(loaduserinfo2)
            elif(requestdata["query"] == 'userPlugins'):
                loaduserinfo3 = ("select roleid,alm,autogenpath,dashboard,deadcode,"
                                +"ice,mindmap,neuron2d,neuron3d,oxbowcode,reports,weboccular from "
                                +"userpermissions where roleid = "
                                +requestdata["roleid"]+" allow filtering")
                queryresult = n68session.execute(loaduserinfo3)
                for keys in licensedata['plugins']:
                    if(keys != 'ice'):
                        if(licensedata['plugins'][keys] == True):
                            ui_plugins_list.append(keys)
                for keys in (queryresult.current_rows)[0]:
                    if(keys not in ui_plugins_list):
                        (queryresult.current_rows)[0][keys] = False
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. loadUserInfo')
            return jsonify(res)
    except Exception as loaduserinfoexc:
        servicesException("loadUserInfo_Nineteen68",loaduserinfoexc)
        return jsonify(res)

################################################################################
# END OF LOGIN SCREEN
################################################################################


################################################################################
# BEGIN OF MIND MAPS
# INCLUDES : all Mindmap related queries
################################################################################

#getting Release_iDs of Project
@app.route('/create_ice/getReleaseIDs_Ninteen68',methods=['POST'])
def getReleaseIDs_Ninteen68():
    app.logger.info("Inside getReleaseIDs_Ninteen68")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getReleaseDetails = ("select releasename,releaseid from icetestautomation.releases "+
            "where projectid"+'='+ projectid+query['delete_flag'])
            queryresult = icesession.execute(getReleaseDetails)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.warn("Empty data received. getReleaseIDs_Ninteen68")
    except Exception as e:
        servicesException("getReleaseIDs_Ninteen68",e)
    return jsonify(res)


@app.route('/create_ice/getCycleIDs_Ninteen68',methods=['POST'])
def getCycleIDs_Ninteen68():
    app.logger.info("Inside getCycleIDs_Ninteen68")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            releaseid=requestdata['releaseid']
            getCycleDetails = ("select cyclename,cycleid from icetestautomation.cycles "+
            "where releaseid"+'='+ releaseid+query['delete_flag'])
            queryresult = icesession.execute(getCycleDetails)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.warn("Empty data received. getCycleIDs_Ninteen68")
    except Exception as e:
        servicesException("getCycleIDs_Ninteen68",e)
    return jsonify(res)

@app.route('/create_ice/getProjectType_Nineteen68',methods=['POST'])
def getProjectType_Nineteen68():
    app.logger.info("Inside getProjectType_Nineteen68")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getProjectType = ("select projecttypeid FROM icetestautomation.projects "+
            "where projectid"+'='+ projectid+query['delete_flag'])
            queryresult = icesession.execute(getProjectType)
            getProjectTypeName = ("select projecttypename FROM icetestautomation.projecttype "+
            "where projecttypeid"+'='+ str(queryresult.current_rows[0]['projecttypeid']))
            queryresult1 = icesession.execute(getProjectTypeName)
            res={'rows':queryresult.current_rows,'projecttype':queryresult1.current_rows}
       else:
            app.logger.warn("Empty data received. getProjectType_Nineteen68")
    except Exception as e:
        servicesException("getProjectType_Nineteen68",e)
    return jsonify(res)

#getting ProjectID and names of project sassigned to particular user
@app.route('/create_ice/getProjectIDs_Nineteen68',methods=['POST'])
def getProjectIDs_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getProjectIDs_Nineteen68. Query: "
            +str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            prjDetails={
                'projectId':[],
                'projectName':[],
                'appType':[]
            }
            userid=requestdata['userid']
            getProjIds = "select projectids FROM icepermissions where userid="+userid
            projidsresult = icesession.execute(getProjIds)
            projidsresult = projidsresult.current_rows
            if(len(projidsresult)!=0):
                projidsresult=projidsresult[0]['projectids']
                prjids=[]
                for pid in projidsresult:
                    prjids.append(str(pid))
                if(requestdata['query'] == 'emptyflag'):
                    modulequery="select distinct projectid from modules"
                    modulequeryresult = icesession.execute(modulequery)
                    modpids=[]
                    emppid=[]
                    for row in modulequeryresult.current_rows:
                        modpids.append(str(row['projectid']))
                    for pid in prjids:
                        if pid not in modpids:
                            emppid.append(pid)
                    prjids=emppid

                for pid in prjids:
                    getprojectdetails = ("select projectid,projectname,projecttypeid FROM icetestautomation.projects "+
                    "where projectid="+pid+query['delete_flag'])
                    queryresult = icesession.execute(getprojectdetails)
                    prjDetail=queryresult.current_rows
                    if(len(prjDetail)!=0):
                        prjDetails['projectId'].append(str(prjDetail[0]['projectid']))
                        prjDetails['projectName'].append(prjDetail[0]['projectname'])
                        prjDetails['appType'].append(str(prjDetail[0]['projecttypeid']))
            res={'rows':prjDetails}
        else:
            app.logger.warn("Empty data received. getProjectIDs_Nineteen68")
    except Exception as e:
        servicesException("getProjectIDs_Nineteen68",e)
    return jsonify(res)

#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/getNames_Ninteen68',methods=['POST'])
def getAllNames_ICE():
    app.logger.info("Inside getAllNames_ICE")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            name=requestdata['name']
            nodeid=requestdata['id']
            getname_query=(query[name]+nodeid+query['delete_flag'])
            queryresult = icesession.execute(getname_query)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.warn("Empty data received. getAllNames_ICE")
    except Exception as e:
        servicesException("getAllNames_ICE",e)
    return jsonify(res)

#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/testsuiteid_exists_ICE',methods=['POST'])
def testsuiteid_exists_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside testsuiteid_exists_ICE. Query: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='suite_check':
                testsuite_exists(requestdata['project_id'],requestdata['module_name'],requestdata['versionnumber'])
            else:
                testsuite_exists(requestdata['project_id'],requestdata['module_name'],requestdata['versionnumber'],requestdata['module_id'])
            testsuite_check=query[query_name]
            queryresult = icesession.execute(testsuite_check)
            res={'rows':queryresult.current_rows}
        else:
            app.logger.warn("Empty data received. testsuiteid_exists_ICE")
    except Exception as e:
        servicesException("testsuiteid_exists_ICE",e)
    return jsonify(res)

@app.route('/create_ice/testscenariosid_exists_ICE',methods=['POST'])
def testscenariosid_exists_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside testscenariosid_exists_ICE. Query: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='scenario_check':
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'],requestdata['versionnumber'])
            else:
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'],requestdata['versionnumber'],requestdata['scenario_id'])
            testscenario_check=query[query_name]
            queryresult = icesession.execute(testscenario_check)
            res={'rows':queryresult.current_rows}
        else:
            app.logger.warn("Empty data received. testscenariosid_exists_ICE")
    except Exception as e:
        servicesException("testscenariosid_exists_ICE",e)
    return jsonify(res)


@app.route('/create_ice/testscreenid_exists_ICE',methods=['POST'])
def testscreenid_exists_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside testscreenid_exists_ICE. Query: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='screen_check':
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'],requestdata['versionnumber'])
            else:
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'],requestdata['versionnumber'],requestdata['screen_id'])
            testscreen_check=query[query_name]
            queryresult = icesession.execute(testscreen_check)
            res={'rows':queryresult.current_rows}
        else:
            app.logger.warn("Empty data received. testscreenid_exists_ICE")
    except Exception as e:
        servicesException("testscreenid_exists_ICE",e)
    return jsonify(res)

@app.route('/create_ice/testcaseid_exists_ICE',methods=['POST'])
def testcaseid_exists_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside testcaseid_exists_ICE. Query: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='testcase_check':
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'],requestdata['versionnumber'])
            else:
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'],requestdata['versionnumber'],requestdata['testcase_id'])
            testcase_check=query[query_name]
            queryresult = icesession.execute(testcase_check)
            res={'rows':queryresult.current_rows}
        else:
            app.logger.warn("Empty data received. testcaseid_exists_ICE")
    except Exception as e:
        servicesException("testcaseid_exists_ICE",e)
    return jsonify(res)

@app.route('/create_ice/get_node_details_ICE',methods=['POST'])
def get_node_details_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside get_node_details_ICE. Name: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_node_data=query[query_name]+requestdata['id']+query['delete_flag']
            queryresult = icesession.execute(get_node_data)
            res={'rows':queryresult.current_rows}
##            if(len(queryresult.current_rows)!=0 and res['rows'][0]['history'] != None):
##                res['rows'][0]['history']=dict(res['rows'][0]['history'])
        else:
            app.logger.warn("Empty data received. get_node_details_ICE")
    except Exception as e:
        servicesException("get_node_details_ICE",e)
    return jsonify(res)

@app.route('/create_ice/delete_node_ICE',methods=['POST'])
def delete_node_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside delete_node_ICE. Name: "+str(requestdata["name"]))
        if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_delete_query(requestdata['id'],requestdata['node_name'],requestdata['version_number'],requestdata['parent_node_id'])
            delete_query=query[query_name]
            queryresult = icesession.execute(delete_query)
            res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. delete_node_ICE")
    except Exception as e:
        servicesException("delete_node_ICE",e)
    return jsonify(res)

@app.route('/create_ice/insertInSuite_ICE',methods=['POST'])
def insertInSuite_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside insertInSuite_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagsuite'):
                tags="['"+requestdata['tags']+"']"
                if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                    fetchOldData=("select tags from modules where "
                    +"modulename='"+requestdata['modulename']+"' and versionnumber="
                    +str(requestdata['oldversionnumber'])+" and projectid="
                    +requestdata['oldprojectid']+query['delete_flag'])
                    fetchqueryresult = icesession.execute(fetchOldData)
                    if (len(fetchqueryresult.current_rows)!=0 and (fetchqueryresult.current_rows[0]['tags'] is not None)):
                        fetchqueryresult = fetchqueryresult.current_rows[0]
                        tags="['"+"','".join(fetchqueryresult['tags'])+"']"
                #history=createHistory("create","modules",requestdata)
                create_suite_query1 = ("insert into modules "
                +"(projectid,modulename,moduleid,versionnumber,createdby,createdon,"
                +" createdthrough,deleted,skucodemodule,tags,testscenarioids) values( "
                +requestdata['projectid']+",'" + requestdata['modulename']
                +"'," + requestdata['moduleid'] + ","+str(requestdata['versionnumber'])
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                + ",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])
                +", '"+requestdata['skucodemodule']+"',"+tags+",[]) IF NOT EXISTS")
                queryresult = icesession.execute(create_suite_query1)
                res={'rows':'Success'}
            elif(requestdata["query"] == 'selectsuite'):
                create_suite_query2 = ("select moduleid from modules "
                +" where modulename='"+requestdata["modulename"]+"' and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(create_suite_query2)
                res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. insertInSuite_ICE")
    except Exception as e:
        servicesException("insertInSuite_ICE",e)
    return jsonify(res)

@app.route('/create_ice/insertInScenarios_ICE',methods=['POST'])
def insertInScenarios_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside insertInScenarios_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagscenarios'):
                tags="['"+requestdata['tags']+"']"
                if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                    fetchOldData=("select tags from testscenarios where "
                    +"testscenarioname='"+requestdata['testscenarioname']+"' and versionnumber="
                    +str(requestdata['oldversionnumber'])+" and projectid="
                    +requestdata['oldprojectid']+query['delete_flag'])
                    fetchqueryresult = icesession.execute(fetchOldData)
                    if (len(fetchqueryresult.current_rows)!=0 and (fetchqueryresult.current_rows[0]['tags'] is not None)):
                        fetchqueryresult = fetchqueryresult.current_rows[0]
                        tags="['"+"','".join(fetchqueryresult['tags'])+"']"
                #history=createHistory("create","testscenarios",requestdata)
                create_scenario_query1 = ("insert into testscenarios(projectid,"
                +"testscenarioname,testscenarioid,versionnumber,createdby"
                +",createdon,skucodetestscenario,tags,testcaseids,deleted) values ("
                +requestdata['projectid'] + ",'"+requestdata['testscenarioname']
                +"',"+requestdata['testscenarioid']+","+str(requestdata['versionnumber'])
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                +", '"+requestdata['skucodetestscenario']+"',"+tags+",[],"+str(requestdata['deleted'])+") IF NOT EXISTS")
                queryresult = icesession.execute(create_scenario_query1)
                res={'rows':'success'}
            elif(requestdata["query"] == 'deletescenarios'):
                delete_scenario_query = ("delete testcaseids from testscenarios"
                +" where testscenarioid="+requestdata['testscenarioid']+" and "
                +"testscenarioname='"+requestdata['testscenarioname'] +"' and "
                +"projectid = "+requestdata['projectid']+" and versionnumber="
                +str(requestdata['versionnumber'])+" IF EXISTS")
                queryresult = icesession.execute(delete_scenario_query)
                res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. insertInScenarios_ICE")
    except Exception as e:
        servicesException("insertInScenarios_ICE",e)
    return jsonify(res)

@app.route('/create_ice/insertInScreen_ICE',methods=['POST'])
def insertInScreen_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside insertInScreen_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagscreen'):
                tags="['"+requestdata['tags']+"']"
                screendata=""
                if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                    fetchOldData=("select tags,screendata from screens where "
                    +"screenname='"+requestdata['screenname']+"' and versionnumber="
                    +str(requestdata['oldversionnumber'])+" and projectid="
                    +requestdata['oldprojectid']+query['delete_flag'])
                    fetchqueryresult = icesession.execute(fetchOldData)
                    if (len(fetchqueryresult.current_rows)!=0):
                        fetchqueryresult = fetchqueryresult.current_rows[0]
                        screendata=fetchqueryresult['screendata']
                        if (fetchqueryresult['tags'] is not None):
                            tags="['"+"','".join(fetchqueryresult['tags'])+"']"
                #history=createHistory("create","screens",requestdata)
                create_screen_query1 = ("insert into screens (projectid,screenname,"
                +" screenid,versionnumber,createdby,createdon,createdthrough,"
                +" deleted,screendata,skucodescreen,tags) values ("+requestdata['projectid']
                +", '"+requestdata['screenname']+"'," + requestdata['screenid']
                +" , "+str(requestdata['versionnumber'])
                +" ,'"+requestdata['createdby']+"'," + str(getcurrentdate())
                +", '"+requestdata['createdthrough']+"' , "+str(requestdata['deleted'])
                +",'"+screendata+"','"+requestdata['skucodescreen']+"',"+tags+") IF NOT EXISTS")
                queryresult = icesession.execute(create_screen_query1)
                res={'rows':'Success'}
            elif(requestdata["query"] == 'selectscreen'):
                select_screen_query = ("select screenid from screens where "
                +"screenname='"+requestdata['screenname']+"' and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(select_screen_query)
                res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. insertInScreen_ICE")
    except Exception as e:
        servicesException("insertInScreen_ICE",e)
    return jsonify(res)

@app.route('/create_ice/insertInTestcase_ICE',methods=['POST'])
def insertInTestcase_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside insertInTestcase_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagtestcase'):
                tags="['"+requestdata['tags']+"']"
                testcasesteps=""
                if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                    fetchOldData=("select tags,testcasesteps from testcases where "
                    +"testcasename='"+requestdata['testcasename']+"' and versionnumber="
                    +str(requestdata['oldversionnumber'])+" and screenid="
                    +requestdata['oldscreenid']+query['delete_flag'])
                    fetchqueryresult = icesession.execute(fetchOldData)
                    if (len(fetchqueryresult.current_rows)!=0):
                        fetchqueryresult = fetchqueryresult.current_rows[0]
                        testcasesteps=fetchqueryresult['testcasesteps']
                        if (fetchqueryresult['tags'] is not None):
                            tags="['"+"','".join(fetchqueryresult['tags'])+"']"
                #history=createHistory("create","testcases",requestdata)
                create_testcase_query1 = ("insert into testcases (screenid,"
                +"testcasename,testcaseid,versionnumber,createdby,createdon,"
                +"createdthrough,deleted,skucodetestcase,tags,testcasesteps)values ("
                +requestdata['screenid'] + ",'" + requestdata['testcasename']
                +"'," + requestdata['testcaseid'] + ","+str(requestdata['versionnumber'])
                +",'"+ requestdata['createdby']+"'," + str(getcurrentdate())+", '"
                +requestdata['createdthrough'] +"',"+str(requestdata['deleted'])+",'"
                +requestdata['skucodetestcase']+"',"+tags+",'"+testcasesteps+"') IF NOT EXISTS")
                queryresult = icesession.execute(create_testcase_query1)
                res={'rows':'Success'}
            elif(requestdata["query"] == 'selecttestcase'):
                select_testcase_query = ("select testcaseid from testcases "
                +"where testcasename='"+requestdata['tags']+"'  and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(select_testcase_query)
                res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. insertInTestcase_ICE")
    except Exception as e:
        servicesException("insertInTestcase_ICE",e)
    return jsonify(res)

@app.route('/create_ice/updateTestScenario_ICE',methods=['POST'])
def updateTestScenario_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateTestScenario_ICE. Modified_flag: "
            +str(requestdata["modifiedflag"]))
        if not isemptyrequest(requestdata):
            ##requestdata['testcaseid']=','.join(str(idval) for idval in requestdata['testcaseid'])
            #history=createHistory("update","testscenarios",requestdata)
            if(requestdata['modifiedflag']):
                updateicescenario_query =("update testscenarios set "
                +"testcaseids=testcaseids+["+requestdata['testcaseid']
                +"],modifiedby='"+requestdata['modifiedby']
                +"',modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',modifiedon="+str(getcurrentdate())
                +" where projectid ="+requestdata['projectid']
                +"and testscenarioid ="+requestdata['testscenarioid']
                +" and testscenarioname = '"+requestdata['testscenarioname']
                +"' and versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            else:
                updateicescenario_query =("update testscenarios set "
                +"testcaseids=testcaseids+["+requestdata['testcaseid']
                +"] where projectid ="+requestdata['projectid']
                +"and testscenarioid ="+requestdata['testscenarioid']
                +" and testscenarioname = '"+requestdata['testscenarioname']
                +"' and versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            queryresult = icesession.execute(updateicescenario_query)
            res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. updateTestScenario_ICE")
    except Exception as e:
        servicesException("updateTestScenario_ICE",e)
    return jsonify(res)

@app.route('/create_ice/updateModule_ICE',methods=['POST'])
def updateModule_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateModule_ICE. Modified_flag: "
            +str(requestdata["modifiedflag"]))
        if not isemptyrequest(requestdata):
            requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
            #history=createHistory("update","modules",requestdata)
            if(requestdata['modifiedflag']):
                updateicemodules_query = ("update modules set testscenarioids ="
                +"["+requestdata['testscenarioids']+"],modifiedby='"+requestdata['modifiedby']
                +"',modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',modifiedon="+str(getcurrentdate())+" where moduleid="
                +requestdata['moduleid']+" and projectid="+requestdata['projectid']
                +" and modulename='"+requestdata['modulename']+"' and "
                +"versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            else:
                updateicemodules_query = ("update modules set "
                +"testscenarioids = ["+requestdata['testscenarioids']+"] where "
                +"moduleid="+requestdata['moduleid']+" and "
                +"projectid="+requestdata['projectid']+" and "
                +"modulename='"+requestdata['modulename']+"' and "
                +"versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            queryresult = icesession.execute(updateicemodules_query)
            res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. updateModule_ICE")
    except Exception as e:
        servicesException("updateModule_ICE",e)
    return jsonify(res)

@app.route('/create_ice/updateModulename_ICE',methods=['POST'])
def updateModulename_ICE():
    app.logger.info("Inside updateModulename_ICE")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
             #history=createHistory("rename","modules",requestdata)
             requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
             update_modulename_query =("insert into modules "
             +"(projectid,modulename,moduleid,versionnumber,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
             +" createdthrough,deleted,skucodemodule,tags,testscenarioids) values ("
             +requestdata['projectid']+",'" + requestdata['modulename']
             +"'," + requestdata['moduleid'] + ","+str(requestdata['versionnumber'])
             +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
             +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + str(getcurrentdate())
             + ",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])
             +", '"+requestdata['skucodemodule']+"',['"+requestdata['tags']+"'],["+requestdata['testscenarioids']+"]) IF NOT EXISTS")
             queryresult = icesession.execute(update_modulename_query)
             res={'rows':'Success'}
       else:
            app.logger.warn("Empty data received. updateModulename_ICE")
    except Exception as e:
        servicesException("updateModulename_ICE",e)
    return jsonify(res)

@app.route('/create_ice/updateTestscenarioname_ICE',methods=['POST'])
def updateTestscenarioname_ICE():
    app.logger.info("Inside updateTestscenarioname_ICE")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            #history=createHistory("rename","testscenarios",requestdata)
            requestdata['testcaseids'] = ','.join(str(idval) for idval in requestdata['testcaseids'])
            update_testscenario_name_query =("insert into testscenarios "
            +"(projectid,testscenarioname,testscenarioid,versionnumber,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
            +" deleted,skucodetestscenario,tags,testcaseids) values ("
            +requestdata['projectid']+",'"+ requestdata['testscenarioname']
            +"',"+requestdata['testscenarioid']+","+str(requestdata['versionnumber'])
            +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
            +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + str(requestdata['createdon'])
            + ","+str(requestdata['deleted'])+",'"+requestdata['skucodetestscenario']+"',['"
            +requestdata['tags']+"'],["+requestdata['testcaseids']+"]) IF NOT EXISTS")
            queryresult = icesession.execute(update_testscenario_name_query)
            res={'rows':'Success'}
       else:
            app.logger.warn("Empty data received. updateTestscenarioname_ICE")
    except Exception as e:
        servicesException("updateTestscenarioname_ICE",e)
    return jsonify(res)


@app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
def updateScreenname_ICE():
    app.logger.info("Inside updateScreenname_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if(requestdata['screendata'] == ''):
            requestdata['screendata'] = ' '
        if not isemptyrequest(requestdata):
            #history=createHistory("rename","screens",requestdata)
            update_screenname_query =("insert into screens (projectid,screenname,"
            +"screenid,versionnumber,createdby,createdon,createdthrough,deleted,"
            +"modifiedby,modifiedbyrole,modifiedon,screendata,skucodescreen,tags"
            +") values ("+requestdata['projectid']+",'"+requestdata['screenname']
            +"',"+requestdata['screenid']+","+str(requestdata['versionnumber'])
            +",'"+requestdata['createdby']+"',"+requestdata['createdon']
            +",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])
            +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
            +"',"+str(getcurrentdate())+",'"+requestdata['screendata']
            +"','"+requestdata['skucodescreen']+"',['"+requestdata['tags']+"']) IF NOT EXISTS")
            queryresult = icesession.execute(update_screenname_query)
            res={'rows':'Success'}
        else:
            app.logger.warn("Empty data received. updateScreenname_ICE")
    except Exception as e:
        servicesException("updateScreenname_ICE",e)
    return jsonify(res)


@app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
def updateTestcasename_ICE():
    app.logger.info("Inside updateTestcasename_ICE")
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if(requestdata['testcasesteps'] == ''):
            requestdata['testcasesteps'] = ' '
       if not isemptyrequest(requestdata):
            #history=createHistory("rename","testcases",requestdata)
            update_testcasename_query =("insert into testcases (screenid,testcasename,"
            "testcaseid,versionnumber,createdby,createdon,createdthrough,deleted,"
            +"modifiedby,modifiedbyrole,modifiedon,skucodetestcase,tags,"
            +"testcasesteps) values ("+requestdata['screenid']+",'"
            +requestdata['testcasename']+"',"+requestdata['testcaseid']+","
            +str(requestdata['versionnumber'])+",'"+requestdata['createdby']
            +"',"+str(requestdata['createdon'])+",'"+requestdata['createdthrough']
            +"',"+str(requestdata["deleted"])+",'"+requestdata['modifiedby']
            +"','"+requestdata['modifiedbyrole']+"',"+str(getcurrentdate())
            +",'"+requestdata['skucodetestcase']+"',['"+requestdata['tags']
            +"'],'"+requestdata['testcasesteps']+"') IF NOT EXISTS")
            queryresult = icesession.execute(update_testcasename_query)
            res={'rows':'Success'}
       else:
            app.logger.warn("Empty data received. updateTestcasename_ICE")
    except Exception as e:
        servicesException("updateTestcasename_ICE",e)
    return jsonify(res)


##@app.route('/create_ice/submitTask',methods=['POST'])
##def submitTask():
##    res={'rows':'fail'}
##    try:
##        requestdata=json.loads(request.data)
##        app.logger.info("Inside submitTask. Table: "+str(requestdata["table"]))
##        if not isemptyrequest(requestdata):
##            #history=createHistory("submit",requestdata['table'].lower(),requestdata)
##            if(requestdata['table'].lower()=='screens'):
##                query1=("update screens set history=history + "+str(history)+" where screenid="
##                +str(requestdata['details']['screenID_c'])+" and screenname='"+requestdata['details']['screenName']
##                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
##                +str(requestdata['versionnumber']))
##                queryresult = icesession.execute(query1)
##                res={'rows':'Success'}
##            if(requestdata['table'].lower()=='testscenarios'):
##                query2=("update testscenarios set history=history + "+str(history)+" where testscenarioid="
##                +str(requestdata['details']['testScenarioID_c'])+" and testscenarioname='"+requestdata['details']['testScenarioName']
##                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
##                +str(requestdata['versionnumber']))
##                queryresult = icesession.execute(query2)
##                res={'rows':'Success'}
##            if(requestdata['table'].lower()=='modules'):
##                query3=("update modules set history=history + "+str(history)+" where moduleid="
##                +str(requestdata['details']['moduleID_c'])+" and modulename='"+requestdata['details']['moduleName']
##                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
##                +str(requestdata['versionnumber']))
##                queryresult = icesession.execute(query3)
##                res={'rows':'Success'}
##            if(requestdata['table'].lower()=='testcases'):
##                query4=("update testcases set history=history + "+str(history)+" where testcaseid="
##                +str(requestdata['details']['testCaseID_c'])+" and testcasename='"+requestdata['details']['testCaseName']
##                +"' and screenid="+str(requestdata['details']['screenID_c'])+" and versionnumber="
##                +str(requestdata['versionnumber']))
##                queryresult = icesession.execute(query4)
##                res={'rows':'Success'}
##        else:
##            app.logger.warn("Empty data received. submitTask")
##    except Exception as e:
##        servicesException("submitTask",e)
##    return jsonify(res)
################################################################################
# END OF MIND MAPS
################################################################################


################################################################################
# BEGIN OF DESIGN SCREEN
# INCLUDES : scraping/ws-screen/design testcase creation
################################################################################

#keywords loader for design screen
@app.route('/design/getKeywordDetails_ICE',methods=['POST'])
def getKeywordDetails():
    app.logger.info("Inside getKeywordDetails")
    res={'rows':'fail'}
    try:
        projecttypename = request.data
        if not (projecttypename == '' or projecttypename == 'undefined'
                or projecttypename == 'null' or projecttypename == None):
            keywordquery=("select objecttype, toJson(keywords) from keywords "
                            +"where projecttypename in "
                            +"('"+projecttypename+"','Generic') ALLOW FILTERING")
            queryresult = icesession.execute(keywordquery)
            resultset=[]
            for eachrow in queryresult.current_rows:
                objecttype = eachrow['objecttype']
                keywords =  eachrow['system.tojson(keywords)']
                eachobject={'objecttype':objecttype,'keywords':keywords}
                resultset.append(eachobject)
            res={'rows':resultset}
        else:
            app.logger.warn('Empty data received. getKeywordDetails')
    except Exception as keywordsexc:
        servicesException("getKeywordDetails",keywordsexc)
    return jsonify(res)

#test case reading service
@app.route('/design/readTestCase_ICE',methods=['POST'])
def readTestCase_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside readTestCase_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == "readtestcase"):
                readtestcasequery1 = ("select testcasesteps,testcasename "
                    +"from testcases where screenid= " + requestdata["screenid"]
                    +" and testcasename='"+requestdata["testcasename"]+"'"
                    +" and versionnumber="+str(requestdata["versionnumber"])
                    +" and testcaseid=" + requestdata["testcaseid"]
                    + query['delete_flag'])
                queryresult = icesession.execute(readtestcasequery1)
            elif(requestdata['query'] == "testcaseid"):
                readtestcasequery2 = ("select screenid,testcasename,testcasesteps"
                +" from testcases where testcaseid="+ requestdata['testcaseid'] + query['delete_flag'])
                queryresult = icesession.execute(readtestcasequery2)
                count = debugcounter + 1
                userid = requestdata['userid']
                counterupdator('testcases',userid,count)
            elif(requestdata['query'] == "screenid"):
                readtestcasequery3 = ("select testcaseid,testcasename,testcasesteps "
                +"from testcases where screenid=" + requestdata['screenid']
                + " and versionnumber="+str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(readtestcasequery3)
            res= {"rows": queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. reading Testcase')
    except Exception as readtestcaseexc:
        servicesException("readTestCase_ICE",readtestcaseexc)
    return jsonify(res)


# fetches the screen data
@app.route('/design/getScrapeDataScreenLevel_ICE',methods=['POST'])
def getScrapeDataScreenLevel_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getScrapeDataScreenLevel_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if (requestdata['query'] == 'getscrapedata'):
                getscrapedataquery1=("select screenid,screenname,screendata from "
                +"screens where screenid="+requestdata['screenid']
                +" and projectid="+requestdata['projectid']+query['delete_flag'])
                queryresult = icesession.execute(getscrapedataquery1)
                res = {"rows":queryresult.current_rows}
            elif(requestdata['query'] == 'debugtestcase'):
                getscrapedataquery2=("select screenid,screenname,screendata from "
                +"screens where screenid="+requestdata['screenid']
                + query['delete_flag'])
                queryresult = icesession.execute(getscrapedataquery2)
                res = {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. reading Testcase')
    except Exception as getscrapedataexc:
        servicesException("getScrapeDataScreenLevel_ICE",getscrapedataexc)
    return jsonify(res)

# fetches data for debug the testcase
@app.route('/design/debugTestCase_ICE',methods=['POST'])
def debugTestCase_ICE():
    app.logger.info("Inside debugTestCase_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            gettestcasedataquery=("select screenid,testcasename,testcasesteps "
            +"from testcases where testcaseid=" + requestdata['testcaseid']+query['delete_flag'])
            queryresult = icesession.execute(gettestcasedataquery)
            res = {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. reading Testcase')
    except Exception as debugtestcaseexc:
        servicesException("debugTestCase_ICE",debugtestcaseexc)
    return jsonify(res)

# updates the screen data
@app.route('/design/updateScreen_ICE',methods=['POST'])
def updateScreen_ICE():
    app.logger.info("Inside updateScreen_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            #history=createHistory("update","screens",requestdata)
            updatescreenquery=("update icetestautomation.screens set"
			+" screendata ='"+ requestdata['scrapedata'] +"',"
			+" modifiedby ='" + requestdata['modifiedby'] + "',"
			+" modifiedon = '" + str(getcurrentdate())
			+"', skucodescreen ='" + requestdata['skucodescreen']
			+"' where screenid = "+requestdata['screenid']
			+" and projectid = "+requestdata['projectid']
			+" and screenname ='" + requestdata['screenname']
			+"' and versionnumber = "+str(requestdata['versionnumber'])
            +" IF EXISTS")
            queryresult = icesession.execute(updatescreenquery)
            res = {"rows":"Success"}
        else:
            app.logger.warn('Empty data received. updating screen')
    except Exception as updatescreenexc:
        servicesException("updateScreen_ICE",updatescreenexc)
    return jsonify(res)

#test case updating service
@app.route('/design/updateTestCase_ICE',methods=['POST'])
def updateTestCase_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateTestCase_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'checktestcaseexist'):
                updatetestcasequery1 = ("select testcaseid from testcases where "
                +"screenid=" + requestdata['screenid']+" and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(updatetestcasequery1)
                res= {"rows": queryresult.current_rows}
            elif(requestdata["query"] == 'updatetestcasedata'):
                #history=createHistory("update","testcases",requestdata)
                updatetestcasequery2 = ("update testcases set "
                + "modifiedby = '" + requestdata['modifiedby']
                + "', modifiedon='" + str(getcurrentdate())
        		+"',  skucodetestcase='" + requestdata["skucodetestcase"]
        		+"',  testcasesteps='" + requestdata["testcasesteps"]
        		+"' where versionnumber = "+str(requestdata["versionnumber"])
                +" and screenid=" + str(requestdata["screenid"])
                + " and testcaseid=" + str(requestdata["testcaseid"])
                + " and testcasename='" + requestdata["testcasename"] + "' if exists")
                queryresult = icesession.execute(updatetestcasequery2)
                res= {"rows": queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. updating testcases')
    except Exception as updatetestcaseexception:
        servicesException("updateTestCase_ICE",updatetestcaseexception)
    return jsonify(res)

#fetches all the testcases under a test scenario
@app.route('/suite/getTestcaseDetailsForScenario_ICE',methods=['POST'])
def getTestcaseDetailsForScenario_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getTestcaseDetailsForScenario_ICE. Query: "
            +str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'testscenariotable'):
                gettestscenarioquery1=("select testcaseids from testscenarios where "
                +"testscenarioid="+requestdata["testscenarioid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestscenarioquery1)
            elif(requestdata["query"] == 'testcasetable'):
                gettestscenarioquery2=("select testcasename,screenid from "
                +"testcases where testcaseid="+requestdata["testcaseid"]
                +query['delete_flag'])
                queryresult = icesession.execute(gettestscenarioquery2)
            elif(requestdata["query"] == 'screentable'):
                gettestscenarioquery3=("select screenname,projectid from "
                +"screens where screenid="+requestdata["screenid"]
                +query['delete_flag'])
                queryresult = icesession.execute(gettestscenarioquery3)
            elif(requestdata["query"] == 'projecttable'):
                gettestscenarioquery4=("select projectname from projects "
                +"where projectid="+requestdata["projectid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestscenarioquery4)
            res = {'rows':queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. getting testcases from scenarios.')
    except Exception as userrolesexc:
        servicesException("getTestcaseDetailsForScenario_ICE",userrolesexc)
    return jsonify(res)

################################################################################
# END OF DESIGN SCREEN
################################################################################


################################################################################
# BEGIN OF EXECUTION
# INCLUDES : all execution related actions
################################################################################

#get dependant testcases by scenario ids for add dependent testcases
@app.route('/design/getTestcasesByScenarioId_ICE',methods=['POST'])
def getTestcasesByScenarioId_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getTestcasesByScenarioId_ICE. Query: "
            +str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'gettestcaseids'):
                gettestcaseidquery1  = ("select testcaseids from testscenarios "
                +"where testscenarioid = "+requestdata["testscenarioid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestcaseidquery1)
                res= {"rows":queryresult.current_rows}
            elif(requestdata["query"] == 'gettestcasedetails'):
                gettestcaseidquery2 = ("select testcasename from testcases where"
                +" testcaseid = "+requestdata["eachtestcaseid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestcaseidquery2)
                res= {"rows":queryresult.current_rows}
            else:
                res={'rows':'fail'}
        else:
            app.logger.warn('Empty data received. getting testcases.')
    except Exception as e:
        servicesException("getTestcasesByScenarioId_ICE",e)
    return jsonify(res)

#read test suite nineteen68
@app.route('/suite/readTestSuite_ICE',methods=['POST'])
def readTestSuite_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside readTestSuite_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'testsuitecheck'):
                readtestsuitequery1 = ("select donotexecute,conditioncheck, "
                +"getparampaths,testscenarioids from testsuites "
                +" where testsuiteid="+ requestdata['testsuiteid']
                + " and cycleid="+requestdata['cycleid']+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery1)
            elif(requestdata["query"] == 'selectmodule'):
                readtestsuitequery2 = ("select projectid,modulename,moduleid,versionnumber,"
                +"createdby,createdon,createdthrough,deleted,modifiedby,modifiedbyrole,"
                +"modifiedon,skucodemodule,tags,testscenarioids FROM modules where "
                +"moduleid=" + requestdata["moduleid"]+" and modulename='"
                + requestdata["modulename"]+"'"+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery2)
            elif(requestdata["query"] == 'testcasesteps'):
                requestdata['conditioncheck'] = ','.join(str(idval) for idval in requestdata['conditioncheck'])
                requestdata['donotexecute'] = ','.join(str(idval) for idval in requestdata['donotexecute'])
                requestdata['getparampaths'] = ','.join(str('\''+idval+'\'') for idval in requestdata['getparampaths'])
                getparampaths=[]
                for eachgetparampath in requestdata['getparampaths']:
                    if(eachgetparampath == ''):
                        getparampaths.append(' ')
                    else:
                        getparampaths.append(eachgetparampath)
                requestdata['testscenarioids'] = ','.join(str(idval) for idval in requestdata['testscenarioids'])
                #history=createHistory("create","testsuites",requestdata)
                readtestsuitequery3 = ("insert into testsuites "+
                "(cycleid,testsuitename,testsuiteid,versionnumber,conditioncheck,"
                +"createdby,createdon,createdthrough,deleted,donotexecute,getparampaths,"
                +"skucodetestsuite,tags,testscenarioids) values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+str(requestdata["versionnumber"])+",["
                +requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["createdthrough"]+"',"
                +str(requestdata["deleted"])+",["+requestdata["donotexecute"]+"],["
                +requestdata['getparampaths'] +"],'"+requestdata["skucodetestsuite"]+"',['"
                +requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"]) IF NOT EXISTS")
                queryresult = icesession.execute(readtestsuitequery3)
            elif(requestdata["query"] == 'fetchdata'):
                readtestsuitequery4 = ("select * from testsuites "
                +"where testsuiteid = " + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery4)
            elif(requestdata["query"] == 'delete'):
                readtestsuitequery5 = ("delete from testsuites where "+
                "testsuiteid=" + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]
                + " and testsuitename='" + requestdata["testsuitename"]
                +"' and versionnumber="+str(requestdata["versionnumber"])+" IF EXISTS")
                queryresult = icesession.execute(readtestsuitequery5)
            elif(requestdata["query"] == 'updatescenarioinnsuite'):
                requestdata['conditioncheck'] = ','.join(str(idval) for idval in requestdata['conditioncheck'])
                requestdata['donotexecute'] = ','.join(str(idval) for idval in requestdata['donotexecute'])
                requestdata['getparampaths'] = ','.join(str(idval) for idval in requestdata['getparampaths'])
                requestdata['testscenarioids'] = ','.join(str(idval) for idval in requestdata['testscenarioids'])
                #history=createHistory("update","testsuites",requestdata)
                readtestsuitequery6 = ("insert into testsuites (cycleid,testsuitename,"
                +"testsuiteid,versionnumber,conditioncheck,createdby,createdon,"
                +"createdthrough,deleted,donotexecute,getparampaths,modifiedby,"
                +"modifiedon,skucodetestsuite,tags,testscenarioids) values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+str(requestdata["versionnumber"])
                +",["+requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +requestdata["createdon"]+",'"+requestdata["createdthrough"]+"',"
                +str(requestdata["deleted"])+",["+requestdata["donotexecute"]+"],["+
                requestdata["getparampaths"]+"],'"+requestdata["modifiedby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["skucodetestsuite"]+"',['"+
                requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"]) IF NOT EXISTS")
                queryresult = icesession.execute(readtestsuitequery6)
            elif(requestdata["query"] == 'testcasename'):
                readtestsuitequery7 = ("select testscenarioname,projectid from testscenarios where "
                +"testscenarioid=" +  requestdata["testscenarioid"]+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery7)
            elif(requestdata["query"] == 'projectname'):
                readtestsuitequery8 = ("select projectname from projects where "
                +"projectid = " + requestdata["projectid"]+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery8)
            elif(requestdata["query"] == 'readTestSuite_ICE'):
                readtestsuitequery9 = ("select donotexecute,conditioncheck,getparampaths,"
                +"testscenarioids from testsuites where "
                +"testsuiteid= " +requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]
                + " and testsuitename='"+requestdata["testsuitename"]
                +"' and versionnumber="+str(requestdata["versionnumber"])+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery9)
            else:
                return jsonify(res)
        else:
            app.logger.warn('Empty data received. read testsuites.')
            return jsonify(res)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as exporttojsonexc:
        servicesException("readTestSuite_ICE",exporttojsonexc)
        res={'rows':'fail'}
        return jsonify(res)

#-------------------------------------------------
#author : pavan.nayak
#date:31/07/2017
#-------------------------------------------------
@app.route('/suite/updateTestSuite_ICE',methods=['POST'])
def updateTestSuite_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateTestSuite_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'deletetestsuitequery'):
                deletetestsuitequery=("delete conditioncheck,donotexecute,"
                +"getparampaths,testscenarioids from testsuites where cycleid="
                +str(requestdata['cycleid'])
                +" and testsuitename='"+requestdata['testsuitename']
                +"' and testsuiteid="+str(requestdata['testsuiteid'])
                +" and versionnumber ="+str(requestdata['versionnumber'])+" IF EXISTS")
                queryresult = icesession.execute(deletetestsuitequery)
            elif(requestdata['query'] == 'updatetestsuitedataquery'):
                #history=createHistory("update","testsuites",requestdata)
                updatetestsuitedataquery=("update testsuites set"
                +" conditioncheck= conditioncheck + [" + requestdata['conditioncheck']
                +"], donotexecute=donotexecute + [" + str(requestdata['donotexecute'])
                +"],getparampaths=getparampaths + [ "+requestdata['getparampaths']
                +"],testscenarioids=testscenarioids + ["+ requestdata['testscenarioids']
                +"],modifiedby='"+ requestdata['modifiedby']
                +"', modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',skucodetestsuite='"+requestdata['skucodetestsuite']
                +"',tags=['"+requestdata['tags']
                +"'], modifiedon="+str(getcurrentdate())
                +" where cycleid="+ requestdata['cycleid']
                +" and testsuiteid="+ requestdata['testsuiteid']
                +" and versionnumber = "+ str(requestdata['versionnumber'])
                +" and testsuitename='"+ requestdata['testsuitename']
                +"' IF EXISTS;")
                queryresult = icesession.execute(updatetestsuitedataquery)
            else:
                return jsonify(res)
        else:
            app.logger.warn('Empty data received. update testsuite.')
            return jsonify(res)
        res={'rows':'Success'}
        return jsonify(res)
    except Exception as updatetestsuiteexc:
        servicesException("updateTestSuite_ICE",updatetestsuiteexc)
        return jsonify(res)

@app.route('/suite/ExecuteTestSuite_ICE',methods=['POST'])
def ExecuteTestSuite_ICE() :
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'testcaseid'):
                executetestsuitequery1=("select testcaseids from testscenarios where"
                +" testscenarioid=" + requestdata['testscenarioid']+query['delete_flag'])
                queryresult = icesession.execute(executetestsuitequery1)
                global scenarioscounter
                scenarioscounter = 0
                userid=requestdata['userid']
                scenarioscounter = scenarioscounter + 1
                counterupdator('testscenarios',userid,scenarioscounter)
            elif(requestdata['query'] == 'testcasesteps'):
                executetestsuitequery2=("select screenid from testcases where "
                +"testcaseid="+ requestdata['testcaseid']+query['delete_flag'])
                queryresult = icesession.execute(executetestsuitequery2)
            elif(requestdata['query'] == 'getscreendataquery'):
                executetestsuitequery3=("select screendata from screens where "
                +"screenid=" + requestdata['screenid']+query['delete_flag'])
                queryresult = icesession.execute(executetestsuitequery3)
            elif(requestdata['query'] == 'testcasestepsquery'):
                executetestsuitequery4=("select testcasesteps,testcasename from "
                +"testcases where testcaseid = "+ requestdata['testcaseid']+query['delete_flag'])
                queryresult = icesession.execute(executetestsuitequery4)
            elif(requestdata['query'] == 'insertreportquery'):
                executetestsuitequery5=("insert into reports (reportid,executionid,"
                    +"testsuiteid,testscenarioid,executedtime,browser,modifiedon,status,"
                    +"report) values (" + requestdata['reportid'] + ","
                    + requestdata['executionid']+ "," + requestdata['testsuiteid']
                    + "," + requestdata['testscenarioid'] + "," + str(getcurrentdate())
                    + ",'" + requestdata['browser'] + "'," + str(getcurrentdate())
                    + ",'" + requestdata['status']+ "','" + requestdata['report'] + "')")
                queryresult = icesession.execute(executetestsuitequery5)
            elif(requestdata['query'] == 'inserintotexecutionquery'):
               executetestsuitequery6= ("insert into execution (testsuiteid,"
                +"executionid,starttime,endtime,executionstatus) values (" + requestdata['testsuiteid']
                + "," + requestdata['executionid']+ "," + requestdata['starttime']
                + "," + str(getcurrentdate()) + ",'" + requestdata['status'] + "')")
               queryresult = icesession.execute(executetestsuitequery6)
            else:
                return jsonify(res)
        else:
            app.logger.warn('Empty data received. execute testsuite.')
            return jsonify(res)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as execuitetestsuiteexc:
        servicesException("ExecuteTestSuite_ICE",execuitetestsuiteexc)
        return jsonify(res)

################################################################################
# END OF EXECUTION
################################################################################

################################################################################
# START OF SCHEDULING
################################################################################
@app.route('/suite/ScheduleTestSuite_ICE',methods=['POST'])
def ScheduleTestSuite_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside ScheduleTestSuite_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'insertscheduledata'):
                requestdata['testsuiteids']=','.join(str(idval) for idval in requestdata['testsuiteids'])
                requestdata['browserlist'] = ','.join(str(idval) for idval in requestdata['browserlist'])
                scheduletestsuitequery1=("insert into scheduledexecution(cycleid,scheduledatetime,"
                +"scheduleid,browserlist,clientipaddress,userid,scenariodetails,schedulestatus,"
                +"testsuiteids,testsuitename) values (" + requestdata['cycleid'] + ","
                + str(requestdata['scheduledatetime']) + "," + requestdata['scheduleid'] + ",'["
                + requestdata['browserlist'] + "]','" + requestdata['clientipaddress'] + "',"
                + requestdata['userid'] + ",'" + requestdata['scenariodetails'] + "','"
                + requestdata['schedulestatus'] + "',[" + requestdata['testsuiteids'] + "],'"
                + requestdata['testsuitename'] + "')")
                queryresult = icesession.execute(scheduletestsuitequery1)
            elif(requestdata['query'] == 'getscheduledata'):
                scheduletestsuitequery2=("select * from scheduledexecution where "
                +"cycleid="+ requestdata['cycleid'] + " and scheduledatetime='"
                + requestdata['scheduledatetime'] + "' and scheduleid="
                + requestdata['scheduleid'] + " ALLOW FILTERING")
                queryresult = icesession.execute(scheduletestsuitequery2)
            elif(requestdata['query'] == 'updatescheduledstatus'):
                scheduletestsuitequery3=("update scheduledexecution set schedulestatus='"
                + requestdata['schedulestatus'] + "' where cycleid="
                + requestdata['cycleid'] + " and scheduledatetime='"
                + str(requestdata['scheduledatetime']) + "' and scheduleid="
                + requestdata['scheduleid'])
                queryresult = icesession.execute(scheduletestsuitequery3)
            elif(requestdata['query'] == 'getallscheduledetails'):
                scheduletestsuitequery4=""
                if(requestdata['scheduledetails'] == 'getallscheduledata'):
                    scheduletestsuitequery4=("select * from scheduledexecution")
                elif(requestdata['scheduledetails'] == 'getallscheduleddetails'):
                    scheduletestsuitequery4=("select * from scheduledexecution"
                    +" where schedulestatus='scheduled' allow filtering;")
                elif(requestdata['scheduledetails'] == 'checkscheduleddetails'):
                    scheduletestsuitequery4=("select * from scheduledexecution"
                    +" where scheduledatetime='" + requestdata['scheduledatetime'] + "'"
                    +" and clientipaddress='" + requestdata['clientipaddress'] + "' ALLOW FILTERING")
                queryresult = icesession.execute(scheduletestsuitequery4)
            elif(requestdata['query'] == 'getscheduledstatus'):
                scheduletestsuitequery5=("select schedulestatus from scheduledexecution"
                +" where cycleid="+ requestdata['cycleid'] + " and scheduledatetime='"
                + str(requestdata['scheduledatetime']) + "' and scheduleid=" + requestdata['scheduleid'])
                queryresult = icesession.execute(scheduletestsuitequery5)
            else:
                return jsonify(res)
        else:
            app.logger.warn('Empty data received. schedule testsuite.')
            return jsonify(res)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as scheduletestsuiteexc:
        servicesException("ScheduleTestSuite_ICE",scheduletestsuiteexc)
        return jsonify(res)

################################################################################
# END OF SCHEDULING
################################################################################

################################################################################
# BEGIN OF QUALITYCENTRE
# INCLUDES : all qc related actions
################################################################################
#fetches the user roles for assigning during creation/updation user
@app.route('/qualityCenter/qcProjectDetails_ICE',methods=['POST'])
def qcProjectDetails_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside qcProjectDetails_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'getprojectDetails'):
                qcprojectdetailsquery1  = ("select projectids from icepermissions where userid="+requestdata["userid"])
                queryresult = icesession.execute(qcprojectdetailsquery1)
            elif(requestdata["query"] == 'projectname1'):
                qcprojectdetailsquery2 = ("select projectname from projects where projectid="+requestdata["projectid"])
                queryresult = icesession.execute(qcprojectdetailsquery2)
            elif(requestdata["query"] == 'scenariodata'):
                qcprojectdetailsquery3  = ("SELECT testscenarioid,testscenarioname FROM testscenarios where projectid="+requestdata["projectid"])
                queryresult = icesession.execute(qcprojectdetailsquery3)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  jsonify(res)
        else:
            app.logger.warn('Empty data received. getting qcProjectDetails.')
            res =  jsonify(res)
    except Exception as e:
        servicesException("qcProjectDetails_ICE",e)
    return res

@app.route('/qualityCenter/saveQcDetails_ICE',methods=['POST'])
def saveQcDetails_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside saveQcDetails_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'saveQcDetails_ICE'):
                gettestcaseidquery1  = ("INSERT INTO qualitycenterdetails (testscenarioid,qcdetailsid,qcdomain,qcfolderpath,qcproject,qctestcase,qctestset) VALUES ("+requestdata["testscenarioid"]
                +","+requestdata["testscenarioid"]+",'"+requestdata["qcdomain"]+"','"+requestdata["qcfolderpath"]+"','"+requestdata["qcproject"]
                +"','"+requestdata["qctestcase"]+"','"+requestdata["qctestset"]+"')")
                queryresult = icesession.execute(gettestcaseidquery1)
                res= {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. getting saveQcDetails.')
    except Exception as e:
        servicesException("saveQcDetails_ICE",e)
    return jsonify(res)

@app.route('/qualityCenter/viewQcMappedList_ICE',methods=['POST'])
def viewQcMappedList_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside viewQcMappedList_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'qcdetails'):
                viewqcmappedquery1  = ("SELECT * FROM qualitycenterdetails where testscenarioid="+requestdata["testscenarioid"])
                queryresult = icesession.execute(viewqcmappedquery1)
                res= {"rows":queryresult.current_rows}
        else:
            app.logger.warn('Empty data received. getting QcMappedList.')
    except Exception as e:
        servicesException("viewQcMappedList_ICE",e)
    return jsonify(res)
################################################################################
# END OF QUALITYCENTRE
################################################################################

################################################################################
# BEGIN OF ADMIN SCREEN
# INCLUDES : all admin related actions
################################################################################

#fetches the user roles for assigning during creation/updation user
@app.route('/admin/getUserRoles_Nineteen68',methods=['POST'])
def getUserRoles_Nineteen68():
    app.logger.info("Inside getUserRoles_Nineteen68")
    res={'rows':'fail'}
    try:
        userrolesquery="select roleid, rolename from roles"
        queryresult = n68session.execute(userrolesquery)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as userrolesexc:
        servicesException("getUserRoles_Nineteen68",userrolesexc)
        return jsonify(res)


#service renders all the details of the child type
#if domainid is provided all projects in domain is returned
#if projectid is provided all release and cycle details is returned
#if cycleid is provided, testsuite details is returned
@app.route('/admin/getDetails_ICE',methods=['POST'])
def getDetails_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getDetails_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domaindetails'):
                ptype={}
                getdetailsquery0 = ("select projecttypename,projecttypeid from projecttype")
                queryresult0 = icesession.execute(getdetailsquery0)
                for row in queryresult0.current_rows:
                    if (row['projecttypename']=="DesktopJava"):
                        ptype['oebs']=row['projecttypeid']
                    else:
                        ptype[(row['projecttypename']).lower()]=row['projecttypeid']
                del ptype['generic']
                icePlugins=licensedata['plugins']['ice']
                for p in icePlugins:
                    if not icePlugins[p]:
                        del ptype[p]
                ptype=ptype.values()
                getdetailsquery1=("select projectid,projectname,projecttypeid from projects "
                    +"where domainid=" + requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getdetailsquery1)
                projectList=[]
                for prj in queryresult.current_rows:
                    if prj['projecttypeid'] in ptype:
                        projectList.append(prj)
                res={'rows':projectList}
            elif(requestdata["query"] == 'projectsdetails'):
                getdetailsquery2=""
                if(requestdata["subquery"] == 'projecttypeid'):
                    getdetailsquery2=("select projecttypeid,projectname from projects"
                        +" where projectid="+ requestdata['id']+query['delete_flag'])
                elif(requestdata["subquery"] == 'projecttypename'):
                    getdetailsquery2=("select projecttypename from projecttype"
                        +" where projecttypeid=" + requestdata['id'])
                elif(requestdata["subquery"] == 'releasedetails'):
                    getdetailsquery2=("select releaseid,releasename from "
                        +"releases where projectid=" + requestdata['id']+query['delete_flag'])
                elif(requestdata["subquery"] == 'cycledetails'):
                    getdetailsquery2=("select cycleid,cyclename from cycles "
                        +"where releaseid=" + requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getdetailsquery2)
                res={'rows':queryresult.current_rows}
            elif(requestdata["query"] == 'cycledetails'):
                getdetailsquery3=("select testsuiteid,testsuitename "
                    +"from testsuites where cycleid=" + requestdata['id']
                    +query['delete_flag'])
                queryresult = icesession.execute(getdetailsquery3)
                res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. generic details.')
            return jsonify(res)
    except Exception as getdetailsexc:
        servicesException("getDetails_ICE",getdetailsexc)
        return jsonify(res)


#service renders the names of all projects in domain/projects (or) projectname
# releasenames (or) cycle names (or) screennames
@app.route('/admin/getNames_ICE',methods=['POST'])
def getNames_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getNames_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domainsall'):
                getnamesquery1=("select projectid,projectname from projects "
                    +"where domainid="+requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getnamesquery1)
            elif(requestdata["query"] == 'projects'):
                getnamesquery2=("select projectid,projectname from projects "
                    +"where projectid="+requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getnamesquery2)
            elif(requestdata["query"] == 'releases'):
                getnamesquery3=("select releaseid,releasename from releases "
                    +"where releaseid="+requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getnamesquery3)
            elif(requestdata["query"] == 'cycles'):
                getnamesquery4=("select cycleid,cyclename from cycles "
                    +"where cycleid="+requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getnamesquery4)
            elif(requestdata["query"] == 'screens'):
                getnamesquery5=("select screenid,screenname from screens "
                    +"where screenid="+requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getnamesquery5)
            else:
                return jsonify(res)
            res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. generic name details.')
            return jsonify(res)
    except Exception as getnamesexc:
        servicesException("getNames_ICE",getnamesexc)
        return jsonify(res)

#service renders all the domains in DB
@app.route('/admin/getDomains_ICE',methods=['POST'])
def getDomains_ICE():
    app.logger.info("Inside getDomains_ICE")
    res={'rows':'fail'}
    try:
        getdomainsquery="select domainid,domainname from domains"
        queryresult = icesession.execute(getdomainsquery)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as getdomainsexc:
        servicesException("getDomains_ICE",getdomainsexc)
        return jsonify(res)

#service fetches projects assigned to user.
@app.route('/admin/getAssignedProjects_ICE',methods=['POST'])
def getAssignedProjects_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getAssignedProjects_ICE. Query: "
            +str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projectid'):
                getassingedprojectsquery1=("select projectids from "
                        +"icepermissions where userid = "+requestdata['userid']
                        +" and domainid = "+requestdata['domainid'])
                queryresult = icesession.execute(getassingedprojectsquery1)
            elif(requestdata['query'] == 'projectname'):
                getassingedprojectsquery2=("select projectname from projects "
                    +"where projectid = "+requestdata['projectid']
                    +query['delete_flag'])
                queryresult = icesession.execute(getassingedprojectsquery2)
            else:
                return jsonify(res)
            res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. assigned projects.')
            return jsonify(res)
    except Exception as e:
        servicesException("getAssignedProjects_ICE",e)
        return jsonify(res)

#service creates new users into Nineteen68
@app.route('/admin/createUser_Nineteen68',methods=['POST'])
def createUser_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside createUser_Nineteen68. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'allusernames'):
                createuserquery1=("select username from users")
                queryresult = n68session.execute(createuserquery1)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createuser'):
                userid = str(uuid.uuid4())
                deactivated = False
                requestdata['userid']=userid
                requestdata['password'] = "'"+requestdata['password']+"'"
                if(requestdata['ldapuser']):
                    requestdata['password'] = "null"
                #history = createHistory("create","users",requestdata)
                createuserquery2=("insert into users (userid,createdby,createdon,"
                +"defaultrole,deactivated,emailid,firstname,lastname,ldapuser,password,username) values"
                +"( "+str(userid)+" , '"+requestdata['username']+"' , "
                + str(getcurrentdate())+" , "+requestdata['defaultrole']+" , "
                +str(deactivated)+" , '"+requestdata['emailid']+"' , '"
                +requestdata['firstname']+"' , '"+requestdata['lastname']+"' , "
                +str(requestdata['ldapuser'])+" , "+requestdata['password']+" , '"
                +requestdata['username']+"')")
                queryresult = n68session.execute(createuserquery2)
                res={'rows':'Success'}
            elif(requestdata['query'] == 'createciuser'):
                userid = str(uuid.uuid4())
                deactivated = False
                requestdata['userid']=userid
                #history = createHistory("create","users",requestdata)
                createuserquery3=("insert into users (userid,createdby,createdon,"
                +"defaultrole,deactivated,emailid,firstname,lastname,ldapuser,password,username) values"
                +"( "+str(userid)+" , '"+requestdata['username']+"' , "
                + str(getcurrentdate())+" ,null,"
                +str(deactivated)+" ,null,null,null"
                +",null, '"+requestdata['password']+"' , '"
                +requestdata['username']+"')")
                queryresult = n68session.execute(createuserquery3)
                res={'rows':'Success'}
        else:
            app.logger.warn('Empty data received. create user.')
    except Exception as e:
        servicesException("createUser_Nineteen68",e)
    return jsonify(res)

#service fetch user data from Nineteen68
@app.route('/admin/getUserData_Nineteen68',methods=['POST'])
def getUserData_Nineteen68():
    app.logger.info("Inside getUserData_Nineteen68")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            getuserdataquery=("select username,firstname,lastname,emailid,ldapuser,"
               +"defaultrole,additionalroles from users where userid="+str(requestdata['userid']))
            queryresult = n68session.execute(getuserdataquery)
            rows=[]
            for eachkey in queryresult.current_rows:
                additionalroles=[]
                emailid = eachkey['emailid']
                firstname = eachkey['firstname']
                lastname = eachkey['lastname']
                ldapuser = eachkey['ldapuser']
                username = eachkey['username']
                defaultrole = eachkey['defaultrole']
                if eachkey['additionalroles'] != None:
                    for eachrole in eachkey['additionalroles']:
                        additionalroles.append(eachrole)
                eachobject={'userid':requestdata['userid'],'emailid':emailid,
                'firstname':firstname,'lastname':lastname,'ldapuser':ldapuser,
                'username':username,'additionalroles':additionalroles,'defaultrole':defaultrole}
                rows.append(eachobject)
            res={'rows':rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. Get user data.')
            return jsonify(res)
    except Exception as e:
        servicesException("getUserData_Nineteen68",e)
        res={'rows':'fail'}
        return jsonify(res)

#service update user data into Nineteen68
@app.route('/admin/updateUser_Nineteen68',methods=['POST'])
def updateUser_Nineteen68():
    app.logger.info("Inside updateUser_Nineteen68")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            requestdata['additionalroles'] = ','.join(str(roleid) for roleid in requestdata['additionalroles'])
            #history = createHistory("update","users",requestdata)
            if requestdata['password'] == 'existing':
                updateuserquery2=("UPDATE users set "
                +"username='" + requestdata['username']
                + "', firstname='" + requestdata['firstname']
                + "', lastname='" + requestdata['lastname']
                + "', modifiedby='" + requestdata['modifiedby']
                + "', modifiedon=" + str(getcurrentdate())
                + ", emailid='" + requestdata['emailid']
                + "', ldapuser= " + str(requestdata['ldapuser'])
                + ", modifiedbyrole= '" + str(requestdata['modifiedbyrole'])
                + "', additionalroles= {" + str(requestdata['additionalroles'])
                + "} where userid=" + str(requestdata['userid']))
            else:
                updateuserquery2=("UPDATE users set "
                +"username='" + requestdata['username']
                + "', password='" + requestdata['password']
                + "', firstname='" + requestdata['firstname']
                + "', lastname='" + requestdata['lastname']
                + "', modifiedby='" + requestdata['modifiedby']
                + "', modifiedon=" + str(getcurrentdate())
                + ", emailid='" + requestdata['emailid']
                + "', ldapuser= " + str(requestdata['ldapuser'])
                + ", modifiedbyrole= '" + str(requestdata['modifiedbyrole'])
                + "', additionalroles= {" + str(requestdata['additionalroles'])
                + "} where userid=" + str(requestdata['userid']))
            queryresult = n68session.execute(updateuserquery2)
            res={'rows':'Success'}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. update user.')
            return jsonify(res)
    except Exception as e:
        servicesException("updateUser_nineteen68",e)
        res={'rows':'fail'}
        return jsonify(res)

#service creates a complete project structure into ICE keyspace
@app.route('/admin/createProject_ICE',methods=['POST'])
def createProject_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside createProject_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projecttype'):
                projecttypequery=("select projecttypeid from projecttype where"
                +" projecttypename = '"+requestdata['projecttype']+"' allow filtering")
                queryresult = icesession.execute(projecttypequery)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createproject'):
                projectid =uuid.uuid4()
                requestdata['projectid']=projectid
                #history = createHistory("create","projects",requestdata)
                createprojectquery1 = ("insert into projects (domainid,projectname,"
                +"projectid,createdby,createdon,deleted,projecttypeid,"
                +"skucodeproject,tags)values ( "+str(requestdata['domainid'])
                +", '"+requestdata['projectname']+"' , "+str(projectid)
                +", '"+requestdata['createdby']+"',"+str(getcurrentdate())
                +", false, "+requestdata['projecttypeid']
                +",'"+requestdata['skucodeproject']+"' , ['"+requestdata['tags']+"']);")
                projectid = {'projectid':projectid}
                queryresult = icesession.execute(createprojectquery1)
                res={'rows':[projectid]}
            elif(requestdata['query'] == 'createrelease'):
                releaseid=''
                if requestdata.has_key('releaseid'):
                    releaseid=requestdata['releaseid']
                    #history=createHistory("update","releases",requestdata)
                else:
                    releaseid=uuid.uuid4()
                    requestdata['releaseid']=releaseid
                    #history=createHistory("create","releases",requestdata)
                createreleasequery1=("insert into releases (projectid,releasename,"
                +"releaseid,createdby,createdon,deleted,skucoderelease,tags) values "
                +"("+str(requestdata['projectid'])+", '"+requestdata['releasename']
                +"',"+str(releaseid)+",'"+requestdata['createdby']
                +"',"+str(getcurrentdate())+",false,'"+requestdata['skucoderelease']
                +"',['"+requestdata['tags']+"'])")
                releaseid = {'releaseid':releaseid}
                queryresult = icesession.execute(createreleasequery1)
                res={'rows':[releaseid]}
            elif(requestdata['query'] == 'createcycle'):
                cycleid=''
                if requestdata.has_key('cycleid'):
                    cycleid=requestdata['cycleid']
                    #history=createHistory("update","cycles",requestdata)
                else:
                    cycleid=uuid.uuid4()
                    requestdata['cycleid']=cycleid
                    #history=createHistory("create","cycles",requestdata)
                createcyclequery1=("insert into cycles (releaseid,cyclename, "
                +"cycleid,createdby,createdon,deleted,skucodecycle,tags) values "
                +" ("+str(requestdata['releaseid'])+", '"+requestdata['cyclename']
                +"',"+str(cycleid)+",'"+requestdata['createdby']
                +"',"+str(getcurrentdate())+",false,'"+requestdata['skucodecycle']
                +"' ,['"+requestdata['tags']+"'])")
                cycleid = {'cycleid':cycleid}
                queryresult = icesession.execute(createcyclequery1)
                res={'rows':[cycleid]}
        else:
            app.logger.warn('Empty data received. create project.')
    except Exception as createprojectexc:
        servicesException("createProject_ICE",createprojectexc)
    return jsonify(res)

#service updates the specified project structure into ICE keyspace
@app.route('/admin/updateProject_ICE',methods=['POST'])
def updateProject_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateProject_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'deleterelease'):
                updateprojectquery1=("delete from releases where releasename='"
                +requestdata['releasename']+"' and projectid="+requestdata['projectid']
                +" and releaseid="+requestdata['releaseid'])
                queryresult = icesession.execute(updateprojectquery1)
                res={'rows':'Success'}
            elif(requestdata['query'] == 'deletecycle'):
                updateprojectquery2=("delete from cycles where cyclename='"
                +requestdata['cyclename']+"' and releaseid="+requestdata['releaseid']
                +" and cycleid="+requestdata['cycleid'])
                queryresult = icesession.execute(updateprojectquery2)
                res={'rows':'Success'}
        else:
            app.logger.warn('Empty data received. update project.')
    except Exception as updateprojectexc:
        servicesException("updateProject_ICE",updateprojectexc)
    return jsonify(res)

#fetches user data into Nineteen68
@app.route('/admin/getUsers_Nineteen68',methods=['POST'])
def getUsers_Nineteen68():
    app.logger.info("Inside getUsers_Nineteen68")
    res={'rows':'fail'}
    try:
        userid_list = []
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            userroles = requestdata['userroles']
            userrolesarr=[]
            for eachroleobj in userroles:
                if eachroleobj['rolename'] == 'Admin' or eachroleobj['rolename'] == 'Test Manager' :
                    userrolesarr.append(eachroleobj['roleid'])
            domainquery = ("select domainid from projects where projectid="+requestdata['projectid']+" allow filtering")
            queryresultdomain= icesession.execute(domainquery)
            domainid =queryresultdomain.current_rows

            query = ("select userid,projectids from icepermissions where domainid="+str(domainid[0]['domainid'])+" allow filtering")
            queryresult = icesession.execute(query)
            result = queryresult.current_rows

            for rows in result:
                if(str(requestdata['projectid']) in str(rows['projectids'])):
                    userid_list.append(rows['userid'])
            res={}
            userroles=[]
            rids=[]
            for userid in userid_list:
                queryforuser=("select userid, username, defaultrole from users "
                        +"where userid="+str(userid))
                queryresultusername=n68session.execute(queryforuser)
                if not(len(queryresultusername.current_rows) == 0):
                    if not (str(queryresultusername.current_rows[0]['defaultrole']) in userrolesarr):
                        rids.append(userid)
                        userroles.append(queryresultusername.current_rows[0]['username'])
                        res["userRoles"]=userroles
                        res["r_ids"]=rids
        else:
            app.logger.warn('Empty data received. get users - Mind Maps.')
            return jsonify(res)
        return jsonify(res)
    except Exception as getUsersexc:
        servicesException("getUsers_Nineteen68",getUsersexc)
        return jsonify(res)

#service assigns projects to a specific user
@app.route('/admin/assignProjects_ICE',methods=['POST'])
def assignProjects_ICE():
    app.logger.info("Inside assignProjects_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if (requestdata['alreadyassigned'] != True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
                #history=createHistory("assign","icepermissions",requestdata)
                assignprojectsquery1 = ("insert into icepermissions (userid,"
                +" domainid,createdby,createdon,projectids) values"
                +" ("+str(requestdata['userid'])+","+str(requestdata['domainid'])
                +",'"+requestdata['createdby']+"',"+str(getcurrentdate())
                +", ["+str(requestdata['projectids'])+"]);")
                queryresult = icesession.execute(assignprojectsquery1)
            elif (requestdata['alreadyassigned'] == True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
                #history=createHistory("assign","icepermissions",requestdata)
                assignprojectsquery2 = ("update icepermissions set"
                +" projectids = ["+requestdata['projectids']+"] "
                +", modifiedby = '"+requestdata['modifiedby']
                +"', modifiedon = "+str(getcurrentdate())
                +", modifiedbyrole = '"+requestdata['modifiedbyrole']
                +"' WHERE userid = "+str(requestdata['userid'])
                +" and domainid = "+str(requestdata['domainid'])+";")
                queryresult = icesession.execute(assignprojectsquery2)
            else:
                return jsonify(res)
        else:
            app.logger.warn('Empty data received. assign projects.')
            return jsonify(res)
        res={'rows':'Success'}
        return jsonify(res)
    except Exception as assignprojectsexc:
        servicesException("assignProjects_ICE",assignprojectsexc)
        return jsonify(res)

# service fetches all users
@app.route('/admin/getAllUsers_Nineteen68',methods=['POST'])
def getAllUsers_Nineteen68():
    app.logger.info("Inside getAllUsers_Nineteen68")
    res={'rows':'fail'}
    try:
        queryforallusers=("select userid, username, defaultrole from users")
        queryresult = n68session.execute(queryforallusers)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as getallusersexc:
        servicesException("getAllUsers_Nineteen68",getallusersexc)
        return jsonify(res)

@app.route('/admin/getAvailablePlugins',methods=['POST'])
def getAvailablePlugins():
    app.logger.info("Inside getAvailablePlugins")
    res={'rows':'fail'}
    try:
        ice_plugins_list = []
        for keys in licensedata['plugins']['ice']:
            if(licensedata['plugins']['ice'][keys] == True):
                ice_plugins_list.append(keys)
        res={'rows':ice_plugins_list}
        return jsonify(res)
    except Exception as getallusersexc:
        servicesException("getAvailablePlugins",getallusersexc)
        return jsonify(res)

################################################################################
# END OF ADMIN SCREEN
################################################################################


################################################################################
# BEGIN OF REPORTS
# INCLUDES : all reports related actions
################################################################################

#fetching all the suite details
@app.route('/reports/getAllSuites_ICE',methods=['POST'])
def getAllSuites_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getAllSuites_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
        #the code below is commented as per the new requirement
		#ALM #460 - Reports - HTML report takes very
        #long time to open/ hangs when report size is 5MB above
		#author - vishvas.a modified date:27-Sep-2017
            if(requestdata["query"] == 'domainid'):
                getallsuitesquery1 = ("select domainid from icepermissions "
                    +"where userid="+requestdata['userid']+";")
                queryresult = icesession.execute(getallsuitesquery1)
            elif(requestdata["query"] == 'suites'):
                if(requestdata["subquery"] == 'releases'):
                    getallsuitesquery6 = ("select releaseid from releases "
                        +"where projectid="+requestdata['projectid']+query['delete_flag'])
                    queryresult = icesession.execute(getallsuitesquery6)
                elif(requestdata["subquery"] == 'cycles'):
                    getallsuitesquery7 =("select cycleid from cycles "
                        +"where releaseid="+requestdata['releaseid']+query['delete_flag'])
                    queryresult = icesession.execute(getallsuitesquery7)
            elif(requestdata["query"] == 'projects'):
                getallsuitesquery8 = ("select projectids from icepermissions "
                    +"where userid="+requestdata['userid'])
                queryresult = icesession.execute(getallsuitesquery8)
##            elif(requestdata["query"] == 'projectsUnderDomain'):
##                getallsuitesquery2 =("select projectid from projects "
##                                +"where domainid="+requestdata['domainid']+";")
##                queryresult = icesession.execute(getallsuitesquery2)
##            elif(requestdata["query"] == 'releasesUnderProject'):
##                getallsuitesquery3 = ("select releaseid from releases "
##                                +"where projectid="+requestdata['projectid'])
##                queryresult = icesession.execute(getallsuitesquery3)
##            elif(requestdata["query"] == 'cycleidUnderRelease'):
##                getallsuitesquery4 =("select cycleid from cycles "
##                            +"where releaseid="+requestdata['releaseid'])
##                queryresult = icesession.execute(getallsuitesquery4)
##            elif(requestdata["query"] == 'suitesUnderCycle'):
##                getallsuitesquery5 = ("select testsuiteid,testsuitename "
##                    +"from testsuites where cycleid="+requestdata['cycleid'])
##                queryresult = icesession.execute(getallsuitesquery5)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. report suites details.')
            return jsonify(res)
    except Exception as getAllSuitesexc:
        servicesException("getAllSuites_ICE",getAllSuitesexc)
        res={'rows':'fail'}
        return jsonify(res)

#fetching all the suite after execution
@app.route('/reports/getSuiteDetailsInExecution_ICE',methods=['POST'])
def getSuiteDetailsInExecution_ICE():
    app.logger.info("Inside getSuiteDetailsInExecution_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            getsuitedetailsquery = ("select executionid,starttime,endtime,executionstatus "
                    +"from execution where testsuiteid="+requestdata['suiteid'])
            queryresult = icesession.execute(getsuitedetailsquery)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. report suites details execution.')
            return jsonify(res)
    except Exception as getsuitedetailsexc:
        servicesException("getSuiteDetailsInExecution_ICE",getsuitedetailsexc)
        return jsonify(res)

#fetching all the reports status
@app.route('/reports/reportStatusScenarios_ICE',methods=['POST'])
def reportStatusScenarios_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside reportStatusScenarios_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'executiondetails'):
                getreportstatusquery1 = ("select reportid,executionid,browser,comments,"
                +"executedtime,modifiedby,modifiedbyrole,modifiedon,report,status,"
                +"testscenarioid,testsuiteid from reports "
                +"where executionid="+requestdata['executionid']+" and testsuiteid="
                +requestdata['testsuiteid']+" ALLOW FILTERING")
                queryresult = icesession.execute(getreportstatusquery1)
            elif(requestdata["query"] == 'scenarioname'):
                getreportstatusquery2 = ("select testscenarioname "
                +"from testscenarios where testscenarioid="+requestdata['scenarioid']
                +" ALLOW FILTERING")
                queryresult = icesession.execute(getreportstatusquery2)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. report status of scenarios.')
            return jsonify(res)
    except Exception as getreportstatusexc:
        servicesException("reportStatusScenarios_ICE",getreportstatusexc)
        res={'rows':'fail'}
        return jsonify(res)

#fetching the reports
@app.route('/reports/getReport_Nineteen68',methods=['POST'])
def getReport_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside getReport_Nineteen68. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'projectsUnderDomain'):
                getreportquery1 =("select report,executedtime,testscenarioid "
                +"from reports where reportid=" +requestdata['reportid']
                +" ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery1)
            elif(requestdata["query"] == 'scenariodetails'):
                getreportquery2 =("select testscenarioname,projectid "
                +"from testscenarios where testscenarioid="
                + requestdata['scenarioid']+query['delete_flag'])
                queryresult = icesession.execute(getreportquery2)
            elif(requestdata["query"] == 'cycleid'):
                getreportquery3 =("select cycleid from testsuites where "
                +"testsuiteid=" + requestdata['suiteid']
                + " and testsuitename = '" + requestdata['suitename']+"'"
                + query['delete_flag'])
                queryresult = icesession.execute(getreportquery3)
            elif(requestdata["query"] == 'cycledetails'):
                getreportquery4 =("select cyclename,releaseid from cycles "
                +"where cycleid=" + requestdata['cycleid']  + query['delete_flag'])
                queryresult = icesession.execute(getreportquery4)
            elif(requestdata["query"] == 'releasedetails'):
                getreportquery5 =("select releasename,projectid from releases "
                +"where releaseid=" + requestdata['releaseid'] + query['delete_flag'])
                queryresult = icesession.execute(getreportquery5)
            elif(requestdata["query"] == 'projectdetails'):
                getreportquery6 =("select projectname,domainid from projects "
                +"where projectid=" + requestdata['projectid']  + query['delete_flag'])
                queryresult = icesession.execute(getreportquery6)
            elif(requestdata["query"] == 'domaindetails'):
                getreportquery7 =("select domainname from domains where "
                +"domainid=" + requestdata['domainid'] + " ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery7)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. report.')
            return jsonify(res)
    except Exception as getreportexc:
        servicesException("getReport_Nineteen68",getreportexc)
        return jsonify(res)

#export json feature on reports
@app.route('/reports/exportToJson_ICE',methods=['POST'])
def exportToJson_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside exportToJson_ICE. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'reportdata'):
                exporttojsonquery1 = ("select report from reports "
                +"where reportid ="+ requestdata['reportid'] + " ALLOW FILTERING ")
                queryresult = icesession.execute(exporttojsonquery1)
            elif(requestdata["query"] == 'scenarioid'):
                exporttojsonquery2 = ("select testscenarioid from reports "
                +"where reportid ="+ requestdata['reportid'] + " ALLOW FILTERING ")
                queryresult = icesession.execute(exporttojsonquery2)
            elif(requestdata["query"] == 'scenarioname'):
                exporttojsonquery3 = ("select testscenarioname from "
                +"testscenarios where testscenarioid="+requestdata['scenarioid']
                +query['delete_flag'])
                queryresult = icesession.execute(exporttojsonquery3)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.warn('Empty data received. JSON Exporting.')
            return jsonify(res)
    except Exception as exporttojsonexc:
        servicesException("exportToJson_ICE",exporttojsonexc)
        res={'rows':'fail'}
        return jsonify(res)

################################################################################
# END OF REPORTS
################################################################################


################################################################################
# BEGIN OF HISTORY
################################################################################

##def createHistory(query, table, request_data):
##    try:
##        history={}
##        createclone=False
##        requestdata=dict(request_data)
##        if(requestdata.has_key('history') and requestdata['history'] != None):
##            req_history=requestdata['history']
##            for keys in req_history:
##                history[keys.encode('utf-8')]=req_history[keys].encode('utf-8')
##        if(requestdata.has_key("query")):
##            del requestdata["query"]
##        if(requestdata.has_key("subquery")):
##            createclone=True
##            del requestdata["subquery"]
##        if(requestdata.has_key("modifiedflag")):
##            del requestdata["modifiedflag"]
##        primary_keys={'users':['userid'],
##                    'projects':['projectid','domainid','projectname'],
##                    'cycles':['cycleid','releaseid','cyclename'],
##                    'releases':['releaseid','projectid','releasename'],
##                    'icepermissions':['userid','domainid'],
##                    'modules':['moduleid','projectid','modulename','versionnumber'],
##                    'testsuites':['testsuiteid','cycleid','testsuitename','versionnumber'],
##                    'testscenarios':['testscenarioid','projectid','testscenarioname','versionnumber'],
##                    'screens':['screenid','projectid','screenname','versionnumber'],
##                    'testcases':['testcaseid','screenid','testcasename','versionnumber']
##                    }
##        versionquery=''
##        if(query=='submit'):
##            if(table=='screens'):
##                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['screenID_c']
##            elif(table=='testscenarios'):
##                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['testScenarioID_c']
##            elif(table=='modules'):
##                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['moduleID_c']
##            elif(table=='testcases'):
##                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['testCaseID_c']
##        else:
##            versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+str(requestdata[primary_keys[table][0]])
##        if(table=='users'):
##            queryresult=n68session.execute(versionquery)
##        else:
##            queryresult=icesession.execute(versionquery)
##        if(query=='submit' and requestdata['status']=='complete'):
##            version=getHistoryLatestVersion(queryresult.current_rows,table,history,query)
##        else:
##            version=getHistoryLatestVersion(queryresult.current_rows,table,history)
##        value=""
##        if(query=='create'):
##            data=str(requestdata)#.replace("'","\'").replace('"',"'")
##            if(createclone):
##                desc_str='Replicated '
##            else:
##                desc_str='Created '
##            value={
##            'description':desc_str+table[:-1]+' with values '+data,
##            'timestamp':str(getcurrentdate()),
##            'user':str(requestdata['createdby'])
##            }
##        elif(query=='update'):
##            data={}
##            for keys in requestdata:
##                if (keys not in primary_keys[table] and keys != 'modifiedby'
##                and keys != 'modifiedon' and keys != 'modifiedbyrole'):
##                    data[keys]=requestdata[keys]
##            data=str(data).replace("'","\'").replace('"',"'")
##            user_str=''
##            if(table=='projects'):
##                user_str=requestdata['createdby']
##            else:
##                user_str=requestdata['modifiedby']
##            value={
##            'description':'Updated properties: '+str(data),
##            'timestamp':str(getcurrentdate()),
##            'user':str(user_str)
##            }
##        elif(query=='assign'):
##            user_str=''
##            if(requestdata['alreadyassigned']!=True):
##                user_str=requestdata['createdby']
##            else:
##                user_str=requestdata['modifiedby']
##            value={
##            'description':'Assigned project '+str(requestdata['projectids'])+'with domain '+str(requestdata['domainid'])+' to user '+str(requestdata['userid']),
##            'timestamp':str(getcurrentdate()),
##            'user':str(user_str)
##            }
##        elif(query=='rename'):
##            desc_str=''
##            if(table=='modules'):
##                desc_str='Renamed module to '+requestdata['modulename']
##            elif(table=='testscenarios'):
##                desc_str='Renamed scenario to '+requestdata['testscenarioname']
##            elif(table=='screens'):
##                desc_str='Renamed screen to '+requestdata['screenname']
##            elif(table=='testcases'):
##                desc_str='Renamed testcase to '+requestdata['testcasename']
##            value={
##            'description':desc_str,
##            'timestamp':str(getcurrentdate()),
##            'user':str(requestdata['modifiedby'])
##            }
##        elif(query=='submit'):
##            desc_str=''
##            if(requestdata['status']=='review'):
##                if(table=='modules'):
##                    desc_str='Submitted module '+requestdata['details']['moduleName']+' for review'
##                elif(table=='testscenarios'):
##                    desc_str='Submitted scenario '+requestdata['details']['testScenarioName']+' for review'
##                elif(table=='screens'):
##                    desc_str='Submitted screen '+requestdata['details']['screenName']+' for review'
##                elif(table=='testcases'):
##                    desc_str='Submitted testcase '+requestdata['details']['testCaseName']+' for review'
##            elif(requestdata['status']=='complete'):
##                if(table=='modules'):
##                    desc_str='Completed module '+requestdata['details']['moduleName']
##                elif(table=='testscenarios'):
##                    desc_str='Completed scenario '+requestdata['details']['testScenarioName']
##                elif(table=='screens'):
##                    desc_str='Completed screen '+requestdata['details']['screenName']
##                elif(table=='testcases'):
##                    desc_str='Completed testcase '+requestdata['details']['testCaseName']
##            elif(requestdata['status']=='reassigned'):
##                if(table=='modules'):
##                    desc_str='Reassigned module '+requestdata['details']['moduleName']+' for review'
##                elif(table=='testscenarios'):
##                    desc_str='Reassigned scenario '+requestdata['details']['testScenarioName']+' for review'
##                elif(table=='screens'):
##                    desc_str='Reassigned screen '+requestdata['details']['screenName']+' for review'
##                elif(table=='testcases'):
##                    desc_str='Reassigned testcase '+requestdata['details']['testCaseName']+' for review'
##            value={
##            'description':desc_str,
##            'timestamp':str(getcurrentdate()),
##            'user':str(requestdata['username'])
##            }
##        value=str(value).replace("'",'\"')
##        history[version]=value
##        del requestdata
##        return history
##    except Exception as e:
##        servicesException("createHistory",e)
##
##
##def getHistoryLatestVersion(res,table,hist,*args):
##    try:
##        oldverslist=[]
##        histFlag=False
##        versions=''
##        newver=''
##        if (hist is not None and len(hist)!=0):
##            oldverslist=hist.keys()
##            histFlag=True
##        if (len(res)!=0):
##            if(table=='users'):
##                versions=res[0]['nineteen68.getversions(history)']
##            else:
##                versions=res[0]['icetestautomation.getversions(history)']
##            if(versions==''):
##                return '000.001'
##            elif(len(oldverslist)==0):
##                oldverslist=versions.split(',')
##        elif (not histFlag):
##            return '000.000'
##        oldver=max(oldverslist)
##        if(len(args)!=0):
##            import math
##            newver = str(math.ceil(float(oldver)))
##            newver=newver.split('.')
##        else:
##            newver=str(float(oldver)+0.001).split('.')
##        if(len(newver[0])==1):
##            newver[0]="00"+newver[0]
##        elif(len(newver[0])==2):
##            newver[0]="0"+newver[0]
##        if(len(newver[1])==1):
##            newver[1]=newver[1]+"00"
##        elif(len(newver[1])==2):
##            newver[1]=newver[1]+"0"
##        newver= '.'.join(newver)
##        return newver
##    except Exception as e:
##        app.logger.error("Error in getHistoryLatestVersion")
##
################################################################################
# END OF HISTORY
################################################################################


################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################

#encrpytion utility AES
@app.route('/utility/encrypt_ICE/aes',methods=['POST'])
def encrypt_ICE():
    app.logger.info("Inside encrypt_ICE")
    res = "fail"
    try:
        import base64
        from Crypto.Cipher import AES
        BS = 16
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        key = b'\x74\x68\x69\x73\x49\x73\x41\x53\x65\x63\x72\x65\x74\x4b\x65\x79'
        raw=request.data
        if not (raw is None and raw is ''):
            raw = pad(raw)
            cipher = AES.new( key, AES.MODE_ECB)
            res={'rows':base64.b64encode(cipher.encrypt( raw ))}
            return jsonify(res)
        else:
            app.logger.error("Invalid input")
            return str(res)
    except Exception as e:
        servicesException("encrypt_ICE",e)
        return str(res)

#directly updates license data
@app.route('/utility/dataUpdator_ICE',methods=['POST'])
def dataUpdator_ICE():
    app.logger.info("Inside dataUpdator_ICE")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if requestdata['query'] == 'testsuites':
                count = requestdata['count']
                userid = requestdata['userid']
                response = counterupdator('testsuites',userid,count)
                if response != True:
                    res={'rows':'fail'}
                else:
                    res={'rows':'success'}
            else:
                res = {'rows':'fail'}
        else:
            app.logger.warn('Empty data received. Data Updator.')
    except Exception as e:
        servicesException("dataUpdator_ICE",e)
    return jsonify(res)

#directly updates user access
@app.route('/utility/userAccess_Nineteen68',methods=['POST'])
def userAccess_Nineteen68():
    app.logger.info("Inside userAccess_Nineteen68")
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            roleid=requestdata['roleid']
            servicename=requestdata['servicename']
            roleaccessquery = ("select servicelist from userpermissions "
                +"where roleid ="+ roleid + " ALLOW FILTERING ")
            queryresult = n68session.execute(roleaccessquery)
            statusflag = False
            for each in queryresult.current_rows[0]['servicelist']:
                if servicename == str(each):
                    statusflag = True
                    break
            if statusflag:
                res={'rows':'True'}
            else:
                res={'rows':'False'}
        else:
            app.logger.warn('Empty data received. user Access Permission.')
    except Exception as useraccessexc:
        servicesException("userAccess_Nineteen68",useraccessexc)
    return jsonify(res)
################################################################################
# END OF UTILITIES
################################################################################

@app.route('/server',methods=['POST'])
def checkServer():
    app.logger.info("Inside checkServer")
    response = "fail"
    status = 500
    from flask import Response
    try:
        if(onlineuser == True or offlineuser == True):
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
    for keys in licensedata['plugins']['ice']:
        if(licensedata['plugins']['ice'][keys] == True):
            ice_plugins_list.append(keys)
    res={"id":"da9b196d-8021-4a68-be2b-753ec267305e","res":"fail","ts_now":str(datetime.now()),"connect_time":str(datetime.now()),"plugins":str(ice_plugins_list)}
    response = {"node_check":False,"ice_check":wrap(json.dumps(res),ice_ndac_key)}
    ice_uuid=None
    ice_ts=None
    try:
        requestdata=json.loads(request.data)
        app.logger.info("Inside updateActiveIceSessions. Query: "+str(requestdata["query"]))
        if not isemptyrequest(requestdata):
            activeicesessions=json.loads(unwrap(redisSession.get('icesessions'),db_keys))
            if(requestdata['query']=='disconnect'):
                username=requestdata['username'].lower()
                if(activeicesessions.has_key(username)):
                    del activeicesessions[username]
                    redisSession.set('icesessions',wrap(json.dumps(activeicesessions),db_keys))
                res['res']="success"

            elif(requestdata['query']=='connect' and requestdata.has_key('icesession')):
                icesession = unwrap(requestdata['icesession'],ice_ndac_key)
                icesession = json.loads(icesession)
                ice_uuid=icesession['ice_id']
                ice_ts=icesession['connect_time']
                if('.' not in ice_ts):
                    ice_ts = ice_ts + '.000000'
                username=icesession['username'].lower()
                latest_access_time=datetime.strptime(ice_ts, '%Y-%m-%d %H:%M:%S.%f')
                res['id']=ice_uuid
                res['connect_time']=ice_ts
                app.logger.debug("Connected clients: "+str(activeicesessions.keys()))

                #To check whether user exists in db or not
                authenticateuser = "select userid from users where username='"+username+"' ALLOW FILTERING"
                queryresult = n68session.execute(authenticateuser)
                if len(queryresult.current_rows) == 0:
                    res['err_msg'] = "Unauthorized: Access denied, user is not registered with Nineteen68"
                    response = {"node_check":"userNotValid","ice_check":wrap(json.dumps(res),ice_ndac_key)}
                else:
                    #To reject connection with same usernames
                    user_channel=redisSession.pubsub_numsub("ICE1_normal_"+username,"ICE1_scheduling_"+username)
                    user_channel_cnt=int(user_channel[0][1]+user_channel[1][1])
                    if(user_channel_cnt == 0 and activeicesessions.has_key(username)):
                        del activeicesessions[username]
                    if(activeicesessions.has_key(username) and activeicesessions[username] != ice_uuid):
                        res['err_msg'] = "Connection exists with same username"
                        response["ice_check"]=wrap(json.dumps(res),ice_ndac_key)
                    #To check if license is available
                    elif(len(activeicesessions)>=int(licensedata['allowedIceSessions'])):
                        res['err_msg'] = "All ice sessions are in use"
                        response["ice_check"]=wrap(json.dumps(res),ice_ndac_key)
                    #To add in active ice sessions
                    else:
                        activeicesessions=json.loads(unwrap(redisSession.get('icesessions'),db_keys))
                        activeicesessions[username] = ice_uuid
                        redisSession.set('icesessions',wrap(json.dumps(activeicesessions),db_keys))
                        res['res']="success"
                        response = {"node_check":"allow","ice_check":wrap(json.dumps(res),ice_ndac_key)}
        else:
            app.logger.warn('Empty data received. updateActiveIceSessions.')
    except redis.ConnectionError as exc:
        app.logger.critical(printErrorCodes('217'))
        servicesException("updateActiveIceSessions",exc)
    except Exception as exc:
        servicesException("updateActiveIceSessions",exc)
    return jsonify(response)

##################################################
# BEGIN OF CHATBOT
##################################################

#Prof J First Service: Getting Best Matches
@app.route('/chatbot/getTopMatches_ProfJ',methods=['POST'])
def getTopMatches_ProfJ():
    app.logger.info("Inside getTopMatches_ProfJ")
    try:
##        print "getting top matches for ya.."
##        print request.data
        query = str(request.data)
        global newQuesInfo
        global savedQueries
        #Importing Modules for Prof J
##        import xlrd
##        from collections import OrderedDict
##        import simplejson as json
##        from nltk.stem import PorterStemmer

        #Step 2 Matching query with Data
        profj = ProfJ(pages,questions,answers,keywords,weights,pquestions,newQuesInfo,savedQueries)
        response,newQuesInfo,savedQueries = profj.start(query)
        #if response[0][1] == "Please be relevant..I work soulfully for Nineteen68":
            #response[0][1] = str(chatbot.get_response(query))
##        print "---------------The status of global variable---------------"
##        print "newQuesInfo after this query: ",newQuesInfo
##        print "State of saved query after this query: ",savedQueries
##        print"------------------------------------------------------------"
        res={'rows':response}
    except Exception as e:
        res={'rows':'fail'}
    return jsonify(res)

#Prof J Second Service: Updating the Question's Frequency
@app.route('/chatbot/updateFrequency_ProfJ',methods=['POST'])
def updateFrequency_ProfJ():
    app.logger.info("Inside updateFrequency_ProfJ")
    try:
##        print "updating the frequency.."
##        print request.data
        qid = request.data
        weights[int(qid)] += 1
##        print weights[int(qid)]
        temp = []
        temp.append(qid)
        temp.append(weights[int(qid)])
##        print(weights[int(qid)])
        response = True
        res={'rows': response}
    except Exception as e:
        res={'rows':'fail'}
    return jsonify(res)

################################################################################
# END OF CHATBOT
################################################################################


################################################################################
# BEGIN OF INTERNAL COMPONENTS
################################################################################

################################################################################
# BEGIN OF GLOBAL VARIABLES
################################################################################

query={}
query['module']='select modulename,testscenarioids FROM modules where moduleid='
query['scenario']='select testscenarioname FROM testscenarios where testscenarioid='
query['screen']='select screenname FROM screens where screenid='
query['testcase']='select testcasename FROM testcases where testcaseid='
#Getting complete details of single node
mine='\x4e\x36\x38\x53\x51\x4c\x69\x74\x65\x44\x61\x74\x61\x53\x65\x63\x72\x65\x74\x4b\x65\x79\x43\x6f\x6d\x70\x4f\x4e\x65\x6e\x74\x73'
query['module_details']='select * from modules where moduleid='
offreg='\x69\x41\x6d\x4e\x6f\x74\x4f\x6e\x6c\x69\x6e\x65\x55\x73\x65\x72\x49\x4e\x65\x65\x64\x4e\x6f\x74\x52\x65\x67\x69\x73\x74\x65\x72'
query['testscenario_details']='select * from testscenarios where testscenarioid='
query['screen_details']='select * from screens where screenid='
query['testcase_details']='select * from testcases where testcaseid='
query['delete_flag'] = ' and deleted=false allow filtering'
numberofdays=1
omgall="\x4e\x69\x6e\x65\x74\x65\x65\x6e\x36\x38\x6e\x64\x61\x74\x63\x6c\x69\x63\x65\x6e\x73\x69\x6e\x67"
ndacinfo = {
    "macid": "",
    "tkn": "",
}
ecodeServices = {"authenticateUser_Nineteen68":"300","authenticateUser_Nineteen68_ldap":"301",
    "getRoleNameByRoleId_Nineteen68":"302","authenticateUser_Nineteen68_projassigned":"303",
    "loadUserInfo_Nineteen68":"304","getReleaseIDs_Ninteen68":"305","getCycleIDs_Ninteen68":"306",
    "getProjectType_Nineteen68":"307","getProjectIDs_Nineteen68":"308","getAllNames_ICE":"309",
    "testsuiteid_exists_ICE":"310","testscenariosid_exists_ICE":"311","testscreenid_exists_ICE":"312",
    "testcaseid_exists_ICE":"313","get_node_details_ICE":"314","delete_node_ICE":"315",
    "insertInSuite_ICE":"316","insertInScenarios_ICE":"317","insertInScreen_ICE":"318",
    "insertInTestcase_ICE":"319","updateTestScenario_ICE":"320","updateModule_ICE":"321",
    "updateModulename_ICE":"322","updateTestscenarioname_ICE":"323","updateScreenname_ICE":"324",
    "updateTestcasename_ICE":"325","submitTask":"326","getKeywordDetails":"327","readTestCase_ICE":"328",
    "getScrapeDataScreenLevel_ICE":"329","debugTestCase_ICE":"330","updateScreen_ICE":"331",
    "updateTestCase_ICE":"332","getTestcaseDetailsForScenario_ICE":"333","getTestcasesByScenarioId_ICE":"334",
    "readTestSuite_ICE":"335","updateTestSuite_ICE":"336","ExecuteTestSuite_ICE":"337",
    "ScheduleTestSuite_ICE":"338","qcProjectDetails_ICE":"339","saveQcDetails_ICE":"340",
    "viewQcMappedList_ICE":"341","getUserRoles":"342","getDetails_ICE":"343","getNames_ICE":"344",
    "getDomains_ICE":"345","getAssignedProjects_ICE":"346","createUser_Nineteen68":"347",
    "getUserData_Nineteen68":"348","updateUser_Nineteen68":"349","createProject_ICE":"350",
    "updateProject_ICE":"351","getUsers_Nineteen68":"352","assignProjects_ICE":"353",
    "getAllUsers_Nineteen68":"354","getAvailablePlugins":"355","getAllSuites_ICE":"356",
    "getSuiteDetailsInExecution_ICE":"357","reportStatusScenarios_ICE":"358","getReport_Nineteen68":"359",
    "exportToJson_ICE":"360","createHistory":"361","encrypt_ICE":"362","dataUpdator_ICE":"363",
    "userAccess_Nineteen68":"364","checkServer":"365","updateActiveIceSessions":"366",
    "counterupdator":"367","getreports_in_day":"368","getsuites_inititated":"369","getscenario_inititated":"370",
    "gettestcases_inititated":"371","modelinfoprocessor":"372","dataprocessor":"373","reportdataprocessor":"374"
}

################################################################################
# END OF GLOBAL VARIABLES
################################################################################

#################################################################################
# BEGIN OF GENERIC FUNCTIONS
#################################################################################
def initLoggers(level):
    logLevel = logging.ERROR
    consoleFormat = "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s"
    if level.debug:
        logLevel = logging.DEBUG
        consoleFormat = "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s"
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
    fileFormatter = logging.Formatter('''{"timestamp": "%(asctime)s", "file": "%(pathname)s", "lineno.": %(lineno)d, "level": "%(levelname)s", "message": "%(message)s"}''')
    fileHandler = TimedRotatingFileHandler(logspath+'/ndac/ndac'+datetime.now().strftime("_%Y%m%d-%H%M%S")+'.log',when='d', encoding='utf-8', backupCount=1)
    fileHandler.setFormatter(fileFormatter)
    app.logger.addHandler(fileHandler)
    if level.test:
        consoleHandler.setLevel(logging.WARNING)
        fileHandler.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logLevel)
    app.logger.propagate = False
    app.logger.info("Inside initLoggers")

def printErrorCodes(ecode):
    msg = "[ECODE: " + ecode + "] " + ERR_CODE[ecode]
    return msg

def servicesException(srv, exc):
    app.logger.debug("Exception occured in "+srv)
    app.logger.debug(exc)
    app.logger.error("[ECODE: " + ecodeServices[srv] + "] Internal error occured in api")

def isemptyrequest(requestdata):
    flag = False
    global usersession
    if (onlineuser == True):
        for key in requestdata:
            value = requestdata[key]
            if (key != 'additionalroles'
                and key != 'getparampaths' and key != 'testcasesteps'):
                if value == 'undefined' or value == '' or value == 'null' or value == None:
                    app.logger.warn(str(key)+" is empty")
                    flag = True
    else:
        currenttime=datetime.now()
        if usersession != False:
            if (currenttime >= offlinestarttime and currenttime <= offlineendtime):
                for key in requestdata:
                    value = requestdata[key]
                    if (key != 'additionalroles' and key != 'getparampaths'
                     and key != 'testcasesteps'):
                        if value == 'undefined' or value == '' or value == 'null' or value == None:
                            app.logger.warn(str(key)+" is empty")
                            flag = True
            else:
                stopserver()
                flag = True
        else:
            flag = True
            if offlineuser == True:
                app.logger.critical(printErrorCodes('204'))
            else:
                app.logger.critical(printErrorCodes('203'))
    return flag

def getcurrentdate():
    currentdate= datetime.now()
    beginingoftime = datetime.utcfromtimestamp(0)
    differencedate= currentdate - beginingoftime
    return long(differencedate.total_seconds() * 1000.0)

def testsuite_exists(project_id,module_name,version_number,moduleid=''):
    version_number=str(version_number)
    query['suite_check']="select moduleid FROM modules where projectid="+project_id+" and modulename='"+module_name+"' and versionnumber="+version_number+query['delete_flag']
    query['suite_check_id']="select moduleid FROM modules where projectid="+project_id+" and modulename='"+module_name+"' and moduleid="+moduleid+" and versionnumber="+version_number+query['delete_flag']

def testscenario_exists(project_id,testscenario_name,version_number,testscenario_id=''):
    version_number=str(version_number)
    query['scenario_check'] = "select testscenarioid from testscenarios where projectid="+project_id+" and testscenarioname='"+testscenario_name+"' and versionnumber="+version_number+query['delete_flag']
    query['scenario_check_id'] = "select testscenarioid from testscenarios where projectid="+project_id+" and testscenarioname='"+testscenario_name+"' and testscenarioid = "+testscenario_id+" and versionnumber="+version_number+query['delete_flag']


def testscreen_exists(project_id,screen_name,version_number,screen_id=''):
    version_number=str(version_number)
    query['screen_check'] = "select screenid from screens where projectid="+project_id+" and screenname='"+screen_name+"' and versionnumber="+version_number+query['delete_flag']
    query['screen_check_id'] = "select screenid from screens where projectid="+project_id+" and screenname='"+screen_name+"' and screenid = "+screen_id+" and versionnumber="+version_number+query['delete_flag']

def testcase_exists(screen_id,testcase_name,version_number,testcase_id=''):
    version_number=str(version_number)
    query['testcase_check'] = "select testcaseid from testcases where screenid="+screen_id+" and testcasename='"+testcase_name+"' and versionnumber="+version_number+query['delete_flag']
    query['testcase_check_id'] = "select testcaseid from testcases where screenid="+screen_id+" and testcasename='"+testcase_name+"' and testcaseid="+testcase_id+" and versionnumber="+version_number+query['delete_flag']

def get_delete_query(node_id,node_name,node_version_number,node_parentid,projectid=None):
    node_version_number=str(node_version_number)
    query['delete_module']="delete FROM modules WHERE moduleid="+node_id+" and modulename='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid+" IF EXISTS"
    query['delete_testscenario']="delete FROM testscenarios WHERE testscenarioid="+node_id+" and testscenarioname='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid+" IF EXISTS"
    query['delete_screen']="delete FROM screens WHERE screenid="+node_id+" and screenname='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid+" IF EXISTS"
    query['delete_testcase']="delete FROM testcases WHERE testcaseid="+node_id+" and testcasename='"+node_name+"' and versionnumber="+node_version_number+" and screenid="+node_parentid+" IF EXISTS"

############################
# END OF GENERIC FUNCTIONS
############################
################################################################################
# BEGIN OF COUNTERS
################################################################################
def counterupdator(updatortype,userid,count):
    status=False
    try:
        beginingoftime = datetime.utcfromtimestamp(0)
        currentdateindays = getupdatetime() - beginingoftime
        currentdate = long(currentdateindays.total_seconds() * 1000.0)
        updatorarray = ["update counters set counter=counter + ",
                    " where counterdate= "," and userid = "," and countertype= ",";"]
        updatequery=(updatorarray[0]+str(count)+updatorarray[1]
                    +str(currentdate)+updatorarray[2]+userid+updatorarray[3]+"'"
                    +updatortype+"'"+updatorarray[4])
        icesession.execute(updatequery)
        status = True
    except Exception as counterupdatorexc:
        servicesException("counterupdator",counterupdatorexc)
    return status

def getreports_in_day(bgnts,endts):
    res = {"rows":"fail"}
    try:
        query=("select * from reports where executedtime  > "
            +str(bgnts)+" and executedtime <= "+str(endts)+" allow filtering;")
        queryresult = icesession.execute(query)
        res= {"rows":queryresult.current_rows}
    except Exception as getreports_in_dayexc:
        servicesException("getreports_in_day",getreports_in_dayexc)
    return res

def getsuites_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        suitequery=("select * from counters where counterdate > "+str(bgnts)
        +" and counterdate <= "+str(endts)
        +" and countertype='testsuites' ALLOW FILTERING;")
        queryresult = icesession.execute(suitequery)
        res= {"rows":queryresult.current_rows}
    except Exception as getsuites_inititatedexc:
        servicesException("getsuites_inititated",getsuites_inititatedexc)
    return res

def getscenario_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        scenarioquery=("select * from counters where counterdate > "+str(bgnts)
        +" and counterdate <= "+str(endts)
        +" and countertype='testscenarios' ALLOW FILTERING;")
        queryresult = icesession.execute(scenarioquery)
        res= {"rows":queryresult.current_rows}
    except Exception as getscenario_inititatedexc:
        servicesException("getscenario_inititated",getscenario_inititatedexc)
    return res

def gettestcases_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        testcasesquery=("select * from counters where counterdate > "+str(bgnts)
        +" and counterdate <= "+str(endts)
        +" and countertype='testcases' ALLOW FILTERING;")
        queryresult = icesession.execute(testcasesquery)
        res = {"rows":queryresult.current_rows}
    except Exception as gettestcases_inititatedexc:
        servicesException("gettestcases_inititated",gettestcases_inititatedexc)
    return res

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
        bgnts=gettimestamp(bgnyesday)
        endts=gettimestamp(bgnoftday)
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
##            usr_data=0
            for eachrow in dataresp['rows']:
##                userin_data={}
##                userin_data['rns'] = str(eachrow['counter'])
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
##                userin_data['id'] = str(eachrow['userid'])
##                usr_data.append(userin_data)
            respobj['suite_cnt'] = str(total_cnt)
        elif datatofetch == 'testscenarios':
            dataresp=getscenario_inititated(fromdate,todate)
##            usr_data=0
            for eachrow in dataresp['rows']:
##                userin_data={}
##                userin_data['rns'] = str(eachrow['counter'])
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
##                userin_data['id'] = str(eachrow['userid'])
##                usr_data.append(userin_data)
            respobj['cnario_cnt'] = str(total_cnt)
        elif datatofetch == 'testcases':
            dataresp=gettestcases_inititated(fromdate,todate)
##            usr_data=0
            for eachrow in dataresp['rows']:
##                userin_data={}
##                userin_data['rns'] = str(eachrow['counter'])
                total_cnt = total_cnt + int(eachrow['counter'])
                usr_list.append(str(eachrow['userid']))
##                userin_data['id'] = str(eachrow['userid'])
##                usr_data.append(userin_data)
            respobj['tcases_cnt'] = str(total_cnt)
##        respobj['day'] = str(date)
##        respobj['active_usrs'] = usr_data
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
# START LICENSING COMPONENTS
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

def gettimestamp(date):
    timestampdata=''
    import calendar
    date= datetime.strptime(str(date),"%Y-%m-%d %H:%M:%S")
    timestampdata = calendar.timegm(date.utctimetuple()) * 1000
    return timestampdata

def basecheckonls():
    app.logger.info("Inside basecheckonls")
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
            actresp = unwrap(str(connectresponse),omgall)
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
                    global licensedata
                    global onlineuser
                    licensedata=actresp['ldata']
                    if token==actresp['token']:
                        basecheckstatus = True
                    else:
                        dbdata['tkn']=actresp['token']
                        basecheckstatus=dataholder('update',dbdata)
                    onlineuser = True
        else:
            if lsRetryCount<3:
                app.logger.error(printErrorCodes('215'))
                basecheckonls()
            else:
                app.logger.critical(printErrorCodes('216'))
                startTwoDaysTimer()
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('201'))
    return basecheckstatus

def updateonls():
    app.logger.info("Inside updateonls")
    try:
        global licensedata
        dbdata=dataholder('select')
        EXPECTING_RESPONSE=str(int(time.time()*24150))
        modelinfores = modelinfoprocessor()
        if(dbdata.has_key('mdlinfo')):
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
            cronograph()
            res = json.loads(unwrap(str(updateresponse),omgall))
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
                if(res.has_key('ldata')):
                    licensedata = res['ldata']
        else:
            if lsRetryCount<3:
                app.logger.error(printErrorCodes('215'))
                updateonls()
            else:
                dbdata['mdlinfo']=modelinfores
                dataholder('update',dbdata)
                app.logger.critical(printErrorCodes('216'))
                startTwoDaysTimer()
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('202'))

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
    global lsRetryCount,twoDayTimer
    lsRetryCount+=1
    connectionstatus=False
    try:
        lsresponse = requests.post('http://'+lsip+":5000/ndacrequest",data=data)
        if lsresponse.status_code == 200:
            dbdata=dataholder('select')
            if(dbdata.has_key('grace_period')):
                del dbdata['grace_period']
                dataholder('update',dbdata)
            lsRetryCount=0
            connectionstatus = lsresponse.content
            if (twoDayTimer != None and twoDayTimer.isAlive()):
                twoDayTimer.cancel()
                twoDayTimer=None
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('208'))
    return connectionstatus

def offlineuserenabler(startdate,enddate,usermac):
    enabled = False
    # this is provided as there was a request to create a key
    # without mac address
    if usermac != 'nomacaddress':
        mac = sysMAC
    else:
        mac = usermac
    if usermac in mac:
        hastimebegin=timerbegins(startdate,enddate)
        enabled = hastimebegin
    return enabled

def timerbegins(startdate,enddate):
    global offlinestarttime
    offlinestarttime=startdate
    global offlineendtime
    offlineendtime=enddate
    if ((offlinestarttime < offlineendtime) and
        (offlineendtime > datetime.now()) and (datetime.now() >= offlinestarttime)):
        global offlineuser
        global usersession
        usersession=True
        offlineuser = True
    return usersession

def scheduleenabler(starttime):
    try:
        import threading
        runningtime = starttime - datetime.now()
        delay = (runningtime).total_seconds()
        threading.Timer(delay, beginserver).start()
        global offlineuser
        offlineuser = True
    except Exception as e:
        app.logger.debug(e)
        app.logger.error(printErrorCodes('209'))

def cronograph():
    app.logger.info("Chronograph triggred")
    try:
        from threading import Timer
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
                data=unwrap(str(data),mine)
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
    if dbexists:
        dbdata=dataholder('select')
        if dbdata:
            if(dbdata.has_key('grace_period')):
                grace_period = dbdata['grace_period']
            dbmacid=dbdata['macid']
            sysmacid=sysMAC
            if len(dbmacid)==0:
                enndac=True
                dbdata['macid']=sysmacid
                dataholder('update',dbdata)
            elif dbmacid!=sysmacid:
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

    if errCode!=0:
        app.logger.error(printErrorCodes(errCode))
    return enndac

def beginserver():
    if cass_dbup and redis_dbup:
        serve(app,host='127.0.0.1',port=1990)
    else:
        app.logger.critical(printErrorCodes('207'))

def stopserver():
    global onlineuser, usersession, gracePeriodTimer
    if(gracePeriodTimer != None and gracePeriodTimer.isAlive()):
        gracePeriodTimer.cancel()
        gracePeriodTimer = None
    onlineuser = False
    usersession = False
    app.logger.error(printErrorCodes('205'))

def startTwoDaysTimer():
    from threading import Timer
    global twoDayTimer,gracePeriodTimer
    twoDayTimer = Timer(grace_period, stopserver)
    twoDayTimer.start()
    gracePeriodTimer = Timer(3600,saveGracePeriod)
    gracePeriodTimer.start()
    app.logger.info("Two day timer begins")

def saveGracePeriod():
    from threading import Timer
    global gracePeriodTimer,twoDayTimer
    if (twoDayTimer.isAlive()):
        dbdata = dataholder('select')
        if(dbdata.has_key('grace_period')):
            dbdata['grace_period']=dbdata['grace_period'] - 3600
        else:
            dbdata['grace_period']=169200
        dataholder('update',dbdata)
        gracePeriodTimer = Timer(3600,saveGracePeriod)
        gracePeriodTimer.start()

from Crypto import Random
from Crypto.Cipher import AES
BS = 16
def pad(data):
    padding = BS - len(data) % BS
    return data + padding * chr(padding)

def unpad(data):
    return data[0:-ord(data[-1])]

def unwrap(hex_data, key, iv='0'*16):
    data = ''.join(map(chr, bytearray.fromhex(hex_data)))
    aes = AES.new(key, AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data))

def wrap(data, key, iv='0'*16):
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(data)).encode('hex')

##################################
# END LICENSING SERVER COMPONENTS
##################################


####################################
#Begining of ProfJ assist Components
####################################

#Saving assist data in global variables
#Step 1 Loading Data from JSON
##try:
##    import sys
##    base = os.getcwd()
##    #path = base + "\\Portable_python\\ndac\\src\\assist"
##    #sys.path.append(path)

##    import sqlite3
##except:
##    app.logger.error('Error in accessing assist files..')


#Setting up Data
##try:
    # File to read the Data from SQLite File into an array.
##    import sqlite3
##except:
##    print "Error Imprting module sqlite."


class SQLite_DataSetup():
    try:
        def __init__(self):
            self.questions=[] # to store the questions
            self.pages=[] # to store the pages
            self.keywords=[] # to store the keywords
            self.weightages=[] # to store the weightages
            self.answers=[] # to store the answers
            self.pquestions=[] #preprocessed questions
            self.newQuesInfo=[] #list to store relevant info about new questions
    except:
        app.logger.error("Error in __init__ function.")

        # Function to Load Data using JSON file.
    def loadData(self):
       # print "wfsdvaqusgwnqbwh"
##        import os
        #print "OS.cwd()------------",os.getcwd()
##        base = os.getcwd()
##        print 'base',base
        path = assistpath + "/ProfJ.db"
        conn = sqlite3.connect(path)
        c = conn.cursor()
           # print data

        # Preparing the lists
        for row in c.execute('SELECT * FROM mainDB'):
            self.weightages.append(int(row[1]))
            self.questions.append(row[2])
            self.answers.append(row[3])
            self.keywords.append(row[4])
            self.pages.append(row[5])
            self.pquestions.append(row[6])

        for col in c.execute('SELECT * FROM NewQuestions'):
            info =[]
            info.append(col[1])
            info.append(col[2])
            info.append(col[3])
            self.newQuesInfo.append(info)
        conn.close()

    try:
        # Function to get the Pages.
        def getPages(self):
            return self.pages
    except:
        app.logger.error("Error in getPages()")

    try:
        # Function to return the Questions.
        def getQuestions(self):
            return self.questions
    except:
        app.logger.error("Error in getQuestions()")

    try:
        # Function to return the Answers.
        def getAnswers(self):
            return self.answers
    except:
        app.logger.error("Error in getAnswers()")

    try:
        # Function to retun the Weights.
        def getWeightages(self):
            return self.weightages
    except:
        app.logger.error("Error in getWeightages()")

    try:
        # Function to return Keywords.
        def getKeywords(self):
            return self.keywords
    except:
        app.logger.error("Error in getKeywords()")

    try:
        # Function to get the Processed Questions.
        def getPQuestions(self):
            return self.pquestions
    except:
        app.logger.error("Error in getPQuestions()")

    try:
        # Function to get the New Questions.
        def getNewQuesInfo(self):
            return self.newQuesInfo
    except:
        app.logger.error("Error in getNewQuesInfo()")

    try:
        # Function to update the captured Queries.
        def updateCaptureTable(self,savedQueries):
            t = []
            for list in savedQueries:
                temp = []
                temp.append(list[0])
                temp.append(list[1])
                temp1 = tuple(temp)
                t.append(temp1)
            #print t
            #inserting values in table:
            conn = sqlite3.connect('ProfJ.db')
            c = conn.cursor()
            c.executemany('INSERT INTO CapturedQueries VALUES (?,?)', t)
            conn.commit()
##            for row in c.execute('SELECT * FROM CapturedQueries'):
##                print row
            conn.close()
            return savedQueries
    except:
        app.logger.error("Error in updateCaptureTable()")
##
##    try:
##            # Function to update the weightages in Database[Used periodically by thread].
##            def updateWeightages(self,weightages):
##                print "inside update weightages..."
##                conn = sqlite3.connect('ProfJ.db')
##                c = conn.cursor()
##                for i in range(len(weightages)):
##                    c.execute('UPDATE mainDB SET Weightage= ? WHERE qid = ?',(weightage[i],i))
##                conn.commit()
##                conn.close()
##                return True
##    except:
##            print "Error in updateCaptureTable()"

    try:
        # Function to update the new questions in the database.
        def updateCaptureTable(self):
            return True
    except:
        app.logger.error("Error in updateCaptureTable()")

try:
    ds = SQLite_DataSetup()
    ds.loadData()
    questions = ds.getQuestions()
    pquestions = ds.getPQuestions()
    pages = ds.getPages()
    weights = ds.getWeightages()
    answers = ds.getAnswers()
    keywords = ds.getKeywords()
    #2 D array: Ques, processed Ques & Frequency
    newQuesInfo = ds.getNewQuesInfo()
    #A list to save every single relevant query asked by user
    savedQueries = [[]]
    updateW = [[]]
except:
    import traceback
    traceback.print_exc()
    app.logger.error('Unable to use assist module SQLite_DataSetups..')


#Training the Bot

#try:
    #chatbot = 0
    #import threading
    #def trainProfJ():

        #try:
            #from chatterbot import ChatBot
        #except:
            #app.logger.error('Portable python used doesnot have chatterbot module..please ask for latest portable python')
        #global chatbot
        #print "starting training parallely"
        #chatbot = ChatBot(

            #'Prof J',
            #trainer='chatterbot.trainers.ChatterBotCorpusTrainer'

        #)
        #Train based on the english corpus
        #chatbot.train("chatterbot.corpus.english")
       # print "chatbot training successfully completed.."

    #Starting chatbot training Parallely
    #threading.Thread(target = trainProfJ).start()
#except:
    #app.logger.error('Unable to train chatbot..Ensure that you have chatterbot modules in Portable Python')


#Updating the sqlite database
updateTime = 60
def updateWeightages():
    try:
        global weights
##        print "inside update weightages..."
        base = os.getcwd()
        path = assistpath+"/ProfJ.db"
        conn = sqlite3.connect(path)
        c = conn.cursor()
##        print "thread called the function...in every : ",updateTime, " seconds"
        for i in range(len(weights)):
            c.execute('UPDATE mainDB SET Weightage= ? WHERE qid = ?',(weights[i],i))
        conn.commit()
        conn.close()
        return True
    except:
        import traceback
        traceback.print_exc()
        app.logger.error('Cannot update weightages in ProfJ database')
#Invoking parallel thread which will update the weightages of the questions in the DB
try:

    from threading import Timer,Thread,Event
    class repeatedTimer():
       def __init__(self,t,hFunction):
          self.t=t
          self.hFunction = hFunction
          self.thread = Timer(self.t,self.handle_function)

       def handle_function(self):
          self.hFunction()
          self.thread = Timer(self.t,self.handle_function)
          self.thread.start()

       def start(self):
          self.thread.start()

       def cancel(self):
          self.thread.cancel()

    updaterThread = repeatedTimer(updateTime,updateWeightages)
    updaterThread.start()
except:
    import traceback
    traceback.print_exc()
    app.logger.error('Cannot access repeatedTimer Module..or it can not call periodic function to update the weightage.')


try:
    import logging
    import logging.config
    from nltk.stem import PorterStemmer
    import simplejson
except:
    import traceback
    traceback.print_exc()
    app.logger.error("Error in importing core modules ProfJ")

class ProfJ():

    def Preprocess(self,query_string):
        #creating configuration for logging
##        import os
        #print "OS.cwd()------------",os.getcwd()
##        base = os.getcwd()
##        print 'BASE in profJ',base
        path = assistpath + "/logging_config.conf"
        logging.config.fileConfig(path,disable_existing_loggers=False)

        # Create logger object. This will be used for logging.
        logger = logging.getLogger("ProfJ")

        logger.info("Qustion asked is "+query_string)

        #Step 1: Punctuations Removal
        query1_str = "".join(c for c in query_string if c not in ('@','!','.',':','>','<','"','\'','?','*','/','&','(',')','-'))
##        print "Query after Step 1 of processing:[punctuations removed] ",query1_str

        #Step 2: Converting string into lowercase
        query2 = [w.lower() for w in query1_str.split()]
        query2_str = " ".join(query2)
##        print "Query after Step 2 of processing:[lower Case] ",query2_str


        #Step 3: Correcting appostropes.. Need this dictionary to be quite large
        APPOSTOPHES = {"s" : "is", "'re" : "are","m":"am"}
        words = (' '.join(query2_str.split("'"))).split()
        query5 = [ APPOSTOPHES[word] if word in APPOSTOPHES else word for word in words]
##        print "Query after Step 3 of processing:[appostophes]: ",query5

        import simplejson
        #Step 4: Normalizing words
        path = assistpath + "/SYNONYMS.json"
        with open(path,"r") as data_file:
                SYNONYMS = simplejson.load(data_file)
        query6 = [ SYNONYMS[word] if word in SYNONYMS else word for word in query5]
##        print "Query after Step 6 of processing:[synonyms]: ",query6


        #Step 5: Stemming
        ps = PorterStemmer()
        query_final=set([ps.stem(i) for i in query6])
##        print "Query after Step 7 of processing:[stemming] ",query_final
        return query_final


    def matcher(self,query_final):
        intersection = []
        for q in self.pquestions:
            q1 = set (q.split(" "))
           # print "Supposedly Questions", q1
            intersection.append (len(query_final & q1))
           # print len(query_final & q1)
        return intersection

    def getTopX(self,intersection):
        relevance=[]
        cnt = 0
        for i in intersection:
            relevance.append(10**(i+2) + self.weights[cnt])
            cnt+=1

        max_index = [i[0] for i in sorted(enumerate(relevance), key=lambda x:x[1],reverse=True)]
        #max_value = [i[1] for i in sorted(enumerate(relevance), key=lambda x:x[1],reverse=True)]

        #print max_value
        # print max_index
        ans = []
        #print "-------------------------------------------------"
        for i in range(self.topX):
            #print questions_original[max_index[i]]
            if(intersection[max_index[i]]==0):
                break
            ans.append(self.questions[max_index[i]])
            #print (self.questions[max_index[i]]+ "( Intersection: "+str(intersection[max_index[i]])+ " Weightage: "+str(self.weights[max_index[i]])+")")
        #print "-------------------------------------------------"
        return ans

    def calculateRel(self,query_final):
            try:
                #Check whether query contains n68 domain or not
##                import sys
##                import os
##                base = os.getcwd()
##                path = base + "\\keywords_db.txt"
                path = assistpath+"/keywords_db.txt"
                f = open(path,"r")
                key = f.read()
                keywords = set(key.split())

                if (len(query_final)==0):
                    match=0
                else:
                    match=len(query_final & keywords)/float(len(query_final))
                #print "Percentage Match [In my domain]", match*100,"%"
                return match
            except:
                app.logger.error("keywords_db.txt not found.")
##                print "keywords_db.txt not foud."

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
        self.savedQueries = savedQueries # Captures all the "Relevant" queries asked by User, It is list of list[[query1,page1],[query2,page2]]

    def setState(self,state):
        self.state = state

    def start(self,userQuery):
        response = []
##        print "I am the right one"
        query_string = userQuery
        self.userQuery = userQuery
        if query_string is not None:
            #when all the plugins will be activeted
            currPage = "mindmaps"
            query_final = self.Preprocess(query_string)
            rel = self.calculateRel(query_final)
            if (rel > 0):
                temp = []
                temp.append(query_string)
                temp.append(currPage)
                self.savedQueries.append(temp)
                #getting intersection
                intersection = self.matcher(query_final)
                #displaying most common and most frequent
                ques = self.getTopX(intersection)
                if ques:
                    for i in range(len(ques)):
                        temp = []
                        temp.append(self.questions.index(ques[i]))
                        temp.append(self.questions[self.questions.index(ques[i])])
                        temp.append(self.answers[self.questions.index(ques[i])])
                        response.append(temp)
##                    print response
                else:
                    response = [[-1,"Sometimes, I may not have the information you need...We recorded your query..will get back to you soon",-1]]
                    flag = True
                    for nques in self.newQuesInfo:
                        if(str(query_final) is nques[1]):
                            nques[2] = nques[2] + 1
                            flag = False
                    if (flag):
                        temp =[]
                        temp.append(str(query_string))
                        temp.append(str(query_final))
                        temp.append(0)
                        self.newQuesInfo.append(temp)

                    #self.newKeys.append(query_string)
            else:
                response = [[-1, "Please be relevant..I work soulfully for Nineteen68", -1]]
        else:
            response = [-1, "Invalid Input...Please try again", -1]
        return response, self.newQuesInfo, self.savedQueries

#Basic Setup of ProfJ Done!
################################################
#End of ProfJ assist components
################################################
################################################################################
# END OF INTERNAL COMPONENTS
################################################################################

def main():
    global lsip,cass_dbup,redis_dbup,icesession,n68session,redisSession,licensedata,chronographTimer
    cleanndac = checkSetup()
    if not cleanndac:
        app.logger.critical(printErrorCodes('214'))
        return False

    try:
        ndac_conf = json.loads(open(config_path).read())
        lsip = ndac_conf['licenseserver']
        if (ndac_conf.has_key('custChronographTimer')):
            chronographTimer = ndac_conf['custChronographTimer']
            app.logger.debug("'custChronographTimer' detected.")
    except Exception as e:
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('218'))
        return False

    try:
        cass_conf=ndac_conf['cassandra']
        cass_user=unwrap(cass_conf['dbusername'],db_keys)
        cass_pass=unwrap(cass_conf['dbpassword'],db_keys)
        cass_auth = PlainTextAuthProvider(username=cass_user, password=cass_pass)
        cluster = Cluster([cass_conf['databaseip']],port=int(cass_conf['dbport']),auth_provider=cass_auth)
        icesession = cluster.connect()
        n68session = cluster.connect()
        icesession.row_factory = dict_factory
        icesession.set_keyspace('icetestautomation')
        n68session.row_factory = dict_factory
        n68session.set_keyspace('nineteen68')
        cass_dbup = True
    except Exception as e:
        cass_dbup = False
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('206'))
        return False

    try:
        redisdb_conf = ndac_conf['redis']
        redisdb_pass = unwrap(redisdb_conf['dbpassword'],db_keys)
        redisSession = redis.StrictRedis(host=redisdb_conf['databaseip'], port=int(redisdb_conf['dbport']), password=redisdb_pass, db=3)
        if redisSession.get('icesessions') is None:
            redisSession.set('icesessions',wrap('{}',db_keys))
        redis_dbup = True
    except Exception as e:
        redis_dbup = False
        app.logger.debug(e)
        app.logger.critical(printErrorCodes('217'))
        return False

    if args.offlinemode:
        app.logger.info("Offline Mode Detected")
        try:
            f = open(args.offlinemode,"r")
            contents = f.read()
            f.close()
            userinformation=unwrap(str(contents),offreg)
            userinfo=ast.literal_eval(userinformation)

            startdate = userinfo['offlinereginfo']['startdate']
            if not ('-' in startdate):
                startdate = datetime.strptime(startdate, '%m/%d/%Y')
                startdate = getbgntime('indate',startdate)
            else:
                startdate = datetime.strptime(startdate, '%m/%d/%Y-%H%M%S')

            enddate = userinfo['offlinereginfo']['enddate']
            if not ('-' in enddate):
                enddate = datetime.strptime(enddate, '%m/%d/%Y')
                enddate = getbgntime('indate',enddate)
            else:
                enddate = datetime.strptime(enddate, '%m/%d/%Y-%H%M%S')
            # this is provided as there was a request to create a key
            # without mac address
            mac = 'nomacaddress'
            if 'mac' in userinfo['offlinereginfo']:
                if userinfo['offlinereginfo']['mac'] != 'NO':
                    mac = userinfo['offlinereginfo']['mac']
            enabled = offlineuserenabler(startdate,enddate,mac)
            licensedata=userinfo['licensedata']
            if enabled == True:
                beginserver()
            else:
                if (startdate > datetime.now()):
                    scheduleenabler(offlinestarttime)
                    app.logger.error("Server starts only after : "+str(offlinestarttime))
                else:
                    app.logger.critical(printErrorCodes('204'))
        except Exception as e:
            app.logger.debug(e)
            app.logger.critical(printErrorCodes('218'))
    else:
        if (basecheckonls()):
            cronograph()
            beginserver()
        else:
            app.logger.critical(printErrorCodes('218'))

if __name__ == '__main__':
    initLoggers(args)
    sysMAC = str(getMacAddress()).strip()
    main()