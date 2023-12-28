import json
import requests
import rasa_query as rasafunctions
from http import HTTPStatus
from flask_caching import Cache

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

    cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 60})

    ##########################################################################################
    ################################## SUPPORTING FUNCTIONS ##################################
    ##########################################################################################

    # Function for request validation
    def validate_request(data, require_projectid=False, require_userid=False):
        projectid = data.get("projectid")
        userid = data.get("sender")
        message = data.get("message")
        metadata = data.get("metadata")
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

        # Check whether "senderid" is present or not
        if require_userid and not userid:
            return {"error": "sender is required"}

        return {
            "projectid": projectid,
            "userid": userid,
            "message": message,
            "metadata": metadata,
            "start_time": start_time,
            "end_time": end_time,
        }


    def compose_payload(data):
        payload = {
            "projectid": data["projectid"],
            "sender": data["userid"],
            "message": data["message"],
            "metadata": data["metadata"],
            "start_time": data["start_time"],
            "end_time": data["end_time"]
        }
        return payload


    def make_rasa_request(endpoint, payload):
        return requests.post(endpoint, json=payload)
    

    def handle_rasa_response(recipient_id, function_name, payload, client, getClientName):
        # This code dynamically checks if a function with a specific name exists in the 'rasafunctions' module
        if function_name in rasafunctions.__dict__ and callable(rasafunctions.__dict__[function_name]):
            function_to_call = rasafunctions.__dict__[function_name]
            datatype, result = function_to_call(payload, client, getClientName)

        transformed_data = {
            "_id": recipient_id,
            "_type": datatype,
            "data": result,
            "status": HTTPStatus.OK
        }

        # Store the result in the cache for 60 seconds
        cache.set(function_name, transformed_data, timeout=60)

        return jsonify(transformed_data), HTTPStatus.OK


    def get_cache_keys():
        return cache.cache._cache.keys()
    

    def get_cache_data(key):
        return cache.get(key)

    ##########################################################################################
    ################################## RASA SERVER ENDPOINT ##################################
    ##########################################################################################

    # rasa_server_endpoint = "https://avoaiapidev.avoautomation.com/rasa_model"
    rasa_server_endpoint = "http://127.0.0.1:5001/rasa_model"


    ##########################################################################################
    ##################################### MAIN API ROUTING ###################################
    ##########################################################################################

    # Status check API
    @app.route("/rasa_testing", methods=["GET"]) 
    def rasa_testing():
        return jsonify({"data": "Rasa DAS API is working...!!!", "status": HTTPStatus.OK}), HTTPStatus.OK
    

    @app.route('/rasa_prompt_model', methods=['POST'])
    def rasa_prompt_model():
        app.logger.debug("Inside rasa_prompt_model")
        try:
            requestdata = request.get_json()
            if not requestdata:
                return jsonify({"data":"Invalid Request Format", "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST
            
            # Check whether user is passing any message or not
            if requestdata["message"] == "":
                return jsonify({"data":"Please Ask a Question...!!!", "status": HTTPStatus.OK}), HTTPStatus.OK
            
            # Check for validating data of incoming request
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST
            
            payload = compose_payload(request_data)
            print(json.dumps(payload, indent=2))

            response = make_rasa_request(rasa_server_endpoint, payload)
            output = response.json()[0]
            recipient_id = output["recipient_id"]
            function_name = output["text"]
            
            # Check if the result is already in the cache
            cached_result = cache.get(function_name)
            if cached_result is not None:
                print("Generated result through cache")
                return jsonify({"data": cached_result, "status": HTTPStatus.OK}), HTTPStatus.OK
            else:
                return handle_rasa_response(recipient_id, function_name, payload, client, getClientName)
        
        except Exception as e:
            return jsonify({"message": str(e), "status": "error"}), HTTPStatus.INTERNAL_SERVER_ERROR