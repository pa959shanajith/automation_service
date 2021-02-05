################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
import json
from datetime import datetime
def LoadServices(app, redissession, dbsession, licensedata):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################
    #DAS service for loading users info
    @app.route('/login/loadUser',methods=['POST'])
    def loadUser():
        app.logger.debug("Inside loadUser.")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                user_data = None
                if requestdata["username"] != "ci_cd":
                    user_data = dbsession.users.find_one({"name":requestdata["username"]})
                res={'rows': user_data}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as loaduser_exc:
            servicesException('loadUser', loaduser_exc, True)
        return jsonify(res)

    #DAS service for incrementing/clearing invalid password count
    @app.route('/login/invalidCredCounter',methods=['POST'])
    def invalidCredCounter():
        app.logger.debug("Inside invalidCredCounter.")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action = requestdata["action"]
            if not isemptyrequest(requestdata):
                if requestdata["username"] == "ci_cd":
                    return jsonify(res)
                if action == "increment":
                    dbsession.users.update_one({"name":requestdata["username"]},{"$inc":{"invalidCredCount":1}})
                if action == "clear":
                    up_data = {
                        'invalidCredCount': 0,
                        'auth.defaultpassword': "",
                        'auth.verificationpassword': ""
                    }
                    dbsession.users.update_one({"name":requestdata["username"]},{'$set': up_data})
                res={'rows': 'success'}
            else:
                app.logger.warn('Empty data received.')
        except Exception as excep:
            servicesException('invalidCredCounter', excep, True)
        return jsonify(res)

    #DAS service for checking password timeout
    @app.route('/login/passtimeout',methods=['POST'])
    def passtimeout():
        app.logger.debug("Inside passtimeout.")
        result='fail'
        res = {'rows': result}
        try:
            requestdata=json.loads(request.data)
            action = requestdata["action"]
            if not isemptyrequest(requestdata):
                if requestdata["username"] == "ci_cd":
                    return jsonify(res)
                user_data = dbsession.users.find_one({"name":requestdata["username"]})
                if action == "forgotPass":
                    defpasstime = user_data['auth']["defaultpasstime"]
                    currtime = datetime.now()
                    diff = (currtime - defpasstime).seconds/60
                    if diff<15:
                        result = "success"
                    else:
                        result = "timeout"
                elif action == "unlock":
                    defpasstime = user_data['auth']["verificationpasstime"]
                    up_data = { 'auth.verificationpassword': ""}
                    currtime = datetime.now()
                    diff = (currtime - defpasstime).seconds/60
                    if diff<15:
                        result = "success"
                        up_data["invalidCredCount"]=0
                    else:
                        result = "timeout"
                    dbsession.users.update_one({'_id':user_data['_id']},{'$set': up_data})
                res['rows'] = result
            else:
                app.logger.warn('Empty data received.')
        except Exception as excep:
            servicesException('passtimeout', excep, True)
        return jsonify(res)

    #add default password for forgot password
    @app.route('/login/forgotPasswordEmail',methods=['POST'])
    def forgotPasswordEmail():
        app.logger.info("Inside forgotPasswordEmail")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                up_data = {
                    "auth.defaultpassword": requestdata["defaultpassword"],
                    "auth.defaultpasstime": datetime.now()
                }
                dbsession.users.update_one({"name":requestdata["username"]},{'$set': up_data})
                res={'rows':'success'}
            else:
                app.logger.warn('Empty data received.')
        except Exception as e:
            servicesException("forgotPasswordEmail", e, True)
        return jsonify(res)

    #add default password for forgot password
    @app.route('/login/unlockAccountEmail',methods=['POST'])
    def unlockAccountEmail():
        app.logger.info("Inside unlockAccountEmail")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                up_data = {
                    "auth.verificationpassword": requestdata["verificationpassword"],
                    "auth.verificationpasstime": datetime.now()
                }
                dbsession.users.update_one({"name":requestdata["username"]},{'$set': up_data})
                res={'rows':'success'}
            else:
                app.logger.warn('Empty data received.')
        except Exception as e:
            servicesException("unlockAccountEmail", e, True)
        return jsonify(res)

    #DAS service for loading permissions info
    @app.route('/login/loadPermission',methods=['POST'])
    def loadPermission():
        app.logger.debug("Inside loadPermission.")
        res={'rows':'fail'}
        dictdata={}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'permissionInfoByRoleID'):
                    permissions_data = dbsession.permissions.find_one({"_id":ObjectId(requestdata["roleid"])})
                    dictdata['roleid'] = permissions_data['_id']
                    dictdata['rolename'] = permissions_data['name']
                    plugins = permissions_data['plugins']
                    lic_plugins = licensedata['plugins']
                    allowed_plugins = []
                    for keys in ui_plugins:
                        allowed_plugins.append({ "pluginName": ui_plugins[keys],"pluginValue": False if lic_plugins[keys] == False else plugins[keys]})
                    dictdata['pluginresult']=allowed_plugins
                    res={'rows': dictdata}
                elif(requestdata["query"] == 'nameidInfoByRoleIDList'):
                    roleids=[]
                    for roleid in requestdata["roleid"]:roleids.append(ObjectId(roleid))
                    data=list(dbsession.permissions.find({"_id" : {"$in":roleids}},{"name":1,"_id":1}))
                    res={'rows': data}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as loadpermission_exc:
            servicesException('loadPermission', loadpermission_exc, True)
        return jsonify(res)

    #service for loading ci_user information
    @app.route('/login/authenticateUser_CI',methods=['POST'])
    def authenticateUser_CI():
        app.logger.debug("Inside authenticateUser_CI")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                queryresult = dbsession.icetokens.find_one({"icename":requestdata["icename"]})
                query = None
                user_query = {"name":"ci_cd"}
                if queryresult is not None:
                    userid = queryresult["_id"]
                    if queryresult['icetype'] == 'normal':
                        userid = queryresult["provisionedto"]
                        user_query = {"_id":queryresult["provisionedto"]}
                    # Mark active tokens that are expired as expired
                    deact_expired_tkn_qry = {"type":"TOKENS","userid":userid,"deactivated":"active","expireson":{"$lt":datetime.today()}}
                    dbsession.thirdpartyintegration.update_many(deact_expired_tkn_qry,{"$set":{"deactivated":"expired"}})
                    # Fetch the token with given token name
                    query = dbsession.thirdpartyintegration.find_one({"userid":userid,"name":requestdata["tokenname"],"type":"TOKENS"})
                if query is not None:
                    user_res=dbsession.users.find_one(user_query,{"defaultrole":1,"name":1})
                    query["userid"] = user_res["_id"]
                    query["role"] = user_res["defaultrole"]
                    query["username"] = user_res["name"]
                else: query = "invalid"
                res= {"rows":query}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as authenticateuserciexc:
            servicesException('authenticateUser_CI',authenticateuserciexc)
        return jsonify(res)

    # service for fetching user profile for given icename or all provisioned ice
    @app.route('/login/fetchICEUser',methods=['POST'])
    def fetchICEUser():
        app.logger.debug("Inside fetchICEUser")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                find_args = {}
                if "icename" in requestdata:
                    find_args["icename"] = requestdata["icename"]
                ice_list=list(dbsession.icetokens.find(find_args))
                user_ids=[i["provisionedto"] for i in ice_list if "provisionedto" in i]
                user_list=list(dbsession.users.find({"_id":{"$in":user_ids}},{"name":1,"defaultrole":1}))
                user_profiles={x["_id"]: x for x in user_list}
                cicd_user=dbsession.users.find({"name":"ci_cd"},{"name":1,"defaultrole":1})
                for row in ice_list:
                    if row["icetype"]=="normal":
                        prv_to = row["provisionedto"]
                        if prv_to in user_ids:
                            row["userid"] = prv_to
                            row["name"] = user_profiles[prv_to]["name"]
                            row["role"] = user_profiles[prv_to]["defaultrole"]
                        #else: dbsession.icetokens.delete_one({"_id": row["_id"]})
                        del row["provisionedto"]
                    else:
                        row["userid"] = cicd_user[0]["_id"]
                        row["name"] = cicd_user[0]["name"]
                        row["role"] = cicd_user[0]["defaultrole"]
                if "icename" in requestdata:
                    if len(ice_list) == 0: ice_list = None
                    else: ice_list = ice_list[0]
                    if "userid" not in ice_list: ice_list = None
                res={'rows':ice_list}
            else:
                app.logger.warn('Empty data received. get user profile for ice.')
        except Exception as fetchICEexc:
            servicesException("fetchICEUser", fetchICEexc, True)
        return jsonify(res)

    # service to check terms and conditions
    @app.route('/login/checkTandC',methods=['POST'])
    def checkTandC():
        app.logger.debug("Inside checkTandC.")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if requestdata["query"]=='loadUserInfo':
                    username = ''
                    if 'username' in requestdata:
                        user = dbsession.users.find_one({"name": requestdata['username']}, {"name":1})
                        if user is None: res['rows'] = 'nouser'
                        else: username = requestdata['username']
                    elif 'icename' in requestdata:
                        ice_detail = dbsession.icetokens.find_one({"icename":requestdata["icename"]}, {"provisionedto": 1, "icetype": 1})
                        if ice_detail is None: res['rows'] = 'nouser'
                        else:
                            if ice_detail['icetype'] == 'ci-cd': # EULA check doesn't apply on CI-CD ICE
                                res['rows'] = 'success'
                            else:
                                user = dbsession.users.find_one({"_id": ice_detail["provisionedto"]}, {"name":1})
                                if user is not None: username = user["name"]
                                else: res['rows'] = 'nouser'
                    if username != '':
                        user_data = list(dbsession.eularecords.find({"username": username}))
                        if len(user_data) > 0:
                            pre_acceptance = user_data[-1]["acceptance"]
                            if pre_acceptance == "Accept":
                                res = {'rows': 'success'}
                elif(requestdata["query"]=='checkTandC'):
                    del requestdata["query"]
                    requestdata["userId"]=ObjectId(requestdata["userId"])
                    dbsession.eularecords.insert_one(requestdata)
                    res={'rows': 'success'}
            else:
                app.logger.warn('Empty data received. in checkTandC')
        except Exception as checkTandCexc:
            servicesException('checkTandC', checkTandCexc, True)
        return jsonify(res)
