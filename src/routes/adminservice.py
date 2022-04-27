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
            res={'rows':licensedata['platforms']}
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
                        if requestdata["auth"]["type"] in ["inhouse", "ldap"]:
                            requestdata["invalidCredCount"]=0
                            requestdata["auth"]["passwordhistory"]=[]
                            requestdata["auth"]["defaultpasstime"]=""
                            requestdata["auth"]["defaultpassword"]=""
                            requestdata["auth"]["verificationpasstime"]=""
                            requestdata["auth"]["verificationpassword"]=""
                        dbsession.users.insert_one(requestdata)
                        res={"rows":"success"}
                elif (action=="update"):
                    if(requestdata["auth"]["password"] == "" and requestdata["auth"]["type"] == "inhouse" ):
                        result=dbsession.users.find_one({"_id":ObjectId(requestdata["userid"])})["auth"]["password"]
                        requestdata["auth"]["password"] = result;
                    update_query = {
                        "firstname":requestdata["firstname"],
                        "lastname":requestdata["lastname"],
                        "email":requestdata["email"],
                        "addroles":[ObjectId(i) for i in requestdata["additionalroles"]],
                        "modifiedby":ObjectId(requestdata["createdby"]),
                        "modifiedbyrole":ObjectId(requestdata["createdbyrole"]),
                        "modifiedon":datetime.now(),
                    }
                    result=dbsession.users.find_one({"_id":ObjectId(requestdata["userid"])})
                    au = result["auth"]
                    if "oldPassword" in requestdata:
                        au["passwordhistory"]=(au["passwordhistory"] + [au["password"]])[-4:]
                        update_query["invalidCredCount"]=0
                    for key in requestdata["auth"]:
                        au[key] = requestdata["auth"][key]
                    update_query["auth"] = au
                    dbsession.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":update_query})
                    res={"rows":"success"}
                elif (action=="resetpassword"):
                    result=dbsession.users.find_one({"name":requestdata["name"]})
                    modifiedby = ObjectId(requestdata.get("modifiedby", result["_id"]))
                    modifiedbyrole = ObjectId(requestdata.get("modifiedbyrole", result["defaultrole"]))
                    update_query = {
                        "modifiedby": modifiedby,
                        "modifiedbyrole": modifiedbyrole,
                        "modifiedon": datetime.now()
                    }
                    au = result["auth"]
                    au["passwordhistory"]=(au["passwordhistory"] + [au["password"]])[-4:]
                    au["password"] = requestdata["password"]
                    au["defaultpassword"] = ""
                    update_query["invalidCredCount"]=0
                    update_query["auth"] = au
                    dbsession.users.update_one({"_id":result["_id"]},{"$set":update_query})
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

    @app.route('/admin/fetchLockedUsers',methods=['POST'])
    def fetchLockedUsers():
        app.logger.info("Inside fetchLockedUsers")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result = list(dbsession.users.find({'invalidCredCount': 5}))
                res={'rows':result}
            else:
                app.logger.warn('Empty data received. users fetch.')
        except Exception as e:
            servicesException("fetchLockedUsers", e, True)
        return jsonify(res)

    @app.route('/admin/unlockUser',methods=['POST'])
    def unlockUser():
        app.logger.info("Inside unlockUser")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                up_data = {
                    "invalidCredCount": 0,
                    "auth.verificationpassword": "",
                    "auth.verificationpasstime": ""
                }
                dbsession.users.update_one({'name':requestdata['username']},{"$set":up_data})
                res={'rows': 'success'}
            else:
                app.logger.warn('Empty data received. user unlock.')
        except Exception as e:
            servicesException("unlockUser", e, True)
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
                        query=dbsession.thirdpartyintegration.find_one({"type":"TOKENS","name":requestdata["name"],"userid":ObjectId(requestdata["userid"])})
                        if(query==None):
                            requestdata["projects"]=[]
                            requestdata["userid"]=ObjectId(requestdata["userid"])
                            requestdata["generatedon"]=datetime.now()
                            requestdata["expireson"]=datetime.strptime(str(requestdata["expireson"]),"%Y-%m-%dT%H:%M:%S.%fZ")
                            result=dbsession.thirdpartyintegration.insert_one(requestdata)
                            res= {'rows':{'token':requestdata["hash"]}}
                        else:
                            res={'rows':'duplicate'}
                if action == "deactivate":
                    if all(key in requestdata for key in ('userid','name')):
                        val=dbsession.thirdpartyintegration.find_one({"type":"TOKENS","userid":ObjectId(requestdata["userid"]),"name":requestdata["name"]},{"hash":1})
                        dbsession.thirdpartyintegration.update_one({"type":"TOKENS","hash":val["hash"],"userid":ObjectId(requestdata["userid"])},{"$set":{"deactivated":"deactivated"}})
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
                if requestdata["type"] == "gitdomaindetails":
                    prj_list = []
                    rdata = requestdata['id']
                    result=dbsession.users.find_one({"_id":ObjectId(rdata["userid"])},{"projects":1,"_id":0})
                    for i in result['projects']:
                        result1=dbsession.projects.find_one({"_id":ObjectId(i),"domain":rdata["domainname"]},{"name":1})
                        if result1: prj_list.append(result1)
                    res={"rows":prj_list}
                elif requestdata["type"] == "domaindetails":
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
                res = {'rows':licensedata['plugins']}
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
                token_query={"icename": requestdata["icename"], "icetype": requestdata["icetype"]}
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
        
    #Saving Git configuration
    @app.route('/admin/gitSaveConfig',methods=['POST'])
    def gitSaveConfig():
        app.logger.debug("Saving Git Configuration")
        requestdata=json.loads(request.data)
        res={'rows':'fail'}
        data={}
        try:
            #check whether the git configuration name is unique
            chk_gitname = dbsession.gitconfiguration.find_one({"name":requestdata["gitConfigName"]},{"name":1})
            if chk_gitname!=None and requestdata["action"]=='create':
                res={"rows":"GitConfig exists"}
                return res
            result = dbsession.gitconfiguration.find_one({"gituser":ObjectId(requestdata["userId"]),"projectid":ObjectId(requestdata["projectId"])},{"_id":1})
            
            current_time = datetime.now()
            if requestdata["action"]=='create':
                if result!=None:
                    res={"rows":"GitUser exists"}
                    return res
                else:
                    data['name'] = requestdata["gitConfigName"]
                    data['gituser'] = ObjectId(requestdata["userId"])
                    data['projectid'] = ObjectId(requestdata["projectId"])
                    data['createdon'] = current_time
                    data['modifiedon'] = current_time
                    data['gitaccesstoken'] = wrap(requestdata["gitAccToken"],ldap_key)
                    data['giturl']= requestdata["gitUrl"]
                    data['gitusername']=requestdata["gitUsername"]
                    data['gituseremail']=requestdata["gitEmail"]
                    dbsession.gitconfiguration.insert_one(data)
                    res1 = "success"
            elif requestdata["action"]=='update':
                data['name'] = requestdata["gitConfigName"]
                data['modifiedon'] = current_time
                data['gitaccesstoken'] = wrap(requestdata["gitAccToken"],ldap_key)
                data['giturl']= requestdata["gitUrl"]
                data['gituseremail']=requestdata["gitEmail"]
                data['gitusername']=requestdata["gitUsername"]
                dbsession.gitconfiguration.update_one({"_id":ObjectId(result["_id"])},{"$set":data})
                res1 = "success"
            elif requestdata["action"]=="delete":
                if result!=None:
                    dbsession.gitconfiguration.delete_one({"_id":result["_id"]})
                res1 = "success"
            res['rows'] = res1
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("gitSaveConfig",e)
        return jsonify(res)

    #Fetch all gitUser data - Edit git
    @app.route('/admin/gitEditConfig', methods=['POST'])
    def gitEditConfig():
        app.logger.info("Inside gitEditConfig")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result=dbsession.gitconfiguration.find_one({"gituser":ObjectId(requestdata["userId"]),"projectid":ObjectId(requestdata["projectId"])},{'name':1, 'gitaccesstoken':1, 'giturl':1, 'gitusername':1,'gituseremail':1, '_id':0})
                if result:
                    result['gitaccesstoken'] = unwrap(result['gitaccesstoken'],ldap_key)
                    res={'rows':result}
                else:
                    res={'rows':"empty"}    
            else:
                app.logger.warn('Empty data received in git user fetch.')
        except Exception as e:
            servicesException("gitEditConfig",e)
        return jsonify(res)

    #Fetch JIRA data 
    @app.route('/admin/getDetails_JIRA', methods=['POST'])
    def getDetails_JIRA():
        app.logger.info("Inside getDetails_JIRA")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result=dbsession.userpreference.find_one({"user":ObjectId(requestdata["userId"])}, {'JIRA':1, '_id':0})
                if result:
                    res={'rows':result['JIRA']}
                else:
                    res={'rows':"empty"}    
            else:
                app.logger.warn('Empty data received in getDetails_JIRA fetch.')
        except Exception as e:
            servicesException("getDetails_JIRA",e)
        return jsonify(res)

    #manage JIRA Details
    @app.route('/admin/manageJiraDetails',methods=['POST'])
    def manageJiraDetails():
        app.logger.info("Inside manageJiraDetails")
        res={'rows':'fail'}
        data={}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result = dbsession.userpreference.find_one({"user":ObjectId(requestdata["userId"])}, {'_id':1})
                result1 = dbsession.userpreference.find_one({"user":ObjectId(requestdata["userId"]), 'JIRA':{'$exists':True, '$ne': None}})
                if requestdata["action"]=="delete":
                    res1 = "success"
                    if result==None:
                        res1 = "fail"
                    elif result1!=None:
                        dbsession.userpreference.update_one({"_id":result["_id"]},{"$unset":{ 'JIRA':""}})
                elif requestdata["action"]=='create':
                    if result1!=None:
                        res1 = "fail"
                    else:
                        if result==None:
                            data['user'] = ObjectId(requestdata["userId"])
                            data['JIRA'] = { 'api': requestdata["jiraAPI"], 'username': requestdata["jiraUsername"] , 'url': requestdata["jiraUrl"]}
                            dbsession.userpreference.insert_one(data)
                            res1 = "success"
                        else:
                            data['JIRA'] = { 'api': requestdata["jiraAPI"], 'username': requestdata["jiraUsername"] , 'url': requestdata["jiraUrl"]}
                            dbsession.userpreference.update_one({"_id":ObjectId(result["_id"])},{"$set":data})
                            res1 = "success"
                elif requestdata["action"]=='update':
                    if result==None:
                        res1 = "fail"
                    else:
                        data['JIRA'] = { 'api': requestdata["jiraAPI"], 'username': requestdata["jiraUsername"] ,'url': requestdata["jiraUrl"] }
                        dbsession.userpreference.update_one({"_id":ObjectId(result["_id"])},{"$set":data})
                        res1 = "success"
            res['rows'] = res1
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("manageJiraDetails",e)
        return jsonify(res)

    #Fetch Zephyr data 
    @app.route('/admin/getDetails_Zephyr', methods=['POST'])
    def getDetails_Zephyr():
        app.logger.info("Inside getDetails_Zephyr")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result=dbsession.userpreference.find_one({"user":ObjectId(requestdata["userId"])}, {'Zephyr':1, '_id':0})
                if result:
                    res={'rows':result['Zephyr']}
                else:
                    res={'rows':"empty"}    
            else:
                app.logger.warn('Empty data received in getDetails_Zephyr fetch.')
        except Exception as e:
            servicesException("getDetails_Zephyr",e)
        return jsonify(res)

    #manage ZEPHYR Details
    @app.route('/admin/manageZephyrDetails',methods=['POST'])
    def manageZephyrDetails():
        app.logger.info("Inside manageZephyrDetails")
        res={'rows':'fail'}
        data={}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                zephyrObject = {}
                userObject = dbsession.userpreference.find_one({"user":ObjectId(requestdata["userId"])})
                if 'zephyrUrl' in requestdata :
                    zephyrObject["url"] = requestdata["zephyrUrl"]
                if 'zephyrAuthType' in requestdata :
                    zephyrObject["authType"] = requestdata["zephyrAuthType"]
                if 'zephyrUsername' in requestdata and 'zephyrPassword' in requestdata :
                    zephyrObject["username"] = requestdata["zephyrUsername"]
                    zephyrObject["password"] = requestdata["zephyrPassword"]
                if 'zephyrToken' in requestdata :
                    zephyrObject["token"] = requestdata["zephyrToken"]
                if requestdata["action"]=="delete":
                    if userObject==None:
                        return jsonify({'rows':'fail'})
                    elif userObject != None and 'Zephyr' in userObject:
                        dbsession.userpreference.update_one({"_id":userObject["_id"]},{"$unset":{ 'Zephyr':""}})
                elif requestdata["action"]=='create':
                    if userObject != None and 'Zephyr' in userObject:
                        return jsonify({'rows':'fail'})
                    else:
                        if userObject==None:
                            data['user'] = ObjectId(requestdata["userId"])
                            data['Zephyr'] = zephyrObject
                            dbsession.userpreference.insert_one(data)
                        else:
                            data['Zephyr'] = zephyrObject
                            dbsession.userpreference.update_one({"_id":ObjectId(userObject["_id"])},{"$set":data})
                elif requestdata["action"]=='update':
                    if userObject==None:
                        return jsonify({'rows':'fail'})
                    else:
                        data['Zephyr'] = zephyrObject
                        dbsession.userpreference.update_one({"_id":ObjectId(userObject["_id"])},{"$set":data})
                return jsonify({'rows':'success'})
            else:
                return jsonify({'rows':'fail'})
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("manageZephyrDetails",e)
        return jsonify(res)

    #service to map avo discover configuration
    @app.route('/admin/avoDiscoverMap',methods=['POST'])
    def avoDiscoverMap():
        app.logger.debug("Inside avoDiscoverMap")
        res={'rows':'fail'}
        data={}
        avoDiscoverFlag = False
        try:
            requestdata=json.loads(request.data)
            action = requestdata['action']
            avodiscoverurl = requestdata['avodiscoverurl']
            avodiscoverauthurl = requestdata['avodiscoverauthurl']
            data['userid'] = ObjectId(requestdata['userid'])
            data['avodiscoveruser'] = requestdata['avodiscoveruser']
            data['avodiscoverpswrd'] = wrap(requestdata['avodiscoverpwsrd'],ldap_key)
            if(action == 'map'):
                chk_user = dbsession.thirdpartyintegration.find_one({'avodiscoverurl':avodiscoverurl,'type':'AvoDiscover'},{'avodiscoverconfig':1})
                if chk_user!=None:
                    for entries in chk_user['avodiscoverconfig']:
                        if entries['userid'] == data['userid']:
                            return jsonify({"rows":"User already mapped"})
                    dbsession.thirdpartyintegration.update_one({'_id':chk_user['_id']},{"$push":{'avodiscoverconfig':data}})
                    avoDiscoverFlag=True
                else:
                    dbsession.thirdpartyintegration.insert_one({'avodiscoverurl':avodiscoverurl,'avodiscoverauthurl':avodiscoverauthurl,'type':'AvoDiscover','avodiscoverconfig':[data]})
                    avoDiscoverFlag = True
            if(avoDiscoverFlag):
                data=[]
                result1={}
                query = list(dbsession.thirdpartyintegration.find({'avodiscoverurl':avodiscoverurl,'type':'AvoDiscover'},{'avodiscoverconfig':1,'_id':0}))
                for i in query[0]['avodiscoverconfig']:
                    data.append({'_id': i['userid'], 'name': i['avodiscoveruser']})
                result1['mappedavodiscoverlist'] = data
                res={'rows':result1}
            else:
                return res
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("avoDiscoverMap", e, True)
        return jsonify(res)

    #service to reset/unmap Avo Discover configuration
    @app.route('/admin/avoDiscoverReset',methods=['POST'])
    def avoDiscoverReset():
        app.logger.debug("Inside avoDiscoverReset")
        res={'rows':'fail'}
        data=[]
        result={}
        avodiscover_flag=False
        try:
            requestdata=json.loads(request.data)
            if(requestdata['action'] == 'unmap'):
                query = dbsession.thirdpartyintegration.find_one({'type':'AvoDiscover'})
                tid = ObjectId(requestdata['targetid'])
                if query != None:
                    if len(query['avodiscoverconfig']) == 1 and query['avodiscoverconfig'][0]['userid'] == tid:
                        dbsession.thirdpartyintegration.delete_one({'_id': query['_id']})
                    else:
                        dbsession.thirdpartyintegration.update_one({'_id': query['_id']}, {"$pull":{'avodiscoverconfig': {'userid': tid}}})
                        upd_query = dbsession.thirdpartyintegration.find_one({'_id': query['_id']})
                        for i in upd_query['avodiscoverconfig']:
                            data.append({'_id': i['userid'], 'name': i['avodiscoveruser']})
            else:
                dbsession.thirdpartyintegration.delete_one({'type':'AvoDiscover','avodiscoverurl':requestdata['avodiscoverurl']})
            result['mappedavodiscoverlist'] = data
            res={'rows':result}
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("avoDiscoverReset", e, True)
        return jsonify(res)

    #service to fetch avo discover configuration
    @app.route('/admin/fetchAvoDiscoverMap',methods=['POST'])
    def fetchAvoDiscoverMap():
        app.logger.debug("Inside fetchAvoDiscoverMap")
        res={'rows':'fail'}
        result={}
        data=[]
        try:
            query = list(dbsession.thirdpartyintegration.find({'type':'AvoDiscover'},{'_id':0}))
            if(len(query)==0):
                return jsonify({"rows":"empty"})
            result['avodiscoverurl'] = query[0]['avodiscoverurl']
            for i in query[0]['avodiscoverconfig']:
                data.append({'_id': i['userid'], 'name': i['avodiscoveruser']})
            result['mappedavodiscoverlist'] = data
            res={'rows':result}
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("fetchAvoDiscoverMap", e, True)
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