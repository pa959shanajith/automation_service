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
            requestdata["token"] = requestdata["executionRequest"]['configurekey']
            # print(Key)
            # To Do delete query key from requestdata.

            # check whether key is already present
            keyAlreadyExist = list(dbsession.configurekeys.find({'token': requestdata["token"]}))

            # case-1 key not present
            if(len(keyAlreadyExist) == 0):
                newRequestData = {item: requestdata[item] for item in requestdata if item not in {'executionRequest'}}
                requestdata["executionRequest"]['version'] = 0
                newRequestData["executionRequestList"] = [{"executionRequest": requestdata["executionRequest"]}]
                dbsession.configurekeys.insert_one(newRequestData)

            else: #key is present
                newList = {}
                newList["executionRequestList"] = keyAlreadyExist[0]["executionRequestList"]
                requestdata["executionRequest"]['version'] = keyAlreadyExist[0]["executionRequestList"][-1]['executionRequest']['version'] + 1
                newList["executionRequestList"].append({"executionRequest": requestdata["executionRequest"]})
                dbsession.configurekeys.update({"_id":ObjectId(keyAlreadyExist[0]['_id'])},{'$set':{"executionRequestList":newList["executionRequestList"]}})
           
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
            # print(queryresult[0]['executionRequest']['testsuiteIds'])
            print(queryresult[0]['executionRequestList'][-1]['executionRequest']['testsuiteIds'])

            res['rows'] = {
                "testSuiteInfo" : queryresult[0]['executionRequestList'][-1]['executionRequest']['testsuiteIds'],
                "version" : queryresult[0]['executionRequestList'][-1]['executionRequest']['version'],
                "avoagentList": queryresult[0]['executionRequestList'][-1]['executionRequest']['avoagents'],
                'executiontype': queryresult[0]['executionRequestList'][-1]['executionRequest']['executiontype'],
                'executionListId': str(uuid.uuid4()),
                # "avogridid" : queryresult[0]['executionRequest']['avogridid']
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

            agentPresent = list(dbsession.avoagents.find({"Hostname": requestdata["Hostname"]}))
            if(len(agentPresent) > 0):
                requestdata['status'] = agentPresent[0]['status']
                requestdata['createdon'] = agentPresent[0]['createdon']
                dbsession.avoagents.update({"_id":ObjectId(agentPresent[0]['_id'])},{'$set':{"recentCall":requestdata['recentCall']}})
            else:
                dbsession.avoagents.insert_one(requestdata)

            res['rows'] = requestdata
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
            # fetching keys which contains given avo agent
            data = list(dbsession.configurekeys.find({"executionRequest.avoagents" : {"$in": [requestdata['avoagents']]}},{'_id': 0,'token': 1}))
            keysList = []
            for dic in data:
                for val in dic.values():
                    keysList.append(val)
            
            # fetching keys which contains no agents => agent list is empty for these keys.
            if len(keysList) == 0:
                data = list(dbsession.configurekeys.find({"executionRequest.avoagents" : []},{'_id': 0,'token': 1}))
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
            correctexecutionRequest = ''
            for executionRequest in executionData[0]['executionRequestList']:
                # print(executionRequest['executionRequest']['version'])
                if executionRequest['executionRequest']['version'] == requestdata['version']:
                    # print('what')
                    correctexecutionRequest = executionRequest
                    break

            executionData[0].pop('executionRequestList')
            executionData[0]['executionRequest'] = correctexecutionRequest['executionRequest']
            print(executionData[0]['executionRequest']['testsuiteIds'].index(testSuiteId))
            index = executionData[0]['executionRequest']['testsuiteIds'].index(testSuiteId)
            executionData[0]['executionRequest']['executionIds'] = [executionData[0]['executionRequest']['executionIds'][index]]
            executionData[0]['executionRequest']['suitedetails'] = [executionData[0]['executionRequest']['suitedetails'][index]]
            executionData[0]['executionRequest']['testsuiteIds'] = [executionData[0]['executionRequest']['testsuiteIds'][index]]



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
                testsuitesdata=dbsession.testsuites.find_one({"mindmapid":ObjectId(moduleDetail['_id'])},{"batchname":1})
                processedData.append({
                    'moduleid' : moduleDetail['_id'],
                    "name" : moduleDetail['name'],
                    'scenarios' : [],
                    'batchname':  testsuitesdata['batchname'] if (testsuitesdata and testsuitesdata['batchname']) else ''
                    # 'batchname': testsuitesdata['batchname']
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


    @app.route('/devops/getConfigureList',methods=['POST'])
    def getConfigureList():
        app.logger.debug("Inside getConfigureList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # print(Key)
            # To Do delete query key from requestdata.
            queryresult = list(dbsession.configurekeys.find({'executionRequestList': { '$elemMatch' : {'executionRequest.invokinguser': requestdata['userid']}}}))
            responseData = []
            for elements in queryresult:
                updatedExecutionReq = elements['executionRequestList'][-1]['executionRequest']
                responseData.append({
                    'configurename': updatedExecutionReq['configurename'],
                    'configurekey': updatedExecutionReq['configurekey'],
                    'project': updatedExecutionReq['suitedetails'][0]['projectname'],
                    'release': updatedExecutionReq['suitedetails'][0]['releaseid'],
                    'executionRequest': updatedExecutionReq
                })
            print(responseData)
            
            res['rows'] = responseData

            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getAvoAgentAndAvoGridList',methods=['POST'])
    def getAvoAgentAndAvoGridList():
        app.logger.debug("Inside getAvoAgentAndAvoGridList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            # print(Key)
            # To Do delete query key from requestdata.
            queryresultavoagent = list(dbsession.avoagents.find({}))
            queryresultavogrid = list(dbsession.avogrids.find({}))

            res['rows'] = {
                'avoagents': queryresultavoagent,
                'avogrids': queryresultavogrid
            }

            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/deleteConfigureKey',methods=['POST'])
    def deleteConfigureKey():
        app.logger.debug("Inside deleteConfigureKey")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)        
            result=dbsession.configurekeys.delete_one({"token":requestdata['key']})

            res['rows'] = 'success'
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)