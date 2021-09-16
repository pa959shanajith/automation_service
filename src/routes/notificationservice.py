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

    @app.route('/notification/getNotificationRules',methods=['POST'])
    def getNotificationRules():
        app.logger.debug("Inside getNotificationRules")
        res={'rows':'fail','err':''}
        try:
            result = list(dbsession.ruletypes.find({},{'description':1, "actionid":1, "_id":0, "action":1}))
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
                priority = requestdata['priority']
                new_rules = [{
                                "groupids": [ObjectId(groupid) for groupid in newrules[ruleid]['groupids']],
                                "additionalrecepients": [ObjectId(others) for others in newrules[ruleid]['additionalrecepients']],
                                "actiontype": str(newrules[ruleid]['actiontype']),
                                "targetnode": newrules[ruleid]['targetnode'],
                                "actionon": newrules[ruleid]['actionon'] if 'actionon' in newrules[ruleid] and newrules[ruleid]['actionon'] else 0,
                                "targetnodeid": ObjectId(newrules[ruleid]['targetnodeid']) if 'targetnodeid' in newrules[ruleid] and newrules[ruleid]['targetnodeid'] else 0,
                                "mindmapid": ObjectId(requestdata['mindmapid']),
                                "priority": str(priority)
                            } for ruleid in newrules]
                new_rule_ids = []
                if len(new_rules) > 0:
                    insert_result = dbsession.ruleconfigurations.insert_many(new_rules,False,True)
                    for inserted_ids, rule_id in zip(insert_result.inserted_ids,newrules.keys()):
                        newrules[rule_id]['dbid'] = inserted_ids
                        new_rule_ids.append(inserted_ids)

                updated_rules_query = [UpdateOne(
                                                {'_id':ObjectId(ruleid)},
                                                {
                                                    '$set':{
                                                        "groupids": [ObjectId(groupid) for groupid in updatedrules[ruleid]['groupids']],
                                                        "additionalrecepients": [ObjectId(others) for others in updatedrules[ruleid]['additionalrecepients']],
                                                        "actiontype": str(updatedrules[ruleid]['actiontype']),
                                                        "targetnode": updatedrules[ruleid]['targetnode'],
                                                        "actionon": updatedrules[ruleid]['actionon'] if 'actionon' in updatedrules[ruleid]  and updatedrules[ruleid]['actionon'] else 0,
                                                        "targetnodeid": ObjectId(updatedrules[ruleid]['targetnodeid']) if 'targetnodeid' in updatedrules[ruleid] and updatedrules[ruleid]['targetnodeid'] else 0,
                                                        "priority": str(priority)
                                                    }   
                                                }
                                                
                                            ) for ruleid in updatedrules]
                
                deleted_rules_query = [DeleteOne({'_id':ObjectId(ruleid) if ruleid and ruleid != '' else 0}) for ruleid in deletedrules]
                updated_rules_query.extend(deleted_rules_query) 
                if len(updated_rules_query) > 0: dbsession.ruleconfigurations.bulk_write(updated_rules_query)

                taskdata = requestdata['taskdata']
                task_rule_map = {}
                taskquery = []
                for taskid in taskdata:
                    task_rule_map[taskid] = []
                    for ruleid in  taskdata[taskid]:
                        if ruleid in newrules:
                            task_rule_map[taskid].append(newrules[ruleid]['dbid']) 
                        else:    
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

    @app.route('/notification/updateTaskRules',methods=['POST'])
    def updateTaskRules():
        app.logger.debug("Inside updateTaskRules")
        res={'rows':'fail','err':''}
        try:
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                nodeid = requestdata['nodeid']
                ruleids = [ObjectId(ruleid) for ruleid in requestdata['ruleids']]
                dbsession.tasks.update_many({"nodeid":ObjectId(nodeid)},{'$set':{'rules':ruleids}})
                res['rows'] = 'success'
                del res['err']
            else:
                app.logger.warn('Empty data received. report.')
                res['err']='Invalid Request: Empty Parameter not allowed'
        except Exception as e:
            servicesException("updateTaskRules", e, True)
            res['err'] = "Exception occurred in updateTaskRules"
        return jsonify(res)


    @app.route('/notification/getNotificationConfiguration',methods=['POST'])
    def getNotificationConfiguration():
        app.logger.debug("Inside getNotificationConfiguration")
        res={'rows':'fail','err':''}
        try:
            email_projection = {'$project':{
                                    "actiontype":1, 
                                    "targetnode":1, 
                                    "actionon":1, 
                                    "targetnodeid":1, 
                                    "additionalrecepientsinfo":1, 
                                    "emails":{ '$setUnion':{
                                            '$reduce': {
                                                'input': "$usersemails",
                                                'initialValue': '$emails',
                                                'in': { '$concatArrays': [ "$$value",["$$this.email"]]}
                                            }
                                        }}
                                    }
                                }
            user_lookup = {'$lookup':{
                                'from':'users',
                                'let':{'userids':'$internalusers'},
                                'pipeline':[
                                    {"$match" : {"$expr" : {"$in": ["$_id", "$$userids"]}}},
                                    {'$project':{"_id":0,"email":1}}
                                ],
                                'as':'usersemails'
                            }
                        }
            groupinfo_projection = {'$project':{
                                        "actiontype":1, 
                                        "targetnode":1, 
                                        "actionon":1, 
                                        "targetnodeid":1, 
                                        "mindmapid":1, 
                                        "additionalrecepientsinfo":1, 
                                        "_id":1, 
                                        "internalusers":{'$setUnion':{
                                                '$reduce': {
                                                    'input': "$groupinfo",
                                                    'initialValue': '$additionalrecepients',
                                                    'in': { '$concatArrays': [ "$$value","$$this.internalusers"]}
                                                }
                                            }},
                                        "emails":{ '$setUnion':{
                                                '$reduce': {
                                                    'input': "$groupinfo",
                                                    'initialValue': [],
                                                    'in': { '$concatArrays': [ "$$value","$$this.otherusers"]}
                                                }
                                            }}
                                        }
                                    }
            notificationgroups_lookup = {"$lookup":{
                                            'from': "notificationgroups",
                                            'let': {"groupids": "$groupids"},
                                            'pipeline':[
                                                {"$match" : {"$expr" : {"$in": ["$_id", "$$groupids"]}}},
                                                {'$project':{"_id":1,"internalusers":1,"otherusers":1}},
                                            ],
                                            'as':"groupinfo",       
                                        }
                                    }
            rule_projection = {'$project':{
                                        'actiontype':'$ruleinfo.actiontype', 
                                        '_id':0,
                                        'targetnode':'$ruleinfo.targetnode',
                                        'actionon':'$ruleinfo.actionon',
                                        'targetnodeid':'$ruleinfo.targetnodeid',
                                        'additionalrecepientsinfo':'$ruleinfo.additionalrecepientsinfo',
                                        'emails':'$ruleinfo.emails'
                                    }
                                }
            
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                result = 'fail'
                if requestdata['fetchby'] == "mindmapbyrule":
                    mindmapid = requestdata['id']
                    aggregate_query = [
                                        {'$match':{'mindmapid': ObjectId(mindmapid)}},
                                        {'$match':{'targetnode':{'$in':['all',requestdata['nodetype']]}}},
                                        notificationgroups_lookup,
                                        groupinfo_projection,
                                        {
                                            '$lookup':{
                                                'from':'users',
                                                'let':{'userids':'$internalusers','extra':[ObjectId(id) for id in requestdata['extraids']]},
                                                'pipeline':[
                                                    {"$match" : {"$expr" :{'$or':[{"$in": ["$_id", "$$userids"]},{"$in": ["$_id", "$$extra"]}]}}},
                                                    {'$project':{"_id":0,"email":1}}
                                                ],
                                                'as':'usersemails'
                                            }
                                        },
                                        email_projection
                                    ] 
                    result = list(dbsession.ruleconfigurations.aggregate(aggregate_query))
                    result = [{"ruleinfo":result}]
                elif requestdata['fetchby'] == "mindmapid" and 'id' in requestdata:
                    mindmapid = requestdata['id']
                    priority = requestdata['priority'] if 'priority' in requestdata else '0'
                    aggregate_query = [
                                        {'$match':{'mindmapid':ObjectId(mindmapid)}},
                                        {'$match':{'mindmapid':priority}},
                                        {"$lookup":{
                                                'from': "notificationgroups",
                                                'let': {"groupids": "$groupids"},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$in": ["$_id", "$$groupids"]}}},
                                                    {'$project':{"_id":1,"groupname":1}},
                                                ],
                                                'as':"groupinfo",       
                                            }
                                        },
                                        {'$lookup':{
                                                'from':'users',
                                                'let':{'userids':'$additionalrecepients'},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$in": ["$_id", "$$userids"]}}},
                                                    {'$project':{"_id":1,"name":1}}
                                                ],
                                                'as':'additional'
                                            }
                                        },
                                        {'$lookup':{
                                                'from':'ruletypes',
                                                'let':{'id':'$actiontype'},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$eq": ["$actionid", '$$id']}}},
                                                    {'$project':{"_id":0,"description":1,"actionid":1,"action":1}}
                                                ],
                                                'as':'ruleinfo'
                                            }
                                        },
                                        {'$unwind':'$ruleinfo'},
                                        {'$project':{
                                                'targetnode':1,
                                                'actionon':1,
                                                'targetnodeid':1,
                                                'groupinfo':1,
                                                'additionalrecepients':'$additional',
                                                'ruledescription':'$ruleinfo.description',
                                                'actionid': '$ruleinfo.actionid',
                                                'action': '$ruleinfo.action'
                                            }
                                        }  
                                    ]  
                    result = list(dbsession.ruleconfigurations.aggregate(aggregate_query))
                elif requestdata['fetchby'] == "task" and 'id' in requestdata:
                    taskid = requestdata['id']
                    aggregate_query = [
                                        {'$match':{'_id': ObjectId(taskid)}},
                                        {"$lookup":{
                                                'from': "ruleconfigurations",
                                                'let': {"rules": "$rules"},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$in": ["$_id", "$$rules"]}}},
                                                    {"$match" : {'$expr' : {'$eq': ['$actiontype',requestdata['ruleactionid']]}}},
                                                    notificationgroups_lookup,
                                                    groupinfo_projection,
                                                    user_lookup,
                                                    email_projection   
                                                ],
                                                'as':"ruleinfo"
                                            }
                                        },
                                        {"$lookup":{
                                                'from': 'users',
                                                'let': {'ids':['$owner','$reviewer']},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$in": ["$_id", '$$ids']}}},
                                                    {'$project':{"_id":1,"name":1,"email":1}}
                                                ],
                                                'as':'taskowners'
                                            }
                                        },
                                        {'$project':{'ruleinfo':1,'_id':0,'taskowners':1,'reviewer':1,'assignedto':'$owner'}}
                                    ]
                    result = list(dbsession.tasks.aggregate(aggregate_query))
                elif requestdata['fetchby'] == "testsuiteid" and 'id' in requestdata:
                    testsuiteid = requestdata['id']
                    nodetype = requestdata['nodetype']
                    actiontype = requestdata['actiontype'] 
                    invoker = dbsession.users.find_one({'_id':ObjectId(requestdata['invokerid'])},{'email':1,'_id':0})
                    aggregate_query = [
                                        {'$match':{'_id': ObjectId(testsuiteid)}},
                                        {'$lookup':{
                                                'from': "ruleconfigurations",
                                                'let':{'id':'$mindmapid'},
                                                'pipeline':[
                                                    {"$match" : {"$expr" : {"$eq": ["$mindmapid", "$$id"]}}},
                                                    {"$match" : {"$expr" : {"$in": ["$targetnode", ["all",nodetype]]}}},
                                                    {"$match" : {"$expr" : {"$eq": ["$actiontype", actiontype]}}},
                                                    notificationgroups_lookup,
                                                    groupinfo_projection,
                                                    user_lookup,
                                                    email_projection
                                                ],
                                                'as':'ruleinfo'
                                            }
                                        }
                                    ]
                    result = list(dbsession.testsuites.aggregate(aggregate_query))
                    if len(result) > 0:
                        result[0]['taskowners'] = [invoker] 
                    else:
                        result.append({'taskowners':[invoker] })
                res['rows'] = result
                del res['err']
            else:
                app.logger.warn('Empty data received. report.')
                res['err']='Invalid Request: Empty Parameter not allowed'
        except Exception as e:
            servicesException("getNotificationConfiguration", e, True)
            res['err'] = "Exception occurred in getNotificationConfiguration"
        return jsonify(res)

################################################################################
# END OF NOTIFICATION SERVICES
################################################################################