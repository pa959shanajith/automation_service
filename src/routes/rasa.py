import json
from datetime import datetime, timedelta
from collections import Counter
import requests
import rasa_query as rasafunctions

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

    ##########################################################################################
    ############################## FUNCTION FOR REQUEST VALIDATION ###########################
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


    # rasa_server_endpoint = "https://avoaiapidev.avoautomation.com/rasa_model"
    rasa_server_endpoint = "http://127.0.0.1:5001/rasa_model"


    ##########################################################################################
    ##################################### MAIN API ROUTING ###################################
    ##########################################################################################

    # Status check API
    @app.route("/rasa_testing", methods=["GET"]) 
    def rasa_testing():
        return jsonify({"data": "Rasa DAS API is working...!!!", "status": 200})
    

    @app.route('/rasa_prompt_model', methods=['POST'])
    def rasa_prompt_model():
        app.logger.debug("Inside rasa_prompt_model")
        try:
            requestdata = request.get_json()
            if not requestdata:
                return jsonify({"data":"Invalid Request Format", "status":400}), 400
            
            # Check whether user is passing any message or not
            if requestdata["message"] == "":
                return jsonify({"data":"Please Ask a Question...!!!", "status":200}), 200
            
            # Check for validating data of incoming request
            request_data = validate_request(requestdata, require_projectid=True, require_userid=True)
            if "error" in request_data:
                return jsonify({"data": request_data["error"], "status": 400}), 400
            
            # Compose request for Rasa
            payload = compose_payload(request_data)
            print(json.dumps(payload, indent=2))

            # Make POST request to rasa server
            response = requests.post(rasa_server_endpoint, json=payload)
            output = response.json()[0]
            function_name = output["text"]

            # This code dynamically checks if a function with a specific name exists in the 'rasafunctions' module, 
            # and if it does, it calls the function and stores the result.
            if function_name in rasafunctions.__dict__ and callable(rasafunctions.__dict__[function_name]):
                function_to_call = rasafunctions.__dict__[function_name]
                print("Function to call: ", function_to_call)
                result = function_to_call(payload, client, getClientName)
            else:
                print(f"Function '{function_name}' not found")

            transformed_data = {
                "recipient_id": output["recipient_id"],
                "data": result,
                "status": 200
            }

            return jsonify(transformed_data), 200
        
        except Exception as e:
            return jsonify({"message": str(e), "status": "error"}), 500