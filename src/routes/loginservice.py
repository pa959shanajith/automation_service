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
                        row["userid"] = cicd_user["_id"]
                        row["name"] = cicd_user["name"]
                        row["role"] = cicd_user["defaultrole"]
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

    #DAS service to check terms and conditions
    @app.route('/login/checkTandC',methods=['POST'])
    def checkTandC():
        app.logger.debug("Inside checkTandC.")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if requestdata["query"]=='loadUserInfo':
                    user_data = None
                    user_data = list(dbsession.eularecords.find({"username":requestdata["input_name"]}))
                    if len(user_data)>0:
                        pre_acceptance = user_data[-1]["acceptance"]
                        if pre_acceptance=="Accept":
                            res={'rows': 'success'}
                elif(requestdata["query"]=='checkTandC'):
                    del requestdata["query"]
                    dbsession.eularecords.insert_one(requestdata)
                    res={'rows': 'success'}
            else:
                app.logger.warn('Empty data received. in checkTandC')
        except Exception as checkTandCexc:
            servicesException('checkTandC', checkTandCexc, True)
        return jsonify(res)
