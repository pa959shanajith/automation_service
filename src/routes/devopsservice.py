# from tkinter import E
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

            if(requestdata['query'] == 'fetchExecutionData'):
                keyDetails = list(dbsession.configurekeys.find({'token': requestdata["key"]},{'executionData': 1,'session': 1}))
                res['rows'] = keyDetails[0]
            else:
                requestdata["token"] = requestdata["executionData"]['configurekey']

                # GEtting data parameterization
                for testsuite in requestdata['executionData']['batchInfo']:
                    testsuiteData = list(dbsession.testsuites.find({'mindmapid':ObjectId(testsuite['testsuiteId'])}))

                    # To handle if document is not present in testsuite collection
                    if not testsuiteData:
                        continue

                    del testsuite['suiteDetails']

                    scenarioIndexFromBackEnd = -1
                    testsuite['suiteDetails'] = []
                    for scenarioids in testsuiteData[0]['testscenarioids']:
                        scenarioIndexFromBackEnd+=1
                        scenarioName = list(dbsession.testscenarios.find({'_id':scenarioids},{'name': 1}))
                        if testsuiteData[0]['donotexecute'][scenarioIndexFromBackEnd]:
                            testsuite['suiteDetails'].append({
                                "condition" : testsuiteData[0]['conditioncheck'][scenarioIndexFromBackEnd],
                                "dataparam" : [testsuiteData[0]['getparampaths'][scenarioIndexFromBackEnd]],
                                "scenarioName" : scenarioName[0]['name'],
                                "scenarioId" : str(scenarioids),
                                "accessibilityParameters" : []
                            })


                # check whether key is already present
                keyAlreadyExist = list(dbsession.configurekeys.find({'token': requestdata["token"]}))

                if(requestdata['executionData']['avogridId'] != ''):
                    agentList = list(dbsession.avogrids.find({'_id': ObjectId(requestdata['executionData']['avogridId'])}))
                    requestdata['executionData']['avoagents'] = {}
                    for agents in agentList[0]['agents']:
                        requestdata['executionData']['avoagents'][agents['Hostname']] = agents['icecount']

                # case-1 key not present
                if(len(keyAlreadyExist) == 0):
                    dbsession.configurekeys.insert_one(requestdata)

                else: #key is present
                    dbsession.configurekeys.update({"_id":ObjectId(keyAlreadyExist[0]['_id'])},{'$set':{"executionData":requestdata["executionData"]}})

                res['rows'] = 'success'


        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/executionList',methods=['POST'])
    def executionList():
        app.logger.debug("Inside executionList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            requestdata['configkey'] = requestdata['executionData']['configurekey']
            requestdata['executionListId'] = requestdata['executionData']['executionListId']
            dbsession.executionlist.insert_one(requestdata)
            res['rows'] = 'success'

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
            queryresult = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']}))

            res['rows'] = {
                "testSuiteInfo" : queryresult[0]['executionRequest']['testsuiteIds'],
                "version" : '0',
                "avoagentList": queryresult[0]['executionRequest']['avoagents'],
                'executiontype': queryresult[0]['executionRequest']['executiontype'],
                'executionListId': queryresult[0]['executionListId'],
                # "avogridid" : queryresult[0]['executionRequest']['avogridid']
            }

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
            queryresult = list(dbsession.avogrids.find({"_id": ObjectId(requestdata["avogridid"])}))
            res['rows'] = queryresult[0]['avoagents']

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

            agentPresent = list(dbsession.avoagents.find({"Hostname": requestdata["Hostname"]}))
            if(len(agentPresent) > 0): #agent already present then update the details
                requestdata['status'] = agentPresent[0]['status']
                requestdata['createdon'] = agentPresent[0]['createdon']
                requestdata['icecount'] = agentPresent[0]['icecount']
                dbsession.avoagents.update({"_id":ObjectId(agentPresent[0]['_id'])},{'$set':{"recentCall":requestdata['recentCall']}})
            else:
                dbsession.avoagents.insert_one(requestdata)

            res['rows'] = requestdata

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
            executionData = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']}))
            correctexecutionRequest = ''
            index = -1
            for info in executionData[0]['executionData']['batchInfo']:
                index+=1
                if info['testsuiteId'] == testSuiteId:
                    break
            executionData[0]['executionData']['batchInfo'] = [executionData[0]['executionData']['batchInfo'][index]]



            res['rows'] = executionData

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getScenariosForDevops',methods=['POST'])
    def getScenariosForDevops():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            
            
            processedData = []
            processedDataIndex = 0
            for moduleDetail in requestdata:
                scenarioids=[]
                mindmapdata=dbsession.mindmaps.find_one({"_id":ObjectId(moduleDetail['_id'])},{"testscenarios":1})
                testsuitesdata=dbsession.testsuites.find_one({"mindmapid":ObjectId(moduleDetail['_id'])})
                processedData.append({
                    'moduleid' : moduleDetail['_id'],
                    "name" : moduleDetail['name'],
                    'scenarios' : [],
                    'batchname':  testsuitesdata['batchname'] if (testsuitesdata and 'batchname' in testsuitesdata and testsuitesdata['batchname']) else ''
                    # 'batchname': testsuitesdata['batchname']
                })
                if "testscenarios" in mindmapdata:
                    for ts in mindmapdata["testscenarios"]:
                        if ts["_id"] not in scenarioids:
                            scenarioids.append(ts["_id"])

                    scenariodetails=list(dbsession.testscenarios.find({"_id":{"$in":scenarioids}},{"_id":1,"name":1}))
                    requiredScenarioDict={}
                    for ts in scenariodetails:
                        requiredScenarioDict[ts['_id']] = ts['name']
                    
                    scenarioids = []
                    for ts in mindmapdata["testscenarios"]:
                        scenarioids.append({
                                '_id': ts['_id'],
                                'name': requiredScenarioDict[ts['_id']]
                            })

                    
                    processedData[processedDataIndex]['scenarios'] = scenarioids
                    processedDataIndex+=1

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
            queryresult = list(dbsession.configurekeys.find({'executionData.batchInfo.projectId': requestdata['projectid']}))
            responseData = []
            for elements in queryresult:
                updatedExecutionReq = elements['executionData']
                responseData.append({
                    'configurename': updatedExecutionReq['configurename'],
                    'configurekey': updatedExecutionReq['configurekey'],
                    'project': updatedExecutionReq['batchInfo'][0]['projectName'],
                    'release': updatedExecutionReq['batchInfo'][0]['releaseId'],
                    'executionRequest': updatedExecutionReq
                })

            res['rows'] = responseData


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
            queryresultavogrid = queryresultavoagent = ''
            if requestdata['query'] == 'all' or requestdata['query'] == 'avoAgentList':
                queryresultavoagent = list(dbsession.avoagents.find({}))
            if requestdata['query'] == 'all' or requestdata['query'] == 'avoGridList':
                queryresultavogrid = list(dbsession.avogrids.find({}))

            res['rows'] = {
                'avoagents': queryresultavoagent,
                'avogrids': queryresultavogrid
            }


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

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/saveAvoAgent',methods=['POST'])
    def saveAvoAgent():
        app.logger.debug("Inside saveAvoAgent")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)

            for agentDetail in requestdata:
                if(agentDetail['action'] == 'update'):
                    dbsession.avoagents.update({"_id":ObjectId(agentDetail['value']['_id'])},{'$set':{"icecount":agentDetail['value']["icecount"] , "status": agentDetail['value']['status']}})
                else:
                    dbsession.avoagents.delete_one({"_id":ObjectId(agentDetail['value']['_id'])})
            
            res['rows'] = 'success'

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/saveAvoGrid',methods=['POST'])
    def saveAvoGrid():
        app.logger.debug("Inside saveAvoGrid")
        res={'rows':'fail'}
        try:

            requestdata=json.loads(request.data)
            action = requestdata["action"]
            value = requestdata["value"]
            # check whether key is already present
            gridAlreadyExist = list(dbsession.avogrids.find({'name': value["name"]}))

            # case-1 key not present
            if(action == "create" and len(gridAlreadyExist) == 0):
                dbsession.avogrids.insert_one(value)
                res['rows'] = 'success'
            elif(action == "update"):
                gridToUpdate = dbsession.avogrids.find_one({'_id': ObjectId(value["_id"])})
                if(value["name"] == gridToUpdate['name'] or len(gridAlreadyExist) == 0):
                    dbsession.avogrids.update({"_id":ObjectId(value['_id'])},{'$set':{"name":value["name"] , "agents": value['agents']}})
                    res['rows'] = 'success'
                else:
                    res['err_msg'] = "Grid Already Exists"
            else:
                res['err_msg'] = "Grid Already Exists"

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/deleteAvoGrid',methods=['POST'])
    def deleteAvoGrid():
        app.logger.debug("Inside deleteAvoGrid")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)        
            result=dbsession.avogrids.delete_one({"_id":ObjectId(requestdata['_id'])})

            res['rows'] = 'success'

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/fetchModuleListDevopsReport',methods=['POST'])
    def fetchModuleListDevopsReport():
        app.logger.debug("Inside fetchModuleListDevopsReport")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)

            queryresult=list(dbsession.executions.find({"executionListId":requestdata["executionListId"]}))
            testSuite = []
            if(len(queryresult) != 0):
                for execution in queryresult:
                    testSuite.append(execution['parent'][0])

                testSuiteData = list(dbsession.testsuites.find({"_id" : {"$in" : testSuite}},{'_id':1,'name':1}))
                for index in range(0,len(testSuite)):
                    testSuiteData[index]['execution_Id'] = queryresult[index]['_id']
                res['rows'] = testSuiteData

        except Exception as e:
            print(e)
            return e
        return jsonify(res)