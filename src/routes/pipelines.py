from bson import ObjectId


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
            {"$project": {"name":1}},
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
                "suite_names": {"$arrayElemAt":["$suiteData.name",0]}
            }
        }
    ]
    return pipeline 


####################################################################################
##################################### DEFECT #######################################
####################################################################################

def pipeline_project_having_more_defects():
    pass