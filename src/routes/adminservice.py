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
    ice_das_key = args[0]
    ldap_key = args[1]
    defcn = ['@Window', '@Object', '@System', '@Excel', '@Mobile', '@Android_Custom', '@Word', '@Custom', '@CustomiOS',
             '@Generic', '@Browser', '@Action', '@Email', '@BrowserPopUp', '@Sap','@Oebs', 'WebService List', 'Mainframe List', 'OBJECT_DELETED']

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
                elif(requestdata['query'] == 'updateprojectname'):
                    dbsession.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"name":requestdata["newprojectname"],"modifiedbyrole":ObjectId(requestdata["modifiedbyrole"]),"modifiedby":ObjectId(requestdata["modifiedby"]),"modifiedon":datetime.now()}})
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
                elif requestdata["type"] == "all":
                    project_list = {}
                    result=dbsession.projects.find({},{"_id":1,"name":1,"domain":1,"type":1})
                    for project in result:
                        project_list[str(project["_id"])] = project
                    res["rows"] = project_list
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
                    requestdata["poolid"] = "None"
                    requestdata[PROVISION_STATUS+"on"]=datetime.now()
                    #user_notexists = True
                    #To restrict multiple ICE provsioning for the same user
                    if requestdata["icetype"]=="normal":
                        requestdata["provisionedto"]=ObjectId(requestdata["provisionedto"])
                        #user_notexists = len(list(dbsession.icetokens.find({"provisionedto":requestdata["provisionedto"]},{"provisionedto":1})))==0
                    if not token_exists: # and user_notexists
                        #currently only icetype and user combination is unique
                        dbsession.icetokens.insert_one(requestdata)
                        enc_token=wrap(token+'@'+requestdata["icetype"]+'@'+requestdata["icename"],ice_das_key)
                        res["rows"] = enc_token
                    else:
                        res["rows"] = "DuplicateIceName"
                elif query == DEREGISTER:
                    if token_exists:
                        dbsession.icetokens.update_one(token_query,{"$set":{"status":DEREGISTER_STATUS,"deregisteredon":datetime.now(),"poolid":"None"}})
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

    @app.route('/admin/manageNotificationChannels',methods=['POST'])
    def manageNotificationChannels():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action = str(requestdata['action'])
            channel = str(requestdata['channel'] if 'channel' in requestdata else '')
            app.logger.info("Inside manageNotificationChannels. Action is "+action+". Channel is "+channel)
            if not isemptyrequest(requestdata):
                query_filter = {"channel":channel,"name":requestdata["name"]}
                result=dbsession.notifications.find_one(query_filter)
                if result is None:
                    if action == "create":
                        del requestdata["action"]
                        requestdata["active"] = True
                        if requestdata["auth"] and type(result["auth"]) != bool and "password" in requestdata["auth"]:
                            requestdata["auth"]["password"] = wrap(requestdata["auth"]["password"],ldap_key)
                        dbsession.notifications.insert_one(requestdata)
                        res["rows"] = "success"
                    else:
                        res["rows"] = "dne"
                else:
                    if action == "create": res["rows"] = "exists"
                    elif action == "disable":
                        dbsession.notifications.update_one(query_filter,{"$set":{"active":False}})
                        res["rows"] = "success"
                    elif action == "enable":
                        dbsession.notifications.update_one(query_filter,{"$set":{"active":True}})
                        res["rows"] = "success"
                    elif action == "delete":
                        dbsession.notifications.delete_one(query_filter)
                        res["rows"] = "success"
                    elif action == "update":
                        del requestdata["action"]
                        del requestdata["name"]
                        if requestdata["auth"] and type(requestdata["auth"]) != bool and "password" in requestdata["auth"]:
                            requestdata["auth"]["password"] = wrap(requestdata["auth"]["password"],ldap_key)
                        if requestdata["proxy"] and "pass" in requestdata["proxy"]:
                            requestdata["proxy"]["pass"] = wrap(requestdata["proxy"]["pass"],ldap_key)
                        dbsession.notifications.update_one(query_filter,{"$set":requestdata})
                        res["rows"] = "success"
            else:
                app.logger.warn('Empty data received. Noifications channels manage.')
        except Exception as managenotfexec:
            servicesException("manageNotificationChannels", managenotfexec, True)
        return jsonify(res)

    @app.route('/admin/getNotificationChannels',methods=['POST'])
    def getNotificationChannels():
        app.logger.info("Inside getNotificationChannels")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action = str(requestdata['action'])
            channel = str(requestdata['channel'] if 'channel' in requestdata else '')
            if not isemptyrequest(requestdata):
                query_filter = {"channel":channel}
                data_filter = None
                name = requestdata["name"] if "name" in requestdata else ""
                if action == "provider": query_filter["provider"] = name
                elif action == "list":
                    query_filter = {}
                    if "filter" in requestdata and requestdata["filter"] == "active": query_filter["active"] = True
                    # data_filter = {"name":1,"provider":1,"channel":1}
                else: query_filter["name"] = name
                result = list(dbsession.notifications.find(query_filter, data_filter))
                for row in result:
                    if "auth" in row and type(row["auth"]) != bool and "password" in row["auth"]:
                        password = row["auth"]["password"]
                        if len(password) > 0:
                            password = unwrap(password, ldap_key)
                            row["auth"]["password"] = password
                    if "proxy" in row and "pass" in row["proxy"]:
                        password = row["proxy"]["pass"]
                        if len(password) > 0:
                            password = unwrap(password, ldap_key)
                            row["proxy"]["pass"] = password
                res["rows"] = result
            else:
                app.logger.warn('Empty data received. Noifications channels fetch.')
        except Exception as getnotfexc:
            servicesException("getNotificationChannels", getnotfexc, True)
        return jsonify(res)

    def update_steps(steps,dataObjects):
        del_flag = False
        try:
            for j in steps:
                j['objectName'], j['url'], j['addTestCaseDetailsInfo'], j['addTestCaseDetails'] = '', '', '', ''
                if 'addDetails' in j:
                    j['addTestCaseDetailsInfo'] = j['addDetails']
                    del j['addDetails']
                if j['custname'] == "@Custom":
                    j['objectName'] = "@Custom"
                    continue
                if 'custname' in j.keys():
                    if j['custname'] in dataObjects.keys():
                        j['objectName'] = dataObjects[j['custname']]['xpath']
                        j['url'] = dataObjects[j['custname']]['url'] if 'url' in dataObjects[j['custname']] else ""
                        j['cord'] = dataObjects[j['custname']]['cord'] if 'cord' in dataObjects[j['custname']] else ""
                        if 'original_device_width' in dataObjects[j['custname']].keys():
                            j['original_device_width'] = dataObjects[j['custname']]['original_device_width']
                            j['original_device_height'] = dataObjects[j['custname']]['original_device_height']
                        j['custname'] = dataObjects[j['custname']]['custname']
                    elif (j['custname'] not in defcn or j['custname']=='OBJECT_DELETED'):
                        j['custname'] = 'OBJECT_DELETED'
                        if j['outputVal'].split(';')[-1] != '##':
                            del_flag = True
        except Exception as e:
            servicesException('exportProject', e, True)
        return del_flag

    @app.route('/admin/exportProject',methods=['POST'])
    def exportProject():
        app.logger.debug("Inside exportProject")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                projectId = ObjectId(requestdata['projectId'])
                del_flag = False
                del_testcases = []
                mindMapsList = list(dbsession.mindmaps.find({'projectid':projectId},{"projectid":1,"name":1,"versionnumber":1,"deleted":1,"type":1,"testscenarios":1}))
                for i in mindMapsList:
                    scenarios = [s['_id'] for s in i['testscenarios']]
                    i['screens'] = []
                    i['testcases'] = []
                    screenList = list(dbsession.screens.find({'parent':{"$in":scenarios}}))
                    testcaseList = []
                    for j in screenList:
                        dataobj_query = list(dbsession.dataobjects.find({"parent" :j['_id']}))
                        if "scrapeinfo" in j and 'header' in j["scrapeinfo"]:
                            screen_json = j['scrapeinfo'] if 'scrapeinfo' in j else {}
                            screen_json["reuse"] = True if(len(j["parent"])>1) else False
                            screen_json["view"] = dataobj_query
                            screen_json["name"] = j["name"]
                        else:
                            screen_json = { "view": dataobj_query, "name":j["name"],
                                            "createdthrough": (j["createdthrough"] if ("createdthrough" in j) else ""),
                                            "scrapedurl": (j["scrapedurl"] if ("scrapedurl" in j) else ""),
                                            "mirror": (j["screenshot"] if ("screenshot" in j) else ""),
                                            "reuse": True if(len(j["parent"])>1) else False
                                        }
                        app_type=dbsession.projects.find_one({'_id':j["projectid"]},{'type':1})['type']
                        screen_json["appType"] = dbsession.projecttypekeywords.find_one({'_id':app_type},{'name':1})['name']
                        screen_json["screenId"] = j['_id']
                        i['screens'].append(screen_json)
                        dataObjects = {}
                        if (dataobj_query != []):
                            for dos in dataobj_query:
                                if 'custname' in dos: dos['custname'] = dos['custname'].strip()
                                dataObjects[dos['_id']] = dos
                        testcaseList = list(dbsession.testcases.find({'screenid':j['_id']},{'screenid':1,'steps':1,'name':1,'parent':1}))
                        for k in testcaseList:
                            del_flag = update_steps(k['steps'],dataObjects)
                        i['testcases'] += testcaseList
                res =  {'rows': mindMapsList}
            else:
                app.logger.warn('Empty data received. exportProject - Admin.')
        except Exception as exportProjectexc:
            servicesException("exportProject", exportProjectexc, True)
        return jsonify(res)

    #Create a new ICE pool
    @app.route('/admin/createPool_ICE',methods=['POST'])
    def create_pool():
        app.logger.debug("Inside pool create")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        inputdata = {}
        error = True
        try:
            result = dbsession.icepools.find({"poolname":requestdata['poolname']})
            index = result.count() - 1
            result = None
            if index >= 0:
                result = "Pool exists"
            elif result == None or result.count() == 0:
                current_time = datetime.now()
                inputdata["poolname"] = requestdata["poolname"]
                inputdata['createdby'] = ObjectId(requestdata["createdby"])
                inputdata['createdon'] = current_time
                inputdata['projectids'] = convert_objectids(requestdata['projectids'])
                inputdata['modifiedby'] = ObjectId(requestdata["createdby"])
                inputdata['modifiedon'] = current_time
                inputdata['createdbyrole'] = ObjectId(requestdata['createdbyrole'])
                inputdata['modifiedbyrole'] =  ObjectId(requestdata['createdbyrole'])
                dbsession.icepools.insert_one(inputdata)
                result = "success"
            res['rows'] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("create_pool",e)
        return jsonify(res)

    #Get ICE which are unassigned
    @app.route('/admin/getUnassgined_ICE',methods=['POST'])
    def get_unassigned_ICE():
        app.logger.debug("Inside get unassigned ICE")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        result = []
        projectids = convert_objectids(requestdata['projectids'])
        try:
            project_users = dbsession.users.find({"projects": { "$in": projectids}})
            for user in project_users:
                user_ice = dbsession.icetokens.find({"provisionedto":user["_id"],"poolid":{"$ne":"None"}})
                for ice in user_ice:
                    result.append(ice["icename"])
            ci_cd_ice = dbsession.icetokens.find({"icetype":"ci-cd","poolid":{"$ne":"None"}})
            for ice in ci_cd_ice:
                result.append(ice["icename"])
            res["rows"] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("configure_pool",e)
        return jsonify(res)


    @app.route('/admin/deleteICE_pools',methods=['POST'])
    def deleteICE_pools():
        app.logger.debug("Inside get all projects")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        poolids = convert_objectids(requestdata['poolids'])
        try:
            for pool in poolids:
                dbsession.icepools.delete_one({"_id":pool})
                ice_list = dbsession.icetokens.update_many({"poolid":pool},{"$set":{"poolid":"None"}})
            res["rows"] = "success"
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("get_all_projects",e)
        return jsonify(res)

    @app.route('/admin/getAvailable_ICE',methods=['POST'])
    def get_available_ICE():
        app.logger.debug("Inside get get available ICE")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        result = {}
        result['available_ice'] = {}
        result['unavailable_ice'] = {}
        try:
            unavailable_ice = dbsession.icetokens.find({"poolid":{"$ne":"None"}})
            available_ice = dbsession.icetokens.find({"poolid":"None"})
            for ice in available_ice:
                result['available_ice'][str(ice["_id"])] = ice
            for ice in unavailable_ice:
                result['unavailable_ice'][str(ice["_id"])] = ice
            res["rows"] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("configure_pool",e)
        return jsonify(res) 

    #Get all ICE in a list of pools (list of Pool => all ICE in all the pools) (one pool in list => all ICE in that pool)
    @app.route('/admin/getICE_pools',methods=['POST'])
    def get_ICE_in_pools():
        app.logger.debug("Inside get ice in pools")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        result = {}
        ice_list = []
        poolids = requestdata['poolids']
        try:
            for pool in poolids:
                ice_list = dbsession.icetokens.find({"poolid":ObjectId(pool)})
                for ice in ice_list:
                    result[str(ice["_id"])] = ice
            res["rows"] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("configure_pool",e)
        return jsonify(res)  

    #Get all ICE in a list of pools (list of Pool => all ICE in all the pools) (one pool in list => all ICE in that pool)
    @app.route('/admin/getICE_userid',methods=['POST'])
    def get_ICE_by_userid():
        app.logger.debug("Inside get ice by username")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        result = {}
        userid = requestdata['userid']
        ice_list = []
        poolids = requestdata['poolids']
        try:
            ice_list = dbsession.icetokens.find({"provisionedto":ObjectId(userid)})
            for ice in ice_list:
                if not ice["poolid"] or str(ice["poolid"]) in poolids or str(ice["poolid"]) == "None":
                    result[str(ice["_id"])] = ice
            res["rows"] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("configure_pool",e)
        return jsonify(res)       

    #Get all pools corresponding to a project or a pool id
    @app.route('/admin/getPools',methods=['POST'])
    def get_pools():
        app.logger.debug("Inside get pools in projects")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        result = {}
        pool_list = []
        projectids = convert_objectids(requestdata['projectids'])
        poolid = requestdata["poolid"]
        try:
            if projectids is not None and len(projectids) > 0:
                pool_list = dbsession.icepools.find({"projectids":{"$in":projectids}})
            elif poolid is not None and poolid == "all":
                pool_list = dbsession.icepools.find({})
            elif poolid is not None:
                pool_list = dbsession.icepools.find({"_id":ObjectId(poolid)})
            for pool in pool_list:
                ice_list = get_ice([pool["_id"]])
                pool["ice_list"] = ice_list
                result[str(pool["_id"])] = pool
            res["rows"] = result
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("get_pools",e)
        return jsonify(res) 

    #ADD/DELETE ICE from pool, ADD/DELETE projects from pool, Update poolname
    @app.route('/admin/updatePool_ICE',methods=['POST'])
    def update_pool():
        app.logger.debug("Inside get pool")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        poolid = requestdata["poolid"]
        addition = requestdata["ice_added"]
        deletion = requestdata["ice_deleted"]
        poolname = requestdata["poolname"]
        projectids = convert_objectids(requestdata["projectids"])
        modifiedby = requestdata["modifiedby"]
        modifiedbyrole = requestdata["modifiedbyrole"]
        try:
            pool = dbsession.icepools.find({"_id":ObjectId(poolid)})
            if not pool or pool.count() == 0:
                res["rows"] = "Pool does not exist"; 
            else:
                pool = pool[0]
                updatePoolid_ICE(pool["_id"], addition, deletion)
                if projectids is not None:
                    pool["projectids"] = projectids 
                pool['modifiedon'] = datetime.now()
                pool['modifiedby'] = ObjectId(modifiedby)
                pool['modifiedbyrole'] = ObjectId(modifiedbyrole)
                if poolname is not None and poolname != pool['poolname']:
                    existing_pools = dbsession.icepools.find({"poolname":poolname})
                    if existing_pools and existing_pools.count() > 0:
                        res["rows"] = "Pool exists"
                    else:
                        pool['poolname'] = requestdata["poolname"]
                        dbsession.icepools.update_one({"_id":pool["_id"]},{"$set":pool})
                        res["rows"] = "success"
                else:
                    dbsession.icepools.update_one({"_id":pool["_id"]},{"$set":pool})
                    res["rows"] = "success"
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("configure_pool",e)
        return jsonify(res) 

    def check_array_exists(data_arr):
        if data_arr is not None and len(data_arr) > 0:
            return True
        return False

    def updatePoolid_ICE(poolid = "", addition = [], deletion = []):
        if check_array_exists(addition):
            for id in addition:
                dbsession.icetokens.update_one({"_id":ObjectId(id)},{"$set":{"poolid":poolid}})
        if check_array_exists(deletion):
            for id in deletion:
                dbsession.icetokens.update_one({"_id":ObjectId(id)},{"$set":{"poolid":"None"}})

    def convert_objectids(projectids):
        objectids = []
        for project in projectids:
            objectids.append(ObjectId(project))
        return objectids

    def get_ice(poolids):
        result = {}
        for pool in poolids:
                ice_list = dbsession.icetokens.find({"poolid":ObjectId(pool)})
                for ice in ice_list:
                    result[str(ice["_id"])] = ice
            
        return result