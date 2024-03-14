import requests
import rasaquery as rasafunctions
from http import HTTPStatus

from utils import *
from generateAI_module import OpenAI_LLM_Model,Other_LLM_Model,Template_Model

def LoadServices(app, redissession, client ,getClientName):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

# BEGIN OF REPORTS
# INCLUDES : all reports related actions
    @app.route('/genAI/validateAI_Token', methods=['POST'])
    def validateToken():
        try:
            request_data = request.get_json()
            required_fields = ['token', 'type','baseURL']
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            headers = {
                'Accept': 'application/json',
                'Content-Type':'application/json'
            }
            addr = "https://aiapidevtest.avoassurecloud.com"
            test_url = addr + '/generate_testcase'
           
            data={'token':request_data['token'], 'type':request_data['type'],'baseURL':request_data['baseURL']}
            json_data = json.dumps(data)
            response = requests.post(test_url,headers=headers,data=json_data,verify = False,timeout=None)
            if response.status_code == 200:
                JsonObject = response.json()
                app.logger.info('testcase generated successfully')
                return jsonify({'rows':JsonObject, 'message': 'valid token'}), 200
            elif response.status_code == 400:
                app.logger.error('Bad Request')
                return jsonify({'rows':"fail", 'message': 'Bad Request'}), 400
            elif response.status_code == 401:
                app.logger.error('Unauthorized user')
                return jsonify({'rows':"fail", 'message': 'Unauthorized token'}), 401
            elif response.status_code == 403:
                app.logger.error('user does not have the necessary permissions to access')
                return jsonify({'rows':"fail", 'message': 'user does not have the necessary permissions to access'}), 403
            elif response.status_code == 404 :
                app.logger.error('Source not found')
                return jsonify({'rows':"fail", 'message': 'Source not found'}), 404
            elif response.status_code == 500 :
                app.logger.error('Internal Server Error')
                return jsonify({'rows':"fail", 'message': 'Internal Server Error'}), 500
            elif response.status_code == 504 :
                app.logger.error('Gateway Time-out')
                return jsonify({'rows':"fail", 'message': 'Gateway Time-out'}), 504

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
    

    @app.route('/genAI/createModel', methods=['POST'])
    def createModel():
        try:
            request_data = request.get_json()
            # required_fields = ['email', 'name','organization','projectname','testcase','type']
            # if all(field not in request_data for field in required_fields):
            #     return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            if "modeltype" in request_data:
                document_LLM_model = Other_LLM_Model(
                api_key = request_data["api_key"],
                model = request_data["model"],
                modeltype = request_data["modeltype"],
                userinfo = request_data["userinfo"],
                name = request_data["name"]
                
            )
            else:    
                document_LLM_model = OpenAI_LLM_Model(
                    openai_api_key = request_data["openai_api_key"],
                    openai_api_type = request_data["openai_api_type"],
                    openai_api_version = request_data["openai_api_version"],
                    openai_api_base = request_data["openai_api_base"],
                    userinfo = request_data["userinfo"],
                    name = request_data["name"],
                    deployment_name = request_data["deployment_name"]
                )

            model_to_insert = document_LLM_model.to_dict()
            insert_result = dbsession.GenAI_Models.insert_one(model_to_insert)

            if insert_result.acknowledged:
                return jsonify({'rows':'success', 'message': 'model saved successfully'}), 200
            else:
                return jsonify({'rows':'fail','error': ' failed to save model '}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500

    @app.route('/genAI/readModel', methods=['POST'])
    def readModel():
        try:
            request_data = request.get_json()

            if 'userid' not in request_data:
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            fetch_result = list(dbsession.GenAI_Models.find({"userinfo.userid":request_data['userid']},
                                                            {"userinfo":0}))

            if len(fetch_result):
                return jsonify({'rows':fetch_result, 'message': 'records found'}), 200
            else:
                return jsonify({'rows':[],'message': 'no records found'}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500

    @app.route('/genAI/editModel', methods=['POST'])
    def editModel():
        try:
            request_data = request.get_json()
            required_fields = ["id","userinfo"]
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]

            document = dbsession.GenAI_Models.find_one({"_id":ObjectId(request_data["id"]),"userinfo.userid":request_data["userinfo"]["userid"]})
            if not document:
                return jsonify({'rows':'fail','error': ' document not found '}), 404
            if "modeltype" in request_data["items"] and request_data["items"]["modeltype"] != document.get("modeltype", ""):
                fields_to_keep = ["createdAt","updatedAt", "_id", "userinfo"]
                document = {k: v for k, v in document.items() if k in fields_to_keep}
            for key,value in request_data["items"].items():
                document[key] = value

            document["updatedAt"] = datetime.now()
            update_document =  dbsession.GenAI_Models.replace_one({"_id":ObjectId(request_data["id"])},document)  
            if update_document.acknowledged:
                return jsonify({'rows':'success', 'message': 'model updated successfully'}), 200
            else:
                return jsonify({'rows':'fail','error': ' failed to update model '}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500


    @app.route('/genAI/deleteModel', methods=['POST'])
    def deleteModel():
        try:
            request_data = request.get_json()
            required_fields = ["id","userinfo"]
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            doc_id = request_data["id"]
            deleted_document = dbsession.GenAI_Models.find_one_and_delete({"_id":ObjectId(doc_id),"userinfo.userid":request_data["userinfo"]["userid"]})
            if not deleted_document:
                return jsonify({'rows':'fail','error': ' document not found '}), 404
              
            return jsonify({'rows':'success', 'message': f"{doc_id} model deleted"}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500                

    @app.route('/genAI/createTemp', methods=['POST'])
    def createTemp():
        try:
            request_data = request.get_json()
            required_fields = [ 'name','domain','model_id','test_type','temperature','active','default','userinfo']
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            find_model_details = dbsession.GenAI_Models.find_one({"_id":ObjectId(request_data["model_id"]),"userinfo.userid":request_data["userinfo"]["userid"]},
                                                                 {"userinfo":0,"createdAt":0,"updatedAt":0})
            if not find_model_details:
                return jsonify({'rows':'fail','error': ' document not found '}), 404

            document_Template_model = Template_Model(
            name = request_data["name"],
            domain = request_data["domain"],
            model_details= find_model_details,
            test_type = request_data["test_type"],
            temperature = request_data["temperature"],
            description = request_data["description"],
            active = request_data["active"],
            default = request_data["default"],
            userinfo = request_data['userinfo']
            )

            template_to_insert = document_Template_model.to_dict()
            insert_result = dbsession.GenAI_Templates.insert_one(template_to_insert)

            if insert_result.acknowledged:
                return jsonify({'rows':'success', 'message': 'model saved successfully'}), 200
            else:
                return jsonify({'rows':'fail','error': ' failed to save model '}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500

    @app.route('/genAI/readTemp', methods=['POST'])
    def readTemp():
        try:
            request_data = request.get_json()

            if 'userid' not in request_data:
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            fetch_result = list(dbsession.GenAI_Templates.find({"userinfo.userid":request_data['userid']},
                                                            {"userinfo":0}))

            if len(fetch_result):
                return jsonify({'rows':fetch_result, 'message': 'records found'}), 200
            else:
                return jsonify({'rows':[],'message': 'no records found'}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500

    @app.route('/genAI/editTemp', methods=['POST'])
    def editTemp():
        try:
            request_data = request.get_json()
            required_fields = ["id","userinfo"]
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]

            document = dbsession.GenAI_Templates.find_one({"_id":ObjectId(request_data["id"]),"userinfo.userid":request_data["userinfo"]["userid"]})
            if not document:
                return jsonify({'rows':'fail','error': ' document not found '}), 404
            for key,value in request_data["items"].items():
                document[key] = value
            document.pop("model_details", None)
            find_model_details = dbsession.GenAI_Models.find_one({"_id":ObjectId(request_data["items"]["model_id"]),"userinfo.userid":request_data["userinfo"]["userid"]},
                                                                 {"userinfo":0,"createdAt":0,"updatedAt":0})
            if not find_model_details:
                return jsonify({'rows':'fail','error': ' document not found '}), 404    
            # for key in list(document.keys()):
            #     if key == "modeltype":    
            document["model_details"] = find_model_details
            document["updatedAt"] = datetime.now()
            update_document =  dbsession.GenAI_Templates.replace_one({"_id":ObjectId(request_data["id"])},document)  
            if update_document.acknowledged:
                return jsonify({'rows':'success', 'message': 'templates updated successfully'}), 200
            else:
                return jsonify({'rows':'fail','error': ' failed to update model '}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500

    @app.route('/genAI/deleteTemp', methods=['POST'])
    def deleteTemp():
        try:
            request_data = request.get_json()
            required_fields = ["id","userinfo"]
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            doc_id = request_data["id"]
            deleted_document = dbsession.GenAI_Templates.find_one_and_delete({"_id":ObjectId(doc_id),"userinfo.userid":request_data["userinfo"]["userid"]})
            if not deleted_document:
                return jsonify({'rows':'fail','error': ' document not found '}), 404
              
            return jsonify({'rows':'success', 'message': f"{doc_id} model deleted"}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500                