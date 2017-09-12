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
#sys.path.append('./packages/Lib/site-packages')
import json
import requests
import subprocess
import sqlite3

import logging
handler=''

from datetime import datetime
import uuid

import ast

from flask import Flask, request , jsonify
from waitress import serve
from logging.handlers import TimedRotatingFileHandler
app = Flask(__name__)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-k","--verbosity", type=str, help="home user"
                    +"registration. Provide the offline registration filename")
args = parser.parse_args()


##os.chdir("..")
#nineteen68 folder location is parent directory
currdir=os.getcwd()
config_path = currdir+'/server_config.json'
assistpath = currdir + "/ndac_internals/assist"
logspath= currdir + "/ndac_internals/logs"

ndac_conf = json.loads(open(config_path).read())

lsip = ndac_conf['ndac']['licenseserver']
from cassandra.cluster import Cluster
from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
dbup = False
try:
    auth = PlainTextAuthProvider(username=ndac_conf['ndac']['dbusername'], password=ndac_conf['ndac']['dbpassword'])
    cluster = Cluster([ndac_conf['ndac']['databaseip']],port=int(ndac_conf['ndac']['dbport']),auth_provider=auth)

    icesession = cluster.connect()
    n68session = cluster.connect()
    icehistorysession = cluster.connect()
    n68historysession = cluster.connect()

    from cassandra.query import dict_factory
    icesession.row_factory = dict_factory
    icesession.set_keyspace('icetestautomation')

    n68session.row_factory = dict_factory
    n68session.set_keyspace('nineteen68')
    dbup = True
except Exception as dbexception:
    app.logger.critical('Error in Database connectivity...');

#default values for offline user
offlinestarttime=''
offlineendtime=''
offlineuser = False
onlineuser = False
usersession = False
lsondayone = ""
lsondaytwo = ""

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
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            authenticateuser = ("select password from users where username = '"
                                +requestdata["username"]+"' "
                                +"allow filtering;")
            queryresult = n68session.execute(authenticateuser)
            res= {"rows":queryresult.current_rows}
            res=closehonor(res)
            if 'dayone' in res:
                app.logger.critical('Licenses will expire tomorrow.')
            elif 'daytwo' in res:
                app.logger.critical('Licenses expired.')
            return jsonify(res)
        else:
            app.logger.error('Empty data received. authentication')
            res=closehonor(res)
            if 'dayone' in res:
                app.logger.critical('Licenses will expire tomorrow.')
            elif 'daytwo' in res:
                app.logger.critical('Licenses expired.')
            return jsonify(res)
    except Exception as authenticateuserexc:
        app.logger.error('Error in authenticateUser.')
        res=closehonor(res)
        if 'dayone' in res:
            app.logger.critical('Licenses will expire tomorrow.')
        elif 'daytwo' in res:
            app.logger.critical('Licenses expired.')
        return jsonify(res)

#service for user ldap validation
@app.route('/login/authenticateUser_Nineteen68/ldap',methods=['POST'])
def authenticateUser_Nineteen68_ldap():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            authenticateuserldap = ("select ldapuser from users where "
                                    +"username = '"+requestdata["username"]+"'"
                                    +"allow filtering;")
            queryresult = n68session.execute(authenticateuserldap)
            res= {"rows":queryresult.current_rows}
            res=closehonor(res)
            return jsonify(res)
        else:
            app.logger.error('Empty data received. authentication')
            res=closehonor(res)
            return jsonify(res)
    except Exception as authenticateuserldapexc:
        app.logger.error('Error in authenticateUser_ldap.')
        res=closehonor(res)
        return jsonify(res)

#service for getting rolename by roleid
@app.route('/login/getRoleNameByRoleId_Nineteen68',methods=['POST'])
def getRoleNameByRoleId_Nineteen68():
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
            app.logger.error('Empty data received. authentication')

            return jsonify(res)
    except Exception as rolenameexc:
        app.logger.error('Error in getRoleNameByRoleId_Nineteen68.')
        return jsonify(res)

#utility checks whether user is having projects assigned
@app.route('/login/authenticateUser_Nineteen68/projassigned',methods=['POST'])
def authenticateUser_Nineteen68_projassigned():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'getUserId'):
                authenticateuserprojassigned1= ("select userid,defaultrole "
                                                +"from users where "
                                                +"username = '"
                                                +requestdata["username"]
                                                +"' allow filtering;")
                queryresult = n68session.execute(authenticateuserprojassigned1)
            elif(requestdata["query"] == 'getUserRole'):
                authenticateuserprojassigned2= ("select rolename from roles"
                                                +" where roleid = "
                                                +requestdata["roleid"]
                                                +" allow filtering;")
                queryresult = n68session.execute(authenticateuserprojassigned2)
            elif(requestdata["query"] == 'getAssignedProjects'):
                authenticateuserprojassigned3= ("select projectids from"
                                            +" icepermissions where userid = "
                                            +requestdata["userid"]
                                            +" allow filtering;")
                queryresult = icesession.execute(authenticateuserprojassigned3)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. authentication')
            return jsonify(res)
    except Exception as authenticateuserprojassignedexc:
        app.logger.error('Error in authenticateUser_projassigned.')
        return jsonify(res)

#service for loading user information
@app.route('/login/loadUserInfo_Nineteen68',methods=['POST'])
def loadUserInfo_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'userInfo'):
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
                loaduserinfo3 = ("select * from "
                                +"userpermissions where roleid = "
                                +requestdata["roleid"]+" allow filtering")
                queryresult = n68session.execute(loaduserinfo3)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. loadUserInfo')
            return jsonify(res)
    except Exception as loaduserinfoexc:
        app.logger.error('Error in loadUserInfo_Nineteen68.')
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
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getReleaseDetails = ("select releasename,releaseid from icetestautomation.releases "+
            "where projectid"+'='+ projectid)
            queryresult = icesession.execute(getReleaseDetails)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. getReleaseIDs_Ninteen68")
    except Exception as e:
        app.logger.error('Error in getReleaseIDs_Ninteen68.')
    return jsonify(res)


@app.route('/create_ice/getCycleIDs_Ninteen68',methods=['POST'])
def getCycleIDs_Ninteen68():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            releaseid=requestdata['releaseid']
            getCycleDetails = ("select cyclename,cycleid from icetestautomation.cycles "+
            "where releaseid"+'='+ releaseid)
            queryresult = icesession.execute(getCycleDetails)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. getCycleIDs_Ninteen68")
    except Exception as e:
        app.logger.error('Error in getCycleIDs_Ninteen68.')
    return jsonify(res)

@app.route('/create_ice/getProjectType_Nineteen68',methods=['POST'])
def getProjectType_Nineteen68():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getProjectType = ("select projecttypeid FROM icetestautomation.projects "+
            "where projectid"+'='+ projectid)
            queryresult = icesession.execute(getProjectType)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. getProjectType_Nineteen68")
    except Exception as e:
        app.logger.error('Error in getProjectType_Nineteen68.')
    return jsonify(res)

#getting ProjectID and names of project sassigned to particular user
@app.route('/create_ice/getProjectIDs_Nineteen68',methods=['POST'])
def getProjectIDs_Nineteen68():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'getprojids'):
                userid=requestdata['userid']
                getProjIds = ("select projectids FROM icetestautomation.icepermissions "+
                "where userid="+userid)
                queryresult = icesession.execute(getProjIds)
                res={'rows':queryresult.current_rows}
            elif (requestdata['query'] == 'getprojectname'):
                projectid=requestdata['projectid']
                getprojectname = ("select projectname,projecttypeid FROM icetestautomation.projects "+
                "where projectid="+projectid)
                queryresult = icesession.execute(getprojectname)
                res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. getProjectIDs_Nineteen68")
    except Exception as e:
        app.logger.error('Error in getProjectIDs_Nineteen68.')
    return jsonify(res)

#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/getNames_Ninteen68',methods=['POST'])
def getNames_Nineteen68():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            name=requestdata['name']
            nodeid=requestdata['id']
            getname_query=(query[name]+nodeid)
            queryresult = icesession.execute(getname_query)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. getProjectIDs_Nineteen68")
    except Exception as e:
        app.logger.error('Error in getNames_Ninteen68.')
    return jsonify(res)

#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/testscreen_exists_ICE',methods=['POST'])
def testscreen_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            screen_name=requestdata['screen_name']
            screen_check =("select screenid from screens where screenname='"+screen_name
            +"' ALLOW FILTERING")
            queryresult = icesession.execute(screen_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testscreen_exists")
    except Exception as e:
        app.logger.error('Error in testscreen_exists.')
    return jsonify(res)


#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/testcase_exists_ICE',methods=['POST'])
def testcase_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            testcase_name=requestdata['testcase_name']
            testcase_check =("select testcaseid from testcases where testcasename='"+testcase_name
            +"' ALLOW FILTERING")
            queryresult = icesession.execute(testcase_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testcase_exists")
    except Exception as e:
        app.logger.error('Error in testcase_exists.')
    return jsonify(res)


#getting names of module/scenario/screen/testcase name of given id
@app.route('/create_ice/testsuiteid_exists_ICE',methods=['POST'])
def testsuiteid_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='suite_check':
                testsuite_exists(requestdata['project_id'],requestdata['module_name'])
            else:
                testsuite_exists(requestdata['project_id'],requestdata['module_name'],requestdata['module_id'])
            testsuite_check=query[query_name]
            queryresult = icesession.execute(testsuite_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testsuiteid_exists_ICE")
    except Exception as e:
        app.logger.error('Error in testsuiteid_exists_ICE.')
    return jsonify(res)

@app.route('/create_ice/testscenariosid_exists_ICE',methods=['POST'])
def testscenariosid_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='scenario_check':
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'])
            else:
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'],requestdata['scenario_id'])
            testscenario_check=query[query_name]
            queryresult = icesession.execute(testscenario_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testscenariosid_exists")
    except Exception as e:
        app.logger.error('Error in testscenariosid_exists.')
    return jsonify(res)


@app.route('/create_ice/testscreenid_exists_ICE',methods=['POST'])
def testscreenid_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='screen_check':
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'])
            else:
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'],requestdata['screen_id'])
            testscreen_check=query[query_name]
            queryresult = icesession.execute(testscreen_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testscreenid_exists_ICE")
    except Exception as e:
        app.logger.error('Error in testscreenid_exists_ICE.')
    return jsonify(res)

@app.route('/create_ice/testcaseid_exists_ICE',methods=['POST'])
def testcaseid_exists_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='testcase_check':
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'])
            else:
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'],requestdata['testcase_id'])
            testcase_check=query[query_name]
            queryresult = icesession.execute(testcase_check)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testcaseid_exists_ICE")
    except Exception as e:
        app.logger.error('Error in testcaseid_exists_ICE.')
    return jsonify(res)

@app.route('/create_ice/get_node_details_ICE',methods=['POST'])
def get_node_details_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_node_data=query[query_name]+requestdata['id']
            queryresult = icesession.execute(get_node_data)
            res={'rows':queryresult.current_rows}
       else:
            app.logger.error("Empty data received. testcase_exists")
    except Exception as e:
##        print e
##        import traceback
##        traceback.print_exc()
        app.logger.error('Error in testcase_exists.')
    return jsonify(res)

@app.route('/create_ice/delete_node_ICE',methods=['POST'])
def delete_node_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_delete_query(requestdata['id'],requestdata['node_name'],requestdata['version_number'],requestdata['parent_node_id'])
            delete_query=query[query_name]
            queryresult = icesession.execute(delete_query)
            res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. testscenario_exists")
    except Exception as e:
        app.logger.error('Error in testcase_exists.')
    return jsonify(res)

@app.route('/create_ice/insertInSuite_ICE',methods=['POST'])
def insertInSuite_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
           if(requestdata["query"] == 'notflagsuite'):
                create_suite_query1 = ("insert into modules "
                +"(projectid,modulename,moduleid,versionnumber,createdby,createdon,"
                +" createdthrough,deleted,skucodemodule,tags,testscenarioids) values( "
                +requestdata['projectid']+",'" + requestdata['modulename']
                +"'," + requestdata['moduleid'] + ","+requestdata['versionnumber']
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                + ",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])
                +", '"+requestdata['skucodemodule']+"',['"+requestdata['tags']+"'],[])")
                queryresult = icesession.execute(create_suite_query1)
                res={'rows':'Success'}
           elif(requestdata["query"] == 'selectsuite'):
                create_suite_query2 = ("select moduleid from modules "
                +" where modulename='"+requestdata["modulename"]+"' allow filtering;")
                queryresult = icesession.execute(create_suite_query2)
                res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. insertInSuite_ICE")
    except Exception as e:
        app.logger.error('Error in insertInSuite_ICE.')
    return jsonify(res)

@app.route('/create_ice/insertInScenarios_ICE',methods=['POST'])
def insertInScenarios_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
           if(requestdata["query"] == 'notflagscenarios'):
                create_scenario_query1 = ("insert into testscenarios(projectid,"
                +"testscenarioname,testscenarioid,createdby,createdon,skucodetestscenario,"
                +"tags,testcaseids,deleted) values ("+requestdata['projectid'] + ",'"
                +requestdata['testscenarioname']+"',"+requestdata['testscenarioid']
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                +", '"+requestdata['skucodetestscenario']+"',['"+requestdata['tags']+"'],[],"+str(requestdata['deleted'])+")")
                queryresult = icesession.execute(create_scenario_query1)
                res={'rows':'success'}
           elif(requestdata["query"] == 'deletescenarios'):
                delete_scenario_query = ("delete testcaseids from testscenarios"
                +" where testscenarioid="+requestdata['testscenarioid']+" and "
                +"testscenarioname='"+requestdata['testscenarioname'] +"' and "
                +"projectid = "+requestdata['projectid'])
                queryresult = icesession.execute(delete_scenario_query)
                res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. insertInScenarios_ICE")
    except Exception as e:
        app.logger.error('Error in insertInScenarios_ICE.')
    return jsonify(res)

@app.route('/create_ice/insertInScreen_ICE',methods=['POST'])
def insertInScreen_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagscreen'):
                create_screen_query1 = ("insert into screens (projectid,screenname,"
                +" screenid,versionnumber,createdby,createdon,createdthrough,"
                +" deleted,skucodescreen,tags) values ("+requestdata['projectid']
                +", '"+requestdata['screenname']+"'," + requestdata['screenid']
                +" , "+requestdata['versionnumber']+" ,'"+requestdata['createdby']
                +"'," + str(getcurrentdate())+", '"+requestdata['createdthrough']
                +"' , "+str(requestdata['deleted'])+",'"+requestdata['skucodescreen']
                +"',['"+requestdata['tags']+"'] )")
                queryresult = icesession.execute(create_screen_query1)
                res={'rows':'Success'}

            elif(requestdata["query"] == 'selectscreen'):
                select_screen_query = ("select screenid from screens where "
                +"screenname='"+requestdata['screenname']+"' allow filtering;")
                queryresult = icesession.execute(select_screen_query)
                res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. insertInScreen_ICE")
    except Exception as e:
        app.logger.error('Error in insertInScreen_ICE.')
    return jsonify(res)

@app.route('/create_ice/insertInTestcase_ICE',methods=['POST'])
def insertInTestcase_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagtestcase'):
                create_testcase_query1 = ("insert into testcases (screenid,"
                +"testcasename,testcaseid,versionnumber,createdby,createdon,"
                +"createdthrough,deleted,skucodetestcase,tags,testcasesteps)values ("
                +requestdata['screenid'] + ",'" + requestdata['testcasename']
                +"'," + requestdata['testcaseid'] + ","+requestdata['versionnumber']
                +",'"+ requestdata['createdby']+"'," + str(getcurrentdate())+", '"
                +requestdata['createdthrough'] +"',"+str(requestdata['deleted'])+",'"
                +requestdata['skucodetestcase']+"',['"+requestdata['tags']+"'], '')")
                queryresult = icesession.execute(create_testcase_query1)
                res={'rows':'Success'}

            elif(requestdata["query"] == 'selecttestcase'):
                select_testcase_query = ("select testcaseid from testcases "
                +"where testcasename='"+requestdata['tags']+"'  allow filtering")
                queryresult = icesession.execute(select_testcase_query)
                res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. insertInTestcase_ICE")
    except Exception as e:
        app.logger.error('Error in insertInTestcase_ICE.')
    return jsonify(res)

@app.route('/create_ice/updateTestScenario_ICE',methods=['POST'])
def updateTestScenario_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
##            requestdata['testcaseid']=','.join(str(idval) for idval in requestdata['testcaseid'])
            updateicescenario_query =("update testscenarios set "
            +"testcaseids=testcaseids+["+requestdata['testcaseid']
            +"],modifiedby='"+requestdata['modifiedby']
            +"',modifiedon="+str(getcurrentdate())
            +" where projectid ="+requestdata['projectid']
            +"and testscenarioid ="+requestdata['testscenarioid']
            +" and testscenarioname = '"+requestdata['testscenarioname']+"'")
            queryresult = icesession.execute(updateicescenario_query)
            res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. updateTestScenario_ICE")
    except Exception as e:
        app.logger.error('Error in updateTestScenario_ICE.')
    return jsonify(res)

@app.route('/create_ice/updateModule_ICE',methods=['POST'])
def updateModule_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
            updateicemodules_query = ("update modules set "
            +"testscenarioids = ["+requestdata['testscenarioids']+"] where "
            +"moduleid="+requestdata['moduleid']+" and "
            +"projectid="+requestdata['projectid']+" and "
            +"modulename='"+requestdata['modulename']+"' and "
            +"versionnumber="+requestdata['versionnumber'])
            queryresult = icesession.execute(updateicemodules_query)
            res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. updateModule_ICE")
    except Exception as e:
        app.logger.error('Error in updateModule_ICE.')
    return jsonify(res)

@app.route('/create_ice/updateModulename_ICE',methods=['POST'])
def updateModulename_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
             requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
             update_modulename_query =("insert into modules "
             +"(projectid,modulename,moduleid,versionnumber,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
             +" createdthrough,deleted,skucodemodule,tags,testscenarioids) values ("
             +requestdata['projectid']+",'" + requestdata['modulename']
             +"'," + requestdata['moduleid'] + ","+requestdata['versionnumber']
             +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
             +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + str(getcurrentdate())
             + ",'"+requestdata['createdthrough']+"',"+requestdata['deleted']
             +", '"+requestdata['skucodemodule']+"',['"+requestdata['tags']+"'],["+requestdata['testscenarioids']+"])")
             queryresult = icesession.execute(update_modulename_query)
             res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. updateModulename_ICE")
    except Exception as e:
        app.logger.error('Error in updateModulename_ICE.')
    return jsonify(res)

@app.route('/create_ice/updateTestscenarioname_ICE',methods=['POST'])
def updateTestscenarioname_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if not isemptyrequest(requestdata):
            requestdata['testcaseids'] = ','.join(str(idval) for idval in requestdata['testcaseids'])
            update_testscenario_name_query =("insert into testscenarios "
             +"(projectid,testscenarioname,testscenarioid,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
             +" deleted,skucodetestscenario,tags,testcaseids) values ("
             +requestdata['projectid']+",'"+ requestdata['testscenarioname']
             +"',"+requestdata['testscenarioid']
             +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
             +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + requestdata['createdon']
             + ","+requestdata['deleted']+",'"+requestdata['skucodetestscenario']+"',['"
             +requestdata['tags']+"'],["+requestdata['testcaseids']+"])")
            queryresult = icesession.execute(update_testscenario_name_query)
            res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. updateTestscenarioname_ICE")
    except Exception as e:
        app.logger.error('Error in updateTestscenarioname_ICE.')
    return jsonify(res)


@app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
def updateScreenname_ICE():
    res={'rows':'fail'}
    try:

        requestdata=json.loads(request.data)
        if(requestdata['screendata'] == ''):
            requestdata['screendata'] = ' '
        if not isemptyrequest(requestdata):
            update_screenname_query =("insert into screens (projectid,screenname,"
            +"screenid,versionnumber,createdby,createdon,createdthrough,deleted,"
            +"modifiedby,modifiedbyrole,modifiedon,screendata,skucodescreen,tags"
            +") values ("+requestdata['projectid']+",'"+requestdata['screenname']
            +"',"+requestdata['screenid']+","+requestdata['versionnumber']
            +",'"+requestdata['createdby']+"',"+requestdata['createdon']
            +",'"+requestdata['createdthrough']+"',"+requestdata['deleted']
            +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
            +"',"+str(getcurrentdate())+",'"+requestdata['screendata']
            +"','"+requestdata['skucodescreen']+"',['"+requestdata['tags']+"'])")
            queryresult = icesession.execute(update_screenname_query)
            res={'rows':'Success'}
        else:
            app.logger.error("Empty data received. updateScreenname_ICE")
    except Exception as e:
        app.logger.error('Error in updateScreenname_ICE.')
    return jsonify(res)


@app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
def updateTestcasename_ICE():
    res={'rows':'fail'}
    try:
       requestdata=json.loads(request.data)
       if(requestdata['testcasesteps'] == ''):
            requestdata['testcasesteps'] = ' '
       if not isemptyrequest(requestdata):
            update_testcasename_query =("insert into testcases (screenid,testcasename,"
            "testcaseid,versionnumber,createdby,createdon,createdthrough,deleted,"
            +"modifiedby,modifiedbyrole,modifiedon,skucodetestcase,tags,"
            +"testcasesteps) values ("+requestdata['screenid']+",'"
            +requestdata['testcasename']+"',"+requestdata['testcaseid']+","
            +requestdata['versionnumber']+",'"+requestdata['createdby']
            +"',"+requestdata['createdon']+",'"+requestdata['createdthrough']
            +"',"+requestdata['deleted']+",'"+requestdata['modifiedby']
            +"','"+requestdata['modifiedbyrole']+"',"+str(getcurrentdate())
            +",'"+requestdata['skucodetestcase']+"',['"+requestdata['tags']
            +"'],'"+requestdata['testcasesteps']+"')")
            queryresult = icesession.execute(update_testcasename_query)
            res={'rows':'Success'}
       else:
            app.logger.error("Empty data received. updateTestcasename_ICE")
    except Exception as e:
        app.logger.error('Error in updateTestcasename_ICE.')
    return jsonify(res)

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
            return jsonify(res)
        else:
            app.logger.error('Empty data received. getKeywordDetails')
            return jsonify(res)
    except Exception as keywordsexc:
        app.logger.error('Error in getKeywordDetails.')
        return jsonify(res)

#test case reading service
@app.route('/design/readTestCase_ICE',methods=['POST'])
def readTestCase_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == "readtestcase"):
                readtestcasequery1 = ("select testcasesteps,testcasename "
                                +"from testcases where "
                                +"screenid= " + requestdata["screenid"]
                                +" and testcasename='"+requestdata["testcasename"]+"'"
                                +" and versionnumber="+str(requestdata["versionnumber"])
                                +" and testcaseid=" + requestdata["testcaseid"])
                queryresult = icesession.execute(readtestcasequery1)
            elif(requestdata['query'] == "testcaseid"):
                readtestcasequery2 = ("select screenid,testcasename,testcasesteps"
                +" from testcases where testcaseid="+ requestdata['testcaseid'])
                queryresult = icesession.execute(readtestcasequery2)
                count = debugcounter + 1
                userid = requestdata['userid']
                counterupdator('testcases',userid,count)
            elif(requestdata['query'] == "screenid"):
                readtestcasequery3 = ("select testcaseid,testcasename,testcasesteps "
                +"from testcases where screenid=" + requestdata['screenid'])
                queryresult = icesession.execute(readtestcasequery3)
        else:
            app.logger.error('Empty data received. reading Testcase')
            return jsonify(res)
        res= {"rows": queryresult.current_rows}
        return jsonify(res)
    except Exception as readtestcaseexc:
        app.logger.error('Error in readTestCase_ICE.')
        return jsonify(res)


# fetches the screen data
@app.route('/design/getScrapeDataScreenLevel_ICE',methods=['POST'])
def getScrapeDataScreenLevel_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if (requestdata['query'] == 'getscrapedata'):
                getscrapedataquery1=("select screenid,screenname,screendata from "
                +"screens where screenid="+requestdata['screenid']
                +" and projectid="+requestdata['projectid']+" allow filtering ;")
                queryresult = icesession.execute(getscrapedataquery1)
                res = {"rows":queryresult.current_rows}
            elif(requestdata['query'] == 'debugtestcase'):
                getscrapedataquery2=("select screenid,screenname,screendata from "
                +"screens where screenid="+requestdata['screenid']
                +" allow filtering ;")
                queryresult = icesession.execute(getscrapedataquery2)
                res = {"rows":queryresult.current_rows}
        else:
            app.logger.error('Empty data received. reading Testcase')
            return jsonify(res)
        return jsonify(res)
    except Exception as getscrapedataexc:
        app.logger.error('Error in getScrapeDataScreenLevel_ICE.')
        return jsonify(res)

# fetches data for debug the testcase
@app.route('/design/debugTestCase_ICE',methods=['POST'])
def debugTestCase_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            gettestcasedataquery=("select screenid,testcasename,testcasesteps "
            +"from testcases where testcaseid=" + requestdata['testcaseid'])
            queryresult = icesession.execute(gettestcasedataquery)
            res = {"rows":queryresult.current_rows}
        else:
            app.logger.error('Empty data received. reading Testcase')
            return jsonify(res)
        return jsonify(res)
    except Exception as debugtestcaseexc:
        app.logger.error('Error in debugTestCase_ICE.')
        return jsonify(res)

# updates the screen data
@app.route('/design/updateScreen_ICE',methods=['POST'])
def updateScreen_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            updatescreenquery=("update icetestautomation.screens set"
			+" screendata ='"+ requestdata['scrapedata'] +"',"
			+" modifiedby ='" + requestdata['modifiedby'] + "',"
			+" modifiedon = '" + str(getcurrentdate())
			+"', skucodescreen ='" + requestdata['skucodescreen']
			+"' where screenid = "+requestdata['screenid']
			+" and projectid = "+requestdata['projectid']
			+" and screenname ='" + requestdata['screenname']
			+"' and versionnumber = "+str(requestdata['versionnumber'])
            +" IF EXISTS; ")
            queryresult = icesession.execute(updatescreenquery)
            res = {"rows":"Success"}

        else:
            app.logger.error('Empty data received. updating screen')
            return jsonify(res)
        return jsonify(res)
    except Exception as updatescreenexc:
        app.logger.error('Error in updateScreen_ICE.')
        return jsonify(res)

#test case updating service
@app.route('/design/updateTestCase_ICE',methods=['POST'])
def updateTestCase_ICE():
##    requestdata=json.loads(request.data)
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'checktestcaseexist'):
                updatetestcasequery1 = ("select testcaseid from testcases where "
                +"screenid=" + requestdata['screenid'] +  " allow filtering")
                queryresult = icesession.execute(updatetestcasequery1)
                res= {"rows": queryresult.current_rows}
                res =  jsonify(res)
            elif(requestdata["query"] == 'updatetestcasedata'):
                updatetestcasequery2 = ("update testcases set "
                + "modifiedby = '" + requestdata['modifiedby']
                + "', modifiedon='" + str(getcurrentdate())
        		+"',  skucodetestcase='" + requestdata["skucodetestcase"]
        		+"',  testcasesteps='" + requestdata["testcasesteps"]
        		+"' where versionnumber = "+str(requestdata["versionnumber"])
                +" and screenid=" + str(requestdata["screenid"])
                + " and testcaseid=" + str(requestdata["testcaseid"])
                + " and testcasename='" + requestdata["testcasename"] + "' if exists;")
                queryresult = icesession.execute(updatetestcasequery2)
                res= {"rows": queryresult.current_rows}
                res =  jsonify(res)
        else:
            app.logger.error('Empty data received. updating testcases')
            res =  jsonify(res)
    except Exception as updatetestcaseexception:
        app.logger.error('Error in updateTestCase_ICE.')
    return res

#fetches all the testcases under a test scenario
@app.route('/suite/getTestcaseDetailsForScenario_ICE',methods=['POST'])
def getTestcaseDetailsForScenario_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'testscenariotable'):
                gettestscenarioquery1=("select testcaseids from testscenarios where "
                +"testscenarioid="+requestdata["testscenarioid"])
                queryresult = icesession.execute(gettestscenarioquery1)
            elif(requestdata["query"] == 'testcasetable'):
                gettestscenarioquery2=("select testcasename,screenid from "
                +"testcases where testcaseid="+requestdata["testcaseid"])
                queryresult = icesession.execute(gettestscenarioquery2)
            elif(requestdata["query"] == 'screentable'):
                gettestscenarioquery3=("select screenname,projectid from "
                +"screens where screenid="+requestdata["screenid"])
                queryresult = icesession.execute(gettestscenarioquery3)
            elif(requestdata["query"] == 'projecttable'):
                gettestscenarioquery4=("select projectname from projects "
                +"where projectid="+requestdata["projectid"])
                queryresult = icesession.execute(gettestscenarioquery4)
            res = {'rows':queryresult.current_rows}
            res =  jsonify(res)
        else:
            app.logger.error('Empty data received. getting testcases from scenarios.')
            res =  jsonify(res)
    except Exception as userrolesexc:
        app.logger.error('Error in getTestcaseDetailsForScenario_ICE.')
    return res

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
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'gettestcaseids'):
                gettestcaseidquery1  = ("select testcaseids from testscenarios "
                +"where testscenarioid = "+requestdata["testscenarioid"]+" allow filtering")
                queryresult = icesession.execute(gettestcaseidquery1)
            elif(requestdata["query"] == 'gettestcasedetails'):
                gettestcaseidquery2 = ("select testcasename from testcases where"
                +" testcaseid = "+requestdata["eachtestcaseid"]+" allow filtering")
                queryresult = icesession.execute(gettestcaseidquery2)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  jsonify(res)
        else:
            app.logger.error('Empty data received. getting testcases.')
            res =  jsonify(res)
    except Exception as gettestcasesbyscenarioidexception:
        app.logger.error('Error in getTestcasesByScenarioId_ICE.')
    return res

#read test suite nineteen68
@app.route('/suite/readTestSuite_ICE',methods=['POST'])
def readTestSuite_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'testsuitecheck'):
                readtestsuitequery1 = ("select donotexecute,conditioncheck, "
                +"getparampaths,testscenarioids from testsuites "
                +" where testsuiteid="+ requestdata['testsuiteid']
                + " and cycleid="+requestdata['cycleid'])
                queryresult = icesession.execute(readtestsuitequery1)
            elif(requestdata["query"] == 'selectmodule'):
                readtestsuitequery2 = ("select * FROM modules where "
                +"moduleid=" + requestdata["moduleid"]
                + " and modulename='" + requestdata["modulename"]
                + "' allow filtering")
                queryresult = icesession.execute(readtestsuitequery2)
            elif(requestdata["query"] == 'testcasesteps'):
                requestdata['conditioncheck'] = ','.join(str(idval) for idval in requestdata['conditioncheck'])
                requestdata['donotexecute'] = ','.join(str(idval) for idval in requestdata['donotexecute'])
                requestdata['getparampaths'] = ','.join(str("'"+idval+"'") for idval in requestdata['getparampaths'])
                getparampaths=[]
                for eachgetparampath in requestdata['getparampaths']:
                    if(eachgetparampath == ''):
                        getparampaths.append(' ')
                    else:
                        getparampaths.append(eachgetparampath)
                requestdata['testscenarioids'] = ','.join(str(idval) for idval in requestdata['testscenarioids'])
                readtestsuitequery3 = ("insert into testsuites "+
                "(cycleid,testsuitename,testsuiteid,versionnumber,conditioncheck,"
                +"createdby,createdon,createdthrough,deleted,donotexecute,getparampaths,skucodetestsuite,tags,testscenarioids) "+
                "values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+requestdata["versionnumber"] +",["
                +requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["createdthrough"]+"',"
                +requestdata["deleted"]+",["+requestdata["donotexecute"]+"],["
                +requestdata['getparampaths'] +"],'"+requestdata["skucodetestsuite"]+"',['"
                +requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"])")
                queryresult = icesession.execute(readtestsuitequery3)
            elif(requestdata["query"] == 'fetchdata'):
                readtestsuitequery4 = ("select * from testsuites "+
                "where testsuiteid = " + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"] + " allow filtering")
                queryresult = icesession.execute(readtestsuitequery4)
            elif(requestdata["query"] == 'delete'):
                readtestsuitequery5 = ("delete from testsuites where "+
                "testsuiteid=" + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]
                + " and testsuitename='" + requestdata["testsuitename"] + "'")
                queryresult = icesession.execute(readtestsuitequery5)
            elif(requestdata["query"] == 'updatescenarioinnsuite'):
                requestdata['conditioncheck'] = ','.join(str(idval) for idval in requestdata['conditioncheck'])
                requestdata['donotexecute'] = ','.join(str(idval) for idval in requestdata['donotexecute'])
                requestdata['getparampaths'] = ','.join(str(idval) for idval in requestdata['getparampaths'])
                requestdata['testscenarioids'] = ','.join(str(idval) for idval in requestdata['testscenarioids'])
                readtestsuitequery6 = ("insert into testsuites (cycleid,testsuitename,testsuiteid,versionnumber,conditioncheck,"
                +"createdby,createdon,createdthrough,deleted,donotexecute,"
                +"getparampaths,modifiedby,modifiedon,skucodetestsuite,tags,testscenarioids) values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+requestdata["versionnumber"]
                +",["+requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +requestdata["createdon"]+",'"+requestdata["createdthrough"]+"',"
                +requestdata["deleted"]+",["+requestdata["donotexecute"]+"],["+
                requestdata["getparampaths"]+"],'"+requestdata["modifiedby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["skucodetestsuite"]+"',['"+
                requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"])")
                queryresult = icesession.execute(readtestsuitequery6)
            elif(requestdata["query"] == 'testcasename'):
                readtestsuitequery7 = ("select testscenarioname,projectid from testscenarios where "
                +"testscenarioid=" +  requestdata["testscenarioid"])
                queryresult = icesession.execute(readtestsuitequery7)
            elif(requestdata["query"] == 'projectname'):
                readtestsuitequery8 = ("select projectname from projects where "
                +"projectid = " + requestdata["projectid"] + " allow filtering")
                queryresult = icesession.execute(readtestsuitequery8)
            elif(requestdata["query"] == 'readTestSuite_ICE'):
                readtestsuitequery9 = ("select donotexecute,conditioncheck,getparampaths,testscenarioids from testsuites where "
                +"testsuiteid= " +requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]
                + " and testsuitename='" + requestdata["testsuitename"] + "'")
                queryresult = icesession.execute(readtestsuitequery9)
            else:
                return jsonify(res)
        else:
            app.logger.error('Empty data received. assign projects.')
            return jsonify(res)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)

    except Exception as exporttojsonexc:
        app.logger.error('Error in readTestSuite_ICE.')
##        import traceback
##        traceback.print_exc()
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
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'deletetestsuitequery'):
                deletetestsuitequery=("delete conditioncheck,donotexecute,"
                +"getparampaths,testscenarioids from testsuites where cycleid="
                +str(requestdata['cycleid'])
                +" and testsuitename='"+requestdata['testsuitename']
                +"' and testsuiteid="+str(requestdata['testsuiteid'])
                +" and versionnumber ="+str(requestdata['versionnumber'])+";")
                queryresult = icesession.execute(deletetestsuitequery)
            elif(requestdata['query'] == 'updatetestsuitedataquery'):
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
                +" and versionnumber = "+ str( requestdata['versionnumber'])
                +" and testsuitename='"+ requestdata['testsuitename']
                +"';")
                queryresult = icesession.execute(updatetestsuitedataquery)
            else:
                return jsonify(res)
        else:
            app.logger.error('Empty data received. assign projects.')
            return jsonify(res)
        res={'rows':'Success'}
        return jsonify(res)
    except Exception as updatetestsuiteexc:
        app.logger.error('Error in updateTestSuite_ICE')
        return jsonify(res)

@app.route('/suite/ExecuteTestSuite_ICE',methods=['POST'])
def ExecuteTestSuite_ICE() :
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'testcaseid'):
                executetestsuitequery1=("select testcaseids from testscenarios where"
                +" testscenarioid=" + requestdata['testscenarioid'])
                queryresult = icesession.execute(executetestsuitequery1)
                global scenarioscounter
                scenarioscounter = 0
                userid=requestdata['userid']
                scenarioscounter = scenarioscounter + 1
                counterupdator('testscenarios',userid,scenarioscounter)
            elif(requestdata['query'] == 'testcasesteps'):
                executetestsuitequery2=("select screenid from testcases where "
                +"testcaseid="+ requestdata['testcaseid'])
                queryresult = icesession.execute(executetestsuitequery2)
            elif(requestdata['query'] == 'getscreendataquery'):
                executetestsuitequery3=("select screendata from screens where "
                +"screenid=" + requestdata['screenid'])
                queryresult = icesession.execute(executetestsuitequery3)
            elif(requestdata['query'] == 'testcasestepsquery'):
                executetestsuitequery4=("select testcasesteps,testcasename from "
                +"testcases where testcaseid = "+ requestdata['testcaseid'])
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
            +"executionid,starttime,endtime) values (" + requestdata['testsuiteid']
            + "," + requestdata['executionid']+ "," + requestdata['starttime']
            + "," + str(getcurrentdate()) + ")")
               queryresult = icesession.execute(executetestsuitequery6)
            else:
                return jsonify(res)
        else:
            app.logger.error('Empty data received. assign projects.')
            return jsonify(res)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as execuitetestsuiteexc:
        app.logger.error('Error in execuiteTestSuite_ICE')
        return jsonify(res)

################################################################################
# END OF EXECUTION
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
            app.logger.error('Empty data received. getting qcProjectDetails.')
            res =  jsonify(res)
    except Exception as gettestcasesbyscenarioidexception:
        app.logger.error('Error in qcProjectDetails_ICE.')
    return res

@app.route('/qualityCenter/saveQcDetails_ICE',methods=['POST'])
def saveQcDetails_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'saveQcDetails_ICE'):
                gettestcaseidquery1  = ("INSERT INTO qualitycenterdetails (testscenarioid,qcdetailsid,qcdomain,qcfolderpath,qcproject,qctestcase,qctestset) VALUES ("+requestdata["testscenarioid"]
                +","+requestdata["testscenarioid"]+",'"+requestdata["qcdomain"]+"','"+requestdata["qcfolderpath"]+"','"+requestdata["qcproject"]
                +"','"+requestdata["qctestcase"]+"','"+requestdata["qctestset"]+"')")
                queryresult = icesession.execute(gettestcaseidquery1)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  jsonify(res)
        else:
            app.logger.error('Empty data received. getting saveQcDetails.')
            res =  jsonify(res)
    except Exception as gettestcasesbyscenarioidexception:
        app.logger.error('Error in saveQcDetails_ICE.')
    return res

@app.route('/qualityCenter/viewQcMappedList_ICE',methods=['POST'])
def viewQcMappedList_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'qcdetails'):
                viewqcmappedquery1  = ("SELECT * FROM qualitycenterdetails where testscenarioid="+requestdata["testscenarioid"])
                queryresult = icesession.execute(viewqcmappedquery1)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  jsonify(res)
        else:
            app.logger.error('Empty data received. getting QcMappedList.')
            res =  jsonify(res)
    except Exception as gettestcasesbyscenarioidexception:
        app.logger.error('Error in viewQcMappedList_ICE.')
    return res
################################################################################
# END OF QUALITYCENTRE
################################################################################

################################################################################
# BEGIN OF ADMIN SCREEN
# INCLUDES : all admin related actions
################################################################################

#fetches the user roles for assigning during creation/updation user
@app.route('/admin/getUserRoles_Nineteen68',methods=['POST'])
def getUserRoles():
    res={'rows':'fail'}
    try:
        userrolesquery="select roleid, rolename from roles"
        queryresult = n68session.execute(userrolesquery)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as userrolesexc:
        app.logger.error('Error in getUserRoles_Nineteen68.')
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
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domaindetails'):
                getdetailsquery1=("select projectid,projectname from projects "
                                    +"where domainid=" + requestdata['id'])
                queryresult = icesession.execute(getdetailsquery1)
            elif(requestdata["query"] == 'projectsdetails'):
                if(requestdata["subquery"] == 'projecttypeid'):
                    getdetailsquery2=("select projecttypeid,projectname "
                            +"from projects where projectid="+ requestdata['id'])
                elif(requestdata["subquery"] == 'projecttypename'):
                    getdetailsquery2=("select projecttypename from projecttype"
                                +" where projecttypeid=" + requestdata['id'])
                elif(requestdata["subquery"] == 'releasedetails'):
                    getdetailsquery2=("select releaseid,releasename from "
                            +"releases where projectid=" + requestdata['id'])
                elif(requestdata["subquery"] == 'cycledetails'):
                    getdetailsquery2=("select cycleid,cyclename from cycles "
                                        +"where releaseid=" + requestdata['id'])
                queryresult = icesession.execute(getdetailsquery2)
            elif(requestdata["query"] == 'cycledetails'):
                getdetailsquery3=("select testsuiteid,testsuitename "
                        +"from testsuites where cycleid=" + requestdata['id'])
                queryresult = icesession.execute(getdetailsquery3)
            else:
                return jsonify(res)
            res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. generic details.')
            return jsonify(res)
    except Exception as getdetailsexc:
        app.logger.error('Error in getDetails_ICE.')
        return jsonify(res)


#service renders the names of all projects in domain/projects
@app.route('/admin/getNames_ICE',methods=['POST'])
def getNames_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domainsall'):
                getnamesquery1=("select projectid,projectname from projects "
                                        +"where domainid="+requestdata['id'])
                queryresult = icesession.execute(getnamesquery1)
            elif(requestdata["query"] == 'projects'):
                getnamesquery2=("select projectid,projectname from projects "
                                    +"where projectid="+requestdata['id'])
                queryresult = icesession.execute(getnamesquery2)
            elif(requestdata["query"] == 'releases'):
                getnamesquery3=("select releaseid,releasename from releases "
                                    +"where releaseid="+requestdata['id'])
                queryresult = icesession.execute(getnamesquery3)
            elif(requestdata["query"] == 'cycles'):
                getnamesquery4=("select cycleid,cyclename from cycles "
                                        +"where cycleid="+requestdata['id'])
                queryresult = icesession.execute(getnamesquery4)
            else:
                return jsonify(res)
            res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. generic name details.')
            return jsonify(res)
    except Exception as getnamesexc:
        app.logger.error('Error in getNames_ICE.')
        return jsonify(res)

#service renders all the domains in DB
@app.route('/admin/getDomains_ICE',methods=['POST'])
def getDomains_ICE():
    res={'rows':'fail'}
    try:
        getdomainsquery="select domainid,domainname from domains"
        queryresult = icesession.execute(getdomainsquery)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as getdomainsexc:
        app.logger.error('Error in getDomains_ICE.')
        return jsonify(res)

#service fetches projects assigned to user.
@app.route('/admin/getAssignedProjects_ICE',methods=['POST'])
def getAssignedProjects_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projectid'):
                getassingedprojectsquery1=("select projectids from "
                        +"icepermissions where userid = "+requestdata['userid']
                        +" and domainid = "+requestdata['domainid'])
                queryresult = icesession.execute(getassingedprojectsquery1)
            elif(requestdata['query'] == 'projectname'):
                getassingedprojectsquery2=("select projectname from projects "
                            +"where projectid = "+requestdata['projectid'])
                queryresult = icesession.execute(getassingedprojectsquery2)
            else:
                return jsonify(res)
            res={'rows':queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. assigned projects.')
            return jsonify(res)
    except Exception as getassingedprojectsexc:
        app.logger.error('Error in getAssignedProjects_ICE.')
        return jsonify(res)

#service creates new users into Nineteen68
@app.route('/admin/createUser_Nineteen68',methods=['POST'])
def createUser_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'allusernames'):
                createuserquery1=("select username from users")
                queryresult = n68session.execute(createuserquery1)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createuser'):
                userid = str(uuid.uuid4())
                deactivated = False
                createuserquery2=("insert into users (userid,createdby,createdon,"
                +"defaultrole,deactivated,emailid,firstname,lastname,ldapuser,password,username) values"
                +"( "+str(userid)+" , '"+requestdata['username']+"' , "
                + str(getcurrentdate())+" , "+requestdata['defaultrole']+" , "
                +str(deactivated)+" , '"+requestdata['emailid']+"' , '"
                +requestdata['firstname']+"' , '"+requestdata['lastname']+"' , "
                +str(requestdata['ldapuser'])+" , '"+requestdata['password']+"' , '"
                +requestdata['username']+"')")
                queryresult = n68session.execute(createuserquery2)
                res={'rows':'Success'}
            else:
                return jsonify(res)
            return jsonify(res)
        else:
            app.logger.error('Empty data received. create user.')
            return jsonify(res)
    except Exception as createusersexc:
        app.logger.error('Error in createUser_Nineteen68.')
        return jsonify(res)

#service update user data into Nineteen68
@app.route('/admin/updateUser_Nineteen68',methods=['POST'])
def updateUser_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'userdetails'):
                updateuserquery1=("select username,firstname,lastname,"
                    +" emailid,ldapuser,additionalroles from users where"
                    +" userid=" + str(requestdata['userid']))
                queryresult = n68session.execute(updateuserquery1)
                rows=[]
                for eachkey in queryresult.current_rows:
                    additionalroles=[]
                    emailid = eachkey['emailid']
                    firstname = eachkey['firstname']
                    lastname = eachkey['lastname']
                    ldapuser = eachkey['ldapuser']
                    username = eachkey['username']
                    if eachkey['additionalroles'] != None:
                        for eachrole in eachkey['additionalroles']:
                            additionalroles.append(eachrole)
                    eachobject={'userid':requestdata['userid'],'emailid':emailid,'firstname':firstname,
                'lastname':lastname,'ldapuser':ldapuser,
                'username':username,'additionalroles':additionalroles}
                    rows.append(eachobject)
                res={'rows':rows}
            elif(requestdata['query'] == 'updateuser'):
                requestdata['additionalroles'] = ','.join(str(roleid) for roleid in requestdata['additionalroles'])
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
            else:
                return jsonify(res)
            return jsonify(res)
        else:
            app.logger.error('Empty data received. update user.')
            return jsonify(res)
    except Exception as updateUserexc:
        app.logger.error('Error in updateUser_nineteen68')
        res={'rows':'fail'}
        return jsonify(res)

#service creates a complete project structure into ICE keyspace
@app.route('/admin/createProject_ICE',methods=['POST'])
def createProject_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projecttype'):
                projecttypequery=("select projecttypeid from projecttype where"
                +" projecttypename = '"+requestdata['projecttype']+"' allow filtering")
                queryresult = icesession.execute(projecttypequery)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createproject'):
                projectid =uuid.uuid4()
                deleted = False
                createprojectquery1 = ("insert into projects (domainid,projectname,"
                +"projectid,createdby,createdon,deleted,projecttypeid,"
                +"skucodeproject,tags)values ( "+str(requestdata['domainid'])
                +", '"+requestdata['projectname']+"' , "+str(projectid)
                +", '"+requestdata['createdby']+"',"+str(getcurrentdate())
                +", "+str(deleted)+", "+requestdata['projecttypeid']
                +",'"+requestdata['skucodeproject']+"' , ['"+requestdata['tags']+"']);")
                projectid = {'projectid':projectid}
                queryresult = icesession.execute(createprojectquery1)
                res={'rows':[projectid]}
            elif(requestdata['query'] == 'createrelease'):
                releaseid =uuid.uuid4()
                deletedonrelease = False
                createprojectquery2=("insert into releases (projectid,releasename,"
                +"releaseid,createdby,createdon,deleted,skucoderelease,tags) values "
                +"("+str(requestdata['projectid'])+", '"+requestdata['releasename']
                +"' ,"+str(releaseid)+",'"+requestdata['createdby']
                +"' ,"+str(getcurrentdate())+","+str(deletedonrelease)
                +",'"+requestdata['skucoderelease']+"' ,['"+requestdata['tags']+"']);")
                releaseid = {'releaseid':releaseid}
                queryresult = icesession.execute(createprojectquery2)
                res={'rows':[releaseid]}
            elif(requestdata['query'] == 'createcycle'):
                cycleid =uuid.uuid4()
                deletedoncycle = False
                createprojectquery3=("insert into cycles (releaseid,cyclename, "
                +"cycleid,createdby,createdon,deleted,skucodecycle,tags) values "
                +" ("+str(requestdata['releaseid'])+", '"+requestdata['cyclename']
                +"',"+str(cycleid)+",'"+requestdata['createdby']
                +"',"+str(getcurrentdate())+","+str(deletedoncycle)
                +",'"+requestdata['skucodecycle']+"' ,['"+requestdata['tags']+"']);")
                queryresult = icesession.execute(createprojectquery3)
                res={'rows':'Success'}
            else:
                return jsonify(res)
            return jsonify(res)
        else:
            app.logger.error('Empty data received. create project.')
            return jsonify(res)
    except Exception as createprojectexc:
        app.logger.error('Error in createProject_ICE')
        return jsonify(res)

#service updates the specified project structure into ICE keyspace
@app.route('/admin/updateProject_ICE',methods=['POST'])
def updateProject_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
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
            app.logger.error('Empty data received. update project.')
            return jsonify(res)
        return jsonify(res)
    except Exception as updateprojectexc:
            app.logger.error('Error in updateProject_ICE')
            return jsonify(res)

#fetches user data into Nineteen68
@app.route('/admin/getUsers_Nineteen68',methods=['POST'])
def getUsers_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            userroles = requestdata['userroles']
            userrolesarr=[]
            for eachroleobj in userroles:
                if eachroleobj['rolename'] == 'Admin' or eachroleobj['rolename'] == 'Test Manager' :
                    userrolesarr.append(eachroleobj['roleid'])
            useridslistquery = ("select userid from icepermissions where "
                +"projectids contains "+requestdata['projectid']+" allow filtering;")
            queryresultuserids= icesession.execute(useridslistquery)
            res={}
            userroles=[]
            rids=[]
            for row in queryresultuserids.current_rows:
                queryforuser=("select userid, username, defaultrole from users "
                        +"where userid="+str(row['userid']))
                queryresultusername=n68session.execute(queryforuser)
                if not(len(queryresultusername.current_rows) == 0):
                    if not (str(queryresultusername.current_rows[0]['defaultrole']) in userrolesarr):
                        rids.append(row['userid'])
                        userroles.append(queryresultusername.current_rows[0]['username'])
                        res["userRoles"]=userroles
                        res["r_ids"]=rids
        else:
            app.logger.error('Empty data received. get users - Mind Maps.')
            return jsonify(res)
        return jsonify(res)
    except Exception as getUsersexc:
        app.logger.error('Error in getUsers_Nineteen68')
        return jsonify(res)

#service assigns projects to a specific user
@app.route('/admin/assignProjects_ICE',methods=['POST'])
def assignProjects_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if (requestdata['alreadyassigned'] != True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
                assignprojectsquery1 = ("insert into icepermissions (userid,"
                +" domainid,createdby,createdon,projectids) values"
                +" ("+str(requestdata['userid'])+","+str(requestdata['domainid'])
                +",'"+requestdata['createdby']+"',"+str(getcurrentdate())
                +", ["+str(requestdata['projectids'])+"]);")
                queryresult = icesession.execute(assignprojectsquery1)
            elif (requestdata['alreadyassigned'] == True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
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
            app.logger.error('Empty data received. assign projects.')
            return jsonify(res)
        res={'rows':'Success'}
        return jsonify(res)
    except Exception as assignprojectsexc:
        app.logger.error('Error in assignProjects_ICE')
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
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domainid'):
                getallsuitesquery1 = ("select domainid from icepermissions "
                                    +"where userid="+requestdata['userid']+";")
                queryresult = icesession.execute(getallsuitesquery1)
            elif(requestdata["query"] == 'projectsUnderDomain'):
                getallsuitesquery2 =("select projectid from projects "
                                +"where domainid="+requestdata['domainid']+";")
                queryresult = icesession.execute(getallsuitesquery2)
            elif(requestdata["query"] == 'releasesUnderProject'):
                getallsuitesquery3 = ("select releaseid from releases "
                                +"where projectid="+requestdata['projectid'])
                queryresult = icesession.execute(getallsuitesquery3)
            elif(requestdata["query"] == 'cycleidUnderRelease'):
                getallsuitesquery4 =("select cycleid from cycles "
                            +"where releaseid="+requestdata['releaseid'])
                queryresult = icesession.execute(getallsuitesquery4)
            elif(requestdata["query"] == 'suitesUnderCycle'):
                getallsuitesquery5 = ("select testsuiteid,testsuitename "
                    +"from testsuites where cycleid="+requestdata['cycleid'])
                queryresult = icesession.execute(getallsuitesquery5)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. report suites details.')
            return jsonify(res)
    except Exception as getAllSuitesexc:
        app.logger.error('Error in getAllSuites_ICE.')
        res={'rows':'fail'}
        return jsonify(res)

#fetching all the suite after execution
@app.route('/reports/getSuiteDetailsInExecution_ICE',methods=['POST'])
def getSuiteDetailsInExecution_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            getsuitedetailsquery = ("select executionid,starttime,endtime "
                    +"from execution where testsuiteid="+requestdata['suiteid'])
            queryresult = icesession.execute(getsuitedetailsquery)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. report suites details execution.')
            return jsonify(res)
    except Exception as getsuitedetailsexc:
        app.logger.error('Error in getAllSuites_ICE.')
        return jsonify(res)

#fetching all the reports status
@app.route('/reports/reportStatusScenarios_ICE',methods=['POST'])
def reportStatusScenarios_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'executiondetails'):
                getreportstatusquery1 = ("select * from reports "
                +"where executionid="+requestdata['executionid']+" ALLOW FILTERING")
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
            app.logger.error('Empty data received. report status of scenarios.')
            return jsonify(res)
    except Exception as getreportstatusexc:
        app.logger.error('Error in reportStatusScenarios_ICE.')
        res={'rows':'fail'}
        return jsonify(res)

#fetching the reports
@app.route('/reports/getReport_Nineteen68',methods=['POST'])
def getReport_Nineteen68():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'projectsUnderDomain'):
                getreportquery1 =("select report,executedtime,testscenarioid "
                +"from reports where reportid=" +requestdata['reportid']
                +" ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery1)
            elif(requestdata["query"] == 'scenariodetails'):
                getreportquery2 =("select testscenarioname,projectid "
                +"from testscenarios where testscenarioid="
                + requestdata['scenarioid'] + " ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery2)
            elif(requestdata["query"] == 'cycleid'):
                getreportquery3 =("select cycleid from testsuites where "
                +"testsuiteid=" + requestdata['suiteid']
                + " and testsuitename = '" + requestdata['suitename']
                + "' ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery3)
            elif(requestdata["query"] == 'cycledetails'):
                getreportquery4 =("select cyclename,releaseid from cycles "
                +"where cycleid=" + requestdata['cycleid']  + "ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery4)
            elif(requestdata["query"] == 'releasedetails'):
                getreportquery5 =("select releasename,projectid from releases "
                +"where releaseid=" + requestdata['releaseid'] + " ALLOW FILTERING")
                queryresult = icesession.execute(getreportquery5)
            elif(requestdata["query"] == 'projectdetails'):
                getreportquery6 =("select projectname,domainid from projects "
                +"where projectid=" + requestdata['projectid']  + " ALLOW FILTERING")
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
            app.logger.error('Empty data received. report.')
            return jsonify(res)
    except Exception as getreportexc:
        app.logger.error('Error in getReport_Nineteen68.')
        return jsonify(res)

#export json feature on reports
@app.route('/reports/exportToJson_ICE',methods=['POST'])
def exportToJson_ICE():
    res={'rows':'fail'}
    try:
        requestdata=json.loads(request.data)
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
                +" ALLOW FILTERING")
                queryresult = icesession.execute(exporttojsonquery3)
            else:
                return jsonify(res)
            res= {"rows":queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. JSON Exporting.')
            return jsonify(res)
    except Exception as exporttojsonexc:
        app.logger.error('Error in exportToJson_ICE.')
        res={'rows':'fail'}
        return jsonify(res)

################################################################################
# END OF REPORTS
################################################################################


################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################

#encrpytion utility AES
@app.route('/utility/encrypt_ICE/aes',methods=['POST'])
def encrypt_ICE():
    res = "fail"
    try:
        import base64
        from Crypto.Cipher import AES
        BS = 16
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        key = b'\x74\x68\x69\x73\x49\x73\x41\x53\x65\x63\x72\x65\x74\x4b\x65\x79'
        raw=request.data
##        raw= inputval
        if not (raw is None and raw is ''):
            raw = pad(raw)
            cipher = AES.new( key, AES.MODE_ECB)
            res={'rows':base64.b64encode(cipher.encrypt( raw ))}
            return jsonify(res)
        else:
            app.logger.error("Invalid input")
            return str(res)
    except Exception as e:
        app.logger.error('Error in encrypt_ICE.')
        return str(res)

#directly updates license data
@app.route('/utility/dataUpdator_ICE',methods=['POST'])
def dataUpdator_ICE():
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
            app.logger.error('Empty data received. Data Updator.')
    except Exception as exporttojsonexc:
        app.logger.error('Error in dataUpdator_ICE.')
    return jsonify(res)

################################################################################
# END OF UTILITIES
################################################################################

##################################################
# BEGIN OF CHATBOT
##################################################

#Prof J First Service: Getting Best Matches
@app.route('/chatbot/getTopMatches_ProfJ',methods=['POST'])
def getTopMatches_ProfJ():
    try:
##        print "getting top matches for ya.."
##        print request.data
        query = str(request.data)
        global newQuesInfo
        global savedQueries

        #Importing Modules for Prof J

    ##    import xlrd
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
        return jsonify(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        res={'rows':'fail'}

#Prof J Second Service: Updating the Question's Frequency
@app.route('/chatbot/updateFrequency_ProfJ',methods=['POST'])
def updateFrequency_ProfJ():
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
        return jsonify(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        res={'rows':'fail'}

##################################################
# END OF CHATBOT
##################################################



################################################################################
# BEGIN OF INTERNAL COMPONENTS
################################################################################

###########################
# BEGIN OF GLOBAL VARIABLES
###########################

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
numberofdays=1
omgall="\x4e\x69\x6e\x65\x74\x65\x65\x6e\x36\x38\x6e\x64\x61\x74\x63\x6c\x69\x63\x65\x6e\x73\x69\x6e\x67"
ndacinfo = {
                "action": "",
                "sysinfo": {"mac": "","tkn": ""},
                "btchinfo": {
                                "prevbtch": {"prevbtchtym": "","prevbtchmsg": ""},
                                "nxtbtch": "",
                                "btchstts": ""
                },
                "modelinfo": {
                                "reports_in_day": [{"day": "","reprt_cnt": ""}],
        "suites_init":[{"day":"","suite_cnt":"","usr_data":[{"id":"","rns":""}]}],
                                "cnario_init":[{"day":"","cnario_cnt":"","usr_data":[{"id":"","rns":""}]}],
                                "tcases_init":[{"day":"","tcases_cnt":"","usr_data":[{"id":"","rns":""}]}]
                }
}

###########################
# END OF GLOBAL VARIABLES
###########################

############################
# BEGIN OF GENERIC FUNCTIONS
############################
def isemptyrequest(requestdata):
    flag = False
    global offlineuser
    global usersession
    global onlineuser
    if (offlineuser != True and onlineuser != False):
        for key in requestdata:
            value = requestdata[key]
            if (key != 'additionalroles'
                and key != 'getparampaths' and key != 'testcasesteps'):
                if value == 'undefined' or value == '' or value == 'null' or value == None:
                    app.logger.error(key)
                    flag = True
    else:
        global offlinestarttime
        global offlineendtime
        currenttime=datetime.now()
        if usersession != False:
            if (currenttime >= offlinestarttime and currenttime <= offlineendtime):
                for key in requestdata:
                    value = requestdata[key]
                    if (key != 'additionalroles'
                        and key != 'getparampaths' and key != 'testcasesteps'):
                        if value == 'undefined' or value == '' or value == 'null' or value == None:
                            app.logger.error(key)
                            flag = True
            else:
                global handler
                handler.setLevel(logging.CRITICAL)
                app.logger.addHandler(handler)
                app.logger.critical("User validity expired... "
                +"Please contact Nineteen68 Team for Enabling")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
                usersession = False
                flag = True
        else:
            if offlineuser != True:
                flag = True
                app.logger.critical("Access to Nineteen68 Expires.")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
            else:
                flag = True
                global handler
                handler.setLevel(logging.CRITICAL)
                app.logger.addHandler(handler)
                app.logger.critical("User validity expired... "
                +"Please contact Nineteen68 Team for Enabling")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
    return flag

def getcurrentdate():
    currentdate= datetime.now()
    beginingoftime = datetime.utcfromtimestamp(0)
    differencedate= currentdate - beginingoftime
    return long(differencedate.total_seconds() * 1000.0)

def testsuite_exists(project_id,module_name,moduleid=''):
    query['suite_check']="select moduleid FROM modules where projectid="+project_id+" and modulename='"+module_name+"' ALLOW FILTERING"
    query['suite_check_id']="select moduleid FROM modules where projectid="+project_id+" and modulename='"+module_name+"' and moduleid="+moduleid+" ALLOW FILTERING"

def testscenario_exists(project_id,testscenario_name,testscenario_id=''):
    query['scenario_check'] = "select testscenarioid from testscenarios where projectid="+project_id+" and testscenarioname='"+testscenario_name+"' ALLOW FILTERING"
    query['scenario_check_id'] = "select testscenarioid from testscenarios where projectid="+project_id+" and testscenarioname='"+testscenario_name+"' and testscenarioid = "+testscenario_id+" ALLOW FILTERING"


def testscreen_exists(project_id,screen_name,screen_id=''):
    query['screen_check'] = "select screenid from screens where projectid="+project_id+" and screenname='"+screen_name+"' ALLOW FILTERING"
    query['screen_check_id'] = "select testscenarioid from testscenarios where projectid="+project_id+" and testscenarioname='"+screen_name+"' and testscenarioid = "+screen_id+" ALLOW FILTERING"

def testcase_exists(screen_id,testcase_name,testcase_id=''):
    query['testcase_check'] = "select testcaseid from testcases where screenid="+screen_id+" and testcasename='"+testcase_name+"' ALLOW FILTERING"
    query['testcase_check_id'] = "select testcaseid from testcases where screenid="+screen_id+" and testcasename='"+testcase_name+"' and testcaseid="+testcase_id+" ALLOW FILTERING"

def get_delete_query(node_id,node_name,node_version_number,node_parentid,projectid=None):
    node_version_number=str(node_version_number)
    query['delete_module']="delete FROM modules WHERE moduleid="+node_id+" and modulename='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid
    query['delete_testscenario']="delete FROM testscenarios WHERE testscenarioid="+node_id+" and testscenarioname='"+node_name+"' and projectid="+node_parentid
    query['delete_screen']="delete FROM screens WHERE screenid="+node_id+" and screenname='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid
    query['delete_testcase']="delete FROM testcases WHERE testcaseid="+node_id+" and testcasename='"+node_name+"' and versionnumber="+node_version_number+" and screenid="+node_parentid

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
        currentdateindays = getbgntime('curr',datetime.now()) - beginingoftime
        currentdate = long(currentdateindays.total_seconds() * 1000.0)
        updatorarray = ["update counters set counter=counter + ",
                    " where counterdate= "," and userid = "," and countertype= ",";"]
        updatequery=(updatorarray[0]+str(count)+updatorarray[1]
                    +str(currentdate)+updatorarray[2]+userid+updatorarray[3]+"'"
                    +updatortype+"'"+updatorarray[4])
        icesession.execute(updatequery)
        status = True
    except Exception as counterupdatorexc:
##        import traceback
##        traceback.print_exc()
        app.logger.error('Error in counterupdatorexc.')
    return status

def getreports_in_day(bgnts,endts):
    res = {"rows":"fail"}
    try:
        query=("select * from reports where executedtime  >= "
            +str(bgnts)+" and executedtime <= "+str(endts)+" allow filtering;")
        queryresult = icesession.execute(query)
    ##    print queryresult.current_rows
        res= {"rows":queryresult.current_rows}
    except Exception as getreports_in_dayexc:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 2 reports")
    return res

def getsuites_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        suitequery=("select * from counters where counterdate >= "+str(bgnts)
        +" and counterdate < "+str(endts)
        +" and countertype='testsuites' ALLOW FILTERING;")
        queryresult = icesession.execute(suitequery)
        res= {"rows":queryresult.current_rows}

    except Exception as getsuites_inititatedexc:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 2 suites")
    return res

def getscenario_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        scenarioquery=("select * from counters where counterdate >= "+str(bgnts)
        +" and counterdate < "+str(endts)
        +" and countertype='testscenarios' ALLOW FILTERING;")
        queryresult = icesession.execute(scenarioquery)
        res= {"rows":queryresult.current_rows}
    except Exception as getscenario_inititatedexc:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 2 scenarios")
    return res

def gettestcases_inititated(bgnts,endts):
    res = {"rows":"fail"}
    try:
        testcasesquery=("select * from counters where counterdate >= "+str(bgnts)
        +" and counterdate < "+str(endts)
        +" and countertype='testcases' ALLOW FILTERING;")
        queryresult = icesession.execute(testcasesquery)
        res = {"rows":queryresult.current_rows}

    except Exception as gettestcases_inititatedexc:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 2 cases")
    return res

def modelinfoprocessor(processingdata):
    modelinfo=[]
    try:
        bgnyesday = getbgntime('prev',datetime.now())
        bgnoftday = getbgntime('curr',datetime.now())
        daybforedate=''
        if (processingdata['btchinfo']['btchstts'] == 'error' or
            processingdata['btchinfo']['btchstts'] == ''):
            daybforedate=getbgntime('daybefore',datetime.now())
##        suiteinfo=[]
##        cnarioinfo=[]
##        tcasesinfo=[]
        if daybforedate != '':
            for days in range(0,2):
                dailydata={}
                allusers = []
                bgnts=gettimestamp(daybforedate)
                endts=gettimestamp(bgnyesday)
##                print bgnts
##                print endts
                dailydata['day'] = str(bgnyesday)
                resultset=getreports_in_day(bgnts,endts)
##                modelinfo['reports_in_day']=reportdataprocessor(resultset,daybforedate,bgnyesday)
                reportobj=reportdataprocessor(resultset,daybforedate,bgnyesday)
                dailydata['r_exec_cnt'] = str(reportobj['reprt_cnt'])

##                suiteinfo.append(dataprocessor('testsuites',bgnts,endts,bgnyesday))
                suiteobj=dataprocessor('testsuites',bgnts,endts)
                dailydata['su_exec_cnt'] = str(suiteobj['suite_cnt'])
                allusers = allusers + suiteobj['active_usrs']

##                cnarioinfo.append(dataprocessor('testscenarios',bgnts,endts))
                scenariosobj=dataprocessor('testscenarios',bgnts,endts)
                dailydata['s_exec_cnt'] = str(scenariosobj['cnario_cnt'])
                allusers = allusers + scenariosobj['active_usrs']

##                tcasesinfo.append(dataprocessor('testcases',bgnts,endts))
                testcasesobj=dataprocessor('testcases',bgnts,endts)
                dailydata['t_exec_cnt'] = str(testcasesobj['tcases_cnt'])
                allusers = allusers + testcasesobj['active_usrs']
                print allusers
                licensesarray=[]
                licensesarray.append(str(len(set(allusers))))
                dailydata['license_usd'] = licensesarray
##                modelinfo['suites_init'] = suiteinfo
##                modelinfo['cnario_init'] = cnarioinfo
##                modelinfo['tcases_init'] = tcasesinfo
                modelinfo.append(dailydata)
                daybforedate=bgnyesday
                bgnyesday=bgnoftday
        else:
            dailydata={}
            allusers = []
            dailydata['day'] = str(datetime.now())

            bgnts=gettimestamp(bgnyesday)
            endts=gettimestamp(bgnoftday)
##            print bgnts
##            print endts
            resultset=getreports_in_day(bgnts,endts)
##            modelinfo['reports_in_day']=reportdataprocessor(resultset,bgnyesday,bgnoftday)
            reportobj=reportdataprocessor(resultset,bgnyesday,bgnoftday)
            dailydata['r_exec_cnt'] = str(reportobj['reprt_cnt'])
##            suiteinfo.append(dataprocessor('testsuites',bgnts,endts))
            suiteobj = dataprocessor('testsuites',bgnts,endts)
            dailydata['su_exec_cnt'] = str(suiteobj['suite_cnt'])
            allusers = allusers + suiteobj['active_usrs']
##            cnarioinfo.append(dataprocessor('testscenarios',bgnts,endts))
            scenariosobj = dataprocessor('testscenarios',bgnts,endts)
            dailydata['s_exec_cnt'] = str(scenariosobj['cnario_cnt'])
            allusers = allusers + scenariosobj['active_usrs']
##            tcasesinfo.append(dataprocessor('testcases',bgnts,endts))
            testcasesobj = dataprocessor('testcases',bgnts,endts)
            dailydata['t_exec_cnt'] = str(testcasesobj['tcases_cnt'])
            allusers = allusers + testcasesobj['active_usrs']
            print allusers
            licensesarray=[]
            licensesarray.append(str(len(set(allusers))))
            dailydata['license_usd'] = licensesarray
            modelinfo.append(dailydata)
##            modelinfo['suites_init'] = suiteinfo
##            modelinfo['cnario_init'] = cnarioinfo
##            modelinfo['tcases_init'] = tcasesinfo
    except Exception as e:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 3")
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
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas 4")
    return respobj

def reportdataprocessor(resultset,fromdate,todate):
    processorres = False
    count = 0
    try:
        eachreports_in_day={"reprt_cnt":"","day":""}
        curr=datetime.now()
        if resultset['rows'] != 'fail':
            for eachrow in resultset['rows']:
                exectime=eachrow['executedtime']
                if exectime != None:
                    if (exectime >= fromdate and exectime < todate):
                        count = count + 1
        eachreports_in_day['day'] = str(todate)
        eachreports_in_day['reprt_cnt'] = str(count)
    except Exception as reportdataprocessorexc:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to perform internal actions")
    return eachreports_in_day

################################################################################
# END OF COUNTERS
################################################################################
################################################################################
# START LICENSING COMPONENTS
################################################################################
def getMacAddress():
    mac=''
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
    import time
    import calendar
##    print time.strftime(str(date))
    date= datetime.strptime(str(date),"%Y-%m-%d %H:%M:%S")
    timestampdata = calendar.timegm(date.utctimetuple()) * 1000
    return timestampdata


def basecheckonls():
    basecheckstatus=False
##    print mac
##    data= {"action":"register","sysinfo":physical_trans,"visited":"no"}
    baserequest= {"action": "register","sysinfo": {"mac": mac.strip(),"token": ""},
                   "visited": "no"}
    try:
        baserequest=wrap(str(baserequest),omgall)
        connectresponse = connectingls(baserequest)
##        print 'connectresponse:::',connectresponse
        if connectresponse != False:
            actresp = unwrap(str(connectresponse),omgall)
##            print 'This is the value',actresp
            actresp = ast.literal_eval(actresp)
            if actresp['action'] == 'error':
                    app.logger.error(actresp['lsinfotondac']['message'])
            else:
                baseresponse = ndacinfo
                baseresponse['sysinfo']['tkn']=actresp['lsinfotondac']['lstokentondac'];
##                baseresponse['sysinfo']['tkn']='';
                baseresponse['sysinfo']['mac']=mac.strip();
                baseresponse['action']=actresp['action']
##                print 'NDAC info:::\n\n',baseresponse
                wrappedbaseresponse=wrap(str(baseresponse),mine)
                dataholderresp=dataholder(wrappedbaseresponse,'new')
                if dataholderresp != False:
                    basecheckstatus = dataholderresp
##                a=dataholder(mywrapeddata,'select')
##                print '\n\n\n',a
##                myunwrapeddata=unwrap(str(a),mine)
##                print '\n\n',myunwrapeddata
            global onlineuser
            onlineuser = True
        else:
            app.logger.error("Unable to connect to Server")
    except Exception as e:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas")
    return basecheckstatus

def updateonls():
    global lsondayone
    global lsondaytwo
    try:
        selected=dataholder('','select')
        myunwrapeddata=unwrap(str(selected),mine)
        processingdata = ast.literal_eval(myunwrapeddata)
        updaterequest={}
        modelinfo={}
        updaterequest['sysinfo'] = processingdata['sysinfo']
        updaterequest['modelinfo']=modelinfo
##        modelinfores = modelinfoprocessor(processingdata)
##        updaterequest['modelinfo']['execs_in_day']=modelinfores
        modelinfores = modelinfoprocessor(processingdata)
        updaterequest['modelinfo'] = modelinfores
        updaterequest['action'] = 'update'
        wrappedupdaterequest=wrap(str(updaterequest),omgall)
        updateresponse = connectingls(wrappedupdaterequest)
        if updateresponse != False:
            cronograph()
            updateresponse=unwrap(str(updateresponse),omgall)
            updateresponse = ast.literal_eval(updateresponse)
            if updateresponse['action'] == 'error':
                app.logger.error(updateresponse['lsinfotondac']['message'])
                errorstorage=dataholder('','select')
                errorunwrap=unwrap(str(errorstorage),mine)
                errorprocessed = ast.literal_eval(errorunwrap)
                failtime=datetime.now()
                errorprocessed['btchinfo']['prevbtch']['prevbtchtym'] =str(failtime)
                errorprocessed['btchinfo']['prevbtch']['prevbtchmsg'] = updateresponse['lsinfotondac']['message']
                nxtbatch = getbgntime('nxt',failtime)
                errorprocessed['btchinfo']['nxtbtch'] = str(nxtbatch)
                errorprocessed['btchinfo']['btchstts'] = updateresponse['action']
                errorprocessed['action'] = 'update'
                errorprocessed=wrap(str(errorstorage),mine)
                updatestatus = dataholder(errorprocessed,'update')
                if lsondayone != True and lsondaytwo != True:
                    lsondayone = True
                    app.logger.error("Could not connect to Server")
                elif lsondayone == True and lsondaytwo !=True:
                    lsondaytwo = True
                    global onlineuser
                    onlineuser = False
                    app.logger.error("License Expired.")
            else:
                completemsg=updateresponse['lsinfotondac']['message']
                token=processingdata['sysinfo']['tkn']
                tokenreturned=completemsg.split('success')[1]
                if (token == tokenreturned):
                    lsondayone = False
                    lsondaytwo = False
                    successstorage=dataholder('','select')
                    successunwrap=unwrap(str(successstorage),mine)
                    successstorage = ast.literal_eval(successunwrap)
                    successstorage['action'] = 'update'
                    successstorage['btchinfo']['btchstts'] = 'success'
                    successstorage['btchinfo']['nxtbtch'] = str(getbgntime('nxt',datetime.now()))
                    successstorage=wrap(str(successstorage),mine)
                    updatestatus = dataholder(str(successstorage),'update')
                else:
                    app.logger.error('Server Authentication Failed.Invalid Server Authentication.')
                    errorstorage=dataholder('','select')
                    errorunwrap=unwrap(str(errorstorage),mine)
                    errorprocessed = ast.literal_eval(errorunwrap)
                    failtime=datetime.now()
                    errorprocessed['btchinfo']['prevbtch']['prevbtchtym'] =str(failtime)
                    errorprocessed['btchinfo']['prevbtch']['prevbtchmsg'] = updateresponse['lsinfotondac']['message']
                    nxtbatch = getbgntime('nxt',failtime)
                    errorprocessed['btchinfo']['nxtbtch'] = str(nxtbatch)
                    errorprocessed['btchinfo']['btchstts'] = updateresponse['action']
                    errorprocessed['action'] = 'update'
                    errorprocessed=wrap(str(errorstorage),mine)
                    updatestatus = dataholder(errorprocessed,'update')
                    if lsondayone != True and lsondaytwo != True:
                        lsondayone = True
                        app.logger.error("Could not connect to Server")
                    elif lsondayone == True and lsondaytwo !=True:
                        lsondaytwo = True
                        global onlineuser
                        onlineuser = False
                        app.logger.error("License Expired.")
        else:
            if lsondayone != True and lsondaytwo != True:
                cronograph()
                lsondayone = True
                app.logger.error("Could not connect to Server")
            elif lsondayone == True and lsondaytwo != True:
                lsondaytwo = True
                global onlineuser
                onlineuser = False
                app.logger.error("Licenses Expired.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        app.logger.critical("Unable to contact storage areas")

def getbgntime(requiredday,currentday):
    import datetime
    day = ''
    if requiredday == 'prev':
        yesterday=currentday - datetime.timedelta(1)
        day=datetime.datetime(yesterday.year, yesterday.month, yesterday.day,0,0,0,0)
    elif requiredday == 'nxt':
        tomorrow=currentday + datetime.timedelta(1)
        day=datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day,0,0,0,0)
    elif requiredday == 'daybefore':
        daybefore=currentday - datetime.timedelta(2)
        day=datetime.datetime(daybefore.year, daybefore.month, daybefore.day,0,0,0,0)
    elif requiredday == 'curr':
        day=datetime.datetime(currentday.year, currentday.month, currentday.day,0,0,0,0)
    elif requiredday == 'indate':
        day=datetime.datetime(currentday.year, currentday.month, currentday.day,0,0,0,0)
    return day

def connectingls(data):
    try:
        connectionstatus=False
        lsresponse = requests.post('http://'+lsip+":5000/ndacrequest",data=data)
##        lsresponse = requests.post("http://127.0.0.1:5000/ndacrequest",data=data)
        if lsresponse.status_code == 200:
            connectionstatus = lsresponse.content
##        else:
##            app.logger.error("Status Code:",lsresponse.content)
    except Exception as e:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("Liscense server must be running")
        connectionstatus = False
    return connectionstatus

def offlineuserenabler(startdate,enddate,usermac):
    enabled = False
    # this is provided as there was a request to create a key
    # without mac address
    if usermac != 'nomacaddress':
        mac = getMacAddress()
    else:
        mac = usermac
    if usermac in mac.strip():
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
    except Exception as scheduleenablerexeption:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("<<<<Issue with the Server>>>>")

def cronograph():
    try:
        from threading import Timer
        x=datetime.today()
        updatehr=00
        updatemin=00
        updatesec=00
        updatemcrs=00
        y=x.replace(day=x.day+1, hour=updatehr, minute=updatemin, second=updatesec, microsecond=updatemcrs)
        #for development purposes only
##        y=x.replace(day=x.day, hour=x.hour, minute=x.minute+1, second=updatesec, microsecond=updatemcrs)

        delta_t=y-x
        secs=delta_t.seconds+1
        t = Timer(secs, updateonls)
        t.start()
    except Exception as cronoexeption:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("<<<<Issue with the Server>>>>")

def dataholder(data,querytype):
    try:
        dataholderresp=False
        #connect to a database(creates if doesnt exist)
        conn = sqlite3.connect(logspath+"/data.db")
        #create cursor
        cursor = conn.cursor()
        if querytype == 'update':
            conn.execute("UPDATE clndls SET intrtkndt = ? WHERE sysid = 'ndackey'",[data])
            dataholderresp = True
        elif querytype == 'new':
            cursor.execute("CREATE TABLE IF NOT EXISTS clndls (sysid TEXT PRIMARY KEY, intrtkndt TEXT);")
            try:
                cursor.execute("INSERT INTO clndls(sysid,intrtkndt) VALUES ('ndackey','"+data+"')")
            except Exception as e:
                dataholderresp = False
##                app.logger.error("<<<<Running on existing DB>>>>")
            dataholderresp = True
        elif querytype == 'select':
            cursor1=conn.execute("SELECT intrtkndt FROM clndls WHERE sysid='ndackey'")
            for a in cursor1:
                dataholderresp = a[0]
        conn.commit()
        conn.close()
    except Exception as dataholderexeption:
##        import traceback
##        traceback.print_exc()
        app.logger.critical("<<<<Issue with the Storing>>>>")

    return dataholderresp


def beginserver():
    if dbup:
        serve(app,host='127.0.0.1',port=1990)
        app.logger.error("<<<<Server Turns active>>>>")
    else:
        app.logger.critical("<<<<Database needs to be Started>>>>")

def closehonor(result):
    res={}
    global lsondayone
    global lsondaytwo
    if lsondayone == True:
        result["dayone"]="True"
        res=result
    elif lsondaytwo == True:
        res["daytwo"]="True"
    else:
        res=result
    return res

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

if __name__ == '__main__':

##    context = ('cert.pem', 'key.pem')#certificate and key files
##    #https implementation
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context=context)
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context='adhoc')

    #http implementations
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    inhandler = TimedRotatingFileHandler(logspath+'/ndac/ndac'+datetime.now().strftime("_%Y%m%d-%H%M%S")+'.log',when='d', encoding='utf-8', backupCount=1)
    global handler
    handler=inhandler
    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.propagate = False
    mac = getMacAddress()
    ndacinfo['sysinfo']['mac']=mac
    if args.verbosity:
        try:
            f = open(sys.argv[-1],"r")
            contents = f.read()
            f.close()
            userinformation=unwrap(str(contents),offreg)
            userinfo=ast.literal_eval(userinformation)

            startdate = userinfo['offlinereginfo']['startdate']
            if not ('-' in startdate):
                startdate = datetime.strptime(startdate, '%m/%d/%Y')
                startdate = getbgntime('indate',startdate)
##                print startdate
##                startdate = datetime.strptime(startdate,'%m/%d/%Y %H%M%S')
            else:
                startdate = datetime.strptime(startdate, '%m/%d/%Y-%H%M%S')

            enddate = userinfo['offlinereginfo']['enddate']
            if not ('-' in enddate):
                enddate = datetime.strptime(enddate, '%m/%d/%Y')
                enddate = getbgntime('indate',enddate)
##                print enddate
##                enddate = datetime.strptime(enddate,'%m/%d/%Y %H%M%S')
            else:
                enddate = datetime.strptime(enddate, '%m/%d/%Y-%H%M%S')
            # this is provided as there was a request to create a key
            # without mac address
            if 'mac' in userinfo['offlinereginfo']:
                if userinfo['offlinereginfo']['mac'] != 'NO':
                    mac = userinfo['offlinereginfo']['mac']
                else:
                    mac = 'nomacaddress'
            enabled = offlineuserenabler(startdate,enddate,mac)
            if enabled == True:
                beginserver()
            else:
                if (startdate > datetime.now()):
                    scheduleenabler(offlinestarttime)
                    app.logger.error("Server starts only after : "+str(offlinestarttime))
                else:
                    app.logger.error("Please contact Team - Nineteen68. Issue: offlineuser.key");
        except Exception as e:
##            import traceback
##            traceback.print_exc()
            app.logger.critical("Please contact Team - Nineteen68. Issue: Offline user")

    else:
        if (basecheckonls()):
            cronograph()
        ##        app.run(host='127.0.0.1',port=1990,debug=False)

            beginserver()