import json
from datetime import datetime, timedelta
from collections import Counter

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)


    #########################################################################
    ######################### API SUPPORT FUNCTIONS #########################
    #########################################################################

    # Function for request validation
    def validate_request(data, require_projectid=False, require_userid=False, require_profileid=False, require_execListid=False):
        projectid = data.get("projectid")
        userid = data.get("userid")
        profileid = data.get("profileid")
        execListID = data.get("execlistid")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # Case 1: User passes starttime but not endtime
        if start_time and not end_time:
            end_time = datetime.now().strftime("%Y-%m-%d")

        # Case 2: User didn't pass starttime and endtime
        if not start_time and not end_time: 
            end_time = datetime.now().strftime("%Y-%m-%d")
            six_months_ago = datetime.now() - timedelta(days=180)
            start_time = six_months_ago.strftime("%Y-%m-%d")

        # Check whether "projectid" is present or not
        if require_projectid and not projectid:
            return {"error": "projectid is required"}
        
        # Check whether "userid" is present if required
        if require_userid and not userid:
            return {"error": "userid is required"}
        
        # Check whether "profileid" is present or not
        if require_profileid and not profileid:
            return {"error": "profileid is required"}
        
        # Check whether "profileid" is present or not
        if require_execListid and not execListID:
            return {"error": "execListID is required"}

        return {
            "projectid": projectid,
            "userid": userid,
            "profileid": profileid,
            "execListID": execListID,
            "start_time": start_time,
            "end_time": end_time,
        }


    # convert the starttime and endtime in mongo comparable format
    def date_conversion(start_time, end_time):
        formatted_starttime = start_time + " 00:00:00.000Z"
        formatted_endtime = end_time + " 23:59:59.999Z"
        start_datetime = datetime.strptime(formatted_starttime, "%Y-%m-%d %H:%M:%S.%fZ")
        end_datetime = datetime.strptime(formatted_endtime, "%Y-%m-%d %H:%M:%S.%fZ")
        return start_datetime, end_datetime


    # Function to generate response data for module level execution status
    def fetch_profilelevel_execution_status(requestdata, projectid, userid, starttime, endtime):
        try:
            clientName = getClientName(requestdata) 
            print("REquest data: ", requestdata)     
            print("client name: ", clientName)     
            print()  
            dbsession = client[clientName]
        except Exception as e:
            return e

        try:
            start_datetime, end_datetime = date_conversion(starttime, endtime)
            result = list(dbsession.configurekeys.find({"executionData.batchInfo.projectId": projectid,
                                                            "session.userid": userid},
                                                            {"_id":0,"token":1, 
                                                            "executionData.configurename":1}))
            
            # Pipeline to fetch module level execution statuses
            def pipeline_function(key):
                pipeline = [
                    {
                        "$match":{"configurekey": key}
                        },
                    {
                        "$group": {
                            "_id":"$executionListId",
                            "modStatus": {
                                "$push": {
                                    "_id": "$_id",
                                    "status":"$status"
                                    }
                                },
                            "startDate": {
                                "$first": "$starttime"
                                }
                            }
                        },
                    {'$lookup': {
                            'from':"reports",
                            'localField':"modStatus._id",
                            'foreignField':"executionid",
                            'as':"reportdata"
                            }
                        },
                    {
                        "$project": {
                            "_id": 1,
                            "modStatus": "$modStatus.status",
                            "scestatus": "$reportdata.status",
                            "startDate": 1
                            }
                        },
                    {
                        "$sort": {"startDate":-1}
                        }
                ]
                result_1 =list(dbsession.executions.aggregate(pipeline))
                return result_1
            
            # Dictionary to store the transformed data
            transformed_data = []

            for keys in result:
                temp_dict = {}
                profileid = keys["token"]
                profilename = keys["executionData"]["configurename"]
                
                # Create a dictionary for each exec_detail
                exec = pipeline_function(profileid)

                exec_details = []
                count = 0
                for detail in exec:
                    count += 1
                    execlist_id = detail["_id"]
                    execlist_name = "Execution" + str(count)
                    executiontime = detail["startDate"]
                    mod_status_counter = Counter(detail["modStatus"])
                    sce_status_counter = Counter(detail["scestatus"])

                    exec_details.append({
                        "execlistid": execlist_id,
                        "execlist_name": execlist_name,
                        "execution_time": str(executiontime),
                        "mod_status": dict(mod_status_counter),
                        "sce_status": dict(sce_status_counter)
                    })

                # Update the transformed data dictionary
                transformed_data.append({
                    "profileid": profileid,
                    "profilename": profilename,
                    "exec_details": exec_details
                })

            return transformed_data
        
        except Exception as e:
            return e



    #########################################################################
    ######################### MODULE EXECUTION API ##########################
    #########################################################################

    # Status check API
    @app.route("/DAS_test", methods=["GET"])    
    def das_testing():
        return jsonify({"data": "Static Visualization API ready...!!!", "status": 200})
    

    # POST API to fetch executions count at module level
    @app.route("/profileLevel_ExecutionStatus", methods=["POST"])
    def api_profilelevel_execution_analysis():
        app.logger.debug("Inside Profile_Level_Execution_Status")
        try:
            data = request.get_json()
            request_data = validate_request(data, require_projectid=True, require_userid=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})
            
            projectid = request_data["projectid"]
            userid = request_data["userid"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]
            


            result = fetch_profilelevel_execution_status(data, projectid, userid, start_time, end_time)
            print(json.dumps({"data": result, "start_time": start_time, "end_time": end_time, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")

            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})

        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})