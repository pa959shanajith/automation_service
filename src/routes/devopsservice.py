from warnings import catch_warnings
from utils import *
import json
def LoadServices(app, redissession, dbsession):
    setenv(app)

    @app.route('/devops/configurekey',methods=['POST'])
    def configureKey():
        app.logger.debug("Inside configureKey")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            requestdata["token"] = "firstkey"
            # print(Key)
            # To Do delete query key from requestdata.
            dbsession.configurekeys.insert_one(requestdata)
            res['rows'] = 'success'
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getTestSuite',methods=['POST'])
    def getTestSuite():
        app.logger.debug("Inside getTestSuite")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # print(Key)
            # To Do delete query key from requestdata.
            queryresult = list(dbsession.configurekeys.find({"token": requestdata['key']}))
            print(queryresult[0]['executionRequest']['testsuiteIds'])
            res['rows'] = {
                "testSuiteInfo" : queryresult[0]['executionRequest']['testsuiteIds'] ,
                "avogridid" : queryresult[0]['executionRequest']['avogridid']
            }
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getAgents',methods=['POST'])
    def getAgents():
        app.logger.debug("Inside getAgents")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # print(Key)
            # To Do delete query key from requestdata.
            queryresult = list(dbsession.avogrids.find({"_id": ObjectId(requestdata["avogridid"])}))
            print(queryresult[0]['avoagents'])
            res['rows'] = queryresult[0]['avoagents']
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/agentDetails',methods=['POST'])
    def agentDetails():
        app.logger.debug("Inside agentDetails")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # requestdata["token"] = "firstkey"
            # print(Key)
            # To Do delete query key from requestdata.
            dbsession.avoagents.insert_one(requestdata)
            res['rows'] = 'success'
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/keysList',methods=['POST'])
    def keysList():
        app.logger.debug("Inside keysList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # requestdata["token"] = "firstkey"
            # print(Key)
            # To Do delete query key from requestdata.
            data = list(dbsession.configurekeys.find({"executionRequest.avoagents" : {"$in": [requestdata['avoagents']]}},{'_id': 0,'token': 1}))
            keysList = []
            for dic in data:
                for val in dic.values():
                    keysList.append(val)


            res['rows'] = keysList
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)