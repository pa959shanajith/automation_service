from bson import ObjectId

####################################################################################
##################################### COMMON #######################################
####################################################################################

def fetch_tokens(projectid, userid):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid
            }
        },
        {
            "$project": {
                "_id": 0,
                "token": 1,
                "executionData.configurename": 1
            }
        }
    ]
    return pipeline

 
####################################################################################
#################################### EXECUTION #####################################
####################################################################################

def fetch_projects(userid):
    pipeline = [
            {"$match": {"_id": ObjectId(userid)}},
            {"$lookup": {
                "from": "projects", 
                "localField": "projects",
                "foreignField": "_id",
                "as": "projectDetails"
            }},
            {"$unwind": "$projectDetails"},
            {"$project": {
                "projectId": "$projectDetails._id",
                "projectName": "$projectDetails.name", 
                "assignedRole": {"$arrayElemAt": [
                "$projectlevelrole.assignedrole",  
                {"$indexOfArray": ["$projects", "$projectDetails._id"]}
                ]}
            }},
            {
                "$addFields": {"roleid": {"$toObjectId": "$assignedRole"}}
            },
            {"$lookup": {
                "from": "permissions", 
                "localField": "roleid",
                "foreignField": "_id",
                "as": "rolename"
                }},
            {"$project": {
                "_id":0,
                "projectName": 1,
                "rolename": {"$arrayElemAt": ["$rolename.name",0]}
                }}
        ]
    return pipeline


def fetch_users(projectid):
    pipeline = [
            {"$match": {"projects": ObjectId(projectid)}},
            {"$project": {"name":1, "_id":0}},
            # need to add role name in the output (database bug)
        ]
    return pipeline


def pipeline_list_module_executed(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent"
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "suiteData"
            }
        },
        {
            "$project": {
                "_id":0,
                "Module Names": {"$arrayElemAt":["$suiteData.name",0]}
            }
        }
    ]
    return pipeline 


def pipeline_count_module_executed(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "Count": {"$sum": 1}
            },  
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "Module Name"
            }
        },
        {
            "$project": {
                "Module Name": {"$arrayElemAt": ["$Module Name.name",0]},
                "Count": 1,
                "_id":0
            }
        },
        {
            "$sort": {
                "Count": -1
            }
        }
    ]
    return pipeline


####################################################################################
##################################### DEFECT #######################################
####################################################################################

def pipeline_module_level_defects_trend_analysis(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "status": {"$in":["Fail","fail"]},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "status_count": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$project": {
                "Module Name": {"$arrayElemAt": ["$moduledata.name",0]},
                "Fail Count": "$status_count",
                "_id":0
            }
        },
        {
            "$sort": {
                "Fail Count": -1
            }
        }
    ]
    return pipeline


def pipeline_module_with_more_defects(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens}, 
                "status": {"$in": ["Fail","fail"]}, 
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}}
        },
        {
            "$project": {
                "parent": "$parent",
                "status": "$status"
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "parent",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "module_name": {"$first": "$moduledata.name"},
                "fail_count": {"$sum": {"$cond": {"if": {"$eq": ["$status", "fail"]}, "then": 1, "else": 0}}},
                "total_count": {
                    "$sum": {
                        "$cond": {
                            "if": {"$in": ["$status", ["pass", "fail"]]},
                            "then": 1,
                            "else": 0
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "module_name": "$module_name", 
                "defect_count": "$fail_count",
                "_id": 0
            }
        },
        {
            "$sort": {"defect_count": -1}
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


