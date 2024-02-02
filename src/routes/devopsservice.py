# from tkinter import E
from unicodedata import name
from warnings import catch_warnings
from utils import *
import json
def LoadServices(app, redissession, client ,getClientName):
    setenv(app) 

    @app.route('/devops/configurekey',methods=['POST'])
    def configureKey():
        app.logger.debug("Inside configureKey")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)       
            dbsession=client[clientName]

            if(requestdata['query'] == 'fetchExecutionData'):
                keyDetails = list(dbsession.configurekeys.find({'token': requestdata["key"]},{'executionData': 1,'session': 1}))
                res['rows'] = keyDetails[0]
            else:
                checkForName =  list(dbsession.configurekeys.find({'executionData.configurename': requestdata['executionData']['configurename'] , 'executionData.batchInfo.projectName':requestdata['executionData']['batchInfo'][0]['projectName'], 'executionData.configurekey': {'$ne':requestdata['executionData']['configurekey'] }},{'executionData': 1}))

                # check if already configurename exists
                if(len(checkForName) != 0):
                    res['rows'] = {'error':{'CONTENT':'Execution Profile name already exists'}}
                    return res['rows']

                requestdata["token"] = requestdata["executionData"]['configurekey']

                # GEtting data parameterization
                for testsuite in requestdata['executionData']['batchInfo']:
                    testsuiteData = list(dbsession.testsuites.find({'mindmapid':ObjectId(testsuite['testsuiteId'])}))
                    # sorting the data
                    requestdata['executionData']['donotexe']['current'][testsuite['testsuiteId']].sort()

                    # To handle if document is not present in testsuite collection
                    if not testsuiteData:
                        continue

                    del testsuite['suiteDetails']

                    scenarioIndexFromBackEnd = -1
                    scenarioIndexFromFrontEnd = 0
                    testsuite['suiteDetails'] = []
                    for scenarioids in testsuiteData[0]['testscenarioids']:
                        scenarioIndexFromBackEnd+=1

                        if scenarioIndexFromFrontEnd >= len(requestdata['executionData']['donotexe']['current'][testsuite['testsuiteId']]):
                            break

                        if requestdata['executionData']['donotexe']['current'][testsuite['testsuiteId']][scenarioIndexFromFrontEnd] == scenarioIndexFromBackEnd:
                            scenarioIndexFromFrontEnd+=1
                            scenarioName = list(dbsession.testscenarios.find({'_id':scenarioids},{'name': 1}))
                            testsuite['suiteDetails'].append({
                                "condition" : testsuiteData[0]['conditioncheck'][scenarioIndexFromBackEnd],
                                "dataparam" : [testsuiteData[0]['getparampaths'][scenarioIndexFromBackEnd]],
                                "scenarioName" : scenarioName[0]['name'],
                                "scenarioId" : str(scenarioids),
                                "accessibilityParameters" : testsuiteData[0]['accessibilityParameters'] if 'accessibilityParameters' in testsuiteData[0] else []
                            })

                    # updating the donotexecute array present in testsuite with the donotexe file coming from from-end
                    testsuiteData[0]['donotexecute'] = [0]*len(testsuiteData[0]['donotexecute'])
                    for index in requestdata['executionData']['donotexe']['current'][testsuite['testsuiteId']]:
                        testsuiteData[0]['donotexecute'][index] = 1

                    dbsession.testsuites.update({"mindmapid":ObjectId(testsuite['testsuiteId'])},{'$set':{"donotexecute":testsuiteData[0]['donotexecute']}})
                    
                    


                # check whether key is already present
                keyAlreadyExist = list(dbsession.configurekeys.find({'token': requestdata["token"]}))

                if(requestdata['executionData']['avogridId'] != ''):
                    agentList = list(dbsession.avogrids.find({'_id': ObjectId(requestdata['executionData']['avogridId'])}))
                    requestdata['executionData']['avoagents'] = {}
                    for agents in agentList[0]['agents']:
                        requestdata['executionData']['avoagents'][agents['Hostname']] = agents['icecount']

                # case-1 key not present
                if(len(keyAlreadyExist) == 0):
                    requestdata["createdAt"] = datetime.utcnow()
                    requestdata["updatedAt"] = datetime.utcnow()
                    dbsession.configurekeys.insert_one(requestdata)

                else: #key is present
                    dbsession.configurekeys.update({"_id":ObjectId(keyAlreadyExist[0]['_id'])},{'$set':{"executionData":requestdata["executionData"],"updatedAt":datetime.utcnow()}})

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
            clientName=getClientName(requestdata)       
            dbsession=client[clientName]
            if 'configurekey' in requestdata['executionData']:
                requestdata['configkey'] = requestdata['executionData']['configurekey']
            elif 'configureKey' in requestdata['executionData']:
                requestdata['configkey'] = requestdata['executionData']['configureKey']
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
            clientName=getClientName(requestdata)       
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)      
            dbsession=client[clientName]
            agentPresent = list(dbsession.avoagents.find({"Hostname": requestdata["Hostname"]}))
            if(len(agentPresent) > 0): #agent already present then update the details
                requestdata['status'] = agentPresent[0]['status']
                requestdata['createdon'] = agentPresent[0]['createdon']
                requestdata['icecount'] = agentPresent[0]['icecount']
                requestdata['currentIceCount'] = requestdata['currentIceCount'] if 'currentIceCount' in requestdata else 0
                dbsession.avoagents.update({"_id":ObjectId(agentPresent[0]['_id'])},{'$set':{"recentCall":requestdata['recentCall'] , "currentIceCount" : requestdata['currentIceCount']}})
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
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)
            dbsession=client[clientName]

            # Fetching the data
            executionData = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']}))
            updatedData = executionData
            correctexecutionRequest = ''
            index = -1
            for info in executionData[0]['executionData']['batchInfo']:
                index+=1
                if info['testsuiteId'] == testSuiteId:
                    break
            
            # Updating the agent sent from Ice.
            updatedData[0]['executionData']['batchInfo'][index]['agentName'] = requestdata['agentName']
            updatedResponse = dbsession.executionlist.update_many({'executionListId':requestdata['executionListId'],"configkey": requestdata['key']},{'$set':{"executionData.batchInfo": updatedData[0]['executionData']['batchInfo']}})

            executionData[0]['executionData']['batchInfo'] = [executionData[0]['executionData']['batchInfo'][index]]
            if 'scenarioIndex' in requestdata:
                executionData[0]['executionData']['batchInfo'][0]['suiteDetails'] = [executionData[0]['executionData']['batchInfo'][0]['suiteDetails'][requestdata['scenarioIndex']]]
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
            clientName=getClientName(requestdata[-1])
            dbsession=client[clientName]
            del(requestdata[-1])
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
            return e
        return jsonify(res)


    @app.route('/devops/getConfigureList',methods=['POST'])
    def getConfigureList():
        app.logger.debug("Inside getConfigureList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            queryresult = list(dbsession.configurekeys.find({'executionData.batchInfo.projectId': requestdata['projectid'] ,
                                                             '$or': [{"executionData.isExecuteNow":False},{"executionData.isExecuteNow": {'$exists':False}}]}))
            responseData = []
            for elements in queryresult:
                updatedExecutionReq = elements['executionData']
                noOfCount = list(dbsession.executions.find({'configurekey':updatedExecutionReq['configurekey']}))
                responseData.append({
                    'configurename': updatedExecutionReq['configurename'],
                    'configurekey': updatedExecutionReq['configurekey'],
                    'project': updatedExecutionReq['batchInfo'][0]['projectName'],
                    'release': updatedExecutionReq['batchInfo'][0]['releaseId'],
                    'executionRequest': updatedExecutionReq,
                    'noOfExecution' : len(noOfCount)
                })
            if "param" in requestdata and requestdata["param"] =="reportData":
                date_info=list(dbsession.executions.aggregate([{"$match":{"projectId":requestdata['projectid']}},{"$group":{"_id":"$configurekey","execDate":{"$last":"$starttime"}}}]))
                for data in responseData:
                    for dateinfo in date_info:
                        if data["configurekey"] == dateinfo["_id"]:
                            data["execDate"] = dateinfo["execDate"]
                            break
            pagecount= requestdata["page"]
            limit = 10

            start_index = (pagecount - 1) * limit
            end_index = start_index + limit

            pagination_data = responseData[start_index:end_index]
            total_count = len(responseData)  
            response = {
                "data" :pagination_data,
                "pagination" : {
                    "page" : pagecount,
                    'limit' : limit,
                    'totalcount' : total_count
                }
            }
            res['rows'] = response
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
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)       
            dbsession=client[clientName]      
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
            clientName=getClientName(requestdata[-1])
            dbsession=client[clientName]
            del requestdata[-1]
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
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]       
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
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]

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

    @app.route('/devops/cacheData',methods=['POST'])
    def cacheData():
        app.logger.debug("Inside cacheData")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
            cacheResult = list(dbsession.cachedb.find({}))

            if 'query' in requestdata:
                if(len(cacheResult) != 0):
                    del cacheResult[0]['_id']

                res['rows'] = cacheResult
            else:
                if(len(cacheResult) == 0):
                    dbsession.cachedb.insert_one(requestdata)

                else: #key is present
                    dbsession.cachedb.replace_one({"_id":cacheResult[0]['_id']},requestdata)

                res['rows'] = 'pass'

        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getAgentModuleList',methods=['POST'])
    def getAgentModuleList():
        app.logger.debug("Inside getAgentModuleList")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
            listOfModules = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId']}))

            agentModuleList = []
            if 'executionData' in listOfModules[0]:
                for testsuite in listOfModules[0]['executionData']['batchInfo']:
                    agentModuleList.append({
                        'testsuiteName':testsuite['testsuiteName'],
                        'agentName': testsuite['agentName'] if 'agentName' in testsuite else ''
                    })

                res['rows'] = agentModuleList

            else:
                res['rows'] = 'fail'

        except Exception as e:
            print(e)
            return e
        return jsonify(res)
    

    @app.route('/devops/fetchHistory',methods=['POST'])
    def fetchHistory():
        app.logger.debug("Inside fetchHistory")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]


            # To do use ISODate function and then send the query

            TF = '%Y-%m-%d %H:%M:%S'
            sdate = datetime.strptime(requestdata['fromDate'], TF)
            scolDate = requestdata['fromDate'].split()[0]
            edate = datetime.strptime(requestdata['toDate'], TF)
            ecolDate = requestdata['toDate'].split()[0]

            dbsession.vidata.delete_many({})
            dbsession.executions.aggregate([
                { "$match": { "starttime": { "$gte":sdate,"$lte": edate }}},
                { "$match": { "executionListId": { "$exists": "true" } }},
                { "$unwind": {
                    "path": "$parent",
                    "preserveNullAndEmptyArrays": True
                    }
                },
                { '$addFields': { 
                    'elistsuiteID' : {"$concat" : ['$executionListId', '_',  { '$convert': {"input" : "$parent", "to" : "string" }} ]}
                }},
                {'$lookup': {
                    "from":'reports',
                    "localField":'_id',
                    "foreignField":'executionid',
                    "as":'scenarioReports'
                }},
                { '$unwind': "$scenarioReports"},
                {
                    "$group": {
                    "_id":  {"f0": "$elistsuiteID"},
                    "eid":  {"$first": "$scenarioReports.executionid" }, 
                    "overallstatus":  {"$first": "$scenarioReports.status" }, 
                    "starttimeConfig": { "$min" : "$starttime"} ,
                    "starttime":  {"$first": "$starttime" }, 
                    "endtime":  {"$first": "$endtime" }, 
                    "batchname":  {"$first": "$batchname" }, 
                    "elistsuiteID":  {"$first": "$elistsuiteID"},
                    "Total":  { "$sum" : 1},   
                    "passCount": { "$sum": { "$cond": [ { "$eq": [ "$scenarioReports.status", 'Pass' ] }, 1, 0 ] } },
                    "failCount": { "$sum": { "$cond": [ { "$eq": [ "$scenarioReports.status", 'Fail' ] }, 1, 0 ] } },
                    "TerminateCount": { "$sum": { "$cond": [ { "$eq": [ "$scenarioReports.status", 'Terminate' ] }, 1, 0 ] } },
                    },
                }, 
                { "$project": { "_id":0   }  } ,
                { "$out": "execStatus_"+ scolDate}
            ])

            dbsession.executionlist.aggregate ([  
                { "$match":{ "executionListId": { "$exists": "true" } }},
                { "$unwind": {
                    "path": "$executionData",
                    "preserveNullAndEmptyArrays": True
                    }
                },
                { "$unwind": {
                    "path": "$executionData.batchInfo",
                    "preserveNullAndEmptyArrays": True
                    }
                },
                { '$addFields': { 
                        'elistsuiteID' : {"$concat" : ['$executionListId', '_',  { '$convert': {"input" : "$executionData.batchInfo.testsuiteId", "to" : "string" }} ]}
                }},
                { "$project": { "_id":0 } },
                { "$out": "execModules_"+ scolDate}
            ])

            dbsession.get_collection("execModules_"+ scolDate).aggregate([{
                "$lookup":{
                        "from": "execStatus_"+ scolDate,
                        "localField": "elistsuiteID",
                        "foreignField": "elistsuiteID",
                        "as": "Estatus"
                    },
                },
                { 
                    "$unwind": {
                        "path": "$Estatus",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id":  {"f1": "$elistsuiteID" }, 
                        "elistsuiteID":  {"$first": "$elistsuiteID" }, 
                        "Module":  { "$first" : "$executionData.batchInfo.testsuiteName"}, 
                        "Project": { "$first" : "$executionData.batchInfo.projectName"} ,
                        "configurename": {"$first" : "$executionData.configurename"},
                        "configurekey": {"$first" : "$executionData.configurekey"},
                        "Agentname": {"$first" : "$executionData.batchInfo.agentName"},
                        "StartTimeConfig": { "$min" : "$Estatus.starttime"} ,
                        "Status": { "$first" : "$Estatus.overallstatus"} ,
                        "passCount": { "$first" : "$Estatus.passCount"} ,
                        "failCount": { "$first" : "$Estatus.failCount"} ,
                        "terminateCount": { "$first" : "$Estatus.TerminateCount"} ,
                        "scenarioCount": { "$first" : "$Estatus.Total"} ,
                        "StartTime": { "$first" : "$Estatus.starttime"} ,
                        "EndTime": { "$first" : "$Estatus.endtime"} ,
                        "elistsuiteid":  {"$first": "$elistsuiteID"},
                    },
                },
                {     
                    "$project":{
                        "_id": 0 
                    },
                },
                { "$out": "vidata"},
            ])

            dbsession.get_collection("execStatus_"+ scolDate).drop()
            dbsession.get_collection("execModules_"+ scolDate).drop()

            res['rows'] = list(dbsession.vidata.find({'StartTime': {"$ne": None}}))
        except Exception as e:
            print(e)
            return e
        return jsonify(res)

    @app.route('/devops/getExecutionListDetails',methods=['POST'])
    def getExecutionListDetails():
        app.logger.debug("Inside getExecutionListDetails")
        result = {'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]

                # fetching the data from executionList based on key and executionId
                executionData = list(dbsession.executionlist.find({'executionListId':requestdata['executionListId']}))
                result['rows'] = executionData
            else:
                app.logger.warn('Empty data received for get execution details.')
        except Exception as getexecutionlistdetailsexec:
            servicesException("getExecutionListDetails", getexecutionlistdetailsexec, True)
        return jsonify(result)