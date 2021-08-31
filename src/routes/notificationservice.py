################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from pymongo.operations import InsertOne, UpdateOne, DeleteOne, FindOne
from utils import *
from Crypto.Cipher import AES
import base64

def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################

    @app.route('/notification/getNotificationGroups',methods=['POST'])
    def getNotificationGroups():
        app.logger.debug("Inside getNotificationGroups")
        res={'rows':'fail','err':''}

        try:
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                result = []
                groupids = [ObjectId(id) for id in requestdata.groupids]
                groupnames = requestdata.groupnames
                if len(groupids) == 0 and len(groupnames) == 0:
                    result.extend(list(dbsession.notificationgroups.find({},{"groupname":1,"internalusers":1,"otherusers":1})))
                else:
                    result.extend(list(dbsession.notificationgroups.find({'_id':{'$in':groupids}},{"groupname":1,"internalusers":1,"otherusers":1})))
                    result.extend(list(dbsession.notificationgroups.find({'groupname':{'$in':groupnames}},{"groupname":1,"internalusers":1,"otherusers":1})))
                res['rows'] = result
                del res['err']
            else:
                app.logger.warn('Empty data received. report.')
                res['err']='Invalid Request: Empty Parameter not allowed'
        except Exception as e:
            servicesException("getNotificationGroups", e, True)
            res['err'] = "Exception occurred in getNotificationGroups"
        return jsonify(res)

    @app.route('/notification/updateNotificationGroups',methods=['POST'])
    def updateNotificationGroups():
        app.logger.debug("Inside updateNotificationGroups")
        res={'rows':'fail','err':''}

        try:
            requestdata=json.loads(request.data)
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                if requestdata.action.lower() == "create":
                    groupdata = requestdata.groupdata
                    query = [InsertOne(
                                        {
                                        'createdon': datetime.now(),
                                        'createdbyrole': ObjectId(requestdata.modifiedbyrole),
                                        'createdby': ObjectId(requestdata.modifiedby),
                                        'internalusers': groupdata[id]['internalusers'],
                                        'otherusers': groupdata[id]['otherusers']
                                        }
                                    ) for id in groupdata ]
                   
                    dbsession.notificationgroups.bulk_write(query)
                
                elif requestdata.action.lower() == "update":
                    groupdata = requestdata.groupdata
                    query = [UpdateOne(
                                        {'_id' : ObjectId(id)}, 
                                        {'$set' : {
                                            'modifiedon': datetime.now(),
                                            'modifiedbyrole': ObjectId(requestdata.modifiedbyrole),
                                            'modifiedby': ObjectId(requestdata.modifiedby),
                                            'internalusers': groupdata[id]['internalusers'],
                                            'otherusers': groupdata[id]['otherusers']}
                                            }
                                    ) for id in groupdata ]

                    dbsession.notificationgroups.bulk_write(query);                
                elif requestdata.action.lower() == "delete":
                    groupdata = requestdata.groupdata
                    query = [DeleteOne({'_id' : ObjectId(id)}) for id in groupdata]
                    dbsession.notificationgroups.bulk_write(query);                
               
                res['rows'] = 'success'
                del res['err']
            else:
                app.logger.warn('Empty data received. report.')
                res['err']='Invalid Request: Empty Parameter not allowed'
        except Exception as e:
            servicesException("updateNotificationGroups", e, True)
            res['err'] = "Exception occurred in updateNotificationGroups"
        return jsonify(res)

    @app.route('/notification/getNotificationRules',methods=['GET'])
    def getNotificationRules():
        app.logger.debug("Inside getNotificationRules")
        res={'rows':'fail','err':''}
        try:
            result = dbsession.notificationrules.find({})
            res['rows'] = result
            del res['err']
        except Exception as e:
            servicesException("getNotificationRules", e, True)
            res['err'] = "Exception occurred in getNotificationRules"
        return jsonify(res)

   
################################################################################
# END OF NOTIFICATION SERVICES
################################################################################