from bson import ObjectId

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