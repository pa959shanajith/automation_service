from bson import ObjectId

# Dictionary to store the type of presentable data
data_type = {
    1: "table",
    2: "chart",
    3: "text",
    4: "table/chart"
}

##########################################################################################
################################### COMMON FUNCTIONS #####################################
##########################################################################################

def mongo_connection(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
        return dbsession
    except Exception as e:
        return e


##########################################################################################
################################### MODULE FUNCTIONS #####################################
##########################################################################################

# Function fetches all the projects the user is assigned to along with their role names
def list_of_projects(requestdata, client, getClientName):
    dbsession = mongo_connection(requestdata, client, getClientName)

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
            {"$project": {
                "projectId": 1,
                "projectName": 1,
                "assignedRole": {
                    "$toObjectId": "$assignedRole"
                }}
            },
            {"$lookup": {
                "from": "permissions", 
                "localField": "assignedRole",
                "foreignField": "_id",
                "as": "rolename"
                }},
            {"$project": {
                "_id":0,
                "projectName": 1,
                "rolename": {"$arrayElemAt": ["$rolename.name",0]}
                }}
        ]
        result = list(dbsession.users.aggregate(pipeline))
        return result
    
    try:
        datatype = data_type[1]
        userid = requestdata["sender"]
        result = fetch_projects(userid=userid)
        return datatype, result
    except Exception as e:
        return e


def list_of_project_users(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        projectid = requestdata["projectid"]
        datatype = data_type[1]
        result = list(dbsession.users.find({"projects": ObjectId(projectid)}, {"name":1}))
        result.append({"Total Users": len(result)})
        return datatype, result
    except Exception as e:
        return e


def count_mod_executed_proj_prof_level(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    def get_pipeline():
        pass

    try:
        user_id = requestdata["sender"]
        profile_id = requestdata["metadata"]["profileid"]
        role_id = requestdata["roleid"]

        # Fetch the assigned role for this role_id
        role_name = list(dbsession.permissions.find({"_id":ObjectId(role_id)}, {"_id":0, "name":1}))[0]["name"]

        # Project Level Data
        if not profile_id:
            pass
        #     if role_name == "Quality Manager":
        #         pipeline = get_pipeline()
        #         result = dbsession.aggregate(pipeline)

        #     elif role_name == "Quality Lead":
        #         pipeline = get_pipeline(user_id=user_id)
        #         result = dbsession.aggregate(pipeline)

        # Profile Level Data
        else:
            pipeline = get_pipeline(profile_id=profile_id, user_id=user_id)  
            # result = dbsession.aggregate(pipeline)

        return "text", "testing code"

    except Exception as e:
        pass


def mod_executed_proj_prof_level(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # Data at project level
        if not profileid:
            results = list(dbsession.configurekeys.find({"executionData.batchInfo.projectId": projectid,
                                                        "session.userid": userid},
                                                        {"_id":0,"token":1, 
                                                        "executionData.configurename":1}))
            print(results)
            return "text", "Shaurya Suman"

    except Exception as e:
        return e


##########################################################################################
################################### DEFECT FUNCTIONS #####################################
##########################################################################################
    
def project_having_more_defects(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        project_id = requestdata["projectid"]
        user_id = requestdata["sender"]
        role_id = requestdata["roleid"]
        profile_id = requestdata["metadata"]["profileid"]
 
        # Fetch the assigned role for this role_id
        role_name = list(dbsession.permissions.find({"_id":ObjectId(role_id)}, {"_id":0, "name":1}))[0]["name"]
        
 
        # # Project Level Data
        # if not profile_id:
        #     if role_name == "Quality Manager":
        #         pipeline_result = get_pipeline(projectid=project_id)
        #         return pipeline_result
 
        #     elif role_name == "Quality Lead":
        #         pipeline_result = get_pipeline(projectid=project_id, userid=user_id)
        #         # result = dbsession.aggregate(pipeline)
        #         return pipeline_result
 
        # # Profile Level Data
        # else:
        #     pipeline_result = get_pipeline(projectid=project_id, userid=user_id, profileid=profile_id)  
        #     # result = dbsession.aggregate(pipeline)
        #     return pipeline_result
 
    except Exception as e:
        return e

##########################################################################################
################################### DEFAULT FUNCTIONS ####################################
##########################################################################################
    
def default_fallback(requestdata, client, getClientName):
    try:
        datatype = data_type[3]
        result = "I'm sorry, I don't have an answer for that right now. I'll learn and improve over time. Please ask another question."
        return datatype, result
    except Exception as e:
        return e