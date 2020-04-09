################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
import traceback
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
            if (not isemptyrequest(requestdata) ):
                if(requestdata["query"] == 'userInfobyName'):
                    user_data = n68session.users.find_one({"name":requestdata["username"]})
                    res={'rows': user_data}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as loaduser_exc:
            app.logger.debug(traceback.format_exc())
            servicesException('loadUser_Nineteen68',loaduser_exc)
        return jsonify(res)

    #NDAC service for loading permissions info
    @app.route('/login/loadPermission_Nineteen68',methods=['POST'])
    def loadPermission_Nineteen68():
        app.logger.debug("Inside loadPermission_Nineteen68.")
        res={'rows':'fail'}
        dictdata={}
        try:
            requestdata=json.loads(request.data)
            if (not isemptyrequest(requestdata) ):
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
            app.logger.debug(traceback.format_exc())
            servicesException('loadPermission_Nineteen68',loadpermission_exc)
        return jsonify(res)

    #service for loading ci_user information
    @app.route('/login/authenticateUser_Nineteen68_CI',methods=['POST'])
    def authenticateUser_Nineteen68_CI():
        app.logger.debug("Inside authenticateUser_Nineteen68_CI")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                queryresult = n68session.users.find_one({"name":requestdata["username"]},{"_id":1, "defaultrole": 1})
                query = None
                if queryresult is not None:
                    n68session.thirdpartyintegration.update_many({"type":"TOKENS","userid":queryresult["_id"],"deactivated":"active","expireson":{"$lt":datetime.today()}},{"$set":{"deactivated":"expired"}})
                    query = n68session.thirdpartyintegration.find_one({"userid":queryresult["_id"],"name":requestdata["tokenname"],"type":"TOKENS"})
                if query is not None: query["role"] = queryresult["defaultrole"]
                res= {"rows":query}
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as authenticateuserciexc:
            servicesException('authenticateUser_Nineteen68_CI',authenticateuserciexc)
        return jsonify(res)