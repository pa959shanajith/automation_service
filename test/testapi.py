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
auth = PlainTextAuthProvider(username='nineteen68', password='TA@SLK2017')
c = Cluster(['10.41.31.130'],auth_provider=auth)

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
##    requestdata=request.data
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
##			"screenid": "47ab4fe1-2114-4e67-8e89-ecefc2a99872",
##			"testcasename":"BatchExecution_TestCase1",
##			"testcaseid" : "74a090e4-0f67-4727-9229-6fa2f6112021",
##            "versionnumber" : 1
##		}
##    response = readTestCase_ICE(data)
##    print response
#   ----------------------------

#########################
# TEST COMPONENTS END
#########################