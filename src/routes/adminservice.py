################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from bson.objectid import ObjectId
from datetime import datetime
import json
from Crypto.Cipher import AES
import codecs
import uuid

ldap_key = "".join(['l','!','g','#','t','W','3','l','g','G','h','1','3','@','(',
    'c','E','s','$','T','p','R','0','T','c','O','I','-','k','3','y','S'])

def wrap(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex').decode('utf-8')

def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')

def unpad(data):
    return data[0:-ord(data[-1])]

def unwrap(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data, 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def LoadServices(app, redissession, dbsession,licensedata,*args):
    setenv(app)
    ice_das_key=args[0]

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

    @app.route('/admin/getAvailablePlugins',methods=['POST'])
    def getAvailablePlugins():
        app.logger.debug("Inside getAvailablePlugins")
        res={'rows':'fail'}
        try:
            ice_plugins_list = []
            for keys in licensedata['platforms']:
                if(licensedata['platforms'][keys] == True):
                    ice_plugins_list.append(keys)
            res={'rows':ice_plugins_list}
            return jsonify(res)
        except Exception as getallusersexc:
            servicesException("getAvailablePlugins", getallusersexc, True)
            return jsonify(res)


    # Service to create/edit/delete users in Avo Assure
    @app.route('/admin/manageUserDetails',methods=['POST'])
    def manageUserDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action=requestdata["action"]
            del requestdata["action"]
            app.logger.info("Inside manageUserDetails. Query: "+str(action))
            if not isemptyrequest(requestdata):
                if requestdata["name"] in ["support.avoassure","ci_cd"]:
                    app.logger.error("Cannot perform read/write operation on priviliged user: "+requestdata["name"])
                    res={"rows":"forbidden"}
                elif(action=="delete"):
                    result=dbsession.users.delete_one({"name":requestdata['name']})
                    # Delete assigned tasks
                    dbsession.tasks.delete_many({"assignedto":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    dbsession.tasks.delete_many({"owner":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    dbsession.tasks.update_many({"reviewer":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}},{"$set":{"status":"inprogress","reviewer":""}})
                    res={"rows":"success"}
                elif(action=="create"):
                    result=dbsession.users.find_one({"name":requestdata['name']},{"name":1})
                    if result!=None:
                        res={"rows":"exists"}
                    else:
                        requestdata["defaultrole"]=ObjectId(requestdata["defaultrole"])
                        requestdata["createdby"]=ObjectId(requestdata["createdby"])
                        requestdata["createdbyrole"]=ObjectId(requestdata["createdbyrole"])
                        requestdata["modifiedby"]=ObjectId(requestdata["createdby"])
                        requestdata["modifiedbyrole"]=ObjectId(requestdata["createdbyrole"])
                        requestdata["createdon"]=datetime.now()
                        requestdata["modifiedon"]=datetime.now()
                        requestdata["deactivated"]="false"
                        requestdata["addroles"]=[]
                        requestdata["projects"]=[]
                        dbsession.users.insert_one(requestdata)
                        res={"rows":"success"}
                elif (action=="update"):
                    update_query = {
                        "firstname":requestdata["firstname"],
                        "lastname":requestdata["lastname"],
                        "email":requestdata["email"],
                        "addroles":[ObjectId(i) for i in requestdata["additionalroles"]],
                        "auth":requestdata["auth"],
                        "modifiedby":ObjectId(requestdata["createdby"]),
                        "modifiedbyrole":ObjectId(requestdata["createdbyrole"]),
                        "modifiedon":datetime.now()
                    }
                    dbsession.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":update_query})
                    res={"rows":"success"}
                elif (action=="resetpassword"):
                    update_query = {
                        "auth.password":requestdata["password"],
                        "modifiedby":ObjectId(requestdata["modifiedby"]),
                        "modifiedbyrole":ObjectId(requestdata["modifiedbyrole"]),
                        "modifiedon":datetime.now()
                    }
                    dbsession.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":update_query})
                    res={"rows":"success"}
            else:
                app.logger.warn('Empty data received. manage users.')
        except Exception as e:
            servicesException("manageUserDetails", e, True)
        return jsonify(res)

    @app.route('/admin/getUserDetails',methods=['POST'])
    def getUserDetails():
        app.logger.info("Inside getUserDetails")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if "userid" in requestdata:
                    result=dbsession.users.find_one({"_id":ObjectId(requestdata["userid"])},{"name":1,"firstname":1,"lastname":1,"email":1,"defaultrole":1,"addroles":1,"auth":1})
                    if result is not None:
                        if result["name"] in ["support.avoassure","ci_cd"]: result = None
                        else: result["rolename"]=dbsession.permissions.find_one({"_id":result["defaultrole"]})["name"]
                        if "auth" not in result: result["auth"] = {"type": "inhouse"}
                        elif "password" in result["auth"]: del result["auth"]["password"]
                    res={'rows':result}
                else:
                    perms_list = dbsession.permissions.find({},{"_id":1,"name":1})
                    perms = {x["_id"]: x["name"] for x in perms_list}
                    result=list(dbsession.users.find({"name":{"$nin":["support.avoassure","ci_cd"]}},{"_id":1,"name":1,"defaultrole":1}))
                    for i in result:
                        i["rolename"]=perms[i["defaultrole"]]
                    res={'rows':result}
            else:
                app.logger.warn('Empty data received. users fetch.')
        except Exception as e:
            servicesException("getUserDetails", e, True)
        return jsonify(res)

    @app.route('/admin/getUserRoles',methods=['POST'])
    def getUserRoles():
        app.logger.debug("Inside getUserRoles")
        res={'rows':'fail'}
        try:
            requestdata={}
            if request.data:
                requestdata=json.loads(request.data)
            if "id" in requestdata:
                result=list(dbsession.permissions.find({"_id":requestdata["id"]},{"name":1}))
                res={'rows':result}
            else:
                result=list(dbsession.permissions.find({"name":{"$ne":"CI_CD"}},{"_id":1,"name":1}))
                res={'rows':result}
        except Exception as userrolesexc:
            servicesException("getUserRoles", userrolesexc, True)
        return jsonify(res)

    #service renders all the domains in DB
    @app.route('/admin/getDomains_ICE',methods=['POST'])
    def getDomains_ICE():
        app.logger.debug("Inside getDomains_ICE")
        res={'rows':'fail'}
        try:
            result=dbsession.projects.distinct("domain")
            res={'rows':result}
        except Exception as getdomainsexc:
            servicesException("getDomains_ICE", getdomainsexc, True)
        return jsonify(res)

    #service to get token details
    @app.route('/admin/getCIUsersDetails',methods=['POST'])
    def getCIUsersDetails():
        app.logger.debug("Inside getCIUsersDetails")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if "user_id" in requestdata:
                    dbsession.thirdpartyintegration.update_many({"type":"TOKENS","userid":ObjectId(requestdata["user_id"]),"deactivated":"active","expireson":{"$lt":datetime.today()}},{"$set":{"deactivated":"expired"}})
                    query=list(dbsession.thirdpartyintegration.find({"type":"TOKENS","userid":ObjectId(requestdata["user_id"])},{"hash":0}))
                    res={'rows':query}
        except Exception as getCIUserssexc:
            servicesException("getCIUsersDetails", getCIUserssexc, True)
        return jsonify(res)

    @app.route('/admin/manageCIUsers',methods=['POST'])
    def manageCIUsers():
        app.logger.debug("Inside manageCIUsers")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action=requestdata["action"]
            del requestdata["action"]
            if not isemptyrequest(requestdata):
                if action == "create":
                    if all(key in requestdata for key in ('userid', 'hash','name')):
                        query=dbsession.thirdpartyintegration.find_one({"name":requestdata["name"],"userid":ObjectId(requestdata["userid"])})
                        if(query==None):
                            requestdata["projects"]=[]
                            requestdata["userid"]=ObjectId(requestdata["userid"])
                            requestdata["generatedon"]=datetime.now()
                            requestdata["expireson"]=datetime.strptime(str(requestdata["expireson"]),'%d-%m-%Y %H:%M')
                            result=dbsession.thirdpartyintegration.insert_one(requestdata)
                            res= {'rows':{'token':requestdata["hash"]}}
                        else:
                            res={'rows':'duplicate'}
                if action == "deactivate":
                    if all(key in requestdata for key in ('userid','name')):
                        val=dbsession.thirdpartyintegration.find_one({"userid":ObjectId(requestdata["userid"]),"name":requestdata["name"]},{"hash":1})
                        dbsession.thirdpartyintegration.update_one({"hash":val["hash"],"userid":ObjectId(requestdata["userid"])},{"$set":{"deactivated":"deactivated"}})
                        result=list(dbsession.thirdpartyintegration.find({"type":"TOKENS","userid":ObjectId(requestdata["userid"])},{"hash":0}))
                        res={'rows':result}
        except Exception as getCITokensexc:
            servicesException("manageCIUsers", getCITokensexc, True)
        return jsonify(res)

    #service renders the names of all projects in domain/projects (or) projectname
    # releasenames (or) cycle names (or) screennames
    @app.route('/admin/getNames_ICE',methods=['POST'])
    def getNames_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getNames_ICE. Query: "+str(requestdata["type"]))
            if not isemptyrequest(requestdata):
                if requestdata["type"] =="domainsall" :
                    result=list(dbsession.projects.find({"domain":requestdata["id"][0]},{"_id":1,"name":1}))
                    res={'rows':result}
                elif requestdata["type"]=="projects":
                    projectids=[]
                    for i in requestdata["id"]:
                        projectids.append(ObjectId(i))
                    result=list(dbsession.projects.find({"_id":{"$in":projectids}}))
                    res={'rows':result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. generic name details.')
        except Exception as getnamesexc:
            servicesException("getNames_ICE", getnamesexc, True)
        return jsonify(res)

    #service creates a complete project structure into ICE keyspace
    @app.route('/admin/createProject_ICE',methods=['POST'])
    def createProject_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside createProject_ICE. Query: create Project")
            if not isemptyrequest(requestdata):
                requestdata["createdon"]=requestdata["modifiedon"]=datetime.now()
                requestdata["type"]=dbsession.projecttypekeywords.find_one({"name":requestdata["type"]},{"_id":1})["_id"]
                requestdata["createdon"]=requestdata["modifiedon"]=datetime.now()
                requestdata["createdbyrole"]=ObjectId(requestdata["createdbyrole"])
                requestdata["createdby"]=ObjectId(requestdata["createdby"])
                requestdata["modifiedby"]=ObjectId(requestdata["modifiedby"])
                requestdata["modifiedbyrole"]=ObjectId(requestdata["modifiedbyrole"])
                for i in requestdata["releases"]:
                    i["createdon"]=requestdata["createdon"]
                    i["modifiedon"]=requestdata["modifiedon"]
                    i["createdbyrole"]=requestdata["createdbyrole"]
                    i["createdby"]=requestdata["createdby"]
                    i["modifiedby"]=requestdata["modifiedby"]
                    i["modifiedbyrole"]=requestdata["modifiedbyrole"]
                    for j in i["cycles"]:
                        j["_id"]=ObjectId()
                        j["createdon"]=requestdata["createdon"]
                        j["modifiedon"]=requestdata["modifiedon"]
                        j["createdbyrole"]=requestdata["createdbyrole"]
                        j["createdby"]=requestdata["createdby"]
                        j["modifiedby"]=requestdata["modifiedby"]
                        j["modifiedbyrole"]=requestdata["modifiedbyrole"]
                dbsession.projects.insert_one(requestdata)
                res={"rows":"success"}
            else:
                app.logger.warn('Empty data received. create project.')
        except Exception as createprojectexc:
            servicesException("createProject_ICE", createprojectexc, True)
        return jsonify(res)

    #service updates the specified project structure into ICE keyspace
    @app.route('/admin/updateProject_ICE',methods=['POST'])
    def updateProject_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateProject_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata['query'] == 'deleterelease'):
                    # dbsession.projects.update({"id":ObjectId(requestdata["projectid"])},{"$pull":{"releases.name":requestdata["releasename"]}})
                    res={"rows":"success"}
                elif(requestdata['query'] == 'deletecycle'):
                    # dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$pull":{"releases.cycles._id":ObjectId(requestdata["cycleid"]),"releases.cycles.name":requestdata["name"]}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'createrelease'):
                    releases=dbsession.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
                    a={}
                    a["createdby"]=a["modifiedby"]=ObjectId(requestdata["createdby"])
                    a["createdbyrole"]=a["modifiedbyrole"]=ObjectId(requestdata["createdbyrole"])
                    a["createdon"]=a["modifiedon"]=datetime.now()
                    for j in requestdata["cycles"]:
                        j["_id"]=ObjectId()
                        j["createdby"]=j["modifiedby"]=ObjectId(requestdata["createdby"])
                        j["createdbyrole"]=j["modifiedbyrole"]=ObjectId(requestdata["createdbyrole"])
                        j["createdon"]=j["modifiedon"]=datetime.now()
                        del j["newStatus"]
                    a["cycles"]=requestdata["cycles"]
                    a["name"]=requestdata["releasename"]
                    releases.append(a)
                    dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'createcycle'):
                    result=dbsession.projects.find_one({"_id":ObjectId(requestdata["projectid"])},{"releases":1})["releases"]
                    for i in result:
                        if i["name"]== requestdata["releaseid"]:
                            cycles={}
                            cycles["modifiedby"]=cycles["createdby"]=ObjectId(requestdata["createdby"])
                            cycles["modifiedon"]=cycles["createdon"]=datetime.now()
                            cycles["modifiedbyrole"]=cycles["createdbyrole"]=ObjectId(requestdata["createdbyrole"])
                            cycles["_id"]=ObjectId()
                            cycles["name"]=requestdata["name"]
                            i["cycles"].append(cycles)
                    dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":result}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'editrelease'):
                    releases=dbsession.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
                    for i in releases:
                        if i["name"] == requestdata["releasename"]:
                            i["modifiedbyrole"]=ObjectId(requestdata["modifiedbyrole"])
                            i["modifiedby"]=ObjectId(requestdata["modifiedby"])
                            i["modifiedon"]=datetime.now()
                            i["name"]=requestdata["newreleasename"]
                    dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'editcycle'):
                    releases=dbsession.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
                    for i in releases:
                        if i["name"]==requestdata["releaseid"]:
                            cycles=i["cycles"]
                            for j in cycles:
                                if j["_id"]==ObjectId(requestdata["cycleid"]):
                                    j["name"]=requestdata["newcyclename"]
                                    j["modifiedbyrole"]=ObjectId(requestdata["modifiedbyrole"])
                                    j["modifiedby"]=ObjectId(requestdata["modifiedby"])
                                    j["modifiedon"]=datetime.now()
                    dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
                    res={'rows':'success'}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. update project.')
        except Exception as updateprojectexc:
            servicesException("updateProject_ICE", updateprojectexc, True)
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
            app.logger.debug("Inside getDetails_ICE.")
            if not isemptyrequest(requestdata):
                if requestdata["type"] == "domaindetails":
                    result=list(dbsession.projects.find({"domain":requestdata["id"]},{"name":1}))
                    res={"rows":result}
                elif requestdata["type"] == "projectsdetails":
                    result=dbsession.projects.find_one({"_id":ObjectId(requestdata["id"])},{"releases":1,"domain":1,"name":1,"type":1})
                    result["type"]=dbsession.projecttypekeywords.find_one({"_id":result["type"]},{"name":1})["name"]
                    res={"rows":result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. generic details.')
        except Exception as getdetailsexc:
            servicesException("getDetails_ICE", getdetailsexc, True)
        return jsonify(res)

    @app.route('/admin/manageLDAPConfig',methods=['POST'])
    def manageLDAPConfig():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.info("Inside manageLDAPConfig. Action is "+str(requestdata['action']))
            if not isemptyrequest(requestdata):
                query_filter = {"type":"LDAP","name":requestdata["name"]}
                result=dbsession.thirdpartyintegration.find_one(query_filter)
                bc = "bindcredentials"
                if (requestdata['action'] == "delete"):
                    if result != None:
                        dbsession.thirdpartyintegration.delete_one(query_filter)
                    res["rows"] = "success"
                elif (requestdata['action'] == "create"):
                    if result != None: res["rows"] = "exists"
                    else:
                        del requestdata["action"]
                        requestdata[bc] = wrap(requestdata[bc],ldap_key) if bc in requestdata else ''
                        requestdata["fieldmap"]=json.loads(requestdata["fieldmap"])
                        requestdata["type"]="LDAP"
                        dbsession.thirdpartyintegration.insert_one(requestdata)
                        res["rows"] = "success"
                elif (requestdata['action'] == "update"):
                    if result != None:
                        update_query = {
                            "url":requestdata["url"],
                            "basedn":requestdata["basedn"],
                            "secure":requestdata["secure"],
                            "auth":requestdata["auth"],
                            "binddn":requestdata["binddn"],
                            "fieldmap":json.loads(requestdata["fieldmap"])
                        }
                        if "cert" in requestdata: update_query["cert"] = requestdata["cert"]
                        if bc in requestdata: update_query[bc] = wrap(requestdata[bc], ldap_key)
                        dbsession.thirdpartyintegration.update_one(query_filter,{"$set":update_query})
                        res["rows"] = "success"
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. LDAP config manage.')
        except Exception as manageldapexc:
            servicesException("manageLDAPConfig", manageldapexc, True)
        return jsonify(res)

    @app.route('/admin/getLDAPConfig',methods=['POST'])
    def getLDAPConfig():
        app.logger.info("Inside getLDAPConfig")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                query_filter = {"type":"LDAP"}
                if "name" in requestdata:
                    query_filter["name"] = requestdata["name"]
                    result = dbsession.thirdpartyintegration.find_one(query_filter)
                    if result is None: result = []
                    else:
                        if "secure" not in result: result["secure"] = "false"
                        password = result["bindcredentials"]
                        if len(password) > 0:
                            password = unwrap(password, ldap_key)
                            result["bindcredentials"] = password
                else:
                    result = list(dbsession.thirdpartyintegration.find(query_filter,{"name":1}))
                res["rows"] = result
            else:
                app.logger.warn('Empty data received. LDAP config fetch.')
        except Exception as getallusersexc:
            servicesException("getLDAPConfig", getallusersexc, True)
        return jsonify(res)

    @app.route('/admin/manageSAMLConfig',methods=['POST'])
    def manageSAMLConfig():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.info("Inside manageSAMLConfig. Action is "+str(requestdata['action']))
            if not isemptyrequest(requestdata):
                query_filter = {"type":"SAML","name":requestdata["name"]}
                result=dbsession.thirdpartyintegration.find_one(query_filter)
                if requestdata['action'] == "delete":
                    if result != None:
                        dbsession.thirdpartyintegration.delete_one(query_filter)
                    res["rows"] = "success"
                elif (requestdata['action'] == "create"):
                    if result != None: res["rows"] = "exists"
                    else:
                        del requestdata["action"]
                        requestdata["type"]="SAML"
                        dbsession.thirdpartyintegration.insert_one(requestdata)
                        res["rows"] = "success"
                elif (requestdata['action'] == "update"):
                    if result != None:
                        del requestdata["action"]
                        del requestdata["name"]
                        dbsession.thirdpartyintegration.update_one(query_filter,{"$set":requestdata})
                        res["rows"] = "success"
            else:
                app.logger.warn('Empty data received. SAML config manage.')
        except Exception as managesamlexc:
            servicesException("manageSAMLConfig", managesamlexc, True)
        return jsonify(res)

    @app.route('/admin/getSAMLConfig',methods=['POST'])
    def getSAMLConfig():
        app.logger.info("Inside getSAMLConfig")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                query_filter = {"type":"SAML"}
                if "name" in requestdata:
                    query_filter["name"] = requestdata["name"]
                    result = dbsession.thirdpartyintegration.find_one(query_filter)
                    if result is None: result = []
                else:
                    result = list(dbsession.thirdpartyintegration.find(query_filter,{"name":1}))
                res["rows"] = result
            else:
                app.logger.warn('Empty data received. SAML config fetch.')
        except Exception as getsamlexc:
            servicesException("getSAMLConfig", getsamlexc, True)
        return jsonify(res)

    @app.route('/admin/manageOIDCConfig',methods=['POST'])
    def manageOIDCConfig():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.info("Inside manageOIDCConfig. Action is "+str(requestdata['action']))
            if not isemptyrequest(requestdata):
                query_filter = {"type":"OIDC","name":requestdata["name"]}
                result=dbsession.thirdpartyintegration.find_one(query_filter)
                if requestdata['action'] == "delete":
                    if result != None:
                        dbsession.thirdpartyintegration.delete_one(query_filter)
                    res["rows"] = "success"
                elif (requestdata['action'] == "create"):
                    if result != None: res["rows"] = "exists"
                    else:
                        del requestdata["action"]
                        requestdata["type"]="OIDC"
                        dbsession.thirdpartyintegration.insert_one(requestdata)
                        res["rows"] = "success"
                elif (requestdata['action'] == "update"):
                    if result != None:
                        del requestdata["action"]
                        del requestdata["name"]
                        dbsession.thirdpartyintegration.update_one(query_filter,{"$set":requestdata})
                        res["rows"] = "success"
            else:
                app.logger.warn('Empty data received. OIDC config manage.')
        except Exception as manageoidcexc:
            servicesException("manageOIDCConfig", manageoidcexc, True)
        return jsonify(res)

    @app.route('/admin/getOIDCConfig',methods=['POST'])
    def getOIDCConfig():
        app.logger.info("Inside getOIDCConfig")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                query_filter = {"type":"OIDC"}
                if "name" in requestdata:
                    query_filter["name"] = requestdata["name"]
                    result = dbsession.thirdpartyintegration.find_one(query_filter)
                    if result is None: result = []
                else:
                    result = list(dbsession.thirdpartyintegration.find(query_filter,{"name":1}))
                res["rows"] = result
            else:
                app.logger.warn('Empty data received. OIDC config fetch.')
        except Exception as getoidcexc:
            servicesException("getOIDCConfig", getoidcexc, True)
        return jsonify(res)

    #service assigns projects to a specific user
    @app.route('/admin/assignProjects_ICE',methods=['POST'])
    def assignProjects_ICE():
        app.logger.debug("Inside assignProjects_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                domains=dbsession.projects.distinct("domain")
                project={}
                for i in domains:
                    projects=list(dbsession.projects.find({"domain":i},{"_id":1}))
                    project[i]=[]
                    for j in projects:
                        project[i].append(j["_id"])
                assigned_pro=dbsession.users.find_one({"_id":ObjectId(requestdata["userid"])},{"projects":1})["projects"]
                if (requestdata['alreadyassigned'] != True):
                    projects=assigned_pro
                    for i in requestdata["projectids"]:
                        projects.append(ObjectId(i))
                    result=dbsession.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"projects":projects}})
                    res={'rows':'success'}
                elif (requestdata['alreadyassigned'] == True):
                    result=[]
                    for i in requestdata["projectids"]:
                        result.append(ObjectId(i))
                    diff_pro=list(set(assigned_pro) - set(result))
                    remove_pro=[]
                    for k,v in project.items():
                        for i in range(0,len(diff_pro)):
                            if k != requestdata["domainid"] and diff_pro[i] in v:
                                result.append(diff_pro[i])
                            elif k == requestdata["domainid"] and diff_pro[i] in v:
                                remove_pro.append(diff_pro[i])

                    result=dbsession.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"projects":result}})
                    dbsession.tasks.delete_many({"projectid":{"$in":remove_pro},"assignedto":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    dbsession.tasks.delete_many({"projectid":{"$in":remove_pro},"owner":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    dbsession.tasks.update_many({"projectid":{"$in":remove_pro},"reviewer":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}},{"$set":{"status":"inprogress","reviewer":""}})
                    res={'rows':'success'}
                else:
                   res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. assign projects.')
        except Exception as assignprojectsexc:
            servicesException("assignProjects_ICE", assignprojectsexc, True)
        return jsonify(res)

    #service fetches projects assigned to user.
    @app.route('/admin/getAssignedProjects_ICE',methods=['POST'])
    def getAssignedProjects_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getAssignedProjects_ICE. Query: "
                +str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata['query'] == 'projectid'):
                    result=dbsession.users.find_one({"_id":ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
                    res={"rows":result}
                elif(requestdata['query'] == 'projectname'):
                    projectids=[]
                    for i in requestdata["projectid"]:
                        projectids.append(ObjectId(i))
                    result=list(dbsession.projects.find({"_id":{"$in":projectids},"domain":requestdata["domain"]},{"name":1}))
                    res={"rows":result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. assigned projects.')
        except Exception as e:
            servicesException("getAssignedProjects_ICE", e, True)
        return jsonify(res)

    @app.route('/admin/getUsers',methods=['POST'])
    def getUsers():
        app.logger.debug("Inside getUsers")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result=list(dbsession.users.find({"projects":{"$in":[ObjectId(requestdata["projectid"])]}},{"name":1,"defaultrole":1,"addroles":1}))
                res={"rows":result}
            else:
                app.logger.warn('Empty data received. get users - Mind Maps.')
        except Exception as getUsersexc:
            servicesException("getUsers", getUsersexc, True)
        return jsonify(res)

    @app.route('/admin/getPreferences',methods=['POST'])
    def getPreferences():
        app.logger.debug("Inside getPreferences")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result = list(dbsession.permissions.find({"name":{"$ne":"CI_CD"}},{"name":1,"plugins":1,"_id":0}))
                res = {'rows':result}
            else:
                app.logger.warn('Empty data received. get user preferences.')
        except Exception as getdomainsexc:
            servicesException("getPreferences", getdomainsexc, True)
        return jsonify(res)

    @app.route('/admin/fetchICE',methods=['POST'])
    def fetchICE():
        app.logger.debug("Inside fetchICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                find_args = {}
                if "user" in requestdata:
                    find_args["provisionedto"] = ObjectId(requestdata["user"])
                result=list(dbsession.icetokens.find(find_args))
                user_ids=[i["provisionedto"] for i in result if "provisionedto" in i]
                result1=list(dbsession.users.find({"_id":{"$in":user_ids}},{"name":1}))
                user_ids={x["_id"]: x["name"] for x in result1}
                for row in result:
                    if row["icetype"]=="normal":
                        prv_to = row["provisionedto"]
                        if prv_to in user_ids: row["username"] = user_ids[prv_to]
                        else:
                            dbsession.icetokens.delete_one({"_id": row["_id"]})
                            row["provisionedto"] = "--Deleted--"
                    else: row["username"]="N/A"
                res={'rows':result}
            else:
                app.logger.warn('Empty data received. get ice provisions.')
        except Exception as fetchICEexc:
            servicesException("fetchICE", fetchICEexc, True)
        return jsonify(res)

    @app.route('/admin/provisionICE',methods=['POST'])
    def iceprovisions():
        app.logger.debug("Inside provisions")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                query = str(requestdata.pop("query"))
                app.logger.debug("Inside provisionICE. Query: "+query)
                token=str(uuid.uuid4())
                token_query={"icetype": requestdata["icetype"], "icename": requestdata["icename"]}
                token_exists = len(list(dbsession.icetokens.find(token_query, {"icename":1})))!=0
                if query==PROVISION:
                    requestdata["token"]=token
                    requestdata["status"]=PROVISION_STATUS
                    requestdata[PROVISION_STATUS+"on"]=datetime.now()
                    user_notexists = True
                    #To restrict multiple ICE provsioning for the same user
                    if requestdata["icetype"]=="normal":
                        requestdata["provisionedto"]=ObjectId(requestdata["provisionedto"])
                        user_notexists = len(list(dbsession.icetokens.find({"provisionedto":requestdata["provisionedto"]},{"provisionedto":1})))==0
                    if not token_exists and user_notexists:
                        #currently only icetype and user combination is unique
                        dbsession.icetokens.insert_one(requestdata)
                        enc_token=wrap(token+'@'+requestdata["icetype"]+'@'+requestdata["icename"],ice_das_key)
                        res["rows"] = enc_token
                    else:
                        res["rows"] = "DuplicateIceName"
                elif query == DEREGISTER:
                    if token_exists:
                        dbsession.icetokens.update_one(token_query,{"$set":{"status":DEREGISTER_STATUS,"deregisteredon":datetime.now()}})
                        res["rows"] = 'success'
                elif query == 're'+REGISTER:
                    if token_exists:
                        dbsession.icetokens.update_one(token_query,{"$set":{"status":PROVISION_STATUS,"token":token,"provisionedon":datetime.now()}})
                        enc_token = wrap(token+'@'+requestdata["icetype"]+'@'+requestdata["icename"],ice_das_key)
                        res["rows"] = enc_token
            else:
                app.logger.warn('Empty data received. provisionICE - Admin.')
        except Exception as provisionICEexc:
            servicesException("provisionICE", provisionICEexc, True)
        return jsonify(res)