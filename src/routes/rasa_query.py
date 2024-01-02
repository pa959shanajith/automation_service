from bson import ObjectId

# Dictionary to store the type of presentable data
data_type = {
    1: "table",
    2: "chart",
    3: "text",
    4: "table/chart"
}

##########################################################################################
#################################### MONGO FUNCTIONS #####################################
##########################################################################################

def list_of_projects(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        datatype = data_type[1]
        result = list(dbsession.projects.find({}, {"name":1}))
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

    
def default_fallback(requestdata, client, getClientName):
    try:
        datatype = data_type[3]
        result = "I'm sorry, I don't have an answer for that right now. I'll learn and improve over time. Please ask another question."
        return datatype, result
    except Exception as e:
        return e