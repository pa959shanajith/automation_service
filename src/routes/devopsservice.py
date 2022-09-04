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

            if(requestdata['query'] == 'fetchExecutionData'):
                keyDetails = list(dbsession.configurekeys.find({'token': requestdata["key"]},{'executionData': 1,'session': 1}))
                res['rows'] = keyDetails[0]
            else:
                requestdata["token"] = requestdata["executionData"]['configurekey']
                # check whether key is already present
                keyAlreadyExist = list(dbsession.configurekeys.find({'token': requestdata["token"]}))

                if(requestdata['executionData']['avogridId'] != ''):
                    agentList = list(dbsession.avogrids.find({'_id': ObjectId(requestdata['executionData']['avogridId'])}))
                    requestdata['executionData']['avoagents'] = {}
                    for agents in agentList[0]['agents']:
                        requestdata['executionData']['avoagents'][agents['Hostname']] = agents['icecount']

                # case-1 key not present
                if(len(keyAlreadyExist) == 0):
                    # newRequestData = {item: requestdata[item] for item in requestdata if item not in {'executionRequest'}}
                    # requestdata["executionRequest"]['version'] = 0
                    # newRequestData["executionRequestList"] = [{"executionRequest": requestdata["executionRequest"]}]
                    dbsession.configurekeys.insert_one(requestdata)

                else: #key is present
                    # newList = {}
                    # newList["executionRequestList"] = keyAlreadyExist[0]["executionRequestList"]
                    # requestdata["executionRequest"]['version'] = keyAlreadyExist[0]["executionRequestList"][-1]['executionRequest']['version'] + 1
                    # newList["executionRequestList"].append({"executionRequest": requestdata["executionRequest"]})
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
            requestdata['configkey'] = requestdata['executionRequest']['configurekey']
            requestdata['executionListId'] = requestdata['executionRequest']['executionListId']
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
            # print(Key)
            # To Do delete query key from requestdata.
            queryresult = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']}))
            print(queryresult[0]['executionRequest']['testsuiteIds'])
            # print(queryresult[0]['executionRequestList'][-1]['executionRequest']['testsuiteIds'])

            res['rows'] = {
                "testSuiteInfo" : queryresult[0]['executionRequest']['testsuiteIds'],
                "version" : '0',
                "avoagentList": queryresult[0]['executionRequest']['avoagents'],
                'executiontype': queryresult[0]['executionRequest']['executiontype'],
                'executionListId': queryresult[0]['executionListId'],
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
                requestdata['icecount'] = agentPresent[0]['icecount']
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
            executionData = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']},{'executionRequest': 1}))
            correctexecutionRequest = ''
            # for executionRequest in executionData[0]['executionRequestList']:
            #     # print(executionRequest['executionRequest']['version'])
            #     if executionRequest['executionRequest']['version'] == requestdata['version']:
            #         # print('what')
            #         correctexecutionRequest = executionRequest
            #         break

            # executionData[0].pop('executionRequestList')
            # executionData[0]['executionRequest'] = correctexecutionRequest['executionRequest']
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
            queryresult = list(dbsession.configurekeys.find({'session.userid': requestdata['userid']}))
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
            queryresultavogrid = queryresultavoagent = ''
            if requestdata['query'] == 'all' or requestdata['query'] == 'avoAgentList':
                queryresultavoagent = list(dbsession.avoagents.find({}))
            if requestdata['query'] == 'all' or requestdata['query'] == 'avoGridList':
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
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

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


            # if(action == "create") :
            #     # check whether key is already present
            #     gridAlreadyExist = list(dbsession.avogrids.find({'name': value["name"]}))

            #     # case-1 key not present
            #     if(len(gridAlreadyExist) == 0):
            #         dbsession.avogrids.insert_one(value)
            #         res['rows'] = 'success'
            #     else:
            #         res['err_msg'] = "Grid Already Exists"
            # else:
            #     # check whether key is already present
            #     gridAlreadyExist = list(dbsession.avogrids.find({'name': value["name"]}))
            #     if(len(gridAlreadyExist) == 0):
            #         dbsession.avogrids.update({"_id":ObjectId(requestdata['_id'])},{'$set':{"name":value["name"] , "agents": value['agents']}})

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
            # if not isemptyrequest(requestdata):
            #     print("I am inside")

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
                res['rows'] = testSuiteData

            # if not isemptyrequest(requestdata):
            #     print("I am inside")

        except Exception as e:
            print(e)
            return e
        return jsonify(res)