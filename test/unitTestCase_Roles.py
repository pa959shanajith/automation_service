#-------------------------------------------------------------------------------
# Name:        das.py
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
from os import access
#sys.path.append('./packages/Lib/site-packages')
import json
##import requests
##import subprocess
##import sqlite3
##
##import logging
##handler=''

from datetime import datetime
import uuid

##import ast
##
##from flask import Flask, request , jsonify
##from waitress import serve
##from logging.handlers import TimedRotatingFileHandler
##app = Flask(__name__)
##
##import argparse
##parser = argparse.ArgumentParser()
##parser.add_argument("-k","--verbosity", type=str, help="home user"
##                    +"registration. Provide the offline registration filename")
##args = parser.parse_args()
##

##os.chdir("..")
#Avo Assure folder location is parent directory
##currdir=os.getcwd()
##config_path = currdir+'/server_config.json'
##assistpath = currdir + "/das_internals/assist"
##logspath= currdir + "/das_internals/logs"
##
##das_conf = json.loads(open(config_path).read())
##
##lsip = das_conf['licenseserver']
from cassandra.cluster import Cluster
#from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
dbup = False
try:
    auth = PlainTextAuthProvider(username='nineteen68', password='TA@SLK2017')
    cluster = Cluster(['10.41.31.120'],port=9042,auth_provider=auth)

    icesession = cluster.connect()
    dbsession = cluster.connect()
    icehistorysession = cluster.connect()
    dbhistorysession = cluster.connect()

    from cassandra.query import dict_factory
    icesession.row_factory = dict_factory
    icesession.set_keyspace('icetestautomation')

    dbsession.row_factory = dict_factory
    dbsession.set_keyspace('nineteen68')
    dbup = True
except Exception as dbexception:
    print ('Error in Database connectivity...');

#default values for offline user
##offlinestarttime=''
##offlineendtime=''
##offlineuser = False
##onlineuser = False
##usersession = False
##lsondayone = ""
##lsondaytwo = ""

#counters for License
##debugcounter = 0
##scenarioscounter = 0
##gtestsuiteid = []
##suitescounter = 0

#server check
##@app.route('/')
def server_ready():
    return 'Data Server Ready!!!'


################################################################################
# BEGIN OF LOGIN SCREEN
# INCLUDES : Login components
################################################################################

#service for login to Avo Assure
#@app.route('/login/authenticateUser',methods=['POST'])
def authenticateUser():
    res={'rows':'fail'}
    try:
        #requestdata=json.loads(request.data)
        #if not isemptyrequest(requestdata):
            authenticateuser = ("select password from users where username = '"
                                +requestdata["username"]+"' "
                                +" ALLOW FILTERING;")
            queryresult = dbsession.execute(authenticateuser)
            res= {"rows":queryresult.current_rows}
            res=closehonor(res)
##            if 'dayone' in res:
##                app.logger.critical('Licenses will expire tomorrow.')
##            elif 'daytwo' in res:
##                app.logger.critical('Licenses expired.')
            return res
##        else:
##            print ('Empty data received. authentication')
##            res=closehonor(res)
##            if 'dayone' in res:
##                app.logger.critical('Licenses will expire tomorrow.')
##            elif 'daytwo' in res:
##                app.logger.critical('Licenses expired.')
##            return jsonify(res)
    except Exception as authenticateuserexc:
        print ('Error in authenticateUser.')
        res=closehonor(res)
##        if 'dayone' in res:
##            app.logger.critical('Licenses will expire tomorrow.')
##        elif 'daytwo' in res:
##            app.logger.critical('Licenses expired.')
        return res

#service for user ldap validation
#@app.route('/login/authenticateUser/ldap',methods=['POST'])
def authenticateUser_ldap():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            authenticateuserldap = ("select ldapuser from users where "
                                    +"username = '"+requestdata["username"]+"'"
                                    +"allow filtering;")
            queryresult = dbsession.execute(authenticateuserldap)
            res= {"rows":queryresult.current_rows}
            res=closehonor(res)
            return res
##        else:
##            print ('Empty data received. authentication')
##            res=closehonor(res)
##            return jsonify(res)
    except Exception as authenticateuserldapexc:
        print ('Error in authenticateUser_ldap.')
        res=closehonor(res)
        return res

#service for getting rolename by roleid
#@app.route('/login/getRoleNameByRoleId',methods=['POST'])
def getRoleNameByRoleId():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            rolename = ("select rolename from roles where "
                        +"roleid = "+requestdata["roleid"]
                        +" allow filtering;")
            queryresult = dbsession.execute(rolename)
            res = {"rows":queryresult.current_rows}
            return res
##        else:
##            print ('Empty data received. authentication')
##
##            return jsonify(res)
    except Exception as rolenameexc:
        print ('Error in getRoleNameByRoleId.')
        return res

#utility checks whether user is having projects assigned
#@app.route('/login/authenticateUser/projassigned',methods=['POST'])
def authenticateUser_projassigned():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'getUserId'):
                authenticateuserprojassigned1= ("select userid,defaultrole "
                                                +"from users where "
                                                +"username = '"
                                                +requestdata["username"]
                                                +"' allow filtering;")
                queryresult = dbsession.execute(authenticateuserprojassigned1)
            elif(requestdata["query"] == 'getUserRole'):
                authenticateuserprojassigned2= ("select rolename from roles"
                                                +" where roleid = "
                                                +requestdata["roleid"]
                                                +" allow filtering;")
                queryresult = dbsession.execute(authenticateuserprojassigned2)
            elif(requestdata["query"] == 'getAssignedProjects'):
                authenticateuserprojassigned3= ("select projectids from"
                                            +" icepermissions where userid = "
                                            +requestdata["userid"]
                                            +" allow filtering;")
                queryresult = icesession.execute(authenticateuserprojassigned3)
            else:
                return res
            res= {"rows":queryresult.current_rows}
            return res
##        else:
##            print ('Empty data received. authentication')
##            return jsonify(res)
    except Exception as authenticateuserprojassignedexc:
        print 'Error in authenticateUser_projassigned.'
        return res

#service for loading user information
#@app.route('/login/loadUserInfo',methods=['POST'])
def loadUserInfo():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'userInfo'):
                loaduserinfo1 = ("select userid, emailid, firstname, lastname, "
                                +"defaultrole, ldapuser, additionalroles, username "
                                +"from users where username = "+
                                "'"+requestdata["username"]+"' allow filtering")
                queryresult = dbsession.execute(loaduserinfo1)
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
                return res
            elif(requestdata["query"] == 'loggedinRole'):
                loaduserinfo2 = ("select rolename from roles where "
                                    +"roleid = "+requestdata["roleid"]
                                    +" allow filtering")
                queryresult = dbsession.execute(loaduserinfo2)
            elif(requestdata["query"] == 'userPlugins'):
                loaduserinfo3 = ("select * from "
                                +"userpermissions where roleid = "
                                +requestdata["roleid"]+" allow filtering")
                queryresult = dbsession.execute(loaduserinfo3)
            else:
                return res
            res= {"rows":queryresult.current_rows}
            return res
##        else:
##            print ('Empty data received. loadUserInfo')
##            return jsonify(res)
    except Exception as loaduserinfoexc:
        print ('Error in loadUserInfo.')
        return res

################################################################################
# END OF LOGIN SCREEN
################################################################################


################################################################################
# BEGIN OF MIND MAPS
# INCLUDES : all Mindmap related queries
################################################################################

#getting Release_iDs of Project
#@app.route('/create_ice/getReleaseIDs',methods=['POST'])
def getReleaseIDs():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getReleaseDetails = ("select releasename,releaseid from icetestautomation.releases "+
            "where projectid"+'='+ projectid+query['delete_flag'])
            queryresult = icesession.execute(getReleaseDetails)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. getReleaseIDs")
    except Exception as e:
        print ('Error in getReleaseIDs.')
    return res


#@app.route('/create_ice/getCycleIDs',methods=['POST'])
def getCycleIDs():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            releaseid=requestdata['releaseid']
            getCycleDetails = ("select cyclename,cycleid from icetestautomation.cycles "+
            "where releaseid"+'='+ releaseid+query['delete_flag'])
            queryresult = icesession.execute(getCycleDetails)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. getCycleIDs")
    except Exception as e:
        print ('Error in getCycleIDs.')
    return res

#@app.route('/create_ice/getProjectType',methods=['POST'])
def getProjectType():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            projectid=requestdata['projectid']
            getProjectType = ("select projecttypeid FROM icetestautomation.projects "+
            "where projectid"+'='+ projectid+query['delete_flag'])
            queryresult = icesession.execute(getProjectType)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. getProjectType")
    except Exception as e:
        print ('Error in getProjectType.')
    return res

#getting ProjectID and names of project sassigned to particular user
#@app.route('/create_ice/getProjectIDs',methods=['POST'])
def getProjectIDs():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'getprojids'):
                userid=requestdata['userid']
                getProjIds = ("select projectids FROM icetestautomation.icepermissions "+
                "where userid="+userid)
                queryresult = icesession.execute(getProjIds)
                res={'rows':queryresult.current_rows}
            elif (requestdata['query'] == 'getprojectname'):
                projectid=requestdata['projectid']
                getprojectname = ("select projectname,projecttypeid FROM icetestautomation.projects "+
                "where projectid="+projectid+query['delete_flag'])
                queryresult = icesession.execute(getprojectname)
                res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. getProjectIDs")
    except Exception as e:
        print ('Error in getProjectIDs.')
    return res

#getting names of module/scenario/screen/testcase name of given id
#@app.route('/create_ice/getNames',methods=['POST'])
def getAllNames_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            name=requestdata['name']
            nodeid=requestdata['id']
            getname_query=(query[name]+nodeid+query['delete_flag'])
            queryresult = icesession.execute(getname_query)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. getAllNames_ICE")
    except Exception as e:
        print ('Error in getAllNames_ICE.')
    return res

#getting names of empty projects for project replication
#@app.route('/create_ice/getEmptyProjects_ICE',methods=['POST'])
def getEmptyProjects_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            modulequery="select distinct projectid from modules"
            modulequeryresult = icesession.execute(modulequery)
            modpids=[]
            for row in modulequeryresult.current_rows:
                modpids.append(str(row['projectid']))
            emptyProjects={
                'projectId':[],
                'projectName':[]
            }
            for pid in requestdata['projectids']:
                if pid not in modpids:
                    getemptyprojectsquery="select projectid,projectname from projects where projectid="+pid
                    queryresult = icesession.execute(getemptyprojectsquery)
                    prjDetail=queryresult.current_rows
                    if(len(prjDetail)!=0):
                        emptyProjects['projectId'].append(str(prjDetail[0]['projectid']))
                        emptyProjects['projectName'].append(prjDetail[0]['projectname'])
            res={'rows':emptyProjects}
##       else:
##            print ("Empty data received. getEmptyProjects_ICE")
    except Exception as e:
        print (e)
        print ('Error in getEmptyProjects_ICE.')
    return (res)

#getting names of module/scenario/screen/testcase name of given id
#@app.route('/create_ice/testscreen_exists_ICE',methods=['POST'])
def testscreen_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            screen_name=requestdata['screen_name']
            screen_check =("select screenid from screens where screenname='"+screen_name
            +"' ALLOW FILTERING")
            queryresult = icesession.execute(screen_check)
            res={'rows':queryresult.current_rows}
##       else:
##            app.logger.error("Empty data received. testscreen_exists")
    except Exception as e:
        print ('Error in testscreen_exists.')
    return (res)


#getting names of module/scenario/screen/testcase name of given id
#@app.route('/create_ice/testcase_exists_ICE',methods=['POST'])
def testcase_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            testcase_name=requestdata['testcase_name']
            testcase_check =("select testcaseid from testcases where testcasename='"+testcase_name
            +"' ALLOW FILTERING")
            queryresult = icesession.execute(testcase_check)
            res={'rows':queryresult.current_rows}
##       else:
##            app.logger.error("Empty data received. testcase_exists")
    except Exception as e:
        print ('Error in testcase_exists.')
    return (res)


#getting names of module/scenario/screen/testcase name of given id
#@app.route('/create_ice/testsuiteid_exists_ICE',methods=['POST'])
def testsuiteid_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='suite_check':
                testsuite_exists(requestdata['project_id'],requestdata['module_name'],requestdata['versionnumber'])
            else:
                testsuite_exists(requestdata['project_id'],requestdata['module_name'],requestdata['versionnumber'],requestdata['module_id'])
            testsuite_check=query[query_name]
            queryresult = icesession.execute(testsuite_check)
            res={'rows':queryresult.current_rows}
##       else:
##            app.logger.error("Empty data received. testsuiteid_exists_ICE")
    except Exception as e:
        print ('Error in testsuiteid_exists_ICE.')
    return (res)

#@app.route('/create_ice/testscenariosid_exists_ICE',methods=['POST'])
def testscenariosid_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='scenario_check':
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'],requestdata['versionnumber'])
            else:
                testscenario_exists(requestdata['project_id'],requestdata['scenario_name'],requestdata['versionnumber'],requestdata['scenario_id'])
            testscenario_check=query[query_name]
            queryresult = icesession.execute(testscenario_check)
            res={'rows':queryresult.current_rows}
##       else:
##            app.logger.error("Empty data received. testscenariosid_exists")
    except Exception as e:
        print ('Error in testscenariosid_exists.')
    return (res)


#@app.route('/create_ice/testscreenid_exists_ICE',methods=['POST'])
def testscreenid_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='screen_check':
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'],requestdata['versionnumber'])
            else:
                testscreen_exists(requestdata['project_id'],requestdata['screen_name'],requestdata['versionnumber'],requestdata['screen_id'])
            testscreen_check=query[query_name]
            queryresult = icesession.execute(testscreen_check)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. testscreenid_exists_ICE")
    except Exception as e:
        print ('Error in testscreenid_exists_ICE.')
    return (res)

#@app.route('/create_ice/testcaseid_exists_ICE',methods=['POST'])
def testcaseid_exists_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            if query_name=='testcase_check':
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'],requestdata['versionnumber'])
            else:
                testcase_exists(requestdata['screen_id'],requestdata['testcase_name'],requestdata['versionnumber'],requestdata['testcase_id'])
            testcase_check=query[query_name]
            queryresult = icesession.execute(testcase_check)
            res={'rows':queryresult.current_rows}
##       else:
##            print ("Empty data received. testcaseid_exists_ICE")
    except Exception as e:
        print ('Error in testcaseid_exists_ICE.')
    return (res)

#@app.route('/create_ice/get_node_details_ICE',methods=['POST'])
def get_node_details_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_node_data=query[query_name]+requestdata['id']+query['delete_flag']
            queryresult = icesession.execute(get_node_data)
            res={'rows':queryresult.current_rows}
            if(len(queryresult.current_rows)!=0 and res['rows'][0]['history'] != None):
                res['rows'][0]['history']=dict(res['rows'][0]['history'])
##       else:
##            print ("Empty data received. testcase_exists")
    except Exception as e:
##        print e
##        import traceback
##        traceback.print_exc()
        print ('Error in testcase_exists.')
    return (res)

#@app.route('/create_ice/delete_node_ICE',methods=['POST'])
def delete_node_ICE():
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            query_name=requestdata['name']
            get_delete_query(requestdata['id'],requestdata['node_name'],requestdata['version_number'],requestdata['parent_node_id'])
            delete_query=query[query_name]
            queryresult = icesession.execute(delete_query)
            res={'rows':'Success'}
##       else:
##            print ("Empty data received. testscenario_exists")
    except Exception as e:
        print ('Error in testcase_exists.')
    return (res)

#@app.route('/create_ice/insertInSuite_ICE',methods=['POST'])
def insertInSuite_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
           if(requestdata["query"] == 'notflagsuite'):
                history=createHistory("create","modules",requestdata)
                create_suite_query1 = ("insert into modules "
                +"(projectid,modulename,moduleid,versionnumber,createdby,createdon,"
                +" createdthrough,deleted,history,skucodemodule,tags,testscenarioids) values( "
                +requestdata['projectid']+",'" + requestdata['modulename']
                +"'," + requestdata['moduleid'] + ","+str(requestdata['versionnumber'])
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                + ",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])
                +","+str(history)+", '"+requestdata['skucodemodule']+"',['"+requestdata['tags']+"'],[])")
                queryresult = icesession.execute(create_suite_query1)
                res={'rows':'Success'}
           elif(requestdata["query"] == 'selectsuite'):
                create_suite_query2 = ("select moduleid from modules "
                +" where modulename='"+requestdata["modulename"]+"' and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(create_suite_query2)
                res={'rows':'Success'}
##       else:
##            print ("Empty data received. insertInSuite_ICE")
    except Exception as e:
        print ('Error in insertInSuite_ICE.')
    return (res)

#@app.route('/create_ice/insertInScenarios_ICE',methods=['POST'])
def insertInScenarios_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
           if(requestdata["query"] == 'notflagscenarios'):
                history=createHistory("create","testscenarios",requestdata)
                create_scenario_query1 = ("insert into testscenarios(projectid,"
                +"testscenarioname,testscenarioid,versionnumber,history,createdby,createdon,skucodetestscenario,"
                +"tags,testcaseids,deleted) values ("+requestdata['projectid'] + ",'"
                +requestdata['testscenarioname']+"',"+requestdata['testscenarioid']
                +","+str(requestdata['versionnumber'])+", "+str(history)
                +",'"+requestdata['createdby']+"'," + str(getcurrentdate())
                +", '"+requestdata['skucodetestscenario']+"',['"+requestdata['tags']+"'],[],"+str(requestdata['deleted'])+")")
                queryresult = icesession.execute(create_scenario_query1)
                res={'rows':'success'}
           elif(requestdata["query"] == 'deletescenarios'):
                delete_scenario_query = ("delete testcaseids from testscenarios"
                +" where testscenarioid="+requestdata['testscenarioid']+" and "
                +"testscenarioname='"+requestdata['testscenarioname'] +"' and "
                +"projectid = "+requestdata['projectid']+" and versionnumber="
                +str(requestdata['versionnumber']))
                queryresult = icesession.execute(delete_scenario_query)
                res={'rows':'Success'}
##       else:
##            print ("Empty data received. insertInScenarios_ICE")
    except Exception as e:
         print ('Error in insertInScenarios_ICE.')
    return (res)

#@app.route('/create_ice/insertInScreen_ICE',methods=['POST'])
def insertInScreen_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagscreen'):
                history=createHistory("create","screens",requestdata)
                create_screen_query1 = ("insert into screens (projectid,screenname,"
                +" screenid,versionnumber,history,createdby,createdon,createdthrough,"
                +" deleted,skucodescreen,tags) values ("+requestdata['projectid']
                +", '"+requestdata['screenname']+"'," + requestdata['screenid']
                +" , "+str(requestdata['versionnumber'])+", "+str(history)
                +" ,'"+requestdata['createdby']+"'," + str(getcurrentdate())
                +", '"+requestdata['createdthrough']+"' , "+str(requestdata['deleted'])
                +",'"+requestdata['skucodescreen']+"',['"+requestdata['tags']+"'] )")
                queryresult = icesession.execute(create_screen_query1)
                res={'rows':'Success'}

            elif(requestdata["query"] == 'selectscreen'):
                select_screen_query = ("select screenid from screens where "
                +"screenname='"+requestdata['screenname']+"' and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(select_screen_query)
                res={'rows':'Success'}
##       else:
##            print ("Empty data received. insertInScreen_ICE")
    except Exception as e:
        print ('Error in insertInScreen_ICE.')
    return (res)

#@app.route('/create_ice/insertInTestcase_ICE',methods=['POST'])
def insertInTestcase_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'notflagtestcase'):
                history=createHistory("create","testcases",requestdata)
                create_testcase_query1 = ("insert into testcases (screenid,"
                +"testcasename,testcaseid,versionnumber,history,createdby,createdon,"
                +"createdthrough,deleted,skucodetestcase,tags,testcasesteps)values ("
                +requestdata['screenid'] + ",'" + requestdata['testcasename']
                +"'," + requestdata['testcaseid'] + ","+str(requestdata['versionnumber'])
                +", "+str(history)+",'"+ requestdata['createdby']+"'," + str(getcurrentdate())+", '"
                +requestdata['createdthrough'] +"',"+str(requestdata['deleted'])+",'"
                +requestdata['skucodetestcase']+"',['"+requestdata['tags']+"'], '')")
                queryresult = icesession.execute(create_testcase_query1)
                res={'rows':'Success'}

            elif(requestdata["query"] == 'selecttestcase'):
                select_testcase_query = ("select testcaseid from testcases "
                +"where testcasename='"+requestdata['tags']+"'  and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(select_testcase_query)
                res={'rows':'Success'}
##       else:
##            print ("Empty data received. insertInTestcase_ICE")
    except Exception as e:
        print ('Error in insertInTestcase_ICE.')
    return (res)

#@app.route('/create_ice/updateTestScenario_ICE',methods=['POST'])
def updateTestScenario_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            ##requestdata['testcaseid']=','.join(str(idval) for idval in requestdata['testcaseid'])
            history=createHistory("update","testscenarios",requestdata)
            if(requestdata['modifiedflag']):
                updateicescenario_query =("update testscenarios set "
                +"testcaseids=testcaseids+["+requestdata['testcaseid']
                +"],modifiedby='"+requestdata['modifiedby']
                +"',modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',modifiedon="+str(getcurrentdate())
                +", history = history + "+str(history)
                +" where projectid ="+requestdata['projectid']
                +"and testscenarioid ="+requestdata['testscenarioid']
                +" and testscenarioname = '"+requestdata['testscenarioname']
                +"' and versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            else:
                updateicescenario_query =("update testscenarios set "
                +"testcaseids=testcaseids+["+requestdata['testcaseid']
                +"], history = history + "+str(history)
                +" where projectid ="+requestdata['projectid']
                +"and testscenarioid ="+requestdata['testscenarioid']
                +" and testscenarioname = '"+requestdata['testscenarioname']
                +"' and versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            queryresult = icesession.execute(updateicescenario_query)
            res={'rows':'Success'}
##       else:
##            print ("Empty data received. updateTestScenario_ICE")
    except Exception as e:
        print ('Error in updateTestScenario_ICE.')
    return (res)

#@app.route('/create_ice/updateModule_ICE',methods=['POST'])
def updateModule_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
            history=createHistory("update","modules",requestdata)
            if(requestdata['modifiedflag']):
                updateicemodules_query = ("update modules set testscenarioids ="
                +"["+requestdata['testscenarioids']+"],modifiedby='"+requestdata['modifiedby']
                +"',modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',modifiedon="+str(getcurrentdate())+", history = history+"+str(history)+" where moduleid="
                +requestdata['moduleid']+" and projectid="+requestdata['projectid']
                +" and modulename='"+requestdata['modulename']+"' and "
                +"versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            else:
                updateicemodules_query = ("update modules set "
                +"testscenarioids = ["+requestdata['testscenarioids']+"]"+", history=history+"+str(history)+" where "
                +"moduleid="+requestdata['moduleid']+" and "
                +"projectid="+requestdata['projectid']+" and "
                +"modulename='"+requestdata['modulename']+"' and "
                +"versionnumber="+str(requestdata['versionnumber'])+" IF EXISTS")
            queryresult = icesession.execute(updateicemodules_query)
            res={'rows':'Success'}
##       else:
##            print ("Empty data received. updateModule_ICE")
    except Exception as e:
        print ('Error in updateModule_ICE.')
    return (res)

#@app.route('/create_ice/updateModulename_ICE',methods=['POST'])
def updateModulename_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
             history=createHistory("rename","modules",requestdata)
             requestdata['testscenarioids']=','.join(str(idval) for idval in requestdata['testscenarioids'])
             update_modulename_query =("insert into modules "
             +"(projectid,modulename,moduleid,versionnumber,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
             +" createdthrough,deleted,history,skucodemodule,tags,testscenarioids) values ("
             +requestdata['projectid']+",'" + requestdata['modulename']
             +"'," + requestdata['moduleid'] + ","+str(requestdata['versionnumber'])
             +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
             +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + str(getcurrentdate())
             + ",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])+","+str(history)
             +", '"+requestdata['skucodemodule']+"',['"+requestdata['tags']+"'],["+requestdata['testscenarioids']+"])")
             queryresult = icesession.execute(update_modulename_query)
             res={'rows':'Success'}
##       else:
##            print ("Empty data received. updateModulename_ICE")
    except Exception as e:
        print ('Error in updateModulename_ICE.')
    return (res)

#@app.route('/create_ice/updateTestscenarioname_ICE',methods=['POST'])
def updateTestscenarioname_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            history=createHistory("rename","testscenarios",requestdata)
            requestdata['testcaseids'] = ','.join(str(idval) for idval in requestdata['testcaseids'])
            update_testscenario_name_query =("insert into testscenarios "
            +"(projectid,testscenarioname,testscenarioid,versionnumber,history,modifiedby,modifiedbyrole,modifiedon,createdby,createdon,"
            +" deleted,skucodetestscenario,tags,testcaseids) values ("
            +requestdata['projectid']+",'"+ requestdata['testscenarioname']
            +"',"+requestdata['testscenarioid']+","+str(requestdata['versionnumber'])+","+str(history)
            +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
            +"',"+ str(getcurrentdate())+",'"+requestdata['createdby'] +"'," + str(requestdata['createdon'])
            + ","+str(requestdata['deleted'])+",'"+requestdata['skucodetestscenario']+"',['"
            +requestdata['tags']+"'],["+requestdata['testcaseids']+"])")
            queryresult = icesession.execute(update_testscenario_name_query)
            res={'rows':'Success'}
##       else:
##            print ("Empty data received. updateTestscenarioname_ICE")
    except Exception as e:
        print ('Error in updateTestscenarioname_ICE.')
    return (res)


#@app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
def updateScreenname_ICE(requestdata):
    res={'rows':'fail'}
    try:

##        requestdata=json.loads(request.data)
            if(requestdata['screendata'] == ''):
                requestdata['screendata'] = ' '
##        if not isemptyrequest(requestdata):
            history=createHistory("rename","screens",requestdata)
            update_screenname_query =("insert into screens (projectid,screenname,"
            +"screenid,versionnumber,createdby,createdon,createdthrough,deleted,history,"
            +"modifiedby,modifiedbyrole,modifiedon,screendata,skucodescreen,tags"
            +") values ("+requestdata['projectid']+",'"+requestdata['screenname']
            +"',"+requestdata['screenid']+","+str(requestdata['versionnumber'])
            +",'"+requestdata['createdby']+"',"+requestdata['createdon']
            +",'"+requestdata['createdthrough']+"',"+str(requestdata['deleted'])+","+str(history)
            +",'"+requestdata['modifiedby']+"','"+requestdata['modifiedbyrole']
            +"',"+str(getcurrentdate())+",'"+requestdata['screendata']
            +"','"+requestdata['skucodescreen']+"',['"+requestdata['tags']+"'])")
            queryresult = icesession.execute(update_screenname_query)
            res={'rows':'Success'}
##        else:
##            print ("Empty data received. updateScreenname_ICE")
    except Exception as e:
        print ('Error in updateScreenname_ICE.')
    return (res)


#@app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
def updateTestcasename_ICE(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
            if(requestdata['testcasesteps'] == ''):
                requestdata['testcasesteps'] = ' '
##       if not isemptyrequest(requestdata):
            history=createHistory("rename","testcases",requestdata)
            update_testcasename_query =("insert into testcases (screenid,testcasename,"
            "testcaseid,versionnumber,createdby,createdon,createdthrough,deleted,"
            +"modifiedby,modifiedbyrole,modifiedon,history,skucodetestcase,tags,"
            +"testcasesteps) values ("+requestdata['screenid']+",'"
            +requestdata['testcasename']+"',"+requestdata['testcaseid']+","
            +str(requestdata['versionnumber'])+",'"+requestdata['createdby']
            +"',"+str(requestdata['createdon'])+",'"+requestdata['createdthrough']
            +"',"+str(requestdata["deleted"])+",'"+requestdata['modifiedby']
            +"','"+requestdata['modifiedbyrole']+"',"+str(getcurrentdate())+","+str(history)
            +",'"+requestdata['skucodetestcase']+"',['"+requestdata['tags']
            +"'],'"+requestdata['testcasesteps']+"')")
            queryresult = icesession.execute(update_testcasename_query)
            res={'rows':'Success'}
##       else:
##            print ("Empty data received. updateTestcasename_ICE")
    except Exception as e:
        print ('Error in updateTestcasename_ICE.')
    return (res)


#@app.route('/create_ice/submitTask',methods=['POST'])
def submitTask(requestdata):
    res={'rows':'fail'}
    try:
##       requestdata=json.loads(request.data)
##       if not isemptyrequest(requestdata):
            history=createHistory("submit",requestdata['table'].lower(),requestdata)
            if(requestdata['table'].lower()=='screens'):
                query1=("update screens set history=history + "+str(history)+" where screenid="
                +str(requestdata['details']['screenID_c'])+" and screenname='"+requestdata['details']['screenName']
                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
                +str(requestdata['versionnumber']))
                queryresult = icesession.execute(query1)
                res={'rows':'Success'}
            if(requestdata['table'].lower()=='testscenarios'):
                query2=("update testscenarios set history=history + "+str(history)+" where testscenarioid="
                +str(requestdata['details']['testScenarioID_c'])+" and testscenarioname='"+requestdata['details']['testScenarioName']
                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
                +str(requestdata['versionnumber']))
                queryresult = icesession.execute(query2)
                res={'rows':'Success'}
            if(requestdata['table'].lower()=='modules'):
                query3=("update modules set history=history + "+str(history)+" where moduleid="
                +str(requestdata['details']['moduleID_c'])+" and modulename='"+requestdata['details']['moduleName']
                +"' and projectid="+str(requestdata['details']['projectID'])+" and versionnumber="
                +str(requestdata['versionnumber']))
                queryresult = icesession.execute(query3)
                res={'rows':'Success'}
            if(requestdata['table'].lower()=='testcases'):
                query4=("update testcases set history=history + "+str(history)+" where testcaseid="
                +str(requestdata['details']['testCaseID_c'])+" and testcasename='"+requestdata['details']['testCaseName']
                +"' and screenid="+str(requestdata['details']['screenID_c'])+" and versionnumber="
                +str(requestdata['versionnumber']))
                queryresult = icesession.execute(query4)
                res={'rows':'Success'}
##       else:
##            print ("Empty data received. submitTask")
    except Exception as e:
        print ('Error in submitTask.')
    return (res)
################################################################################
# END OF MIND MAPS
################################################################################


################################################################################
# BEGIN OF DESIGN SCREEN
# INCLUDES : scraping/ws-screen/design testcase creation
################################################################################

#keywords loader for design screen
#@app.route('/design/getKeywordDetails_ICE',methods=['POST'])
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
            return (res)
        else:
            print ('Empty data received. getKeywordDetails')
            return (res)
    except Exception as keywordsexc:
        print ('Error in getKeywordDetails.')
        return (res)

#test case reading service
#@app.route('/design/readTestCase_ICE',methods=['POST'])
def readTestCase_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == "readtestcase"):
                readtestcasequery1 = ("select testcasesteps,testcasename "
                                +"from testcases where "
                                +"screenid= " + requestdata["screenid"]
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
##        else:
##            print ('Empty data received. reading Testcase')
##            return (res)
            res= {"rows": queryresult.current_rows}
            return (res)
    except Exception as readtestcaseexc:
        print ('Error in readTestCase_ICE.')
        return (res)


# fetches the screen data
#@app.route('/design/getScrapeDataScreenLevel_ICE',methods=['POST'])
def getScrapeDataScreenLevel_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
##        else:
##            print ('Empty data received. reading Testcase')
##            return (res)
            return (res)
    except Exception as getscrapedataexc:
        print ('Error in getScrapeDataScreenLevel_ICE.')
        return (res)

# fetches data for debug the testcase
#@app.route('/design/debugTestCase_ICE',methods=['POST'])
def debugTestCase_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            gettestcasedataquery=("select screenid,testcasename,testcasesteps "
            +"from testcases where testcaseid=" + requestdata['testcaseid']+query['delete_flag'])
            queryresult = icesession.execute(gettestcasedataquery)
            res = {"rows":queryresult.current_rows}
##        else:
##            print ('Empty data received. reading Testcase')
##            return (res)
            return (res)
    except Exception as debugtestcaseexc:
        print ('Error in debugTestCase_ICE.')
        return (res)

# updates the screen data
#@app.route('/design/updateScreen_ICE',methods=['POST'])
def updateScreen_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            history=createHistory("update","screens",requestdata)
            updatescreenquery=("update icetestautomation.screens set"
			+" screendata ='"+ requestdata['scrapedata'] +"',"
			+" modifiedby ='" + requestdata['modifiedby'] + "',"
			+" modifiedon = '" + str(getcurrentdate())
			+"', skucodescreen ='" + requestdata['skucodescreen']
            +"', history = history+"+str(history)
			+" where screenid = "+requestdata['screenid']
			+" and projectid = "+requestdata['projectid']
			+" and screenname ='" + requestdata['screenname']
			+"' and versionnumber = "+str(requestdata['versionnumber'])
            +" IF EXISTS")
            queryresult = icesession.execute(updatescreenquery)
            res = {"rows":"Success"}

##        else:
##            print ('Empty data received. updating screen')
##            return (res)
            return (res)
    except Exception as updatescreenexc:
        print ('Error in updateScreen_ICE.')
        return (res)

#test case updating service
#@app.route('/design/updateTestCase_ICE',methods=['POST'])
def updateTestCase_ICE(requestdata):
##    requestdata=json.loads(request.data)
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'checktestcaseexist'):
                updatetestcasequery1 = ("select testcaseid from testcases where "
                +"screenid=" + requestdata['screenid']+" and versionnumber="
                +str(requestdata['versionnumber'])+query['delete_flag'])
                queryresult = icesession.execute(updatetestcasequery1)
                res= {"rows": queryresult.current_rows}
                res =  (res)
            elif(requestdata["query"] == 'updatetestcasedata'):
                history=createHistory("update","testcases",requestdata)
                updatetestcasequery2 = ("update testcases set "
                + "modifiedby = '" + requestdata['modifiedby']
                + "', modifiedon='" + str(getcurrentdate())
        		+"',  skucodetestcase='" + requestdata["skucodetestcase"]
        		+"',  testcasesteps='" + requestdata["testcasesteps"]
                +"', history=history+"+str(history)
        		+" where versionnumber = "+str(requestdata["versionnumber"])
                +" and screenid=" + str(requestdata["screenid"])
                + " and testcaseid=" + str(requestdata["testcaseid"])
                + " and testcasename='" + requestdata["testcasename"] + "' if exists")
                queryresult = icesession.execute(updatetestcasequery2)
                res= {"rows": queryresult.current_rows}
                res =  (res)
##        else:
##            print ('Empty data received. updating testcases')
##            res =  (res)
    except Exception as updatetestcaseexception:
        print ('Error in updateTestCase_ICE.')
    return res

#fetches all the testcases under a test scenario
#@app.route('/suite/getTestcaseDetailsForScenario_ICE',methods=['POST'])
def getTestcaseDetailsForScenario_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
            res =  (res)
##        else:
##            print ('Empty data received. getting testcases from scenarios.')
##            res =  (res)
    except Exception as userrolesexc:
        print ('Error in getTestcaseDetailsForScenario_ICE.')
    return res

################################################################################
# END OF DESIGN SCREEN
################################################################################


################################################################################
# BEGIN OF EXECUTION
# INCLUDES : all execution related actions
################################################################################

#get dependant testcases by scenario ids for add dependent testcases
#@app.route('/design/getTestcasesByScenarioId_ICE',methods=['POST'])
def getTestcasesByScenarioId_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'gettestcaseids'):
                gettestcaseidquery1  = ("select testcaseids from testscenarios "
                +"where testscenarioid = "+requestdata["testscenarioid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestcaseidquery1)
            elif(requestdata["query"] == 'gettestcasedetails'):
                gettestcaseidquery2 = ("select testcasename from testcases where"
                +" testcaseid = "+requestdata["eachtestcaseid"]+query['delete_flag'])
                queryresult = icesession.execute(gettestcaseidquery2)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  (res)
##        else:
##            print ('Empty data received. getting testcases.')
##            res =  (res)
    except Exception as gettestcasesbyscenarioidexception:
        print ('Error in getTestcasesByScenarioId_ICE.')
    return res

#read test suite Avo Assure
#@app.route('/suite/readTestSuite_ICE',methods=['POST'])
def readTestSuite_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                history=createHistory("create","testsuites",requestdata)
                readtestsuitequery3 = ("insert into testsuites "+
                "(cycleid,testsuitename,testsuiteid,versionnumber,conditioncheck,"
                +"createdby,createdon,createdthrough,history,deleted,donotexecute,getparampaths,"
                +"skucodetestsuite,tags,testscenarioids) values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+str(requestdata["versionnumber"])+",["
                +requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["createdthrough"]+"',"
                +str(history)+","
                +str(requestdata["deleted"])+",["+requestdata["donotexecute"]+"],["
                +requestdata['getparampaths'] +"],'"+requestdata["skucodetestsuite"]+"',['"
                +requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"])")
                queryresult = icesession.execute(readtestsuitequery3)
            elif(requestdata["query"] == 'fetchdata'):
                readtestsuitequery4 = ("select * from testsuites "
                +"where testsuiteid = " + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]+query['delete_flag'])
                queryresult = icesession.execute(readtestsuitequery4)
                if(len(queryresult.current_rows)!=0 and queryresult.current_rows[0]['history'] != None):
                    queryresult.current_rows[0]['history'] = dict(queryresult.current_rows[0]['history'])
            elif(requestdata["query"] == 'delete'):
                readtestsuitequery5 = ("delete from testsuites where "+
                "testsuiteid=" + requestdata["testsuiteid"]
                + " and cycleid=" + requestdata["cycleid"]
                + " and testsuitename='" + requestdata["testsuitename"]
                +"' and versionnumber="+str(requestdata["versionnumber"]))
                queryresult = icesession.execute(readtestsuitequery5)
            elif(requestdata["query"] == 'updatescenarioinnsuite'):
                requestdata['conditioncheck'] = ','.join(str(idval) for idval in requestdata['conditioncheck'])
                requestdata['donotexecute'] = ','.join(str(idval) for idval in requestdata['donotexecute'])
                requestdata['getparampaths'] = ','.join(str(idval) for idval in requestdata['getparampaths'])
                requestdata['testscenarioids'] = ','.join(str(idval) for idval in requestdata['testscenarioids'])
                history=createHistory("update","testsuites",requestdata)
                readtestsuitequery6 = ("insert into testsuites (cycleid,testsuitename,"
                +"testsuiteid,versionnumber,conditioncheck,createdby,createdon,"
                +"createdthrough,history,deleted,donotexecute,getparampaths,modifiedby,"
                +"modifiedon,skucodetestsuite,tags,testscenarioids) values ("
                +requestdata["cycleid"]+",'"+requestdata["testsuitename"]+"',"
                +requestdata["testsuiteid"]+","+str(requestdata["versionnumber"])
                +",["+requestdata["conditioncheck"]+"],'"+requestdata["createdby"]+"',"
                +requestdata["createdon"]+",'"+requestdata["createdthrough"]+"',"
                +str(history)+","
                +str(requestdata["deleted"])+",["+requestdata["donotexecute"]+"],["+
                requestdata["getparampaths"]+"],'"+requestdata["modifiedby"]+"',"
                +str(getcurrentdate())+",'"+requestdata["skucodetestsuite"]+"',['"+
                requestdata["tags"]+"'],["+requestdata["testscenarioids"]+"])")
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
                return (res)
##        else:
##            print ('Empty data received. assign projects.')
##            return (res)
            res= {"rows":queryresult.current_rows}
            return (res)
    except Exception as exporttojsonexc:
        print ('Error in readTestSuite_ICE.')
        res={'rows':'fail'}
        return (res)

#-------------------------------------------------
#author : pavan.nayak
#date:31/07/2017
#-------------------------------------------------
#@app.route('/suite/updateTestSuite_ICE',methods=['POST'])
def updateTestSuite_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'deletetestsuitequery'):
                deletetestsuitequery=("delete conditioncheck,donotexecute,"
                +"getparampaths,testscenarioids from testsuites where cycleid="
                +str(requestdata['cycleid'])
                +" and testsuitename='"+requestdata['testsuitename']
                +"' and testsuiteid="+str(requestdata['testsuiteid'])
                +" and versionnumber ="+str(requestdata['versionnumber'])+";")
                queryresult = icesession.execute(deletetestsuitequery)
            elif(requestdata['query'] == 'updatetestsuitedataquery'):
                history=createHistory("update","testsuites",requestdata)
                updatetestsuitedataquery=("update testsuites set"
                +" conditioncheck= conditioncheck + [" + requestdata['conditioncheck']
                +"], donotexecute=donotexecute + [" + str(requestdata['donotexecute'])
                +"],getparampaths=getparampaths + [ "+requestdata['getparampaths']
                +"],testscenarioids=testscenarioids + ["+ requestdata['testscenarioids']
                +"],modifiedby='"+ requestdata['modifiedby']
                +"', modifiedbyrole='"+requestdata['modifiedbyrole']
                +"',skucodetestsuite='"+requestdata['skucodetestsuite']
                +"',tags=['"+requestdata['tags']
                +"'], modifiedon="+str(getcurrentdate())+",history=history+"+str(history)
                +" where cycleid="+ requestdata['cycleid']
                +" and testsuiteid="+ requestdata['testsuiteid']
                +" and versionnumber = "+ str(requestdata['versionnumber'])
                +" and testsuitename='"+ requestdata['testsuitename']
                +"';")
                queryresult = icesession.execute(updatetestsuitedataquery)
            else:
                return (res)
##        else:
##            print ('Empty data received. assign projects.')
##            return (res)
            res={'rows':'Success'}
            return (res)
    except Exception as updatetestsuiteexc:
        print ('Error in updateTestSuite_ICE')
        return (res)

#@app.route('/suite/ExecuteTestSuite_ICE',methods=['POST'])
def ExecuteTestSuite_ICE(requestdata) :
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                return (res)
##        else:
##            print ('Empty data received. assign projects.')
##            return (res)
            res={'rows':queryresult.current_rows}
            return (res)
    except Exception as execuitetestsuiteexc:
        print ('Error in execuiteTestSuite_ICE')
        return (res)

################################################################################
# END OF EXECUTION
################################################################################

################################################################################
# START OF SCHEDULING
################################################################################
#@app.route('/suite/ScheduleTestSuite_ICE',methods=['POST'])
def ScheduleTestSuite_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'insertscheduledata'):
                requestdata['testsuiteids']=','.join(str(idval) for idval in requestdata['testsuiteids'])
                requestdata['browserlist'] = ','.join(str(idval) for idval in requestdata['browserlist'])
                scheduletestsuitequery1=("insert into scheduledexecution(cycleid,scheduledatetime,"
                +"scheduleid,browserlist,clientipaddress,clientport,scenariodetails,schedulestatus,"
                +"testsuiteids,testsuitename) values (" + requestdata['cycleid'] + ","
                + str(requestdata['scheduledatetime']) + "," + requestdata['scheduleid'] + ",'["
                + requestdata['browserlist'] + "]','" + requestdata['clientipaddress'] + "',"
                + requestdata['clientport'] + ",'" + requestdata['scenariodetails'] + "','"
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
                if(requestdata['scheduledetails'] == 'getallscheduledata'):
                    scheduletestsuitequery4=("select * from scheduledexecution")
                elif(requestdata['scheduledetails'] == 'getallscheduleddetails'):
                    scheduletestsuitequery4=("select * from scheduledexecution"
                    +" where schedulestatus='scheduled' allow filtering;")
                queryresult = icesession.execute(scheduletestsuitequery4)
            elif(requestdata['query'] == 'getscheduledstatus'):
                scheduletestsuitequery5=("select schedulestatus from scheduledexecution"
                +" where cycleid="+ requestdata['cycleid'] + " and scheduledatetime='"
                + str(requestdata['scheduledatetime']) + "' and scheduleid=" + requestdata['scheduleid'])
                queryresult = icesession.execute(scheduletestsuitequery5)
            else:
                return (res)
##        else:
##            print ('Empty data received. schedule testsuite.')
##            return (res)
            res={'rows':queryresult.current_rows}
            return (res)
    except Exception as scheduletestsuiteexc:
        print ('Error in ScheduleTestSuite_ICE')
        return (res)

################################################################################
# END OF SCHEDULING
################################################################################

################################################################################
# BEGIN OF QUALITYCENTRE
# INCLUDES : all qc related actions
################################################################################
#fetches the user roles for assigning during creation/updation user
#@app.route('/qualityCenter/qcProjectDetails_ICE',methods=['POST'])
def qcProjectDetails_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
            res =  (res)
##        else:
##            print ('Empty data received. getting qcProjectDetails.')
##            res =  (res)
    except Exception as gettestcasesbyscenarioidexception:
        print ('Error in qcProjectDetails_ICE.')
    return res

#@app.route('/qualityCenter/saveQcDetails_ICE',methods=['POST'])
def saveQcDetails_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'saveQcDetails_ICE'):
                gettestcaseidquery1  = ("INSERT INTO qualitycenterdetails (testscenarioid,qcdetailsid,qcdomain,qcfolderpath,qcproject,qctestcase,qctestset) VALUES ("+requestdata["testscenarioid"]
                +","+requestdata["testscenarioid"]+",'"+requestdata["qcdomain"]+"','"+requestdata["qcfolderpath"]+"','"+requestdata["qcproject"]
                +"','"+requestdata["qctestcase"]+"','"+requestdata["qctestset"]+"')")
                queryresult = icesession.execute(gettestcaseidquery1)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  (res)
##        else:
##            print ('Empty data received. getting saveQcDetails.')
##            res =  (res)
    except Exception as gettestcasesbyscenarioidexception:
        print ('Error in saveQcDetails_ICE.')
    return res

#@app.route('/qualityCenter/viewQcMappedList_ICE',methods=['POST'])
def viewQcMappedList_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'qcdetails'):
                viewqcmappedquery1  = ("SELECT * FROM qualitycenterdetails where testscenarioid="+requestdata["testscenarioid"])
                queryresult = icesession.execute(viewqcmappedquery1)
            else:
                res={'rows':'fail'}
            res= {"rows":queryresult.current_rows}
            res =  (res)
##        else:
##            print ('Empty data received. getting QcMappedList.')
##            res =  (res)
    except Exception as gettestcasesbyscenarioidexception:
        print ('Error in viewQcMappedList_ICE.')
    return res
################################################################################
# END OF QUALITYCENTRE
################################################################################

################################################################################
# BEGIN OF ADMIN SCREEN
# INCLUDES : all admin related actions
################################################################################

#fetches the user roles for assigning during creation/updation user
#@app.route('/admin/getUserRoles',methods=['POST'])
def getUserRoles():
    res={'rows':'fail'}
    try:
        userrolesquery="select roleid, rolename from roles"
        queryresult = dbsession.execute(userrolesquery)
        res={'rows':queryresult.current_rows}
        return (res)
    except Exception as userrolesexc:
        print ('Error in getUserRoles.')
        return (res)


#service renders all the details of the child type
#if domainid is provided all projects in domain is returned
#if projectid is provided all release and cycle details is returned
#if cycleid is provided, testsuite details is returned
#@app.route('/admin/getDetails_ICE',methods=['POST'])
def getDetails_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'domaindetails'):
                getdetailsquery1=("select projectid,projectname from projects "
                    +"where domainid=" + requestdata['id']+query['delete_flag'])
                queryresult = icesession.execute(getdetailsquery1)
            elif(requestdata["query"] == 'projectsdetails'):
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
            elif(requestdata["query"] == 'cycledetails'):
                getdetailsquery3=("select testsuiteid,testsuitename "
                    +"from testsuites where cycleid=" + requestdata['id']
                    +query['delete_flag'])
                queryresult = icesession.execute(getdetailsquery3)
            else:
                return (res)
            res={'rows':queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. generic details.')
##            return (res)
    except Exception as getdetailsexc:
        print ('Error in getDetails_ICE.')
        return (res)


#service renders the names of all projects in domain/projects (or) projectname
# releasenames (or) cycle names (or) screennames
#@app.route('/admin/getNames_ICE',methods=['POST'])
def getNames_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                return (res)
            res={'rows':queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. generic name details.')
##            return (res)
    except Exception as getnamesexc:
        print ('Error in getNames_ICE.')
        return (res)

#service renders all the domains in DB
#@app.route('/admin/getDomains_ICE',methods=['POST'])
def getDomains_ICE():
    res={'rows':'fail'}
    try:
        getdomainsquery="select domainid,domainname from domains"
        queryresult = icesession.execute(getdomainsquery)
        res={'rows':queryresult.current_rows}
        return (res)
    except Exception as getdomainsexc:
        print ('Error in getDomains_ICE.')
        return (res)

#service fetches projects assigned to user.
#@app.route('/admin/getAssignedProjects_ICE',methods=['POST'])
def getAssignedProjects_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projectid'):
                getassingedprojectsquery1=("select projectids from "
                        +"icepermissions where userid = "+requestdata['userid']
                        +" and domainid = "+requestdata['domainid'])
                queryresult = icesession.execute(getassingedprojectsquery1)
            elif(requestdata['query'] == 'projectname'):
                getassingedprojectsquery2=("select projectname from projects "
                            +"where projectid = "+requestdata['projectid']+query['delete_flag'])
                queryresult = icesession.execute(getassingedprojectsquery2)
            else:
                return (res)
            res={'rows':queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. assigned projects.')
##            return (res)
    except Exception as getassingedprojectsexc:
        print ('Error in getAssignedProjects_ICE.')
        return (res)

#service creates new users into Avo Assure
#@app.route('/admin/createUser',methods=['POST'])
def createUser(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'allusernames'):
                createuserquery1=("select username from users")
                queryresult = dbsession.execute(createuserquery1)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createuser'):
                userid = str(uuid.uuid4())
                deactivated = False
                requestdata['userid']=userid
                history = createHistory("create","users",requestdata)
                createuserquery2=("insert into users (userid,createdby,createdon,"
                +"defaultrole,deactivated,emailid,firstname,lastname,history,ldapuser,password,username) values"
                +"( "+str(userid)+" , '"+requestdata['username']+"' , "
                + str(getcurrentdate())+" , "+requestdata['defaultrole']+" , "
                +str(deactivated)+" , '"+requestdata['emailid']+"' , '"
                +requestdata['firstname']+"' , '"+requestdata['lastname']+"' , "
                +str(history)+" , "+str(requestdata['ldapuser'])+" , '"+requestdata['password']+"' , '"
                +requestdata['username']+"')")
                queryresult = dbsession.execute(createuserquery2)
                res={'rows':'Success'}
            else:
                return (res)
            return (res)
##        else:
##            print ('Empty data received. create user.')
##            return (res)
    except Exception as createusersexc:
        print ('Error in createUser.')
        return (res)

#service fetch user data from Avo Assure
#@app.route('/admin/getUserData',methods=['POST'])
def getUserData():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            getuserdataquery=("select username,firstname,lastname,emailid,ldapuser,"
               +"defaultrole,additionalroles from users where userid="+str(requestdata['userid']))
            queryresult = dbsession.execute(getuserdataquery)
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
            return (res)
##        else:
##            print ('Empty data received. Get user data.')
##            return (res)
    except Exception as updateUserexc:
        print ('Error in getUserData')
        res={'rows':'fail'}
        return (res)

#service update user data into Avo Assure
#@app.route('/admin/updateUser',methods=['POST'])
def updateUser(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            requestdata['additionalroles'] = ','.join(str(roleid) for roleid in requestdata['additionalroles'])
            history = createHistory("update","users",requestdata)
            if requestdata['password'] == 'existing':
                updateuserquery2=("UPDATE users set "
                +"username='" + requestdata['username']
                + "', firstname='" + requestdata['firstname']
                + "', lastname='" + requestdata['lastname']
                + "', modifiedby='" + requestdata['modifiedby']
                + "', modifiedon=" + str(getcurrentdate())
                + ", emailid='" + requestdata['emailid']
                + "', ldapuser= " + str(requestdata['ldapuser'])
                + ", history=history+"+str(history)
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
                + ", history=history+"+str(history)
                + ", modifiedbyrole= '" + str(requestdata['modifiedbyrole'])
                + "', additionalroles= {" + str(requestdata['additionalroles'])
                + "} where userid=" + str(requestdata['userid']))
            queryresult = dbsession.execute(updateuserquery2)
            res={'rows':'Success'}
            return (res)
##        else:
##            print ('Empty data received. update user.')
##            return (res)
    except Exception as updateUserexc:
        print ('Error in updateUser')
        res={'rows':'fail'}
        return (res)

#service creates a complete project structure into ICE keyspace
#@app.route('/admin/createProject_ICE',methods=['POST'])
def createProject_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata['query'] == 'projecttype'):
                projecttypequery=("select projecttypeid from projecttype where"
                +" projecttypename = '"+requestdata['projecttype']+"' allow filtering")
                queryresult = icesession.execute(projecttypequery)
                res={'rows':queryresult.current_rows}
            elif(requestdata['query'] == 'createproject'):
                projectid =uuid.uuid4()
                requestdata['projectid']=projectid
                history = createHistory("create","projects",requestdata)
                createprojectquery1 = ("insert into projects (domainid,projectname,"
                +"projectid,createdby,createdon,deleted,history,projecttypeid,"
                +"skucodeproject,tags)values ( "+str(requestdata['domainid'])
                +", '"+requestdata['projectname']+"' , "+str(projectid)
                +", '"+requestdata['createdby']+"',"+str(getcurrentdate())
                +", false, "+str(history)+", "+requestdata['projecttypeid']
                +",'"+requestdata['skucodeproject']+"' , ['"+requestdata['tags']+"']);")
                projectid = {'projectid':projectid}
                queryresult = icesession.execute(createprojectquery1)
                res={'rows':[projectid]}
            elif(requestdata['query'] == 'createrelease'):
                releaseid=''
                if requestdata.has_key('releaseid'):
                    releaseid=requestdata['releaseid']
                    history=createHistory("update","releases",requestdata)
                else:
                    releaseid=uuid.uuid4()
                    requestdata['releaseid']=releaseid
                    history=createHistory("create","releases",requestdata)
                createreleasequery1=("insert into releases (projectid,releasename,"
                +"releaseid,createdby,createdon,deleted,history,skucoderelease,tags) values "
                +"("+str(requestdata['projectid'])+", '"+requestdata['releasename']
                +"',"+str(releaseid)+",'"+requestdata['createdby']
                +"',"+str(getcurrentdate())+",false,"+str(history)+",'"+requestdata['skucoderelease']
                +"',['"+requestdata['tags']+"'])")
                releaseid = {'releaseid':releaseid}
                queryresult = icesession.execute(createreleasequery1)
                res={'rows':[releaseid]}
            elif(requestdata['query'] == 'createcycle'):
                cycleid=''
                if requestdata.has_key('cycleid'):
                    cycleid=requestdata['cycleid']
                    history=createHistory("update","cycles",requestdata)
                else:
                    cycleid=uuid.uuid4()
                    requestdata['cycleid']=cycleid
                    history=createHistory("create","cycles",requestdata)
                createcyclequery1=("insert into cycles (releaseid,cyclename, "
                +"cycleid,createdby,createdon,deleted,history,skucodecycle,tags) values "
                +" ("+str(requestdata['releaseid'])+", '"+requestdata['cyclename']
                +"',"+str(cycleid)+",'"+requestdata['createdby']
                +"',"+str(getcurrentdate())+",false,"+str(history)+",'"+requestdata['skucodecycle']
                +"' ,['"+requestdata['tags']+"'])")
                cycleid = {'cycleid':cycleid}
                queryresult = icesession.execute(createcyclequery1)
                res={'rows':[cycleid]}
            else:
                return (res)
            return (res)
##        else:
##            print ('Empty data received. create project.')
##            return (res)
    except Exception as createprojectexc:
        print ('Error in createProject_ICE')
        return (res)

#service updates the specified project structure into ICE keyspace
#@app.route('/admin/updateProject_ICE',methods=['POST'])
def updateProject_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
##        else:
##            print ('Empty data received. update project.')
##            return (res)
            return (res)
    except Exception as updateprojectexc:
            print ('Error in updateProject_ICE')
            return (res)

#fetches user data into Avo Assure
#@app.route('/admin/getUsers',methods=['POST'])
def getUsers():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                queryresultusername=dbsession.execute(queryforuser)
                if not(len(queryresultusername.current_rows) == 0):
                    if not (str(queryresultusername.current_rows[0]['defaultrole']) in userrolesarr):
                        rids.append(row['userid'])
                        userroles.append(queryresultusername.current_rows[0]['username'])
                        res["userRoles"]=userroles
                        res["r_ids"]=rids
##        else:
##            print ('Empty data received. get users - Mind Maps.')
##            return (res)
            return (res)
    except Exception as getUsersexc:
        print ('Error in getUsers')
        return (res)

#service assigns projects to a specific user
#@app.route('/admin/assignProjects_ICE',methods=['POST'])
def assignProjects_ICE(requestdata):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if (requestdata['alreadyassigned'] != True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
                history=createHistory("assign","icepermissions",requestdata)
                assignprojectsquery1 = ("insert into icepermissions (userid,"
                +" domainid,createdby,createdon,history,projectids) values"
                +" ("+str(requestdata['userid'])+","+str(requestdata['domainid'])
                +",'"+requestdata['createdby']+"',"+str(getcurrentdate())
                +","+str(history)
                +", ["+str(requestdata['projectids'])+"]);")
                queryresult = icesession.execute(assignprojectsquery1)
            elif (requestdata['alreadyassigned'] == True):
                requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
                history=createHistory("assign","icepermissions",requestdata)
                assignprojectsquery2 = ("update icepermissions set"
                +" projectids = ["+requestdata['projectids']+"] "
                +", modifiedby = '"+requestdata['modifiedby']
                +"', modifiedon = "+str(getcurrentdate())
                +", modifiedbyrole = '"+requestdata['modifiedbyrole']
                +"', history = history+"+str(history)
                +" WHERE userid = "+str(requestdata['userid'])
                +" and domainid = "+str(requestdata['domainid'])+";")
                queryresult = icesession.execute(assignprojectsquery2)
            else:
                return (res)
##        else:
##            print ('Empty data received. assign projects.')
##            return (res)
            res={'rows':'Success'}
            return (res)
    except Exception as assignprojectsexc:
        print assignprojectsexc
        print ('Error in assignProjects_ICE')
        return (res)

# service fetches all users
#@app.route('/admin/getAllUsers',methods=['POST'])
def getAllUsers():
    res={'rows':'fail'}
    try:
        queryforallusers=("select userid, username, defaultrole from users")
        queryresult = dbsession.execute(queryforallusers)
        res={'rows':queryresult.current_rows}
        return (res)
    except Exception as getallusersexc:
        print ('Error in getAllUsers')
        return (res)

################################################################################
# END OF ADMIN SCREEN
################################################################################


################################################################################
# BEGIN OF REPORTS
# INCLUDES : all reports related actions
################################################################################

#fetching all the suite details
#@app.route('/reports/getAllSuites_ICE',methods=['POST'])
def getAllSuites_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                return (res)
            res= {"rows":queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. report suites details.')
##            return (res)
    except Exception as getAllSuitesexc:
        print ('Error in getAllSuites_ICE.')
        res={'rows':'fail'}
        return (res)

#fetching all the suite after execution
#@app.route('/reports/getSuiteDetailsInExecution_ICE',methods=['POST'])
def getSuiteDetailsInExecution_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            getsuitedetailsquery = ("select executionid,starttime,endtime "
                    +"from execution where testsuiteid="+requestdata['suiteid'])
            queryresult = icesession.execute(getsuitedetailsquery)
            res= {"rows":queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. report suites details execution.')
##            return (res)
    except Exception as getsuitedetailsexc:
        print ('Error in getAllSuites_ICE.')
        return (res)

#fetching all the reports status
#@app.route('/reports/reportStatusScenarios_ICE',methods=['POST'])
def reportStatusScenarios_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
            if(requestdata["query"] == 'executiondetails'):
                getreportstatusquery1 = ("select reportid,executionid,browser,comments,"
                +"executedtime,modifiedby,modifiedbyrole,modifiedon,report,status,"
                +"testscenarioid,testsuiteid from reports "
                +"where executionid="+requestdata['executionid']+" ALLOW FILTERING")
                queryresult = icesession.execute(getreportstatusquery1)
            elif(requestdata["query"] == 'scenarioname'):
                getreportstatusquery2 = ("select testscenarioname "
                +"from testscenarios where testscenarioid="+requestdata['scenarioid']
                +" ALLOW FILTERING")
                queryresult = icesession.execute(getreportstatusquery2)
            else:
                return (res)
            res= {"rows":queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. report status of scenarios.')
##            return (res)
    except Exception as getreportstatusexc:
        print ('Error in reportStatusScenarios_ICE.')
        res={'rows':'fail'}
        return (res)

#fetching the reports
#@app.route('/reports/getReport',methods=['POST'])
def getReport():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                return (res)
            res= {"rows":queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. report.')
##            return (res)
    except Exception as getreportexc:
        print (getreportexc)
        print ('Error in getReport.')
        return (res)

#export json feature on reports
#@app.route('/reports/exportToJson_ICE',methods=['POST'])
def exportToJson_ICE():
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
##        if not isemptyrequest(requestdata):
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
                return (res)
            res= {"rows":queryresult.current_rows}
            return (res)
##        else:
##            print ('Empty data received. JSON Exporting.')
##            return (res)
    except Exception as exporttojsonexc:
        print ('Error in exportToJson_ICE.')
        res={'rows':'fail'}
        return (res)

################################################################################
# END OF REPORTS
################################################################################


################################################################################
# BEGIN OF HISTORY
################################################################################

def createHistory(query, table, requestdata):
    try:
        history={}
        if(requestdata.has_key('history') and requestdata['history'] != None):
            req_history=requestdata['history']
            for keys in req_history:
                history[keys.encode('utf-8')]=req_history[keys].encode('utf-8')
        primary_keys={'users':['userid'],
                    'projects':['projectid','domainid','projectname'],
                    'cycles':['cycleid','releaseid','cyclename'],
                    'releases':['releaseid','projectid','releasename'],
                    'icepermissions':['userid','domainid'],
                    'modules':['moduleid','projectid','modulename','versionnumber'],
                    'testsuites':['testsuiteid','cycleid','testsuitename','versionnumber'],
                    'testscenarios':['testscenarioid','projectid','testscenarioname','versionnumber'],
                    'screens':['screenid','projectid','screenname','versionnumber'],
                    'testcases':['testcaseid','screenid','testcasename','versionnumber']
                    }
        versionquery=''
        if(query=='submit'):
            if(table=='screens'):
                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['screenID_c']
            elif(table=='testscenarios'):
                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['testScenarioID_c']
            elif(table=='modules'):
                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['moduleID_c']
            elif(table=='testcases'):
                versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+requestdata['details']['testCaseID_c']
        else:
            versionquery="select getversions(history) from "+table+" where "+primary_keys[table][0]+"="+str(requestdata[primary_keys[table][0]])
        if(table=='users'):
            queryresult=dbsession.execute(versionquery)
        else:
            queryresult=icesession.execute(versionquery)
        if(query=='submit' and requestdata['status']=='complete'):
            version=getHistoryLatestVersion(queryresult.current_rows,table,history,query)
        else:
            version=getHistoryLatestVersion(queryresult.current_rows,table,history)
        if(query=='create'):
            data=str(requestdata)#.replace("'","\'").replace('"',"'")
            value={
            'description':'Created '+table[:-1]+' with values '+data,
            'timestamp':str(getcurrentdate()),
            'user':str(requestdata['createdby'])
            }
            value=str(value).replace("'",'\"')
            history[version]=value
        elif(query=='update'):
            data={}
            for keys in requestdata:
                if (keys not in primary_keys[table] and keys != 'modifiedby'
                and keys != 'modifiedon' and keys != 'modifiedbyrole'):
                    data[keys]=requestdata[keys]
            data=str(data).replace("'","\'").replace('"',"'")
            user_str=''
            if(table=='projects'):
                user_str=requestdata['createdby']
            else:
                user_str=requestdata['modifiedby']
            value={
            'description':'Updated properties: '+str(data),
            'timestamp':str(getcurrentdate()),
            'user':str(user_str)
            }
            value=str(value).replace("'",'\"')
            history[version]=value
        elif(query=='assign'):
            user_str=''
            if(requestdata['alreadyassigned']!=True):
                user_str=requestdata['createdby']
            else:
                user_str=requestdata['modifiedby']
            value={
            'description':'Assigned project '+str(requestdata['projectids'])+'with domain '+str(requestdata['domainid'])+' to user '+str(requestdata['userid']),
            'timestamp':str(getcurrentdate()),
            'user':str(user_str)
            }
            value=str(value).replace("'",'\"')
            history[version]=value
        elif(query=='rename'):
            desc_str=''
            if(table=='modules'):
                desc_str='Renamed module to '+requestdata['modulename']
            elif(table=='testscenarios'):
                desc_str='Renamed scenario to '+requestdata['testscenarioname']
            elif(table=='screens'):
                desc_str='Renamed screen to '+requestdata['screenname']
            elif(table=='testcases'):
                desc_str='Renamed testcase to '+requestdata['testcasename']
            value={
            'description':desc_str.encode('utf-8'),
            'timestamp':str(getcurrentdate()),
            'user':str(requestdata['modifiedby'])
            }
            value=str(value).replace("'",'\"')
            history[version]=value
        elif(query=='submit'):
            desc_str=''
            if(requestdata['status']=='review'):
                if(table=='modules'):
                    desc_str='Submitted module '+requestdata['details']['moduleName']+' for review'
                elif(table=='testscenarios'):
                    desc_str='Submitted scenario '+requestdata['details']['testScenarioName']+' for review'
                elif(table=='screens'):
                    desc_str='Submitted screen '+requestdata['details']['screenName']+' for review'
                elif(table=='testcases'):
                    desc_str='Submitted testcase '+requestdata['details']['testCaseName']+' for review'
            elif(requestdata['status']=='complete'):
                if(table=='modules'):
                    desc_str='Completed module '+requestdata['details']['moduleName']
                elif(table=='testscenarios'):
                    desc_str='Completed scenario '+requestdata['details']['testScenarioName']
                elif(table=='screens'):
                    desc_str='Completed screen '+requestdata['details']['screenName']
                elif(table=='testcases'):
                    desc_str='Completed testcase '+requestdata['details']['testCaseName']
            elif(requestdata['status']=='reassigned'):
                if(table=='modules'):
                    desc_str='Reassigned module '+requestdata['details']['moduleName']+' for review'
                elif(table=='testscenarios'):
                    desc_str='Reassigned scenario '+requestdata['details']['testScenarioName']+' for review'
                elif(table=='screens'):
                    desc_str='Reassigned screen '+requestdata['details']['screenName']+' for review'
                elif(table=='testcases'):
                    desc_str='Reassigned testcase '+requestdata['details']['testCaseName']+' for review'
            value={
            'description':desc_str.encode('utf-8'),
            'timestamp':str(getcurrentdate()),
            'user':str(requestdata['username'])
            }
            value=str(value).replace("'",'\"')
            history[version]=value
        return history
    except Exception as e:
        print ('Error in createHistory.')


def getHistoryLatestVersion(res,table,hist,*args):
    try:
        oldverslist=[]
        histFlag=False
        versions=''
        newver=''
        if (hist is not None and len(hist)!=0):
            oldverslist=hist.keys()
            histFlag=True
        if (len(res)!=0):
            if(table=='users'):
                versions=res[0]['nineteen68.getversions(history)']
            else:
                versions=res[0]['icetestautomation.getversions(history)']
            if(versions==''):
                return '000.001'
            elif(len(oldverslist)==0):
                oldverslist=versions.split(',')
        elif (not histFlag):
            return '000.000'
        oldver=max(oldverslist)
        if(len(args)!=0):
            import math
            newver = str(math.ceil(float(oldver)))
            newver=newver.split('.')
        else:
            newver=str(float(oldver)+0.001).split('.')
        if(len(newver[0])==1):
            newver[0]="00"+newver[0]
        elif(len(newver[0])==2):
            newver[0]="0"+newver[0]
        if(len(newver[1])==1):
            newver[1]=newver[1]+"00"
        elif(len(newver[1])==2):
            newver[1]=newver[1]+"0"
        newver= '.'.join(newver)
        return newver
    except Exception as e:
        print ("Error in getHistoryLatestVersion")

################################################################################
# END OF HISTORY
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
query['delete_flag'] = ' and deleted=false allow filtering'
numberofdays=1
omgall="\x4e\x69\x6e\x65\x74\x65\x65\x6e\x36\x38\x6e\x64\x61\x74\x63\x6c\x69\x63\x65\x6e\x73\x69\x6e\x67"
dasinfo = {
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
                and key != 'getparampaths' and key != 'testcasesteps' and key != 'history'):
                if value == 'undefined' or value == '' or value == 'null' or value == None:
                    print (key)
                    flag = True
    else:
        global offlinestarttime
        global offlineendtime
        currenttime=datetime.now()
        if usersession != False:
            if (currenttime >= offlinestarttime and currenttime <= offlineendtime):
                for key in requestdata:
                    value = requestdata[key]
                    if (key != 'additionalroles' and key != 'getparampaths'
                     and key != 'testcasesteps' and key != 'history'):
                        if value == 'undefined' or value == '' or value == 'null' or value == None:
                            print (key)
                            flag = True
            else:
                global handler
                handler.setLevel(logging.CRITICAL)
                app.logger.addHandler(handler)
                app.logger.critical("User validity expired... "
                +"Please contact Avo Assure Team for Enabling")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
                usersession = False
                flag = True
        else:
            if offlineuser != True:
                flag = True
                app.logger.critical("Access to Avo Assure Expired.")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
            else:
                flag = True
                global handler
                handler.setLevel(logging.CRITICAL)
                app.logger.addHandler(handler)
                app.logger.critical("User validity expired... "
                +"Please contact Avo Assure Team for Enabling")
                handler.setLevel(logging.disable(logging.CRITICAL))
                app.logger.addHandler(handler)
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
    query['delete_module']="delete FROM modules WHERE moduleid="+node_id+" and modulename='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid
    query['delete_testscenario']="delete FROM testscenarios WHERE testscenarioid="+node_id+" and testscenarioname='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid
    query['delete_screen']="delete FROM screens WHERE screenid="+node_id+" and screenname='"+node_name+"' and versionnumber="+node_version_number+" and projectid="+node_parentid
    query['delete_testcase']="delete FROM testcases WHERE testcaseid="+node_id+" and testcasename='"+node_name+"' and versionnumber="+node_version_number+" and screenid="+node_parentid

#directly updates user access
##@app.route('/utility/userAccess',methods=['POST'])
def userAccess(requestdata):
    res={'rows':'fail'}
    try:
        #requestdata=json.loads(request.data)

##        if not isemptyrequest(request):
        roleid=requestdata['roleid']
        servicename=requestdata['servicename']
        roleaccessquery = ("select servicelist from userpermissions "
            +"where roleid ="+ roleid + " ALLOW FILTERING ")
        queryresult = dbsession.execute(roleaccessquery)
        statusflag = False
        for each in queryresult.current_rows[0]['servicelist']:
            if servicename == str(each):
                statusflag = True
                break
        if statusflag:
            res={'rows':'True'}
        else:
            res={'rows':'False'}
##        else:
##            print('Empty data received. user Access Permission.')
    except Exception as useraccessexc:
        import traceback
        traceback.print_exc()
        print('Error in userAccess.')
    return res
############################
# END OF GENERIC FUNCTIONS
############################

if __name__ == '__main__':
    #getEmptyProjects_ICE
##    data = {
##        "userid": 'e1e86675-c82c-44bb-b8ba-59ca251b5a49',
##		"query": "getprojids"
##    }
##    response = getEmptyProjects_ICE(data)
##
    #get_node_details_ICE
##    data = {
##        'name': 'Testcase_del20',
##        'id': '07c8ee58-79d1-430d-9bab-d47d29565c82'
##    }
##    response = get_node_details_ICE(data)
##
    #insertInSuite_ICE
##    data = {
##        "query":'notflagsuite',
##		'projectid': 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##		'modulename': 'Module_batch',
##		'moduleid': 'da9b196d-8021-4a68-be2b-753ec267305e',
##		'versionnumber': '0',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodemodule': 'skucodemodule',
##		'tags': 'tags'
##    }
##    response = insertInSuite_ICE(data)
##
    #insertInScenarios_ICE
##    data = {
##        "query": 'notflagscenarios',
##		'projectid': '803f2330-4a4a-4611-99ad-6c319f4811fb',
##		'testscenarioname': 'Scenario_sap',
##		'testscenarioid': 'f94e6ae8-77a0-442f-b699-bb47ba17ef52',
##		'versionnumber': '0',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodetestscenario': 'skucodetestscenario',
##		'tags': 'tags'
##    }
##    response = insertInScenarios_ICE(data)
##
    #insertInScreen_ICE
##    data = {
##        "query": 'notflagscreen',
##		'projectid': 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##		'screenname': 'Screen_batch',
##		'screenid': '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		'versionnumber': '0',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodescreen': 'skucodescreen',
##		'tags': 'tags'
##    }
##    response = insertInScreen_ICE(data)
##
    #insertInTestcase_ICE
##    data = {
##        "query": 'notflagtestcase',
##		'screenid': '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		'testcasename': 'Testcase_batch1',
##		'testcaseid': 'bbdc3479-bf09-4e17-b4fc-98e97ca1cb62',
##		'versionnumber': '0',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodetestcase': 'skucodetestcase',
##		'tags': 'tags'
##    }
##    response = insertInTestcase_ICE(data)
##
    #updateTestScenario_ICE
##    data = {
##        'testcaseid': ['2a3f8555-cc85-47c6-85de-c6c69facce2b'],
##		'modifiedby': 'sakshi.goyal',
##		'modifiedbyrole': 'Admin',
##		'projectid': '803f2330-4a4a-4611-99ad-6c319f4811fb',
##		'testscenarioid': 'f94e6ae8-77a0-442f-b699-bb47ba17ef52',
##		'modifiedflag': True,
##		'testscenarioname': 'Scenario_sap',
##		'versionnumber': '0'
##    }
##    response = updateTestScenario_ICE(data)
##
    #updateModule_ICE
##    data = {
##        'testscenarioids': ['23f78264-e13e-4d91-93e5-1c3563fe26d4', 'daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa'],
##    	'moduleid': 'da9b196d-8021-4a68-be2b-753ec267305e',
##    	'projectid': 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##    	'modulename': 'Module_batch',
##    	'modifiedflag': True,
##    	'modifiedby': 'sakshi.goyal',
##    	'modifiedbyrole':'Admin',
##    	'versionnumber': '0'
##    }
##    response = updateModule_ICE(data)
##
    #updateModulename_ICE
##    data = {
##        'projectid': 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##		'modulename': 'Module_batch_new',
##		'moduleid': 'da9b196d-8021-4a68-be2b-753ec267305e',
##		'versionnumber': '0',
##		'modifiedby': 'sakshi.goyal',
##		'modifiedbyrole': 'Admin',
##		'modifiedon': str(getcurrentdate()),
##		'history':{'000.001': '{\"timestamp\": \"1508862935184\", \"description\": \"Updated properties: {u\"testscenarioids\": \"23f78264-e13e-4d91-93e5-1c3563fe26d4,daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa\", u\"modifiedflag\": True}\", \"user\": \"sakshi.goyal\"}'},
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodemodule': 'skucodemodule',
##		'tags': 'tags',
##		'testscenarioids': ['23f78264-e13e-4d91-93e5-1c3563fe26d4', 'daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa'],
##		'createdon': '2017-09-11 18:26:20+0000'
##    }
##    response = updateModulename_ICE(data)
##
    #updateTestscenarioname_ICE
##    data = {
##        'projectid': '803f2330-4a4a-4611-99ad-6c319f4811fb',
##		'testscenarioname': 'Scenario_sap_new',
##		'testscenarioid': 'f94e6ae8-77a0-442f-b699-bb47ba17ef52',
##		'versionnumber': '0',
##		'modifiedby': 'sakshi.goyal',
##		'modifiedbyrole': 'Admin',
##		'modifiedon': str(getcurrentdate()),
##		'history':{'000.001': '{\"timestamp\": \"1508862935184\", \"description\": \"Updated properties: {u\"testscenarioids\": \"23f78264-e13e-4d91-93e5-1c3563fe26d4,daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa\", u\"modifiedflag\": True}\", \"user\": \"sakshi.goyal\"}'},
##		'createdon': '2017-09-04 12:07:47+0000',
##		'createdby': 'sakshi.goyal',
##		'deleted': False,
##		'skucodetestscenario': 'skucodetestscenario',
##		'tags': 'tags',
##		'testcaseids': ['2a3f8555-cc85-47c6-85de-c6c69facce2b']
##    }
##    response = updateTestscenarioname_ICE(data)
##
    #updateScreenname_ICE
##    data = {
##        'projectid': 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##		'screenname': 'Screen_batch_new',
##		'screenid': '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		'modifiedby': 'sakshi.goyal',
##		'modifiedbyrole': 'Admin',
##		'modifiedon': str(getcurrentdate()),
##		'history':{'000.001': '{\"timestamp\": \"1508862935184\", \"description\": \"Updated properties: {u\"testscenarioids\": \"23f78264-e13e-4d91-93e5-1c3563fe26d4,daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa\", u\"modifiedflag\": True}\", \"user\": \"sakshi.goyal\"}'},
##		'createdon': '2017-09-11 18:26:20+0000',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodescreen': 'skucodescreen',
##		'tags': 'tags',
##		'screendata': 'null',
##		'versionnumber': '0'
##    }
##    response = updateScreenname_ICE(data)
##
    #updateTestcasename_ICE
##    data = {
##        'screenid': '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		'testcasename': 'Testcase_batch1_new',
##		'testcaseid': 'bbdc3479-bf09-4e17-b4fc-98e97ca1cb62',
##		'modifiedby': 'sakshi.goyal',
##		'modifiedbyrole': 'Admin',
##		'modifiedon': str(getcurrentdate()),
##		'history':{'000.001': '{\"timestamp\": \"1508862935184\", \"description\": \"Updated properties: {u\"testscenarioids\": \"23f78264-e13e-4d91-93e5-1c3563fe26d4,daf650d4-9c22-4fd0-9d5e-4f4f42f0ffaa\", u\"modifiedflag\": True}\", \"user\": \"sakshi.goyal\"}'},
##		'createdon': '2017-09-11 18:26:20+0000',
##		'createdby': 'sakshi.goyal',
##		'createdthrough': 'Mindmaps Creation',
##		'deleted': False,
##		'skucodescreen': 'skucodescreen',
##		'tags': 'tags',
##		'testcasesteps': 'null',
##		"versionnumber": '0'
##    }
##    response = updateTestcasename_ICE(data)
##
    #submitTask
##    data = {
##        'status':'review',
##		'table':'SCREENS',
##		'details':{
##            "screenID": "1ce878b8-a17e-493c-9333-794395af6daf",
##            "screenID_c": "aca3418e-3ca8-4ab0-a688-5a3a05d639b8",
##            "createdBy": "sakshi.goyal",
##            "testScenarioID": "34572435-dac8-4153-96d7-b725eab19e43",
##            "screenName": "Screen_web",
##            "childIndex": "1",
##            "projectID": "c713e52f-d2d7-4e1d-8208-4007a287f22c",
##            "createdOn": "null"
##        },
##		'username':'sakshi.goyal',
##		'versionnumber':'0'
##    }
##    response = submitTask(data)
##
    #updateScreen_ICE
##    data = {
##        "scrapedata": 'null',
##		"modifiedby": 'sakshi.goyal',
##		"skucodescreen": 'skucodescreen',
##		"screenid": '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		"projectid": 'c713e52f-d2d7-4e1d-8208-4007a287f22c',
##		"screenname": 'Screen_batch',
##		"versionnumber": '0'
##    }
##    response = updateScreen_ICE(data)
##
    #updateTestCase_ICE
##    data = {
##        "screenid": '3cff8b89-ce90-4df5-a411-0f6463fbf894',
##		"query": "updatetestcasedata",
##		"modifiedby": 'sakshi.goyal',
##		"skucodetestcase": 'skucodescreen',
##		"testcasesteps": 'null',
##		"versionnumber": '0',
##		"testcaseid": 'bbdc3479-bf09-4e17-b4fc-98e97ca1cb62',
##		"testcasename": 'Testcase_batch1'
##    }
##    response = updateTestCase_ICE(data)
##
    #readTestSuite_ICE
##    data1 = {
##        "cycleid": '434211f4-0089-4662-ae6b-492b47504ca5',
##		"testsuitename": 'Module_sap',
##		"testsuiteid": 'a07bad1c-e467-4ff3-8158-83180cf95981',
##		"versionnumber": '0',
##		"conditioncheck": [0],
##		"createdby": "Admin",
##		"createdthrough": "createdthrough",
##		"deleted": False,
##		"donotexecute": [1],
##		"getparampaths": [''],
##		"skucodetestsuite": "skucodetestsuite",
##		"tags": "tags",
##		"testscenarioids": ['f94e6ae8-77a0-442f-b699-bb47ba17ef52'],
##		"query": "testcasesteps"
##    }
##    data2 = {
##        "cycleid": '434211f4-0089-4662-ae6b-492b47504ca5',
##		"testsuitename": 'Module_sap',
##		"testsuiteid": 'a07bad1c-e467-4ff3-8158-83180cf95981',
##		"versionnumber": 0,
##		"conditioncheck": [0],
##		"createdby": 'Admin',
##		"createdon": '2017-10-24 15:16:23+0000',
##		"createdthrough": "createdthrough",
##		"deleted": False,
##		"history":{},
##		"donotexecute": [1],
##		"getparampaths": [''],
##		"modifiedby": "sakshi.goyal",
##		"skucodetestsuite": "skucodetestsuite",
##		"tags": "tags",
##		"testscenarioids": "[f94e6ae8-77a0-442f-b699-bb47ba17ef52]",
##		"query": "updatescenarioinnsuite"
##    }
##    response = readTestSuite_ICE(data1)
##    response = readTestSuite_ICE(data2)
##
    #updateTestSuite_ICE
##    data = {
##        "query": "updatetestsuitedataquery",
##		"conditioncheck": [0],
##		"donotexecute": [1],
##		"getparampaths": [''],
##		"testscenarioids": ['f94e6ae8-77a0-442f-b699-bb47ba17ef52'],
##		"modifiedby": 'sakshi.goyal',
##		"modifiedbyrole": 'Admin',
##		"cycleid": '434211f4-0089-4662-ae6b-492b47504ca5',
##		"testsuiteid": 'a07bad1c-e467-4ff3-8158-83180cf95981',
##		"testsuitename": 'Module_sap',
##		"versionnumber": '0',
##		"skucodetestsuite": "skucodetestsuite",
##		"tags": "tags"
##    }
##    response = updateTestSuite_ICE(data)
##
    #ExecuteTestSuite_ICE
##    data = {
##        "testsuiteid": '17d2a8d8-f5eb-4544-bd9e-94f5c9382d5b',
##		"executionid": '02ef0b05-4f8d-4f09-85ac-643b59428a24',
##		"starttime": '2017-03-09 07:50:30+0000',
##		"status": 'Pass',
##		"query": "inserintotexecutionquery"
##    }
##    response = ExecuteTestSuite_ICE(data)
##
    #ScheduleTestSuite_ICE
##    data = {
##        "cycleid": '9c2584e3-32b3-428b-9c0a-2a9a63984558',
##		"scheduledatetime": '1508340780000',
##		"scheduleid": 'd0bddd3e-b96f-48d0-b0cd-eb04c9e3cbed',
##		"browserlist": ["1"],
##		"clientipaddress": 'sakshi.goyal',
##		"clientport": "9494",
##		"scenariodetails": [{"condition":0,"dataparam":[" "],"executestatus":1,"scenarioids":"dfa020fd-aeee-4c0d-991b-c83e1b46c07e","scenarioname":"Scenario_023"},{"condition":0,"dataparam":[" "],"executestatus":1,"scenarioids":"46508acc-9586-4870-b76c-c06ecae80188","scenarioname":"Scenario_0xx"}],
##		"schedulestatus": 'success',
##		"testsuiteids": ['2565ac0d-fcc8-4cb9-b470-e2fe8cfcae99'],
##		"testsuitename": 'Module_test',
##		"query": "insertscheduledata"
##    }
##    response = ScheduleTestSuite_ICE(data)
##
    #createUser
##    data = {
##        "query": "createuser",
##		"createdby": 'admin',
##		"defaultrole": '566702ae-8caf-42e9-9b20-fc2381c4cc0f',
##		"emailid": 'test@avo.com',
##		"firstname": 'test',
##		"lastname": 'das',
##		"ldapuser": False,
##		"password": '$2a$10$YoK5z0QdFn3yijy0WuyB/.i6XhaLbwE3pdkd3/MlWtIA.13XcQJO2',
##		"username": 'test_das'
##    }
##    response = createUser(data)
##
    #updateUser
##    data = {
##        "userid": 'b89440ff-2b93-4311-a0a9-b53475a7eb2d',
##		"additionalroles": 'null',
##		"deactivated": False,
##		"emailid": 'test@avo.com',
##		"firstname": 'test',
##		"lastname": 'das',
##		"ldapuser": False,
##		"modifiedby": 'admin',
##		"modifiedbyrole": 'b5e9cb4a-5299-4806-b7d7-544c30593a6e',
##		"password": '$2a$10$YoK5z0QdFn3yijy0WuyB/.i6XhaLbwE3pdkd3/MlWtIA.13XcQJO2',
##		"username": 'test_das'
##    }
##    response = updateUser(data)
##
    #createProject_ICE
##    data = {
##        "query": "createproject",
##		"domainid": 'a144b468-e84f-4e7c-9a8a-0a658330212e',
##		"projectname": 'test_project',
##		"createdby": 'admin_user',
##		"projecttypeid": 'c957b36d-00f9-4445-8827-a864b317e74c',
##		"skucodeproject": "skucodeproject",
##		"tags": "tags"
##    }
##    response = createProject_ICE(data)

    #assignProjects_ICE
##    data = {
##        "alreadyassigned": False,
##		"userid": 'e2ed3832-9abf-4c2d-a4b2-fe7755cf7f71',
##		"domainid": 'a144b468-e84f-4e7c-9a8a-0a658330212e',
##		"createdby": 'admin_user',
##		"projectids": ['8c41d97a-9b8a-472b-a654-554162792c12']
##    }
##    response = assignProjects_ICE(data)



    #userAccess
##    data = {
##            "roleid": "b5e9cb4a-5299-4806-b7d7-544c30593a6e",
####            "servicename":"assignProjects_ICE",
##            "servicename":"updateScreen_ICE",
##    }
