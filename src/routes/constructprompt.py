from http import HTTPStatus

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

    #########################################################################
    ######################### API SUPPORT FUNCTIONS #########################
    #########################################################################

    # Function for request validation
    def validate_request(data, require_userid=False, require_projectid=False, require_token=False):
        userid = data.get("userid")
        projectid = data.get("projectid")
        configkey = data.get("configkey")

        # Check whether "userid" is present if required
        if require_userid and not userid:
            return {"error": "userid is required"}
        
        # Check whether "projectid" is present if required
        if require_projectid and not projectid:
            return {"error": "projectid is required"}
        
        # Check whether "token" is present if required
        if require_token and not configkey:
            return {"error": "configkey is required"}
        
        return {
            "userid": userid,
            "projectid": projectid,
            "configkey": configkey
        }
    

    def mongo_connection(requestdata, client, getClientName):
        try:
            clientName = getClientName(requestdata)
            dbsession = client[clientName]
            return dbsession
        except Exception as e:
            return e
    

    def fetch_projectlist(requestdata, userid):
        dbsession = mongo_connection(requestdata, client, getClientName)

        try:
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
                    "projectId":1,
                    "projectName": 1,
                    "rolename": {"$arrayElemAt": ["$rolename.name",0]}
                    }}
                ]
            result = list(dbsession.users.aggregate(pipeline))
            return result
        except Exception as e:
            return e


    def fetch_profilelist(requestdata, userid, projectid):
        dbsession = mongo_connection(requestdata, client, getClientName)
        
        try:
            pipeline = [
                    {
                        "$match": {
                            "executionData.batchInfo.projectId": projectid,
                            "session.userid": userid
                        }
                    },
                    {
                        "$project": {
                            "token":1,
                            "profilename": "$executionData.configurename"
                        }
                    }
                ]
            result = list(dbsession.configurekeys.aggregate(pipeline))
            
            return result
        except Exception as e:
            return e
        

    def fetch_modulelist(requestdata, token):
        dbsession = mongo_connection(requestdata, client, getClientName)
        try:
            pipeline = [
                    {
                        "$match": {"configkey": token}
                    },
                    {"$unwind": "$executionData.batchInfo"},
                    {
                        "$group": {
                        "_id": "$executionData.batchInfo.testsuiteId",
                        "testsuiteName": {"$first": "$executionData.batchInfo.testsuiteName"}
                        }
                    },
                ]
            result = list(dbsession.executionlist.aggregate(pipeline))
            return result
        
        except Exception as e:
            return e


    ##########################################################################
    ############################# MAIN API ROUTING ###########################
    ##########################################################################

    # Status check API
    @app.route("/construct_prompt_testing", methods=["GET"]) 
    def construct_prompt_testing():
        return jsonify({"data": "Construct Prompt API is working...!!!", "status": HTTPStatus.OK}), HTTPStatus.OK
    
    
    @app.route("/fetch_projects", methods=["POST"]) 
    def fetch_projects():
        app.logger.debug("Inside Fetch Projects")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_userid=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST

            userid = request_data["userid"]
            
            result = fetch_projectlist(requestdata, userid)
            return jsonify({"data": result, "status": HTTPStatus.OK}), HTTPStatus.OK
        
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": HTTPStatus.INTERNAL_SERVER_ERROR}),HTTPStatus.INTERNAL_SERVER_ERROR
        

    @app.route("/fetch_profiles", methods=["POST"]) 
    def fetch_profiles():
        app.logger.debug("Inside Fetch Profiles")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_userid=True, require_projectid=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST

            userid = request_data["userid"]
            projectid = request_data["projectid"]
            
            result = fetch_profilelist(requestdata, userid, projectid)
            return jsonify({"data": result, "status": HTTPStatus.OK}), HTTPStatus.OK
        
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": HTTPStatus.INTERNAL_SERVER_ERROR}),HTTPStatus.INTERNAL_SERVER_ERROR
        

    @app.route("/fetch_modules", methods=["POST"]) 
    def fetch_modules():
        app.logger.debug("Inside Fetch Modules")
        try:
            requestdata = request.get_json()
            request_data = validate_request(requestdata, require_token=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST

            token = request_data["configkey"]
            
            result = fetch_modulelist(requestdata, token)
            return jsonify({"data": result, "status": HTTPStatus.OK}), HTTPStatus.OK
        
        except Exception as e:
            return jsonify({"data": {"message": str(e)}, "status": HTTPStatus.INTERNAL_SERVER_ERROR}),HTTPStatus.INTERNAL_SERVER_ERROR