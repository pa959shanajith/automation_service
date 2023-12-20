import json
from datetime import datetime, timedelta
from collections import Counter
import requests

from utils import *


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

    rasa_server_endpoint = "https://avoaiapidev.avoautomation.com/rasa_model"

    # Status check API
    @app.route("/rasa_testing", methods=["GET"]) 
    def rasa_testing():
        return jsonify({"data": "Rasa API is working...!!!", "status": 200})
    

    @app.route('/rasa_prompt_model', methods=['POST'])
    def rasa_prompt_model():
        try:
            payload = request.get_json()
            #print(json.dumps(data,indent=2))

            if not payload:
                return jsonify({"data":"Invalid Request Format", "status":400}), 400

            if payload["message"] == "":
                return jsonify({"data":"Please Ask a Question...!!!", "status":200}), 200

            # Make POST request to rasa server
            response = requests.post(rasa_server_endpoint, json=payload)
            output = response.json()[0]
            return jsonify(output), 200
        
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500