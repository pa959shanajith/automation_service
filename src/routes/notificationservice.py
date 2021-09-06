################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from pymongo.operations import InsertOne, UpdateOne, DeleteOne
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
                groupids = [ObjectId(id) for id in requestdata['groupids']]
                groupnames = requestdata['groupnames']
                if len(groupids) == 0 and len(groupnames) == 0:
                    result.extend(list(dbsession.notificationgroups.find({},{"groupname":1,"_id":1})))
                else:
                    user_lookup = {
                                    '$lookup':
                                        {
                                            'from': "users",
                                            'localField': "internalusers",
                                            'foreignField': "_id",
                                            'as': "internal_user_info"
                                        },         
                                }
                    projection = {
                                    "$project": {
                                        "_id": 1,
                                        "otherusers": 1,
                                        "internal_user_info._id": 1,
                                        "internal_user_info.email": 1,
                                        "internal_user_info.name": 1,
                                    }
                                }
                                    
                    id_aggregator = [
                                        { 
                                            '$match':{'_id':{'$in':groupids}}
                                        },
                                        user_lookup,
                                        projection
                                    ] 
                    name_aggregator = [
                                        { 
                                            '$match':{"groupname":{'$in':groupnames}}
                                        },
                                        user_lookup,
                                        projection
                                    ]
                    result_ids = list(dbsession.notificationgroups.aggregate(id_aggregator))
                    result_names = list(dbsession.notificationgroups.aggregate(name_aggregator))
                    result.extend(result_ids)
                    result.extend(result_names)

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
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                groupdata = requestdata['groupdata']
                if requestdata['action'].lower() == "create":
                    query = [InsertOne(
                                        {
                                        'groupname': groupdata[id]['groupname'],
                                        'createdon': datetime.now(),
                                        'createdbyrole': ObjectId(requestdata['modifiedbyrole']),
                                        'createdby': ObjectId(requestdata['modifiedby']),
                                        'internalusers': [ObjectId(iuid) for iuid in groupdata[id]['internalusers']],
                                        'otherusers': groupdata[id]['otherusers']
                                        }
                                    ) for id in groupdata ]
                   
                    dbsession.notificationgroups.bulk_write(query)
                
                elif requestdata['action'].lower() == "update":
                    query = [UpdateOne(
                                        {'_id' : ObjectId(id)}, 
                                        {'$set' : {
                                            'groupname': groupdata[id]['groupname'],
                                            'modifiedon': datetime.now(),
                                            'modifiedbyrole': ObjectId(requestdata['modifiedbyrole']),
                                            'modifiedby': ObjectId(requestdata['modifiedby']),
                                            'internalusers': [ObjectId(iuid) for iuid in groupdata[id]['internalusers']],
                                            'otherusers': groupdata[id]['otherusers']}
                                            }
                                    ) for id in groupdata ]

                    dbsession.notificationgroups.bulk_write(query);                
                elif requestdata['action'].lower() == "delete":
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


    @app.route('/notification/updateNotificationConfiguration',methods=['POST'])
    def updateNotificationConfiguration():
        app.logger.debug("Inside updateNotificationConfiguration")
        res={'rows':'fail','err':''}
        try:
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                newrules = requestdata['newrules']
                updatedrules = requestdata['updatedrules']
                deletedrules = requestdata['deletedrules']
                otherrules = [ObjectId(id) for id in requestdata['otherrules']]
                new_rules = [{
                                "groupids": [ObjectId(groupid) for groupid in newrules[ruleid]['groupids']],
                                "additionalrecepients": [ObjectId(others) for others in newrules[ruleid]['additionalrecepients']],
                                "actiontype": newrules[ruleid]['actiontype'],
                                "targetnode": newrules[ruleid]['targetnode'],
                                "actionon": newrules[ruleid]['actionon'] if 'actionon' in newrules[ruleid] and newrules[ruleid]['actionon'] else 0,
                                "targetnodeid": ObjectId(newrules[ruleid]['targetnodeid']) if 'targetnodeid' in newrules[ruleid] and newrules[ruleid]['targetnodeid'] else 0
                            } for ruleid in newrules]
                new_rule_ids = []
                if len(new_rules) > 0:
                    insert_result = dbsession.rules.insert_many(new_rules,False,True)

                    for inserted_ids, rule_id in zip(insert_result.inserted_ids,newrules.keys()):
                        newrules[rule_id]['dbid'] = inserted_ids
                        new_rule_ids = inserted_ids

                updated_rules_query = [UpdateOne(
                                                {'_id':ObjectId(ruleid)},
                                                {
                                                    '$set':{
                                                        "groupids": [ObjectId(groupid) for groupid in updatedrules[ruleid]['groupids']],
                                                        "additionalrecepients": [ObjectId(others) for others in updatedrules[ruleid]['additionalrecepients']],
                                                        "actiontype": updatedrules[ruleid]['actiontype'],
                                                        "targetnode": updatedrules[ruleid]['targetnode'],
                                                        "actionon": updatedrules[ruleid]['actionon'] if 'actionon' in updatedrules[ruleid]  and updatedrules[ruleid]['actionon'] else 0,
                                                        "targetnodeid": ObjectId(updatedrules[ruleid]['targetnodeid']) if 'targetnodeid' in updatedrules[ruleid] and updatedrules[ruleid]['targetnodeid'] else 0
                                                    }   
                                                }
                                                
                                            ) for ruleid in updatedrules]
                
                deleted_rules_query = [DeleteOne({'_id':ObjectId(ruleid)}) for ruleid in deletedrules]
                updated_rules_query.extend(deleted_rules_query) 
                if len(updated_rules_query) > 0: dbsession.rules.bulk_write(updated_rules_query)
                
                total_rules = [ObjectId(id) for id in updatedrules]
                total_rules.extend(new_rule_ids)
                total_rules.extend(otherrules)
                dbsession.mindmaps.update_one(
                                                {"_id":ObjectId(requestdata['mindmapid'])},
                                                {"$set":{"rules":[ruleid for ruleid in total_rules]}}
                                            )
                taskdata = requestdata['taskdata']
                task_rule_map = {}
                taskquery = []
                for taskid in taskdata:
                    task_rule_map[taskid] = []
                    for ruleid in  taskdata[taskid]:
                        if ruleid in newrules:
                            task_rule_map[taskid].append(newrules[ruleid]['dbid'])
                        if ruleid in updatedrules or ruleid in requestdata['otherrules']:  
                            task_rule_map[taskid].append(ObjectId(ruleid))
                    taskquery.append(UpdateOne(
                                            {"_id":ObjectId(taskid)},
                                            {"$set":{"rules": task_rule_map[taskid]}}
                            ))
                
                if len(taskquery) > 0: dbsession.tasks.bulk_write(taskquery)
               
                res['rows'] = 'success'
                del res['err']
            else:
                app.logger.warn('Empty data received. report.')
                res['err']='Invalid Request: Empty Parameter not allowed'
        except Exception as e:
            servicesException("updateNotificationConfiguration", e, True)
            res['err'] = "Exception occurred in updateNotificationConfiguration"
        return jsonify(res)

################################################################################
# END OF NOTIFICATION SERVICES
################################################################################