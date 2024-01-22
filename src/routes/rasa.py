import requests
import rasaquery as rasafunctions
from http import HTTPStatus
from flask import Response

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

    ##########################################################################################
    ################################## SUPPORTING FUNCTIONS ##################################
    ##########################################################################################
    
    # Function for request validation
    def validate_request(data, require_projectid=False, require_userid=False, require_metadata=False):
        """
        Validate incoming request data
        Parameters:
            data (dict): Request data
            require_projectid (bool): Whether projectid is required
            require_userid (bool): Whether userid is required
            require_metadata (bool): Whether metadata is required 
        Returns:
            dict: Validation result  
        """

        projectid = data.get("projectid")
        userid = data.get("sender")
        message = data.get("message")
        metadata = data.get("metadata")
        start_time = data.get("starttime")
        end_time = data.get("endtime")

        # Case 1: User passes starttime but not endtime
        if start_time and not end_time:
            end_time = datetime.now().strftime("%Y-%m-%d")

        # Case 2: User didn't pass starttime and endtime
        if not start_time and not end_time:
            end_time = datetime.now().strftime("%Y-%m-%d")
            six_months_ago = datetime.now() - timedelta(days=180)
            start_time = six_months_ago.strftime("%Y-%m-%d")

        # Case 3: User passes endtime but not starttime
        if end_time and not start_time:
            end_time = datetime.now().strftime("%Y-%m-%d")
            six_months_ago = datetime.now() - timedelta(days=180)
            start_time = six_months_ago.strftime("%Y-%m-%d")

        # Check whether "projectid" is present or not
        if require_projectid and not projectid:
            return {"error": "projectid is required"}

        # Check whether "senderid" is present or not
        if require_userid and not userid:
            return {"error": "sender is required"}
        
        # Check whether "metadata" is present or not
        if require_metadata and not metadata:
            return {"error": "metadata is required"}

        return {
            "projectid": projectid,
            "userid": userid,
            "message": message,
            "metadata": metadata,
            "start_time": start_time,
            "end_time": end_time,
        }


    # Function to compose payload
    def compose_payload(data):
        payload = {
            "projectid": data["projectid"],
            "sender": data["userid"],
            "message": data["message"],
            "metadata": data["metadata"],
            "starttime": data["start_time"],
            "endtime": data["end_time"]
        }
        return payload


    # Function to make rasa request
    def make_rasa_request(endpoint, payload):
        return requests.post(endpoint, json=payload)
    

    # Function for dynamic function calling
    def handle_rasa_response(recipient_id, function_name, payload, client, getClientName):
        # This code dynamically checks if a function with a specific name exists in the 'rasafunctions' module
        if function_name in rasafunctions.__dict__ and callable(rasafunctions.__dict__[function_name]):
            function_to_call = rasafunctions.__dict__[function_name]
            datatype, summary, result = function_to_call(payload, client, getClientName)

        else:
            datatype = "text"
            summary = ""
            result = "I'm sorry, I don't have an answer for that right now. I'll learn and improve over time. Please ask another question."
            
        transformed_data = {
            "_id": recipient_id,
            "_type": datatype,
            "_summary": summary,
            "data": result,
            "status": HTTPStatus.OK
        }
        app.logger.debug("rasa_prompt_model returned successful")

        # Store the result in the cache for 60 seconds
        # cache.set(function_name, transformed_data, timeout=60)
        return Response(json.dumps(transformed_data)), HTTPStatus.OK


    ##########################################################################################
    ################################## RASA SERVER ENDPOINT ##################################
    ##########################################################################################

    rasa_server_endpoint = "https://avoaiapidev.avoautomation.com/rasa_model" #enable it to use for production
    # rasa_server_endpoint = "http://127.0.0.1:5001/rasa_model"


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
                transformed_data = {
                    "_type": "no_message",
                    "_summary": "Please Ask a Question...!!!",
                    "data": {"table_data": None, "chart_data": None},
                    "status": HTTPStatus.OK
                }
                return jsonify(transformed_data), HTTPStatus.OK
            
            # Check for validating data of incoming request
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True, require_metadata=True)

            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": HTTPStatus.BAD_REQUEST}), HTTPStatus.BAD_REQUEST
            
            # Compose payload to send to Rasa
            payload = compose_payload(request_data)
            # print("Payload: ", json.dumps(payload, indent=2))

            # Getting RASA response
            response = make_rasa_request(rasa_server_endpoint, payload)

            # fetch required data from RASA response
            output = response.json()[0]
            recipient_id = output["recipient_id"]
            function_name = output["custom"]["function_name"]
            
            return handle_rasa_response(recipient_id, function_name, payload, client, getClientName)
        
        except Exception as e:
            return jsonify({"message": str(e), "status": "error"}), HTTPStatus.INTERNAL_SERVER_ERROR