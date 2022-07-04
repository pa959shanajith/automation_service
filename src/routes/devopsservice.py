from tkinter import E
from unicodedata import name
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


    @app.route('/devops/getExecScenario',methods=['POST'])
    def getExecScenario():
        app.logger.debug("Inside getExecScenario")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            testSuiteId = requestdata['testSuiteId']
            executionData = list(dbsession.configurekeys.find({"token": requestdata['key']}))
            print(executionData[0]['executionRequest']['executionIds'].index(testSuiteId))
            index = executionData[0]['executionRequest']['executionIds'].index(testSuiteId)
            executionData[0]['executionRequest']['executionIds'] = [executionData[0]['executionRequest']['executionIds'][index]]
            executionData[0]['executionRequest']['suitedetails'] = [executionData[0]['executionRequest']['suitedetails'][index]]


            res['rows'] = executionData
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getScenariosForDevops',methods=['POST'])
    def getScenariosForDevops():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # tab=requestdata['tab']
            # app.logger.debug("Inside getScenariosForDevops. Query: "+str(requestdata["name"]))
            # if 'moduleid' in requestdata and requestdata['moduleid']!=None:
            #     mindmapdata=dbsession.mindmaps.find_one({"_id":ObjectId(requestdata["moduleid"])},{"testscenarios":1,"_id":1,"name":1,"projectid":1,"type":1,"versionnumber":1})
            
            
            processedData = []
            processedDataIndex = 0
            for moduleDetail in requestdata:
                scenarioids=[]
                mindmapdata=dbsession.mindmaps.find_one({"_id":ObjectId(moduleDetail['_id'])},{"testscenarios":1})
                processedData.append({
                    'moduleid' : moduleDetail['_id'],
                    "name" : moduleDetail['name'],
                    'scenarios' : []
                })
                if "testscenarios" in mindmapdata:
                    for ts in mindmapdata["testscenarios"]:
                        if ts["_id"] not in scenarioids:
                            scenarioids.append(ts["_id"])

                    scenariodetails=list(dbsession.testscenarios.find({"_id":{"$in":scenarioids}},{"_id":1,"name":1}))
                    processedData[processedDataIndex]['scenarios'] = scenariodetails
                    processedDataIndex+=1

            print(processedData)
            res['rows'] = processedData

        except Exception as e:
            print(e)
            return e
        return jsonify(res)