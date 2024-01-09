from bson import ObjectId
import pipelines

##########################################################################################
################################### COMMON FUNCTIONS #####################################
##########################################################################################

# Mapping for returned data type
data_type = {
    "table": "table",
    "chart": "chart",
    "text": "text",
    "table/chart": "table/chart"
}

# Mapping for chart type
chart_type = {
    "category1": ["bar", "pie", "doughnut"],
    "category2": ["line"]
}


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
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        userid = requestdata["sender"]

        # Data processing
        data_pipeline = pipelines.fetch_projects(userid=userid)
        result = list(dbsession.users.aggregate(data_pipeline))
        return data_type["table"], result

    except Exception as e:
        return e


# Function to fetch the users assigned in a project
def list_of_users(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]

        # Data processing
        data_pipeline = pipelines.fetch_users(projectid=projectid)
        result1 = list(dbsession.users.aggregate(data_pipeline))
        result2 = {
            "Total Users": len(result1),
            "chart_types": chart_type["category1"]
            }
        
        # Final output
        result = {"table_data": result1, "chart_data": result2}
        return data_type["table/chart"], result

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


# Function to fetch module fail count for all the profiles created by user
def module_with_more_defects(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        results = list(dbsession.configurekeys.find({"executionData.batchInfo.projectId": projectid,
                                                            "session.userid": userid},
                                                            {"_id":0,"token":1, 
                                                            "executionData.configurename":1}))
        
        def mongoPipeline(key):
            # Define the aggregation pipeline
            pipeline = [
                        {
                            "$match": {"configurekey": key, "status": "fail"}
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
                                "module_name": {"$arrayElemAt":["$module_name",0]}, 
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

        modules=[]
        for keys in results:
            profileid = keys["token"]
            profilename = keys["executionData"]["configurename"]
        
            # Create a dictionary for each exec_detail
            exec = mongoPipeline(profileid)
            result =list(dbsession.executions.aggregate(exec))
            if result:
                modules.append(result[0])
        return data_type[4], modules

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