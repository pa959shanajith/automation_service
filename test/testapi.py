#-------------------------------------------------------------------------------
# Name:        testapi.py
# Purpose:     replica of restapi
#              for testing the restapi components without flask features
#
# Author:      vishvas.a
#
# Created:     10/07/2017
# Copyright:   (c) vishvas.a 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import json
import datetime
import uuid
##from flask import Flask, request , jsonify
##app = Flask(__name__)

##import logging
##from logging.handlers import RotatingFileHandler
from cassandra.cluster import Cluster
##from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
##parentdir=os.chdir("..")
##config_path = parentdir+'/rest_conf.json'
##rest_config = json.loads(open(config_path).read())
##ip=rest_config['restapi']['databaseip']
##key=rest_config['restapi']['dbusername']
##pswd=rest_config['restapi']['dbpassword']
##auth = PlainTextAuthProvider(username=key, password=pswd)
auth = PlainTextAuthProvider(username='nineteen68', password='TA@SLK2017')
cluster = Cluster(['10.41.31.130'],auth_provider=auth)

icesession = cluster.connect()
n68session = cluster.connect()
icehistorysession = cluster.connect()
n68historysession = cluster.connect()

from cassandra.query import dict_factory

icesession.row_factory = dict_factory
icesession.set_keyspace('icetestautomation')

n68session.row_factory = dict_factory
n68session.set_keyspace('nineteen68')

icehistorysession.row_factory = dict_factory
icehistorysession.set_keyspace('icetestautomationhistory')

n68historysession.row_factory = dict_factory
n68historysession.set_keyspace('nineteen68history')

#server check
##@app.route('/')
def server_ready():
    return 'Data Server Ready!!!'


##################################################
# BEGIN OF LOGIN SCREEN
# INCLUDES : Login components
##################################################
#service for login to Nineteen68
##@app.route('/login/authenticateUser_Nineteen68',methods=['POST'])
def authenticateUser(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    authenticateuser = "select password from users where username = '"+requestdata["username"]+"' allow filtering;"
    queryresult = n68session.execute(authenticateuser)
    res= {"rows":queryresult.current_rows}
    return res

#service for user ldap validation
##@app.route('/login/authenticateUser_Nineteen68/ldap',methods=['POST'])
def authenticateUser_Nineteen68_ldap(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    authenticateuserldap = "select ldapuser from users where username = '"+requestdata["username"]+"' allow filtering;"
    queryresult = n68session.execute(authenticateuserldap)
    res = {"rows":queryresult.current_rows}
    return res

#service for loading user information
##@app.route('/login/loadUserInfo_Nineteen68',methods=['POST'])
def loadUserInfo_Nineteen68(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    if(requestdata["query"] == 'userInfo'):
        loaduserinfo1 = "select userid, emailid, firstname, lastname, defaultrole, ldapuser , additionalroles, username from users where username = '"+requestdata["username"]+"' allow filtering"
        queryresult = n68session.execute(loaduserinfo1)
        rows=[]
        for eachkey in queryresult.current_rows:
        	userid = eachkey['userid']
        	emailid = eachkey['emailid']
        	firstname = eachkey['firstname']
        	lastname = eachkey['lastname']
        	defaultrole = eachkey['defaultrole']
        	ldapuser = eachkey['ldapuser']
        	username = eachkey['username']
        	additionalroles=[]
        	for eachrole in eachkey['additionalroles']:
        		additionalroles.append(eachrole)

        	eachobject={'userid':userid,'emailid':emailid,'firstname':firstname,
        	'lastname':lastname,'defaultrole':defaultrole,'ldapuser':ldapuser,'username':username,'additionalroles':additionalroles}
        	rows.append(eachobject)
        res={'rows':rows}
        return res
    elif(requestdata["query"] == 'loggedinRole'):
        loaduserinfo2 = "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering"
        queryresult = n68session.execute(loaduserinfo2)
        res = {"rows":queryresult.current_rows}
    elif(requestdata["query"] == 'userPlugins'):
        loaduserinfo3 = "select dashboard,deadcode,mindmap,neuron2d,neuron3d,oxbowcode,reports from userpermissions WHERE roleid = "+requestdata["roleid"]+" allow filtering"
        queryresult = n68session.execute(loaduserinfo3)
        res = {"rows":queryresult.current_rows}
    else:
        res={'rows':'fail'}
        return jsonify(res)
    return res

#service for getting rolename by roleid
##@app.route('/login/getRoleNameByRoleId_Nineteen68',methods=['POST'])
def getRoleNameByRoleId_Nineteen68(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    rolename = "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering;"
    queryresult = n68session.execute(rolename)
    res = {"rows":queryresult.current_rows}
    return res

####@app.route('/design/authenticateUser_Nineteen68/ldap',methods=['POST'])
##def authenticateUser_Nineteen68_ci(data):
####    requestdata=json.loads(request.data)
##    requestdata=data
##    authenticateuser = "select password from users where username = '"+requestdata["username"]+"' allow filtering;"
##    queryresult = n68session.execute(authenticateuser)
##    res= {"rows":queryresult.current_rows}
##    return res

#utility checks whether user is having projects assigned
##@app.route('/login/authenticateUser_Nineteen68/projassigned',methods=['POST'])
def authenticateUser_Nineteen68_projassigned(data):
    try:
##        requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'getUsers'):
            authenticateuserprojassigned1= "select userid,defaultrole from users where username = '"+requestdata["username"]+"' allow filtering;"
            queryresult = n68session.execute(authenticateuserprojassigned1)
        elif(requestdata["query"] == 'getUserRole'):
            authenticateuserprojassigned2= "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering;"
            queryresult = n68session.execute(authenticateuserprojassigned2)
        elif(requestdata["query"] == 'getAssignedProjects'):
            authenticateuserprojassigned3= "select projectids from icepermissions where userid = "+requestdata["userid"]+" allow filtering;"
            queryresult = icesession.execute(authenticateuserprojassigned3)
        else:
            res={'rows':'fail'}
            return jsonify(res)
        res= {"rows":queryresult.current_rows}
        return res
##            return jsonify(res)
    except Exception as authenticateuserprojassignedexc:
        print 'Error in authenticateUser_projassigned:\n',authenticateuserprojassignedexc
        res={'rows':'fail'}
        return res
##        return jsonify(res)

#########################
# END OF LOGIN SCREEN
#########################


#########################
# BEGIN OF DESIGN SCREEN
# INCLUDES : scraping/ws-screen/design testcase creation
#########################

#keywords loader for design screen
##@app.route('/design/getKeywordDetails_ICE',methods=['POST'])
def getKeywordDetails(data):
##    projecttypename = request.data
    projecttypename = data
    keywordquery="select objecttype, toJson(keywords) from keywords where projecttypename in ('"+projecttypename+"','Generic') ALLOW FILTERING"
    queryresult = icesession.execute(keywordquery)
    resultset=[]
    for eachrow in queryresult.current_rows:
        objecttype = eachrow['objecttype']
        keywords =  eachrow['system.tojson(keywords)']
        eachobject={'objecttype':objecttype,'keywords':keywords}
        resultset.append(eachobject)
    res={'rows':resultset}
##    return jsonify(res)
    return res

#test case reading service
##@app.route('/design/readTestCase_ICE',methods=['POST'])
def readTestCase_ICE(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    readtestcasequery = "select testcasesteps,testcasename from testcases where screenid= " + requestdata["screenid"] +" and testcasename='"+requestdata["testcasename"]+"'" +" and versionnumber="+str(requestdata["versionnumber"])+" and testcaseid=" + requestdata["testcaseid"];
    queryresult = icesession.execute(readtestcasequery)
    res= {"rows":queryresult.current_rows}
    return res




#########################
# END OF DESIGN SCREEN
#########################

#########################
# BEGIN OF ADMIN SCREEN
# INCLUDES : all admin related actions
#########################

#fetches the user roles for assigning during creation/updation user
##@app.route('/admin/getUserRoles_Nineteen68',methods=['POST'])
def getUserRoles():
    userrolesquery="select roleid, rolename from roles"
    queryresult = n68session.execute(userrolesquery)
    res={'rows':queryresult.current_rows}
##    return jsonify(res)
    return res



#service renders all the details of the child type
#if domainid is provided all projects in domain is returned
#if projectid is provided all release and cycle details is returned
#if cycleid is provided, testsuite details is returned
##@app.route('/admin/getDetails_ICE',methods=['POST'])
def getDetails_ICE(data):
    try:
##        requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'domaindetails'):
            getdetailsquery="select projectid,projectname from projects where domainid=" + requestdata['id'];
            queryresult = icesession.execute(getdetailsquery)
        elif(requestdata["query"] == 'projectsdetails'):
            if(requestdata["subquery"] == 'projecttypeid'):
                getdetailsquery="select projecttypeid,projectname from projects where projectid=" + requestdata['id'];
            elif(requestdata["subquery"] == 'projecttypename'):
                getdetailsquery="select projecttypename from projecttype where projecttypeid=" + requestdata['id'];
            elif(requestdata["subquery"] == 'releasedetails'):
                getdetailsquery="select releaseid,releasename from releases where projectid=" + requestdata['id'];
            elif(requestdata["subquery"] == 'cycledetails'):
                getdetailsquery="select cycleid,cyclename from cycles where releaseid=" + requestdata['id'];
            queryresult = icesession.execute(getdetailsquery)
        elif(requestdata["query"] == 'cycledetails'):
            getdetailsquery="select testsuiteid,testsuitename from testsuites where cycleid=" + requestdata['id'];
            queryresult = icesession.execute(getdetailsquery)
        res={'rows':queryresult.current_rows}
##    return jsonify(res)
        return res
    except Exception as getdetailsexc:
        print 'Error in getDetails_ICE:\n',getdetailsexc
        res={'rows':'fail'}
##    return jsonify(res)
        return res

#service renders the names of all projects in domain/projects
##@app.route('/admin/getNames_ICE',methods=['POST'])
def getNames_ICE(data):
    try:
##        requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'domainsall'):
            getnamesquery1="select projectid,projectname from projects where domainid="+requestdata['id'];
            queryresult = icesession.execute(getnamesquery1)
        elif(requestdata["query"] == 'projects'):
            getnamesquery2="select projectid,projectname from projects where projectid="+requestdata['id'];
            queryresult = icesession.execute(getnamesquery2)
        elif(requestdata["query"] == 'releases'):
            getnamesquery3="select releaseid,releasename from releases where releaseid="+requestdata['id'];
            queryresult = icesession.execute(getnamesquery3)
        elif(requestdata["query"] == 'cycles'):
            getnamesquery4="select cycleid,cyclename from cycles where cycleid="+requestdata['id'];
            queryresult = icesession.execute(getnamesquery4)
        res={'rows':queryresult.current_rows}
##    return jsonify(res)
        return res
    except Exception as getdetailsexc:
        print 'Error in getDetails_ICE:\n',getdetailsexc
        res={'rows':'fail'}
##    return jsonify(res)
        return res

#service renders all the domains in DB
##@app.route('/admin/getDomains_ICE',methods=['POST'])
def getDomains_ICE():

##    requestdata=json.loads(request.data)
    getdomainsquery="select domainid,domainname from domains";
    queryresult = icesession.execute(getdomainsquery)
    res={'rows':queryresult.current_rows}
    return res


#service fetches projects assigned to user.
##@app.route('/admin/getAssignedProjects_ICE',methods=['POST'])
def getAssignedProjects_ICE(data):

##    requestdata=json.loads(request.data)
    requestdata=data
    if(requestdata['query'] == 'projectid'):
        getassingedprojectsquery1="select projectids from icepermissions where userid = "+requestdata['userid']+" and domainid = "+requestdata['domainid']+"";
        queryresult = icesession.execute(getassingedprojectsquery1)
    elif(requestdata['query'] == 'projectname'):
        getassingedprojectsquery2="select projectname from projects where projectid = "+requestdata['projectid'];
        queryresult = icesession.execute(getassingedprojectsquery2)
    res={'rows':queryresult.current_rows}
    return res

#service creates new users into Nineteen68
##@app.route('/admin/createUser_Nineteen68',methods=['POST'])
def createUser_Nineteen68(data):
    requestdata=data
    if(requestdata['query'] == 'allusernames'):
        createuserquery1=("select username from users")
        queryresult = n68session.execute(createuserquery1)
        res={'rows':queryresult.current_rows}
    elif(requestdata['query'] == 'createuser'):
        deactivated=requestdata['deactivated']
        createuserquery2=("insert into users (userid,createdby,createdon,"
                +"defaultrole,deactivated,emailid,firstname,lastname,ldapuser,password,username) values"
                +"( "+requestdata['userid']+" , '"+requestdata['username']+"' , "
                + str(getcurrentdate())+" , "+requestdata['defaultrole']+" , "
                +str(deactivated)+" , '"+requestdata['emailid']+"' , '"
                +requestdata['firstname']+"' , '"+requestdata['lastname']+"' , "
                +requestdata['ldapuser']+" , '"+requestdata['password']+"' , '"
                +requestdata['username']+"')")
##        print createuserquery2
##        queryresult = n68session.execute(createuserquery2)
        res={'rows':'Success'}
    return res

#fetch user data into Nineteen68
##@app.route('/admin/getUsers_Nineteen68',methods=['POST'])
def getUsers_Nineteen68(data):
    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        userroles = requestdata['userroles']
        userrolesarr=[]
        for eachroleobj in userroles:
            if eachroleobj['rolename'] == 'Admin' or eachroleobj['rolename'] == 'Test Manager' :
                userrolesarr.append(eachroleobj['roleid'])
        print userrolesarr
        useridslistquery = "select userid from icepermissions where projectids contains "+requestdata['projectid']+" allow filtering;"
        queryresultuserids= icesession.execute(useridslistquery)

        resultdata={}
        userroles=[]
        rids=[]
        for row in queryresultuserids.current_rows:
            queryforuser="select userid, username, defaultrole from users where userid="+str(row['userid'])
            queryresultusername=n68session.execute(queryforuser)
            if not queryresultusername.current_rows[0]['defaultrole'] in userrolesarr:
            	print queryresultusername.current_rows[0]['username']
                rids.append(row['userid'])
                userroles.append(queryresultusername.current_rows[0]['username'])
                resultdata["userRoles"]=userroles
                resultdata["r_ids"]=rids
        print resultdata
    except Exception as getUsersexc:
        print 'Error in getUsers_Nineteen68:\n',getUsersexc
        res={'rows':'fail'}
##        return jsonify(res)
        return res

#service update user data into Nineteen68
##@app.route('/admin/updateUser_Nineteen68',methods=['POST'])
def updateUser_Nineteen68(data):

    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata['query'] == 'userdetails'):
            updateuserquery1=("select username,password,firstname,lastname,"
                +" emailid,ldapuser,additionalroles from users where"
                +" userid=" + requestdata['userid'])
            queryresult = n68session.execute(updateuserquery1)
            res={'rows':queryresult.current_rows}
        elif(requestdata['query'] == 'updateuser'):
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
            + "', additionalroles= additionalroles + {" + str(requestdata['additionalroles'])
            + "} where userid=" + str(requestdata['userid']))
##            queryresult = n68session.execute(updateuserquery2)
            print updateuserquery2
            res={'rows':'Success'}
        else:
##            return jsonify(res)
            return res
        return res
    except Exception as updateUserexc:
        print updateUserexc
        print 'Error in updateUser_nineteen68'
        res={'rows':'fail'}
##        return jsonify(res)
        return res


#service creates a complete project structure into ICE keyspace
##@app.route('/admin/createProject_ICE',methods=['POST'])
def createProject_ICE(data):

    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata['query'] == 'projecttype'):
            projecttypequery=("select projecttypeid from projecttype where"
            +" projecttypename = '"+requestdata['projecttype']+"' allow filtering")
            queryresult = icesession.execute(projecttypequery)
        elif(requestdata['query'] == 'createproject'):
            projectid =uuid.uuid4()
            deletedonproject = False
            createprojectquery1 = ("insert into projects (domainid,projectname,"
            +"projectid,createdby,createdon,deleted,projecttypeid,"
            +"skucodeproject,tags)values ( "+str(requestdata['domainid'])
            +", '"+requestdata['projectname']+"' , "+str(projectid)
            +", '"+requestdata['createdby']+"',"+str(getcurrentdate())
            +", "+str(deletedonproject)+", "+requestdata['projecttypeid']
            +",'"+requestdata['skucodeproject']+"' , ['"+requestdata['tags']+"']);")
            res={'rows':'Success'}
        elif(requestdata['query'] == 'createrelease'):
            releaseid =uuid.uuid4()
            deletedonrelease = False
            createprojectquery2=("insert into releases (projectid,releasename,"
            +"releaseid,createdby,createdon,deleted,skucoderelease,tags) values "
            +"("+str(requestdata['projectid'])+", '"+requestdata['releasename']
            +"' ,"+str(releaseid)+",'"+requestdata['createdby']
            +"' ,"+str(getcurrentdate())+","+str(deletedonrelease)
            +",'"+requestdata['skucoderelease']+"' ,['"+requestdata['tags']+"']);")
            res={'rows':'Success'}
        elif(requestdata['query'] == 'createcycle'):
            cycleid =uuid.uuid4()
            deletedoncycle = False
            createprojectquery3=("insert into cycles (releaseid,cyclename, "
            +"cycleid,createdby,createdon,deleted,skucodecycle,tags) values "
            +" ("+str(requestdata['releaseid'])+", '"+requestdata['cyclename']
            +"',"+str(cycleid)+",'"+requestdata['createdby']
            +"',"+str(getcurrentdate())+","+str(deletedoncycle)
            +",'"+requestdata['skucodecycle']+"' ,['"+requestdata['tags']+"']);")
##                queryresult = icesession.execute(createprojectquery3)
            res={'rows':'Success'}
        else:
            res={'rows':'fail'}
##            return jsonify(res)
            return res
        return res
    except Exception as updateUserexc:
        print updateUserexc
        print 'Error in updateUser_nineteen68'
        res={'rows':'fail'}
    ##        return jsonify(res)
        return res

#service updates the specified project structure into ICE keyspace
##@app.route('/admin/updateProject_ICE',methods=['POST'])
def updateProject_ICE(data):
    res={'rows':'fail'}
    try:
##        requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata['query'] == 'deleterelease'):
            updateprojectquery1=("delete from releases where releasename='"
            +requestdata['releasename']+"' and projectid="+requestdata['projectid']
            +" and releaseid="+requestdata['releaseid'])
            print updateprojectquery1
        elif(requestdata['query'] == 'deletecycle'):
            updateprojectquery2=("delete from cycles where cyclename='"
            +requestdata['cyclename']+"' and releaseid="+requestdata['releaseid']
            +" and cycleid="+requestdata['cycleid'])
            print updateprojectquery2

    except Exception as updateprojectexc:
            import traceback
            traceback.print_exc()
            print('Error in updateProject_ICE')
            res={'rows':'fail'}
    ##        return jsonify(res)
            return res


#service assigns projects to a specific user
##@app.route('/admin/assignProjects_ICE',methods=['POST'])
def assignProjects_ICE(data):
    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        if (requestdata['alreadyassigned'] != str(True)):
            requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
            assignprojectsquery1 = "insert into icepermissions (userid, "
            +"domainid,createdby,createdon,projectids) values"
            +"("+str(requestdata['userid'])+","+str(requestdata['domainid'])
            +",'"+requestdata['createdby']+"',"+str(getcurrentdate())
            +", ["+requestdata['projectids']+"]);"
            queryresult = icesession.execute(assignprojectsquery2)
        elif (requestdata['alreadyassigned'] == str(True)):
            requestdata['projectids'] = ','.join(str(idval) for idval in requestdata['projectids'])
            assignprojectsquery2 = "update icepermissions set"
            +" projectids = projectids + ["+requestdata['projectids']+"] "
            +" modifiedby = "+requestdata['modifiedby']
            +" modifiedon = "+str(getcurrentdate())
            +" modifiedbyrole = '"+requestdata['modifiedbyrole']
            +"' WHERE userid = "+str(requestdata['userid'])
            +" and domainid = "+str(requestdata['domainid']);"
            queryresult = icesession.execute(assignprojectsquery2)
        else:
    ##        return jsonify(res)
            return res
        res={'rows':'Success'}

##        return jsonify(res)
        return res
    except Exception as assignprojectsexc:
        print 'Error in assignProjects_ICE'
        res={'rows':'fail'}
    ##        return jsonify(res)
        return res

#########################
# END OF ADMIN SCREEN
#########################

##################################################
# BEGIN OF REPORTS
# INCLUDES : all reports related actions
##################################################

#fetching all the suite details
##@app.route('/reports/getAllSuites_ICE',methods=['POST'])
def getAllSuites_ICE(data):
    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'domainid'):
            getallsuitesquery1 = "SELECT domainid FROM icepermissions WHERE userid="+requestdata['userid']+";";
            queryresult = icesession.execute(getallsuitesquery1)
        elif(requestdata["query"] == 'projectsUnderDomain'):
            getallsuitesquery2 = "SELECT projectid FROM projects WHERE domainid="+requestdata['domainid']+";";
            queryresult = icesession.execute(getallsuitesquery2)
        elif(requestdata["query"] == 'releasesUnderProject'):
            getallsuitesquery3 = "SELECT releaseid FROM releases WHERE projectid="+requestdata['projectid'];
            queryresult = icesession.execute(getallsuitesquery3)
        elif(requestdata["query"] == 'cycleidUnderRelease'):
            getallsuitesquery4 = "SELECT cycleid FROM cycles WHERE releaseid="+requestdata['releaseid'];
            queryresult = icesession.execute(getallsuitesquery4)
        elif(requestdata["query"] == 'suitesUnderCycle'):
            getallsuitesquery5 = "SELECT testsuiteid,testsuitename FROM testsuites WHERE cycleid="+requestdata['cycleid'];
            queryresult = icesession.execute(getallsuitesquery5)
        else:
            res={'rows':'fail'}
            return jsonify(res)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as getAllSuitesexc:
        print 'Error in getAllSuites_ICE:\n',getAllSuitesexc
        res={'rows':'fail'}
        return jsonify(res)

#fetching all the suite after execution
##@app.route('/reports/getSuiteDetailsInExecution_ICE',methods=['POST'])
def getSuiteDetailsInExecution_ICE(data):
    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        getsuitedetailsquery = "SELECT executionid,starttime,endtime FROM execution WHERE testsuiteid="+requestdata['suiteid'];
        queryresult = icesession.execute(getsuitedetailsquery)
        res= {"rows":queryresult.current_rows}
##        return jsonify(res)
        return res

    except Exception as getsuitedetailsexc:
        print 'Error in getAllSuites_ICE:\n',getsuitedetailsexc
        res={'rows':'fail'}
##        return jsonify(res)
        return res

#fetching all the report status
##@app.route('/reports/reportStatusScenarios_ICE',methods=['POST'])
def reportStatusScenarios_ICE(data):
    try:
    ##    requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'executiondetails'):
            getreportstatusquery1 = "SELECT * FROM reports where executionid="+requestdata['executionid']+" ALLOW FILTERING";
            queryresult = icesession.execute(getreportstatusquery1)
        elif(requestdata["query"] == 'scenarioname'):
            getreportstatusquery2 = "SELECT testscenarioname FROM testscenarios where testscenarioid="+requestdata['scenarioid']+" ALLOW FILTERING";
            queryresult = icesession.execute(getreportstatusquery2)
        else:
            res={'rows':'fail'}
##            return jsonify(res)
        res= {"rows":queryresult.current_rows}
##        return jsonify(res)
        return res

    except Exception as getsuitedetailsexc:
        print 'Error in getAllSuites_ICE:\n',getsuitedetailsexc
        res={'rows':'fail'}
##        return jsonify(res)
        return res

#fetching the reports
##@app.route('/reports/getReport_Nineteen68',methods=['POST'])
def getReport_Nineteen68(data):
    try:
##        requestdata=json.loads(request.data)
        requestdata=data
        if(requestdata["query"] == 'projectsUnderDomain'):
            getreportquery1 ="select report,executedtime,testscenarioid from reports where reportid=" +requestdata['reportid']+" ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery1)
        elif(requestdata["query"] == 'scenariodetails'):
            getreportquery2 ="select testscenarioname,projectid from testscenarios where testscenarioid=" + requestdata['scenarioid'] + " ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery2)
        elif(requestdata["query"] == 'cycleid'):
            getreportquery3 ="select cycleid from testsuites where testsuiteid=" + requestdata['suiteid'] + " and testsuitename = '" + requestdata['suitename'] + "' ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery3)
        elif(requestdata["query"] == 'cycledetails'):
            getreportquery4 ="select cyclename,releaseid from cycles where cycleid=" + requestdata['cycleid']  + "ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery4)
        elif(requestdata["query"] == 'releasedetails'):
            getreportquery5 ="select releasename,projectid from releases where releaseid=" + requestdata['releaseid'] + " ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery5)
        elif(requestdata["query"] == 'projectdetails'):
            getreportquery6 ="select projectname,domainid from projects where projectid=" + requestdata['projectid']  + " ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery6)
        elif(requestdata["query"] == 'domaindetails'):
            getreportquery7 ="select domainname from domains where domainid=" + requestdata['domainid'] + " ALLOW FILTERING";
            queryresult = icesession.execute(getreportquery7)
        else:
            res={'rows':'fail'}
##            return jsonify(res)
            return res
        res= {"rows":queryresult.current_rows}
##        return jsonify(res)
        return res
    except Exception as getreportexc:
        print 'Error in getReport_Nineteen68:\n',getreportexc
        res={'rows':'fail'}
        return res
##        return jsonify(res)


#export json feature on reports
##@app.route('/reports/exportToJson_ICE',methods=['POST'])
def exportToJson_ICE(data):
##    requestdata=json.loads(request.data)
    requestdata=data
    if(requestdata["query"] == 'reportdata'):
        exporttojsonquery1 = "select report from reports where reportid ="+ requestdata['reportid'] + " ALLOW FILTERING ";
        queryresult = icesession.execute(exporttojsonquery1)
    elif(requestdata["query"] == 'scenarioid'):
        exporttojsonquery2 = "select testscenarioid from reports where reportid ="+ requestdata['reportid'] + " ALLOW FILTERING ";
        queryresult = icesession.execute(exporttojsonquery2)
    elif(requestdata["query"] == 'scenarioname'):
        exporttojsonquery3 = "SELECT testscenarioname FROM testscenarios where testscenarioid="+requestdata['scenarioid']+" ALLOW FILTERING";
        queryresult = icesession.execute(exporttojsonquery3)
    else:
        res={'rows':'fail'}
##            return jsonify(res)
    res= {"rows":queryresult.current_rows}
##        return jsonify(res)
    return res
##################################################
# END OF REPORTS
##################################################


#########################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
#########################

#encrpytion utility AES
##@app.route('/utility/encrypt_ICE/aes',methods=['POST'])
def encrypt_ICE(data):
    try:
        import base64
        from Crypto.Cipher import AES
        BS = 16
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        key = b'\x74\x68\x69\x73\x49\x73\x41\x53\x65\x63\x72\x65\x74\x4b\x65\x79'
##        raw=request.data
        raw= data
        if not (raw is None and raw is ''):
            raw = pad(raw)
            cipher = AES.new( key, AES.MODE_ECB)
            return str(base64.b64encode(cipher.encrypt( raw )))
        else:
            res = {"rows":"fail"}
            return str(res)
    except Exception as e:
        res = {"rows":"fail"}
        return str(res)

#########################
# END OF UTILITIES
#########################


##@app.route('/python/')
##def hello_python():
##   return 'Hello Python'
##
##@app.route('/guest/<guest>')
##def hello_guest(guest):
##   return 'Hello %s as Guest' % guest


#########################
# BEGIN OF INTERNAL COMPONENTS
#########################


def isemptyrequest(requestdata):
    flag = False
    for key in requestdata:
        value = requestdata[key]
        if value == 'undefined' or value == '' or value == 'null' or value == None:
            flag = True
    return flag

def getcurrentdate():
    currentdate= datetime.datetime.now()
    beginingoftime = datetime.datetime.utcfromtimestamp(0)
    differencedate= currentdate - beginingoftime
    return long(differencedate.total_seconds() * 1000.0)


#########################
# END OF INTERNAL COMPONENTS
#########################

if __name__ == '__main__':
#    https implementation
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context=context)
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context='adhoc')
#      http implementations
##    app.run(host='127.0.0.1',port=1990,debug=True)

##    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
##    handler = RotatingFileHandler('restapi.log', maxBytes=10000, backupCount=1)
##    handler.setLevel(logging.ERROR)
##    handler.setFormatter(formatter)
##    app.logger.addHandler(handler)
##    app.run(host='127.0.0.1',port=1990,debug=True)
#########################
# TEST COMPONENTS
#########################
#   ----------------------------
# getKeywordDetails
##    data = <getKeywordDetailsof>
##    data = <getKeywordDetailsof>
##    response = getKeywordDetails(data)
#   ----------------------------
#  getUserRoles
##    response = getUserRoles()
#   ----------------------------
#  encrypt_ICE
##    data = <data>
##    response = encrypt_ICE(data)
##    print response
#   ----------------------------
#  readTestCase_ICE
##    data = {
##			"screenid": "<screenid>",
##			"testcasename":"<testcasename>",
##			"testcaseid" : "<testcaseid>",
##            "versionnumber" : <versionnumber>
##		}
##    response = readTestCase_ICE(data)
##    print response
#   ----------------------------
#  authenticateUser_Nineteen68
##    data = {
##			"username": "<username>"
##		  }
##    response = authenticateUser(data)
##    print response
#   ----------------------------
#  authenticateUser_Nineteen68_ldap
##    data = {
##			"username": "<username>"
##		  }
##    response = authenticateUser_Nineteen68_ldap(data)
##    print response
#   ----------------------------
#  authenticateUser_Nineteen68_projassigned
##    data = {
##			"username": "<username>",
##            "query":"getUsers"
##            "query":"getUserRole",
##            "roleid":"<roleid>"
##            "query":"getAssignedProjects",
##            "userid" :"<userid>"
##		  }
##    response = authenticateUser_Nineteen68_projassigned(data)
##    print response
#   ----------------------------
#  loadUserInfo_Nineteen68
##    data = {
##			"username": <username>,
##            "query": "userInfo",
##            "query": "loggedinRole",
##            "query":"userPlugins",
##            "roleid" :"<roleid>"
##		  }
##    response = loadUserInfo_Nineteen68(data)
##    print response
#   ----------------------------
#  getRoleNameByRoleId_Nineteen68
##    data = {
##            "roleid" :"<roleid>"
##		  }
##    response = getRoleNameByRoleId_Nineteen68(data)
##    print response
#   ----------------------------
#  getAllSuites_ICE
##    data = {
##                "query" : "domainid",
##                "userid" :<userid>,
##                "query" : "projectsUnderDomain",
##                "domainid" :<domainid>
##                "query" :"releasesUnderProject",
##                "projectid":<projectid>
##                "query" :"cycleidUnderRelease",
##                "releaseid":<releaseid>
##                "query": "suitesUnderCycle",
##                "cycleid":<cycleid>
##		  }
##    response = getAllSuites_ICE(data)
##    print response
#   ----------------------------
#   getSuiteDetailsInExecution_ICE
##    data = {
##            "suiteid" :<suiteid>
##		  }
##    response = getSuiteDetailsInExecution_ICE(data)
##    print response
#   ----------------------------
#   reportStatusScenarios_ICE
##    data = {
##            "query":"executiondetails",
##            "executionid" :<executionid>
##            "query" : "scenarioname",
##            "scenarioid":<scenarioid>
##		  }
##    response = reportStatusScenarios_ICE(data)
##    print response
#   ----------------------------
#   getReport_Nineteen68
##    data = {
##            "query":"projectsUnderDomain",
##            "reportid" :<reportid>
##            "query":"scenariodetails",
##            "scenarioid":<scenarioid>
##            "query":"cycleid",
##            "suiteid":<suiteid>
##            "suitename":<suitename>
##            "query":"cycledetails",
##            "cycleid":<cycleid>
##            "query":"releasedetails",
##            "releaseid":<releaseid>
##            "query":"projectdetails",
##            "projectid":<projectid>
##            "query":"domaindetails",
##            "domainid":<domainid>

##		  }
##    response = getReport_Nineteen68(data)
##    print response
#   ----------------------------
#   exportToJson_ICE
##    data = {
##            "query":"scenarioid",
##            "reportid" :"reportid"
##            "query" : "scenarioname",
##            "scenarioid":"scenarioid"
##		  }
##    response = exportToJson_ICE(data)
##    print response
#   ----------------------------
#   getDetails_ICE
##    data = {
##            "query":"domaindetails",
##            "id" :"id"

##            "query":"projectsdetails",
##            "subquery":"projecttypeid",
##            "id" :"id"

##            "query":"projectsdetails",
##            "subquery":"projecttypename",
##            "id" :"id"

##            "query":"projectsdetails",
##            "subquery":"projecttypeid",
##            "id" :"id"

##            "query":"projectsdetails",
##            "subquery":"releasedetails",
##            "id" :"id"

##            "query":"projectsdetails",
##            "subquery":"cycledetails",
##            "id" :"releaseid"

##            "query":"cycledetails",
##            "id" :"id"
##		  }
##    response = getDetails_ICE(data)
##    print response
#   ----------------------------
#   getNames_ICE
##    data = {
##            "query":"domainsall",
##            "id" :"domainid"
##            "query":"projects",
##            "id" :"projectid"
##            "query":"releases",
##            "id" :"releaseid"
##            "query":"cycles",
##            "id" :"id"
##            }
##    response = getNames_ICE(data)
##    print response
#   ----------------------------
###   getDomains_ICE
##    response = getDomains_ICE()
##    print response
#   ----------------------------
#   getAssignedProjects_ICE
##    data = {
##            "query":"projectid",
##            "domainid":<domainid>,
##            "userid":<userid>,
##            "query":<query>,
##            "projectid":<projectid>
##            }
##    response = getAssignedProjects_ICE(data)
##    print response
#   ----------------------------
#   createUser_Nineteen68
##    data = {
##              userid,createdby,createdon,defaultrole,deactivated,emailid,firstname,lastname,ldapuser,password,username
##            "query":"createuser",
##            "userid":<userid>
##            "createdby":<createdby>,
##            "deactivated": <deactivated>,
##            "defaultrole":<defaultrole>,
##            "emailid":<emailid>,
##            "firstname":<firstname>,
##            "lastname":<lastname>,
##            "ldapuser":<ldapuser>,
##            "password":<password>,
##            "username":<username>
##            }
##    response = createUser_Nineteen68(data)
##    print response
#   ----------------------------
#   getUsers_Nineteen68
##    data = {
##    "userroles":<userroles>,
##    "projectid":<projectid>
##    }
##    response = getUsers_Nineteen68(data)
##    print response
#   ----------------------------
#   updateUser_Nineteen68
##    data = {
##        "userid":<userid>
##        "query":"userdetails"
##    }
##    response = updateUser_Nineteen68(data)
##    print response
##    data = {
##        "additionalroles":<additionalroles>,
##        "deactivated" :<deactivated>,
##        "emailid":<emailid>,
##        "firstname":<firstname>,
##        "lastname":<lastname>,
##        "ldapuser":<ldapuser>,
##        "modifiedby":<modifiedby>,
##        "modifiedbyrole" : <modifiedbyrole>
##        "password":<password>
##        "username":<username>,
##        "userid":<userid>,
##        "query":"updateuser"
##    }
##    response = updateUser_Nineteen68(data)
##    print response
#   ----------------------------
#   createProject_ICE
##    data = {
##        "projecttype":"Web",
##        "query":"projecttype"

## domainid,projectname,projectid,createdby,createdon,deleted,projecttypeid,skucodeproject,tags
##        "query" : "createproject",
##        "domainid" : "<domainid>",
##        "projectname":<projectname>",
##        "createdby":<createdby>,
##        "projecttypeid":<projecttypeid>,
##        "skucodeproject" : "skucodeproject",
##        "tags":"tags"

## projectid,releasename,releaseid,createdby,createdon,deleted,skucoderelease,tags
##        "query":"createrelease",
##        "projectid" :<projectid>,
##        "releasename":<releasename>,
##        "createdby":"<createdby>",
##        "skucoderelease":"skucoderelease",
##        "tags":"tags"

##        "query":"createcycle",
##        "releaseid" :<releaseid>,
##        "cyclename":<cyclename>,
##        "createdby":"<createdby>",
##        "skucodecycle":"skucodecycle",
##        "tags":"tags"
##    }
##    response = createProject_ICE(data)
##    print response
#   ----------------------------
#   assignProjects_ICE
##    data = {
##        "projecttype":<projecttype>,
##        "query":"projecttype"
##    }
##    response = assignProjects_ICE(data)
##    print response
#########################
# TEST COMPONENTS END
#########################