from bson import ObjectId
import pipelines
from utils import *

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


# Function for database connection
def mongo_connection(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
        return dbsession
    except Exception as e:
        return e
    

# Function to convert dates in mongo comparable format
def date_conversion(request):
    start_time = request["starttime"]
    end_time = request["endtime"]

    formatted_starttime = start_time + " 00:00:00.000Z"
    formatted_endtime = end_time + " 23:59:59.999Z"
    start_datetime = datetime.strptime(formatted_starttime, "%Y-%m-%d %H:%M:%S.%fZ")
    end_datetime = datetime.strptime(formatted_endtime, "%Y-%m-%d %H:%M:%S.%fZ")

    return start_datetime, end_datetime


class DataPreparation:

    # Function to process tabular data
    def process_table_data(dbsession, collectionname, pipeline):
        collection = getattr(dbsession, collectionname)
        result = list(collection.aggregate(pipeline))
        return result


    def process_final_chart_data(**kwargs):
        # Access the desired values from kwargs
        title = kwargs.get("title", "")
        labels = kwargs.get("labels", [])
        backgroundColor = kwargs.get("backgroundColor", [])
        chartsData = kwargs.get("chartsData", [])
        chartType = kwargs.get("chartType", [])
        displayLegend = kwargs.get("displayLegend", "false")

        data = {
            "title": title,
            "labels": labels,
            "backgroundColor": backgroundColor,
            "chartsData": chartsData,
            "chartType": chartType,
            "displayLegend": displayLegend
        }
        return data


    def merge_table_and_chart_data(tabledata, chartdata):
        merged_data = {"table_data": tabledata, "chart_data": chartdata}
        return merged_data



##########################################################################################
################################# EXECUTION FUNCTIONS ####################################
##########################################################################################

# Function fetches all the projects the user is assigned to along with their role names
def list_of_projects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        userid = requestdata["sender"]

        # Summary for the response
        collection_name = "users"
        title = "Total Projects"
        labels = "Project Count"
        color = "#36a2eb"
        charttype = ["pie", "doughnut"]

        # Data processing
        data_pipeline = pipelines.fetch_projects(userid=userid)
        table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
        chart_result = None  # Initialize chart_result to None
        
        if table_result:
            # Pass values to process_final_chart_data using **kwargs
            chart_result = DataPreparation.process_final_chart_data(
                                                                title=title,
                                                                labels=labels,
                                                                backgroundColor=color,
                                                                chartsData=len(table_result),
                                                                chartType=charttype,
                                                                displayLegend="true"
                                                            )
            datatype = data_type["table/chart"]
            summary = "Please find the list of projects assigned to you along with the role names."
        else:
            datatype = data_type["text"]
            summary = "No data found for the requested query"

        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch the users assigned in a specific project with their roles
def list_of_users(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Data processing
        data_pipeline = pipelines.fetch_users(projectid=projectid)
        result1 = list(dbsession.users.aggregate(data_pipeline))
        result2 = {
            "Total Users": len(result1),
            "chart_types": chart_type["category1"]
            }
        
        if not result1 or not result2:
            return data_type["text"], "Data not found..!!!"
        else:
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


# Function to fetch the list of modules executed in a project or profile
def list_module_executed(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["userid"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        collection_name = "executions"

        # Data processing
        if profileid:
            data_pipeline = pipelines.pipeline_list_module_executed(tokens=[profileid], start_datetime=starttime, end_datetime=endtime)
            result = process_data(dbsession, collection_name, data_pipeline)
            return result

        else:
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
        
            data_pipeline = pipelines.pipeline_list_module_executed(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            result = process_data(dbsession, collection_name, data_pipeline)
            return result

    except Exception as e:
        return e


##########################################################################################
################################### DEFECT FUNCTIONS #####################################
##########################################################################################
    
def project_having_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Data processing
        data_pipeline = pipelines.pipeline_project_having_more_defects()
 
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