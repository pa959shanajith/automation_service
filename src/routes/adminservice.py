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

def LoadServices(app, redissession, n68session,licensedata,*args):
    setenv(app)
    ice_ndac_key=args[0]

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


    # Service to create/edit/delete users in Nineteen68
    @app.route('/admin/manageUserDetails',methods=['POST'])
    def manageUserDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action=requestdata["action"]
            del requestdata["action"]
            app.logger.info("Inside manageUserDetails. Query: "+str(action))
            if not isemptyrequest(requestdata):
                # if n68session.server_info():
                    if(action=="delete"):
                        result=n68session.users.delete_one({"name":requestdata['name']})
                        n68session.tasks.delete_many({"assignedto":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                        n68session.tasks.delete_many({"owner":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                        n68session.tasks.update_many({"reviewer":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}},{"$set":{"status":"inprogress","reviewer":""}})
                        res={"rows":"success"}
                    elif(action=="create"):
                        result=n68session.users.find_one({"name":requestdata['name']},{"name":1})
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
                            if not (requestdata["ldapuser"]):requestdata["ldapuser"]={}
                            else : requestdata["ldapuser"]=json.loads(requestdata["ldapuser"])
                            n68session.users.insert_one(requestdata)
                            res={"rows":"success"}
                    elif (action=="update"):
                        requestdata["modifiedby"]=ObjectId(requestdata["createdby"])
                        requestdata["modifiedbyrole"]=ObjectId(requestdata["createdbyrole"])
                        requestdata["modifiedon"]=datetime.now()
                        addroles=[]
                        for i in requestdata["additionalroles"]:
                            addroles.append(ObjectId(i))
                        if "password" in requestdata:
                            n68session.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"name":requestdata["name"],"firstname":requestdata["firstname"],"lastname":requestdata["lastname"],"email":requestdata["email"],"password":requestdata["password"],"addroles":addroles,"modifiedby":requestdata["modifiedby"],"modifiedbyrole":requestdata["modifiedbyrole"],"modifiedon":requestdata["modifiedon"]}})
                        else:
                            n68session.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"name":requestdata["name"],"firstname":requestdata["firstname"],"lastname":requestdata["lastname"],"email":requestdata["email"],"addroles":addroles,"modifiedby":requestdata["modifiedby"],"modifiedbyrole":requestdata["modifiedbyrole"],"modifiedon":requestdata["modifiedon"]}})
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
            requestdata={}
            if request.data:
                requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                # if n68session.server_info():
                    if "userid" in requestdata:
                        result=n68session.users.find_one({"_id":ObjectId(requestdata["userid"])},{"name":1,"firstname":1,"lastname":1,"email":1,"ldapuser":1,"defaultrole":1,"addroles":1})
                        result["rolename"]=n68session.permissions.find_one({"_id":result["defaultrole"]})["name"]
                        res={'rows':result}
                    else:
                        result=list(n68session.users.find({},{"_id":1,"name":1,"defaultrole":1}))
                        for i in result:
                            i["rolename"]=n68session.permissions.find_one({"_id":i["defaultrole"]})["name"]
                        res={'rows':result}
            else:
                app.logger.warn('Empty data received. users fetch.')
        except Exception as e:
            servicesException("getUserDetails", e, True)
        return jsonify(res)

    @app.route('/admin/getUserRoles_Nineteen68',methods=['POST'])
    def getUserRoles_Nineteen68():
        app.logger.debug("Inside getUserRoles_Nineteen68")
        res={'rows':'fail'}
        try:
            requestdata={}
            if request.data:
                requestdata=json.loads(request.data)
            if "id" in requestdata:
                result=list(n68session.permissions.find({"_id":requestdata["id"]},{"name":1}))
                res={'rows':result}
            else:
                result=list(n68session.permissions.find({},{"_id":1,"name":1}))
                res={'rows':result}
        except Exception as userrolesexc:
            servicesException("getUserRoles_Nineteen68", userrolesexc, True)
        return jsonify(res)

    #service renders all the domains in DB
    @app.route('/admin/getDomains_ICE',methods=['POST'])
    def getDomains_ICE():
        app.logger.debug("Inside getDomains_ICE")
        res={'rows':'fail'}
        try:
            result=n68session.projects.distinct("domain")
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
                    n68session.thirdpartyintegration.update_many({"type":"TOKENS","userid":ObjectId(requestdata["user_id"]),"deactivated":"active","expireson":{"$lt":datetime.today()}},{"$set":{"deactivated":"expired"}})
                    query=list(n68session.thirdpartyintegration.find({"type":"TOKENS","userid":ObjectId(requestdata["user_id"])},{"hash":0}))
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
                        query=n68session.thirdpartyintegration.find_one({"name":requestdata["name"],"userid":ObjectId(requestdata["userid"])})
                        if(query==None):
                            requestdata["projects"]=[]
                            requestdata["userid"]=ObjectId(requestdata["userid"])
                            requestdata["generatedon"]=datetime.now()
                            requestdata["expireson"]=datetime.strptime(str(requestdata["expireson"]),'%d-%m-%Y %H:%M')
                            result=n68session.thirdpartyintegration.insert_one(requestdata)
                            res= {'rows':{'token':requestdata["hash"]}}
                        else:
                            res={'rows':'duplicate'}
                if action == "deactivate":
                    if all(key in requestdata for key in ('userid','name')):
                        val=n68session.thirdpartyintegration.find_one({"userid":ObjectId(requestdata["userid"]),"name":requestdata["name"]},{"hash":1})
                        n68session.thirdpartyintegration.update_one({"hash":val["hash"],"userid":ObjectId(requestdata["userid"])},{"$set":{"deactivated":"deactivated"}})
                        result=list(n68session.thirdpartyintegration.find({"type":"TOKENS","userid":ObjectId(requestdata["userid"])},{"hash":0}))
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
                    result=list(n68session.projects.find({"domain":requestdata["id"][0]},{"_id":1,"name":1}))
                    res={'rows':result}
                elif requestdata["type"]=="projects":
                    projectids=[]
                    for i in requestdata["id"]:
                        projectids.append(ObjectId(i))
                    result=list(n68session.projects.find({"_id":{"$in":projectids}}))
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
                requestdata["type"]=n68session.projecttypekeywords.find_one({"name":requestdata["type"]},{"_id":1})["_id"]
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
                n68session.projects.insert_one(requestdata)
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
                    # n68session.projects.update({"id":ObjectId(requestdata["projectid"])},{"$pull":{"releases.name":requestdata["releasename"]}})
                    res={"rows":"success"}
                elif(requestdata['query'] == 'deletecycle'):
                    # n68session.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$pull":{"releases.cycles._id":ObjectId(requestdata["cycleid"]),"releases.cycles.name":requestdata["name"]}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'createrelease'):
                    releases=n68session.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
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
                    n68session.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'createcycle'):
                    result=n68session.projects.find_one({"_id":ObjectId(requestdata["projectid"])},{"releases":1})["releases"]
                    for i in result:
                        if i["name"]== requestdata["releaseid"]:
                            cycles={}
                            cycles["modifiedby"]=cycles["createdby"]=ObjectId(requestdata["createdby"])
                            cycles["modifiedon"]=cycles["createdon"]=datetime.now()
                            cycles["modifiedbyrole"]=cycles["createdbyrole"]=ObjectId(requestdata["createdbyrole"])
                            cycles["_id"]=ObjectId()
                            cycles["name"]=requestdata["name"]
                            i["cycles"].append(cycles)
                    n68session.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":result}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'editrelease'):
                    releases=n68session.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
                    for i in releases:
                        if i["name"] == requestdata["releasename"]:
                            i["modifiedbyrole"]=ObjectId(requestdata["modifiedbyrole"])
                            i["modifiedby"]=ObjectId(requestdata["modifiedby"])
                            i["modifiedon"]=datetime.now()
                            i["name"]=requestdata["newreleasename"]
                    n68session.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
                    res={'rows':'success'}
                elif(requestdata['query'] == 'editcycle'):
                    releases=n68session.projects.find_one({"_id":ObjectId(requestdata["projectid"])})["releases"]
                    for i in releases:
                        if i["name"]==requestdata["releaseid"]:
                            cycles=i["cycles"]
                            for j in cycles:
                                if j["_id"]==ObjectId(requestdata["cycleid"]):
                                    j["name"]=requestdata["newcyclename"]
                                    j["modifiedbyrole"]=ObjectId(requestdata["modifiedbyrole"])
                                    j["modifiedby"]=ObjectId(requestdata["modifiedby"])
                                    j["modifiedon"]=datetime.now()
                    n68session.projects.update({"_id":ObjectId(requestdata["projectid"])},{"$set":{"releases":releases}})
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
                    result=list(n68session.projects.find({"domain":requestdata["id"]},{"name":1}))
                    res={"rows":result}
                elif requestdata["type"] == "projectsdetails":
                    result=n68session.projects.find_one({"_id":ObjectId(requestdata["id"])},{"releases":1,"domain":1,"name":1,"type":1})
                    result["type"]=n68session.projecttypekeywords.find_one({"_id":result["type"]},{"name":1})["name"]
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
                if "bindcredentials" in requestdata: requestdata["bindcredentials"]=wrap(requestdata["bindcredentials"],ldap_key)
                else: requestdata["bindcredentials"] = ""
                if (requestdata['action'] == "delete"):
                    n68session.thirdpartyintegration.delete_one({"type":"LDAP","name":requestdata["name"]})
                    res={"rows":"success"}
                elif (requestdata['action'] == "create"):
                    del requestdata["action"]
                    requestdata["fieldmap"]=json.loads(requestdata["fieldmap"])
                    result=n68session.thirdpartyintegration.find_one({"type":"LDAP","name":requestdata["name"]})
                    if result != None:
                        res = {"rows":"exists"}
                        return jsonify(res)
                    else:
                        requestdata["type"]="LDAP"
                        n68session.thirdpartyintegration.insert_one(requestdata)
                        res = {"rows":"success"}
                elif (requestdata['action'] == "update"):
                    requestdata["fieldmap"]=json.loads(requestdata["fieldmap"])
                    n68session.thirdpartyintegration.update_one({"name":requestdata["name"]},{"$set":{"url":requestdata["url"],"bindcredentials":requestdata["bindcredentials"],"basedn":requestdata["basedn"],"auth":requestdata["auth"],"binddn":requestdata["binddn"],"fieldmap":requestdata["fieldmap"]}})
                    res = {"rows":"success"}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. LDAP config manage.')
        except Exception as getallusersexc:
            servicesException("manageLDAPConfig", getallusersexc, True)
        return jsonify(res)

    @app.route('/admin/getLDAPConfig',methods=['POST'])
    def getLDAPConfig():
        app.logger.info("Inside getLDAPConfig")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if "name" in requestdata:
                    result = n68session.thirdpartyintegration.find_one({"name":requestdata["name"]})
                    password = result["bindcredentials"]
                    if len(password) > 0:
                        password = unwrap(password, ldap_key)
                        result["bindcredentials"] = password
                    res = {"rows":result}
                else:
                    result=list(n68session.thirdpartyintegration.find({"type":"LDAP"},{"name":1}))
                    res={"rows":result}
            else:
                app.logger.warn('Empty data received. LDAP config fetch.')
        except Exception as getallusersexc:
            servicesException("getLDAPConfig", getallusersexc, True)
        return jsonify(res)

    #service assigns projects to a specific user
    @app.route('/admin/assignProjects_ICE',methods=['POST'])
    def assignProjects_ICE():
        app.logger.debug("Inside assignProjects_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                domains=n68session.projects.distinct("domain")
                project={}
                for i in domains:
                    projects=list(n68session.projects.find({"domain":i},{"_id":1}))
                    project[i]=[]
                    for j in projects:
                        project[i].append(j["_id"])
                assigned_pro=n68session.users.find_one({"_id":ObjectId(requestdata["userid"])},{"projects":1})["projects"]
                if (requestdata['alreadyassigned'] != True):
                    projects=assigned_pro
                    for i in requestdata["projectids"]:
                        projects.append(ObjectId(i))
                    result=n68session.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"projects":projects}})
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

                    # list(n68session.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                    # for idval in requestdata['projectids']:
                    #     result.append(ObjectId(idval))
                    result=n68session.users.update_one({"_id":ObjectId(requestdata["userid"])},{"$set":{"projects":result}})
                    n68session.tasks.delete_many({"projectid":{"$in":remove_pro},"assignedto":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    n68session.tasks.delete_many({"projectid":{"$in":remove_pro},"owner":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}})
                    n68session.tasks.update_many({"projectid":{"$in":remove_pro},"reviewer":ObjectId(requestdata["userid"]),"status":{"$ne":'complete'}},{"$set":{"status":"inprogress","reviewer":""}})
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
                    result=n68session.users.find_one({"_id":ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
                    res={"rows":result}
                elif(requestdata['query'] == 'projectname'):
                    projectids=[]
                    for i in requestdata["projectid"]:
                        projectids.append(ObjectId(i))
                    result=list(n68session.projects.find({"_id":{"$in":projectids},"domain":requestdata["domain"]},{"name":1}))
                    res={"rows":result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. assigned projects.')
        except Exception as e:
            servicesException("getAssignedProjects_ICE", e, True)
        return jsonify(res)

    @app.route('/admin/getUsers_Nineteen68',methods=['POST'])
    def getUsers_Nineteen68():
        app.logger.debug("Inside getUsers_Nineteen68")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                result=list(n68session.users.find({"projects":{"$in":[ObjectId(requestdata["projectid"])]}},{"name":1,"defaultrole":1,"addroles":1}))
                res={"rows":result}
            else:
                app.logger.warn('Empty data received. get users - Mind Maps.')
        except Exception as getUsersexc:
            servicesException("getUsers_Nineteen68", getUsersexc, True)
        return jsonify(res)

    @app.route('/admin/getPreferences',methods=['POST'])
    def getPreferences():
        app.logger.debug("Inside getPreferences")
        res={'rows':'fail'}
        try:
            result=list(n68session.permissions.find({},{"name":1,"plugins":1,"_id":0}))
            res={'rows':result}
        except Exception as getdomainsexc:
            servicesException("getPreferences", getdomainsexc, True)
        return jsonify(res)

    @app.route('/admin/fetchICE',methods=['POST'])
    def fetchICE():
        app.logger.debug("Inside fetchICE")
        res={'rows':'fail'}
        try:
            result=list(n68session.icetokens.find())
            user_ids=[i["provisionedto"] for i in result if "provisionedto" in i]
            result1=list(n68session.users.find({"_id":{"$in":user_ids}},{"name":1}))
            user_ids={x["_id"]: x["name"] for x in result1}
            for row in result:
                if row["icetype"]=="normal" : row["username"]=user_ids[row["provisionedto"]]
                else : row["username"]="N/A"
            res={'rows':result}
        except Exception as fetchICEexc:
            servicesException("fetchICE", fetchICEexc)
        return jsonify(res)
    
    @app.route('/admin/provisionICE',methods=['POST'])
    def iceprovisions():
        app.logger.debug("Inside provisions")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                token=str(uuid.uuid4())
                token_query={"icetype":requestdata["icetype"]}
                #To restrict multiple ICE provsioning to the same user
                if requestdata["icetype"]=="normal":
                    token_query["provisionedto"]=requestdata["provisionedto"]=ObjectId(requestdata["provisionedto"])
                else:
                    requestdata["expireson"]=datetime.strptime(str(requestdata["expireson"]),'%d-%m-%Y %H:%M')
                    token_query["icename"]=requestdata["icename"]
                get_tokens=list(n68session.icetokens.find(token_query))
                if requestdata["query"]==PROVISION:
                    requestdata["token"]=token
                    requestdata["status"]=PROVISION_STATUS
                    requestdata[PROVISION_STATUS+"on"]=datetime.now()
                    requestdata.pop("query")
                    #this condition is valid if ice_names needs to be unique accross Nineteen68
                    ice_names= list(n68session.icetokens.find({"icename":requestdata["icename"]},{"icename":1}))
                    if get_tokens == [] and ice_names==[]:
                    #currently only icetype and user combination is unique
                    # if get_tokens == []:
                        result=n68session.icetokens.insert_one(requestdata)
                        enc_token=wrap(token+"@"+requestdata["icename"],ice_ndac_key)
                        res={"rows":enc_token}
                    else:
                        res={"rows":"DuplicateIceName"}
                elif requestdata["query"]==DEREGISTER:
                    if get_tokens != []:
                        result=n68session.icetokens.update_one(token_query,{"$set":{"status":DEREGISTER_STATUS,"deregisteredon":datetime.now()}})
                        res={'rows':'success'}
                elif requestdata["query"]=='re'+REGISTER:
                    if get_tokens != []:
                        result=n68session.icetokens.update_one(token_query,{"$set":{"status":PROVISION_STATUS,"token":token,"provisionedon":datetime.now()}})
                        enc_token=wrap(token+"@"+requestdata["icename"],ice_ndac_key)
                        res={"rows":enc_token}
                elif requestdata["query"]=="gettoken":
                    if get_tokens != []:
                        citoken=requestdata["token"]
                        result=n68session.icetokens.update_one(token_query,{"$set":{"citoken":citoken}})
                        res={"rows":citoken}
            else:
                app.logger.warn('Empty data received. provisionICE - Admin.')
            
        except Exception as provisionICEexc:
            servicesException("provisionICE", provisionICEexc)
        return jsonify(res)