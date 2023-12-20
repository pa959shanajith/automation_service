import json
from datetime import datetime, timedelta
from collections import Counter

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)


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


    ################## API FUNCTIONS ####################################33

    # convert the starttime and endtime in mongo comparable format
    def date_conversion(start_time, end_time):
        formatted_starttime = start_time + " 00:00:00.000Z"
        formatted_endtime = end_time + " 23:59:59.999Z"
        start_datetime = datetime.strptime(formatted_starttime, "%Y-%m-%d %H:%M:%S.%fZ")
        end_datetime = datetime.strptime(formatted_endtime, "%Y-%m-%d %H:%M:%S.%fZ")
        return start_datetime, end_datetime

    #---------------Fetching the profiles----------------------
    def fetch_profile_names(requestdata,projectid, userid, starttime, endtime):
        try:
            clientName = getClientName(requestdata)
            dbsession = client[clientName]
        except Exception as e:
            return e

        try:
            start_datetime, end_datetime = date_conversion(starttime, endtime)
            result = list(dbsession.configurekeys.aggregate([{"$match": {
                                                                "executionData.batchInfo.projectId": projectid,
                                                                "session.userid": userid
                                                                }},
                                                                {"$project": {
                                                                        "username": "$session.username",
                                                                        "profileName": "$executionData.configurename",
                                                                        "configkey": "$token"}
                                                                }]))
            
            # Create a dictionary in the desired format
            output_dict = {
                "projectid": projectid,
                "userid": userid,
                "username": result[0]["username"],
                "profiles": {}
            }

            # Iterate through the given data and populate the "profiles" dictionary
            for entry in result:
                profile_id = entry['configkey']
                profile_name = entry['profileName']
                output_dict["profiles"][profile_id] = profile_name
            
            return output_dict
        
        except Exception as e:
                return e



    ############################ MODULE EXECUTION API #############################
        
    # Basic API status check
    @app.route("/prompt_based_analysis", methods=["GET"])
    def prompt_based_analysis_testing():
        return jsonify({"data": "Prompt Based Analysis API ready...!!!", "status": 200})


    # POST API to fetch all profile names inside a username at project level
    @app.route("/fetch_profiles", methods=["POST"])
    def fetch_profile_names():
        app.logger.dubug("Inside fetching profiles")
        try:
            requestdata = request.get_json()
            # Validate the request
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})

            projectid = request_data["projectid"]
            userid = request_data["userid"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]

            result = fetch_profile_names(requestdata, projectid, userid, start_time, end_time)
            print(json.dumps({"data": result, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")
                
            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})

            # return Response(json.dumps({"data": result, "status": 200}), content_type='application/json')

        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})