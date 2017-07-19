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
import json
##from flask import Flask, request , jsonify
##app = Flask(__name__)
from cassandra.cluster import Cluster
##from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
auth = PlainTextAuthProvider(username='db username', password='<db password>')
c = Cluster(['<local db ip>'],auth_provider=auth)

icesession = c.connect()
n68session = c.connect()

from cassandra.query import dict_factory
icesession.row_factory = dict_factory
icesession.set_keyspace('icetestautomation')

n68session.row_factory = dict_factory
n68session.set_keyspace('nineteen68')

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
        loaduserinfo1 = "select userid, emailid, firstname, lastname, defaultrole, additionalroles, username from users where username = '"+requestdata["username"]+"' allow filtering"
        queryresult = n68session.execute(loaduserinfo1)
    elif(requestdata["query"] == 'loggedinRole'):
        loaduserinfo2 = "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering"
        queryresult = n68session.execute(loaduserinfo2)
    elif(requestdata["query"] == 'userPlugins'):
        loaduserinfo3 = "select dashboard,deadcode,mindmap,neuron2d,neuron3d,oxbowcode,reports from userpermissions WHERE roleid = "+requestdata["roleid"]+" allow filtering"
        queryresult = n68session.execute(loaduserinfo3)
    else:
        res={'rows':'fail'}
        return jsonify(res)
    res = {"rows":queryresult.current_rows}
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



#########################
# END OF INTERNAL COMPONENTS
#########################

if __name__ == '__main__':
#    https implementation
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context=context)
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context='adhoc')
#      http implementations
##    app.run(host='127.0.0.1',port=1990,debug=True)

#########################
# TEST COMPONENTS
#########################
#   ----------------------------
# getKeywordDetails
##    data = "Web"
##    data = "Mobility"
##    response = getKeywordDetails(data)
#   ----------------------------
#  getUserRoles
##    response = getUserRoles()
#   ----------------------------
#  encrypt_ICE
##    data = "Nineteen68"
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
##			"username": "<username>",
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
##                "userid" :"9b57a7cb-0f82-499c-8e43-adccc247c590"
##                "query" : "projectsUnderDomain",
##                "domainid" :"e1cb0da2-44b8-4f8a-9ba8-8a290174881f"
##                "query" :"releasesUnderProject",
##                "projectid":"57dcec44-4955-4a23-b1d2-14afa8ec3c98"
##                "query" :"cycleidUnderRelease",
##                "releaseid":"0754cf4a-742d-4628-9d25-3b882f78b90d"
##                "query": "suitesUnderCycle",
##                "cycleid":"825c2143-90ac-4c58-b475-390dda7b0eff"
##		  }
##    response = getAllSuites_ICE(data)
##    print response
#   ----------------------------
#   getSuiteDetailsInExecution_ICE
##    data = {
##            "suiteid" :"57ec9be0-4994-4526-beb5-5d042c9073b1"
##		  }
##    response = getSuiteDetailsInExecution_ICE(data)
##    print response
#   ----------------------------
#   reportStatusScenarios_ICE
##    data = {
##            "query":"executiondetails",
##            "executionid" :"20d702da-c365-42dd-97f1-1aebeb12a9dd"
##            "query" : "scenarioname",
##            "scenarioid":"ee567f9a-2451-486a-befc-d0547a99898a"
##		  }
##    response = reportStatusScenarios_ICE(data)
##    print response
#   ----------------------------
#   getReport_Nineteen68
##    data = {
##            "query":"projectsUnderDomain",
##            "reportid" :"e59decbd-9302-46d8-b59b-fe3558aeb18e"
##            "query":"scenariodetails",
##            "scenarioid":"ee567f9a-2451-486a-befc-d0547a99898a"
##            "query":"cycleid",
##            "suiteid":"3abdac8b-7715-4bde-b878-bce48a59d698",
##            "suitename":"Ashwini_Suite1"
##            "query":"cycledetails",
##            "cycleid":"825c2143-90ac-4c58-b475-390dda7b0eff"
##            "query":"releasedetails",
##            "releaseid":"0754cf4a-742d-4628-9d25-3b882f78b90d"
##            "query":"projectdetails",
##            "projectid":"57dcec44-4955-4a23-b1d2-14afa8ec3c98"
##            "query":"domaindetails",
##            "domainid":"e1cb0da2-44b8-4f8a-9ba8-8a290174881f"
##		  }
##    response = getReport_Nineteen68(data)
##    print response
#   ----------------------------
#   exportToJson_ICE
##    data = {
##            "query":"scenarioid",
##            "reportid" :"e59decbd-9302-46d8-b59b-fe3558aeb18e"
##            "query" : "scenarioname",
##            "scenarioid":"ee567f9a-2451-486a-befc-d0547a99898a"
##		  }
##    response = exportToJson_ICE(data)
##    print response
#########################
# TEST COMPONENTS END
#########################