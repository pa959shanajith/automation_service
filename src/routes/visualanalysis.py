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
    def validate_request(data, require_projectid=False, require_userid=False, require_profileid=False, require_execListid=False, require_executionid=False):
        projectid = data.get("projectid")
        userid = data.get("userid")
        profileid = data.get("profileid")
        execListID = data.get("execlistid")
        executionid = data.get("executionid")
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
        
        # Check whether "executionid" is present or not
        if require_executionid and not executionid:
            return {"error": "executionid is required"}

        return {
            "projectid": projectid,
            "userid": userid,
            "profileid": profileid,
            "execListID": execListID,
            "executionid": executionid,
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
                        "$match": {
                            "configurekey": key,
                            "starttime": {"$gte": start_datetime, "$lte": end_datetime}
                            }
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


    # Function return module level execution status within a specified time range (for an execution)
    def fetch_modulelevel_execution_status(requestdata, executionlistid):
        try:
            clientName = getClientName(requestdata) 
            dbsession = client[clientName]
        except Exception as e:
            return e

        try:
            reports = list(dbsession.executions.aggregate([{"$match":{"executionListId":executionlistid}},
                                                        {"$project":{"parent":1,"status":1,"starttime":1}},
                                                        {'$lookup':{
                                                                        'from':"testsuites",
                                                                        'localField':"parent",
                                                                        'foreignField':"_id",
                                                                        'as':"testsuites"
                                                                        }
                                                                    },
                                                        {'$lookup':{
                                                                        'from':"reports",
                                                                        'localField':"_id",
                                                                        'foreignField':"executionid",
                                                                        'as':"reports"
                                                                        } 
                                                                    },
                                                        {"$project":{'modulename':{"$arrayElemAt":["$testsuites.name",0]},"status":1,"starttime":1, "scenarioStatus":"$reports.status"}},
                                                        {"$sort": {"starttime":-1}}
                                                        ]))

            # Count occurrences of each scenario status for each module
            result_list = []
            for data in reports:
                module_id = str(data['_id'])
                status = data['status']
                modulename = data['modulename']
                scenario_statuses = data['scenarioStatus']
                status_counts = Counter(scenario_statuses)
                
                result_data = {
                    '_id': module_id,
                    'modulename': modulename,
                    'status': status,
                    'scenarioStatus': dict(status_counts)
                }
                result_list.append(result_data)

            return result_list
        except Exception as e:
            return e


    # Function to fetch test step pass and fail count for a specific module
    def fetch_teststep_execution_status(requestdata, executionid):
        try:
            clientName = getClientName(requestdata) 
            dbsession = client[clientName]
        except Exception as e:
            return e
        
        try:
            pipeline = [
                    { "$match": { "executionid": executionid } },
                    { "$group": {
                        "_id": {  
                        "executionid": "$executionid",
                        "reportid": "$reportid",
                        "scenarioid": "$scenarioid", 
                        "status": "$status"
                        },
                        "count": { "$sum": 1 }
                    }},
                    { "$group": {
                        "_id": {
                        "executionid": "$_id.executionid",  
                        "reportid": "$_id.reportid",
                        "scenarioid": "$_id.scenarioid"
                        },
                        "statusCount": {
                        "$push": { 
                            "status": "$_id.status",
                            "count": "$count"  
                        }
                        }
                    }}
                ]
            result = dbsession.reportitems.aggregate(pipeline)

            transformed_data = []
            for entry in result:
                report_id = str(entry['_id']['reportid'])
                scenario_id = entry['_id']['scenarioid']

                # Fetch TCgroup_name from testscenario collection
                tc_group_name = dbsession.testscenarios.find_one({'_id': ObjectId(scenario_id)})['name']

                # Extract Pass and Fail counts
                pass_count = next((status['count'] for status in entry['statusCount'] if status.get('status') == 'Pass'), 0)
                fail_count = next((status['count'] for status in entry['statusCount'] if status.get('status') == 'Fail'), 0)

                # Create the desired format
                result_entry = {
                    "reportid": report_id,
                    "scenarioid": scenario_id,
                    "TCgroup_name": tc_group_name,
                    "TCStatus": {
                        "Pass": pass_count,
                        "Fail": fail_count
                    }
                }
                transformed_data.append(result_entry)

            return transformed_data
        except Exception as e:
            return e


    # Function to fetch defect analysis data
    def fetch_defect_data(requestdata, projectid, userid, starttime, endtime):
        try:
            clientName = getClientName(requestdata) 
            dbsession = client[clientName]
        except Exception as e:
            return e

        try:
            start_datetime, end_datetime = date_conversion(starttime, endtime)
            result = dbsession.configurekeys.find({"executionData.batchInfo.projectId": projectid,
                                                            "session.userid": userid},
                                                            {"_id":0,"token":1, 
                                                            "executionData.configurename":1})
            # Dictionary to store the transformed data
            transformed_data = []

            # Iterate over each profileid
            for key in result:
                profileid = key['token']
                profilename = key['executionData']['configurename']
                temp = dbsession.executions.aggregate([{
                                                        "$match": {
                                                            "configurekey": profileid,
                                                            "starttime": {"$gte": start_datetime, "$lte": end_datetime}
                                                            }
                                                        },
                                                    {
                                                        "$group": {
                                                            "_id":"$executionListId",
                                                            "executionids": {"$push": {"_id": "$_id"}},
                                                            }
                                                        },
                                                    ])
                
                defect_details = []
                count = 0
                for value in temp:
                    count += 1
                    executionlist_ID = value['_id']
                    execlist_name = "Execution" + str(count)
                    executionid_list = [str(execution['_id']) for execution in value.get('executionids', [])]

                    failcount_result = dbsession.reportitems.aggregate([{
                                                                                "$match": {
                                                                                "executionid": {"$in": executionid_list},
                                                                                "Keyword": {"$ne": "TestCase Name"}, 
                                                                                "status": "Fail"}
                                                                            },
                                                                            {"$group": {"_id": None, "count": {"$sum": 1}}}
                                                                            ])
                    
                    defect_details.append({
                        "execlistid": executionlist_ID,
                        "execlist_name": execlist_name,
                        "fail_count": failcount_result['count']
                    })

                # Update the transformed data dictionary
                transformed_data.append({
                    "profileid": profileid,
                    "profilename": profilename,
                    "defect_details": defect_details
                })    

            return transformed_data
            
        except Exception as e:
            return e



    #########################################################################
    ######################### MODULE EXECUTION API ##########################
    #########################################################################

    # Status check API
    @app.route("/visual_api_check", methods=["GET"])    
    def das_testing():
        return jsonify({"data": "Static Visualization API ready...!!!", "status": 200})
    

    # POST API to fetch executions count at module level
    @app.route("/profileLevel_ExecutionStatus", methods=["POST"])
    def api_profilelevel_execution_analysis():
        app.logger.debug("Inside Profile_Level_Execution_Status")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})
            
            projectid = request_data["projectid"]
            userid = request_data["userid"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]
            
            result = fetch_profilelevel_execution_status(requestdata, projectid, userid, start_time, end_time)
            print(json.dumps({"data": result, "start_time": start_time, "end_time": end_time, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})

        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})

    
    # POST API to fetch executions count at module level
    @app.route("/moduleLevel_ExecutionStatus", methods=["POST"])
    def api_modulelevel_execution_analysis():
        app.logger.debug("Inside Module_Level_Execution_Status")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_execListid=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})
            
            execListID = request_data["execListID"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]

            result = fetch_modulelevel_execution_status(requestdata, execListID)
            print(json.dumps({"data": result, "start_time": start_time, "end_time": end_time, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")

            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})

        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})
        
    
    # POST API to fetch test steps level executions status
    @app.route("/teststepLevel_ExecutionStatus", methods=["POST"])
    def teststep_execution_analysis():
        app.logger.debug("Inside TestStep_Level_Execution_Status")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_executionid=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})
            
            executionid = request_data["executionid"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]

            result = fetch_teststep_execution_status(requestdata, executionid)
            print(json.dumps({"data": result, "start_time": start_time, "end_time": end_time, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")
        
            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})

        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})


    #########################################################################
    ########################## DEFECT ANALYSIS API ##########################
    #########################################################################

    # POST API to fetch defect executions
    @app.route("/defect_analysis", methods=["POST"])
    def api_defect_execution_analysis():
        app.logger.debug("Inside Defect Analysis")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400})
            
            projectid = request_data["projectid"]
            userid = request_data["userid"]
            start_time = request_data["start_time"]
            end_time = request_data["end_time"]

            result = fetch_defect_data(requestdata, projectid, userid, start_time, end_time)
            print(json.dumps({"data": result, "start_time": start_time, "end_time": end_time, "status": 200}, indent=2))

            # Convert the date string to the desired format
            start_time = datetime.strptime(start_time, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_time = datetime.strptime(end_time, "%Y-%m-%d").strftime("%d/%m/%Y")
        
            return jsonify({"data": result, "start_time": start_time, "end_time": end_time, "status": 200})
        
        # Handle any exceptions with a 500 Internal Server Error response
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": 500})