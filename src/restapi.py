#-------------------------------------------------------------------------------
# Name:        module1
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
app = Flask(__name__)
from cassandra.cluster import Cluster
from flask_cassandra import CassandraCluster
from cassandra.auth import PlainTextAuthProvider
auth = PlainTextAuthProvider(username='<databaseusername>', password='databasepassword')
c = Cluster(['<databaseip>'],auth_provider=auth)

icesession = c.connect()
n68session = c.connect()

from cassandra.query import dict_factory
icesession.row_factory = dict_factory
icesession.set_keyspace('icetestautomation')

n68session.row_factory = dict_factory
n68session.set_keyspace('nineteen68')

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
def authenticateUser():
    try:
        requestdata=json.loads(request.data)
        authenticateuser = "select password from users where username = '"+requestdata["username"]+"' allow filtering;"
        queryresult = n68session.execute(authenticateuser)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as authenticateuserexc:
        print 'Error in authenticateUser:\n',authenticateuserexc
        res={'rows':'fail'}
        return jsonify(res)

#service for user ldap validation
@app.route('/login/authenticateUser_Nineteen68/ldap',methods=['POST'])
def authenticateUser_Nineteen68_ldap():
    try:
        requestdata=json.loads(request.data)
        authenticateuserldap = "select ldapuser from users where username = '"+requestdata["username"]+"' allow filtering;"
        queryresult = n68session.execute(authenticateuserldap)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as authenticateuserldapexc:
        print 'Error in authenticateUser_ldap:\n',authenticateuserldapexc
        res={'rows':'fail'}
        return jsonify(res)

#service for getting rolename by roleid
@app.route('/login/getRoleNameByRoleId_Nineteen68',methods=['POST'])
def getRoleNameByRoleId_Nineteen68():
    try:
        requestdata=json.loads(request.data)
        rolename = "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering;"
        queryresult = n68session.execute(rolename)
        res = {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as rolenameexc:
        import traceback
        traceback.print_exc()
        print 'Error in getRoleNameByRoleId_Nineteen68:\n',rolenameexc
        res={'rows':'fail'}
        return jsonify(res)

#utility checks whether user is having projects assigned
@app.route('/login/authenticateUser_Nineteen68/projassigned',methods=['POST'])
def authenticateUser_Nineteen68_projassigned():
    try:
        requestdata=json.loads(request.data)
        if(requestdata["query"] == 'getUserId'):
            authenticateuserprojassigned1= "select userid,defaultrole from users where username = '"+requestdata["username"]+"' allow filtering;"
            queryresult = n68session.execute(authenticateuserprojassigned1)
        elif(requestdata["query"] == 'getUserRole'):
            authenticateuserprojassigned2= "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering;"
            queryresult = n68session.execute(authenticateuserprojassigned2)
        elif(requestdata["query"] == 'getAssignedProjects'):
            authenticateuserprojassigned3= "select projectids from icepermissions where userid = "+requestdata["userid"]+" allow filtering;"
            queryresult = icesession.execute(authenticateuserprojassigned3)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as authenticateuserprojassignedexc:
        print 'Error in authenticateUser_projassigned:\n',authenticateuserprojassignedexc
        res={'rows':'fail'}
        return jsonify(res)

#service for loading user information
@app.route('/login/loadUserInfo_Nineteen68',methods=['POST'])
def loadUserInfo_Nineteen68():
    try:
        requestdata=json.loads(request.data)
        if(requestdata["query"] == 'userInfo'):
            loaduserinfo1 = "select userid, emailid, firstname, lastname, defaultrole, additionalroles, username from users where username = '"+requestdata["username"]+"' allow filtering"
            queryresult = n68session.execute(loaduserinfo1)
        elif(requestdata["query"] == 'loggedinRole'):
            loaduserinfo2 = "select rolename from roles where roleid = "+requestdata["roleid"]+" allow filtering"
            queryresult = n68session.execute(loaduserinfo2)
        elif(requestdata["query"] == 'userPlugins'):
            loaduserinfo3 = "select dashboard,deadcode,mindmap,neuron2d,neuron3d,oxbowcode,reports from userpermissions WHERE roleid = "+requestdata["roleid"]+" allow filtering"
            queryresult = n68session.execute(loaduserinfo3)
        res= {"rows":queryresult.current_rows}
        return jsonify(res)
    except Exception as loaduserinfoexc:
        print 'Error in loadUserInfo_Nineteen68:\n',loaduserinfoexc
        res={'rows':'fail'}
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
    try:
        projecttypename = request.data
        keywordquery="select objecttype, toJson(keywords) from keywords where projecttypename in ('"+projecttypename+"','Generic') ALLOW FILTERING"
        queryresult = icesession.execute(keywordquery)
        resultset=[]
        for eachrow in queryresult.current_rows:
            objecttype = eachrow['objecttype']
            keywords =  eachrow['system.tojson(keywords)']
            eachobject={'objecttype':objecttype,'keywords':keywords}
            resultset.append(eachobject)
        res={'rows':resultset}
        return jsonify(res)
    except Exception as keywordsexc:
        print 'Error in getKeywordDetails:\n',keywordsexc
        res={'rows':'fail'}
        return jsonify(res)

#test case reading service
@app.route('/design/readTestCase_ICE',methods=['POST'])
def readTestCase_ICE():
    try:
        requestdata=json.loads(request.data)
        readtestcasequery = "select testcasesteps,testcasename from testcases where screenid= " + requestdata["screenid"] +" and testcasename='"+requestdata["testcasename"]+"'" +" and versionnumber="+str(requestdata["versionnumber"])+" and testcaseid=" + requestdata["testcaseid"];
        queryresult = icesession.execute(readtestcasequery)
        res= {"rows": queryresult.current_rows}
        return jsonify(res)
    except Exception as readtestcaseexc:
        print 'Error in readTestCase_ICE:\n',readtestcaseexc
        res={'rows':'fail'}
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
    try:
        userrolesquery="select roleid, rolename from roles"
        queryresult = n68session.execute(userrolesquery)
        res={'rows':queryresult.current_rows}
        return jsonify(res)
    except Exception as userrolesexc:
        print 'Error in getUserRoles_Nineteen68:\n',userrolesexc
        res={'rows':'fail'}
        return jsonify(res)

##################################################
# END OF ADMIN SCREEN
##################################################

##################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
##################################################

#encrpytion utility AES
@app.route('/utility/encrypt_ICE/aes',methods=['POST'])
def encrypt_ICE():
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
            print "Invalid input"
            res = "fail"
            return str(res)
    except Exception as e:
        print 'Error in encrypt_ICE:\n',e
        res = "fail"
        return str(res)

##################################################
# END OF UTILITIES
##################################################



if __name__ == '__main__':
##    context = ('cert.pem', 'key.pem')#certificate and key files
##    #https implementation
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context=context)
##    app.run(host='127.0.0.1',port=1990,debug=True,ssl_context='adhoc')

    app.run(host='127.0.0.1',port=1990,debug=True)