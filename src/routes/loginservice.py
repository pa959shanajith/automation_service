################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
import traceback
import json
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
            servicesException('loadUser_Nineteen68 has encountered an exception : ',loaduser_exc)
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
            servicesException('loadPermission_Nineteen68 has encountered an exception : ',loadpermission_exc)
        return jsonify(res)