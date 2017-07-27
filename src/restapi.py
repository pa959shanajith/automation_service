#-------------------------------------------------------------------------------
# Name:        restapi.py
# Purpose:
#
# Author:      vishvas.a
#
# Created:     10/07/2017
# Copyright:   (c) vishvas.a 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import json
from flask import Flask, request , jsonify
import logging
import datetime
import uuid
from logging.handlers import RotatingFileHandler
app = Flask(__name__)
from cassandra.cluster import Cluster
from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
auth = PlainTextAuthProvider(username='<databaseusername>', password='databasepassword')
cluster = Cluster(['<databaseip>'],auth_provider=auth)


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
@app.route('/')
def server_ready():
    return 'Data Server Ready!!!'

##################################################
# BEGIN OF LOGIN SCREEN
# INCLUDES : Login components
##################################################

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
            return jsonify(res)
        else:
            app.logger.error('Empty data received. authentication')
            return jsonify(res)
    except Exception as authenticateuserexc:
        app.logger.error('Error in authenticateUser.')
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
            return jsonify(res)
        else:
            app.logger.error('Empty data received. authentication')
            return jsonify(res)
    except Exception as authenticateuserldapexc:
        app.logger.error('Error in authenticateUser_ldap.')
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
                loaduserinfo3 = ("select dashboard, deadcode, mindmap, neuron2d,"
                                +"neuron3d, oxbowcode, reports from "
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


#########################
# END OF LOGIN SCREEN
#########################


##################################################
# BEGIN OF DESIGN SCREEN
# INCLUDES : scraping/ws-screen/design testcase creation
##################################################

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
            readtestcasequery = ("select testcasesteps,testcasename "
                            +"from testcases where "
                            +"screenid= " + requestdata["screenid"]
                            +" and testcasename='"+requestdata["testcasename"]+"'"
                            +" and versionnumber="+str(requestdata["versionnumber"])
                            +" and testcaseid=" + requestdata["testcaseid"])
            queryresult = icesession.execute(readtestcasequery)
            res= {"rows": queryresult.current_rows}
            return jsonify(res)
        else:
            app.logger.error('Empty data received. reading Testcase')
            return jsonify(res)
    except Exception as readtestcaseexc:
        app.logger.error('Error in readTestCase_ICE.')
        return jsonify(res)

##################################################
# END OF DESIGN SCREEN
##################################################


##################################################
# BEGIN OF ADMIN SCREEN
# INCLUDES : all admin related actions
##################################################

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
                if not queryresultusername.current_rows[0]['defaultrole'] in userrolesarr:
                    rids.append(row['userid'])
                    userroles.append(queryresultusername.current_rows[0]['username'])
                    res["userRoles"]=userroles
                    res["r_ids"]=rids
            return jsonify(res)
        else:
            app.logger.error('Empty data received. get users - Mind Maps.')
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

##################################################
# END OF ADMIN SCREEN
##################################################

##################################################
# BEGIN OF REPORTS
# INCLUDES : all reports related actions
##################################################

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


##################################################
# END OF REPORTS
##################################################

##################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
##################################################

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

##################################################
# END OF UTILITIES
##################################################

#########################
# BEGIN OF INTERNAL COMPONENTS
#########################


def isemptyrequest(requestdata):
    flag = False
    for key in requestdata:
        value = requestdata[key]
        if key != 'additionalroles':
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
##    context = ('cert.pem', 'key.pem')#certificate and key files
##    #https implementation
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context=context)
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context='adhoc')

    #http implementations
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('restapi.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.run(host='127.0.0.1',port=1990,debug=True)