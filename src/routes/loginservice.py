################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
import json
from datetime import datetime
def LoadServices(app, redissession, n68session, licensedata):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################
    #NDAC service for loading users info
    @app.route('/login/loadUser_Nineteen68',methods=['POST'])
    def loadUser_Nineteen68():
        app.logger.debug("Inside loadUser_Nineteen68.")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                user_data = None
                if requestdata["username"] != "ci_cd":
                    user_data = n68session.users.find_one({"name":requestdata["username"]})
                res={'rows': user_data}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as loaduser_exc:
            servicesException('loadUser_Nineteen68', loaduser_exc, True)
        return jsonify(res)

    #NDAC service for loading permissions info
    @app.route('/login/loadPermission_Nineteen68',methods=['POST'])
    def loadPermission_Nineteen68():
        app.logger.debug("Inside loadPermission_Nineteen68.")
        res={'rows':'fail'}
        dictdata={}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'permissionInfoByRoleID'):
                    permissions_data = n68session.permissions.find_one({"_id":ObjectId(requestdata["roleid"])})
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
                    data=list(n68session.permissions.find({"_id" : {"$in":roleids}},{"name":1,"_id":1}))
                    res={'rows': data}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as loadpermission_exc:
            servicesException('loadPermission_Nineteen68', loadpermission_exc, True)
        return jsonify(res)

    #service for loading ci_user information
    @app.route('/login/authenticateUser_Nineteen68_CI',methods=['POST'])
    def authenticateUser_Nineteen68_CI():
        app.logger.debug("Inside authenticateUser_Nineteen68_CI")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                queryresult = n68session.icetokens.find_one({"icename":requestdata["icename"]})
                query = None
                user_query = {"name":"ci_cd"}
                if queryresult is not None:
                    userid = queryresult["_id"]
                    if queryresult['icetype'] == 'normal':
                        userid = queryresult["provisionedto"]
                        user_query = {"_id":queryresult["provisionedto"]}
                    # Mark active tokens that are expired as expired
                    deact_expired_tkn_qry = {"type":"TOKENS","userid":userid,"deactivated":"active","expireson":{"$lt":datetime.today()}}
                    n68session.thirdpartyintegration.update_many(deact_expired_tkn_qry,{"$set":{"deactivated":"expired"}})
                    # Fetch the token with given token name
                    query = n68session.thirdpartyintegration.find_one({"userid":userid,"name":requestdata["tokenname"],"type":"TOKENS"})
                if query is not None:
                    user_res=n68session.users.find_one(user_query,{"defaultrole":1})
                    query["userid"] = user_res["_id"]
                    query["role"] = user_res["defaultrole"]
                else: query = "invalid"
                res= {"rows":query}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as authenticateuserciexc:
            servicesException('authenticateUser_Nineteen68_CI',authenticateuserciexc)
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
                ice_list=list(n68session.icetokens.find(find_args))
                user_ids=[i["provisionedto"] for i in ice_list if "provisionedto" in i]
                user_list=list(n68session.users.find({"_id":{"$in":user_ids}},{"name":1,"defaultrole":1}))
                user_profiles={x["_id"]: x for x in user_list}
                cicd_user=n68session.users.find({"name":"ci_cd"},{"name":1,"defaultrole":1})
                for row in ice_list:
                    if row["icetype"]=="normal":
                        prv_to = row["provisionedto"]
                        if prv_to in user_ids:
                            row["userid"] = prv_to
                            row["name"] = user_profiles[prv_to]["name"]
                            row["role"] = user_profiles[prv_to]["defaultrole"]
                        #else: n68session.icetokens.delete_one({"_id": row["_id"]})
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
