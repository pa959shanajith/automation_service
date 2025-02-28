################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime
from pymongo import InsertOne


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


    #fetching all the suite details
    @app.route('/reports/getAllSuites_ICE',methods=['POST'])
    def getAllSuites_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getAllSuites_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                if(requestdata["query"] == 'projects'):
                    queryresult1=dbsession.users.find_one({"_id": ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
                    queryresult=list(dbsession.projects.find({"_id":{"$in":queryresult1["projects"]}},{"name":1,"releases":1,"type":1}))
                    res= {"rows":queryresult}
                elif(requestdata["query"] == 'getAlltestSuites'):
                    queryresult=list(dbsession.testsuites.aggregate([
                        {'$match':{
                            'cycleid':ObjectId(requestdata["id"])
                            }
                        },
                        {'$lookup':{
                            'from':"mindmaps",
                            'localField':"mindmapid",
                            'foreignField':"_id",
                            'as':"arr"
                            }
                        },
                        {'$project':{
                            '_id':1,
                            'name':1,
                            'type':{"$arrayElemAt":["$arr.type",0]}
                        }}
                    ]))
                    batchresult=list(dbsession.executions.distinct('batchname',{'parent':{'$in':[i['_id'] for i in queryresult]}}))
                    res= {"rows":{"modules":queryresult,"batch":batchresult}}
                elif(requestdata["query"] == 'getAlltestSuitesDevops'):
                    queryresult = ''
                    if('executionListId' in requestdata['data']):
                        queryresult = list(dbsession.executions.find({
                            'configurekey': requestdata['data']['configurekey'],
                            'executionListId': requestdata['data']['executionListId']
                            },{'parent':1,'_id': 1,'starttime':1,'endtime':1}))
                    else:
                        queryresult = list(dbsession.executions.find({'configurekey': requestdata['data']['configurekey']},{'parent':1}))

                    testSuiteNames = []
                    for ids in queryresult:
                        testSuiteNames.append(ids['parent'][0])

                    testSuiteNames = list(dbsession.testsuites.find({'_id': {'$in': testSuiteNames}},{'name': 1,'_id':1}))
                    dictForTestSuiteIdAndName = {}
                    for result in testSuiteNames:
                        dictForTestSuiteIdAndName[result['_id']] = result['name']
                    
                    for ids in queryresult:
                        ids['moduleName'] = dictForTestSuiteIdAndName[ids['parent'][0]]
                    
                    res = queryresult if 'executionListId' in requestdata['data'] else {"modules": testSuiteNames}

            else:
                app.logger.warn('Empty data received. report suites details.')
        except Exception as getAllSuitesexc:
            servicesException("getAllSuites_ICE",getAllSuitesexc)
        return jsonify(res)

    #fetching all the suite after execution
    @app.route('/reports/getSuiteDetailsInExecution_ICE',methods=['POST'])
    def getSuiteDetailsInExecution_ICE():
        app.logger.debug("Inside getSuiteDetailsInExecution_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                if ("batchname" in requestdata):
                    queryresult=list(dbsession.executions.find({"batchname":requestdata["batchname"]},{"_id":1,"starttime":1,"endtime":1,"status":1,"smart":1,"batchid":1}))
                elif ('configurekey' in requestdata and 'executionListId' in requestdata):
                    queryresult=list(dbsession.executions.find({"executionListId":requestdata["executionListId"],"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1,"smart":1,"batchid":1})) 
                elif ('configurekey' in requestdata):
                    queryresult=list(dbsession.executions.find({"configurekey":requestdata["configurekey"],"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1,"smart":1,"batchid":1})) 
                else:
                    queryresult=list(dbsession.executions.find({"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1,"smart":1,"batchid":1})) 
                res= {"rows":queryresult}
            else:
                app.logger.warn('Empty data received. report suites details execution.')
        except Exception as getsuitedetailsexc:
            servicesException("getSuiteDetailsInExecution_ICE",getsuitedetailsexc)
        return jsonify(res)


    #fetching all the reports status
    @app.route('/reports/reportStatusScenarios_ICE',methods=['POST'])
    def reportStatusScenarios_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside reportStatusScenarios_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if(requestdata["query"] == 'executiondetails'):
                    queryresult = list(dbsession.reports.aggregate([
                    {'$match':{"executionid":{'$in':[ObjectId(i)for i in requestdata["executionid"]]}}},
                    {'$lookup':{
                        'from':"testscenarios",
                        'localField':"testscenarioid",
                        'foreignField':"_id",
                        'as':"arr"
                        }
                    },
                    {'$project':{
                        'testscenarioname':{"$arrayElemAt":["$arr.name",0]},
                        "_id":1,"executionid":1,"executedon":1,"comments":1,"executedtime":1,
                        "modifiedby":1,"modifiedbyrole":1,"modifiedon":1,"status":1,"testscenarioid":1
                        }
                    }
                    ]))
                    res = {"rows":queryresult}
            else:
                app.logger.warn('Empty data received. report status of scenarios.')
        except Exception as getreportstatusexc:
            servicesException("reportStatusScenarios_ICE",getreportstatusexc)
        return jsonify(res)


    #fetching the reports
    @app.route('/reports/getReport',methods=['POST'])
    def getReport():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getReport")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                reports = list(dbsession.reports.find({"_id":ObjectId(requestdata["reportid"])}))
                report_items= list(dbsession.reportitems.find({"_id":reports[0]["reportitems"][0]}))
                scenarios = list(dbsession.testscenarios.find({"_id":reports[0]["testscenarioid"]}))
                execs = list(dbsession.executions.find({"_id":reports[0]["executionid"]}))
                testsuites = list(dbsession.testsuites.find({"_id":execs[0]["parent"][0]}))
                projs = list(dbsession.projects.find({"releases.cycles._id":testsuites[0]["cycleid"]},{'_id':1,'releases':{'$elemMatch': {"cycles._id":testsuites[0]["cycleid"]}},'domain':1,'name':1}))
                
                for cyc in projs[0]["releases"][0]["cycles"]:
                    if testsuites[0]["cycleid"] == cyc["_id"]:
                        cyclename = cyc["name"]
                        break
                        
                reportData = {"rows":report_items[0]["rows"],"overallstatus":reports[0]["overallstatus"]}
                query = {
                    'report': reportData,
                    'executionid': reports[0]['executionid'],
                    'executedtime': reports[0]["executedtime"],
                    'testscenarioid': reports[0]["testscenarioid"],
                    'testscenarioname': scenarios[0]["name"],
                    'testsuitename': testsuites[0]["name"],
                    'projectid': projs[0]["_id"],
                    'domainname': projs[0]["domain"],
                    'projectname': projs[0]["name"],
                    'releasename': projs[0]["releases"][0]["name"],
                    'cyclename': cyclename
                }
                res= {"rows":query}
            else:
                app.logger.warn('Empty data received. report.')
        except KeyError as ex:
            app.logger.debug(ex)
            res['rows'] = []
            return res
        except Exception as getreportexc:
            servicesException("getReport",getreportexc)
        return flask.Response(flask.json.dumps(res), mimetype="application/json")


    #update jira defect id in report data
    @app.route('/reports/updateReportData',methods=['POST'])
    def updateReportData():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateReportData.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                queryresult = dbsession.reports.find({"_id":ObjectId(requestdata["reportid"])},{"reportitems":1})
                report = queryresult[0]['reportitems']
                limit = 15000
                slno = int(requestdata['slno'])
                llimit = slno//limit    #slno should be >= steps
                report_rows = []
                reportitemsid = 0
                for i in range(llimit,len(report)): # practically should iterate once
                    a = list(dbsession.reportitems.find({"_id":report[i],"rows.id":slno},{"rows.$":1}))
                    if(len(a)>0):
                        report_rows=a[0]['rows']
                        reportitemsid =a[0]['_id']
                        break
                row = None
                obj = report_rows[0]
                if obj['id']==int(requestdata['slno']):
                    row = obj
                if "'" in obj['StepDescription']:
                    obj['StepDescription'] = obj['StepDescription'].replace("'",'"')
                if(row!=None):
                    defect = 'jira_defect_id'
                    mongo_query = {
                        "type":"JIRA",
                        "reportid":requestdata["reportid"],
                        "defectid":requestdata['defectid'],
                        "stepDetails":{
                                "stepid": row["id"],
                                "stepdescription": row["StepDescription"].replace('""',"'"),
                                "Keyword": row["Keyword"]
                            }
                        }
                    if 'query' in requestdata and requestdata['query'] == 'defectThroughAzure':
                        defect = 'azure_defect_id'
                        mongo_query['type'] = "AZURE"
                    row.update({defect:str(requestdata['defectid'])})
                    queryresult = dbsession.reportitems.update({"_id":reportitemsid,"rows.id":slno},{"$set":{"rows.$":row}})
                    dbsession.thirdpartyintegration.insert_one(mongo_query)
                    res={'rows':'Success'}
        except Exception as updatereportdataexc:
            app.logger.debug(updatereportdataexc)
            servicesException("updateReportData",updatereportdataexc)
        return jsonify(res)

    #fetching the report by executionId
    @app.route('/reports/getReport_API',methods=['POST'])
    def getReport_API():
        res={'rows':'fail','errMsg':''}
        errMsgVal=''
        errMsg='Invalid '
        errIds=[]
        finalQuery=[]
        correctScenarios=[]
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getReport_API")
            if not isemptyrequest(requestdata) and valid_objectid(requestdata['executionId']):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                filter1 = {"executionid":ObjectId(requestdata["executionId"])}
                if("scenarioIds" in requestdata):
                    scenarioIds = dbsession.reports.distinct("testscenarioid", filter1)
                    for scenId in requestdata["scenarioIds"]:
                        if len(scenId.strip())==0:
                            continue
                        try:
                            if ObjectId(scenId) not in scenarioIds:
                                errIds.append(str(scenId))
                            else:
                                correctScenarios.append(ObjectId(scenId))
                        except:
                            errIds.append(str(scenId))
                    if len(correctScenarios) != 0 or len(errIds) != 0:
                        filter1["testscenarioid"] = {"$in":correctScenarios}

                query = dbsession.reports.aggregate([
                    {'$match':{'testscenarioid':{"$in":correctScenarios},"executionid":ObjectId(requestdata["executionId"])}},
                    { '$lookup':{
                            'from':'testscenarios',
                            'let':{'testscenarioid':'$testscenarioid'},
                            'pipeline':[
                                { '$match': { '$expr': { '$eq': ['$_id', '$$testscenarioid']}}}
                            ],
                            'as':'testscenarios'
                        }
                    },
                    { '$lookup':{
                            'from':'executions',
                            'let':{'excid':'$executionid'},
                            'pipeline':[
                                { '$match': { '$expr': { '$eq': ['$_id', '$$excid']}}},
                                { '$lookup': {
                                    'from': 'testsuites',
                                    'let': { 'tsid': {'$arrayElemAt':['$parent',0]}},
                                    'pipeline': [
                                        { '$match': { '$expr': { '$eq': ['$_id', '$$tsid'] }}},
                                        { '$lookup': {
                                            'from': 'projects',
                                            'let': {'cycleid':'$cycleid'},
                                            'pipeline':[
                                                { "$unwind":"$releases"},
                                                { "$unwind":"$releases.cycles"},
                                                { "$match": { '$expr': { '$eq': ['$releases.cycles._id', '$$cycleid']}}},
                                                { "$project":{'_id':1,'releases':1,'domain':1,'name':1}}
                                            ],
                                            'as' : 'proj' 
                                            }
                                        }
                                    ],
                                    'as': 'testsuites'
                                }},
                                {'$project': {'projects':{'$arrayElemAt':[{'$arrayElemAt':['$testsuites.proj',0]},0]},'mindmapid':{'$arrayElemAt':['$testsuites.mindmapid',0]},'cycleid':{'$arrayElemAt':['$testsuites.cycleid',0]},'name':{'$arrayElemAt':['$testsuites.name',0]},'_id':0}}
                            ],
                            'as':'executions'
                        }         
                    },
                    # { '$lookup': {
                    #         'from': 'reportitems',
                    #         'let': { 'pid': '$reportitems' },
                    #         'pipeline': [
                    #             { '$match': { '$expr': { '$in': ['$_id', '$$pid'] } } },
                    #             {'$unwind': '$rows'},
                    #             { '$replaceRoot': { 'newRoot': '$rows' } }
                    #         ],
                    #         'as':'rows'
                    #     }
                    # },
                    {'$project':{
                            # 'rows':1,
                            'executedtime':1,
                            'overallstatus':1,
                            'cycleid':{'$arrayElemAt':['$executions.cycleid',0]},
                            'testsuitename':{'$arrayElemAt':['$executions.name',0]},
                            'mindmapid':{'$arrayElemAt':['$executions.mindmapid',0]},
                            'projects':{'$arrayElemAt':['$executions.projects',0]},
                            'testscenarioname':{'$arrayElemAt':['$testscenarios.name',0]},
                            'testscenarioid':{'$arrayElemAt':['$testscenarios._id',0]},
                            'executionid':1
                        }
                    }
                ])
                finalQuery=[]
                for reportobj in list(query):
                    prjobj = reportobj['projects']
                    data={
                        'report': {
                            # "rows":reportobj["rows"],
                            "overallstatus":reportobj["overallstatus"]},
                        'testscenarioid': reportobj["testscenarioid"],
                        'testscenarioname': reportobj["testscenarioname"],
                        'domainname': prjobj["domain"],
                        'projectname': prjobj["name"],
                        'reportid': reportobj["_id"],
                        'releasename': prjobj["releases"]["name"],
                        'cyclename': prjobj["releases"]["cycles"]["name"],
                        'moduleid': reportobj["mindmapid"],
                        'testsuitename': reportobj["testsuitename"]
                    }
                    finalQuery.append(data)
                res["rows"] = finalQuery
                if len(errIds) != 0:
                    res["errMsg"] = errMsg+'Scenario Id(s): '+(','.join(errIds))
            else:
                app.logger.warn('Empty data received. report.')
                res["errMsg"] = "Invalid Execution ID"
        except Exception as getreportexc:
            if errMsgVal:
                res['errMsg']=errMsg+'Execution Id: '+errMsgVal
            servicesException("getReport_API", getreportexc, True)
        return flask.Response(flask.json.dumps(res), mimetype="application/json")

    @app.route('/reports/getAccessibilityTestingData_ICE',methods=['POST'])
    def getAccessibilityData_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata["query"])
            app.logger.debug("Inside getAccessibilityTestingData_ICE. Query: " + param)
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
            if requestdata["query"] == 'screendata':
                reports_data = dbsession.accessibilityreports.find({"cycleid": ObjectId(requestdata['cycleid'])},{"screenid":1,"screenname":1})
                result = {}
                for screen in reports_data:
                    result[str(screen["screenid"])]= screen["screenname"]
                res={'rows':result}
            elif requestdata["query"] == 'reportdata':
                reports_data = list(dbsession.accessibilityreports.find({"_id":ObjectId(requestdata['executionid'])}))
                res={'rows':reports_data}
            elif requestdata["query"] == 'insertdata':
                data = []
                reports = requestdata['reports']
                for report in reports:
                    reports_data = {}
                    if "_id" in report:
                        del report["_id"]
                    reports_data['level'] = report['level']
                    reports_data['agent'] = report['agent']
                    reports_data['url'] = report['url']
                    reports_data['cycleid'] = ObjectId(report['cycleid'])
                    reports_data['executionid'] = ObjectId(report['executionid'])
                    reports_data['screenname'] = report['screenname']
                    reports_data['screenid'] = ObjectId(report['screenid'])
                    reports_data['access-rules'] = report['access-rules']
                    reports_data['screenshotpath'] = report['screenshotpath']
                    reports_data['screenshotwidth'] = report['width']
                    reports_data['screenshotheight'] = report['height']
                    reports_data['rulemap'] = {"cat_aria":{},"best-practice":{},"wcag2a":{},"wcag2aa":{},"wcag2aaa":{},"cat_aria":{},"section508":{}}
                    for typeofresult in report['accessibility']:
                        for acc_data in report['accessibility'][typeofresult]:
                            for ruletype in acc_data['tags']:
                                ruletype = ruletype.replace(".","_")
                                if ruletype in reports_data['rulemap']:
                                    if typeofresult not in reports_data['rulemap'][ruletype]:
                                        reports_data['rulemap'][ruletype][typeofresult] = []
                                    reports_data['rulemap'][ruletype][typeofresult].append(acc_data)
                    reports_data['title'] = report['title']
                    reports_data['executedtime'] = datetime.utcnow()
                    data.append(InsertOne(reports_data))
                if len(data) > 0:
                    dbsession.accessibilityreports.bulk_write(data)
                res={'rows':'success'}
            elif requestdata["query"] == 'reportdata_names_only':
                reports_data = list(dbsession.accessibilityreports.find({"screenname":requestdata['screenname']},{"_id":1, "executedtime":1, "title":1}))
                res={'rows':reports_data}
            return jsonify(res)
        except Exception as e:
            servicesException("getAccessibilityTestingData_ICE",e)
            res={'rows':'fail'}
        return jsonify(res)

    @app.route('/reports/getAccessibilityReports_API',methods=['POST'])
    def getAccessibilityReports_API():
        res={'rows':'fail'}
        result = {}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            reports = dbsession.accessibilityreports.find({"executionid":ObjectId(requestdata["executionid"])})
            result = list(reports)
            res['rows'] = result
            return jsonify(res)
        except Exception as e:
            servicesException("getAccessibilityReports_API",e)
            res={'rows':'fail'}
        return jsonify(res)    

    #Fetching Execution Metrics from Reports
    @app.route('/reports/getExecution_metrics_API',methods=['POST'])
    def getExecution_metrics_API():
        res={'rows':'fail','errMsg':''}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getExecution_metrics_API")
            arr = []
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                status_dict={'pass':'Pass','fail':'Fail','skipped':'Skipped','incomplete':'Incomplete','terminate':'Terminate'}
                if requestdata['fromdate'] and requestdata['todate']:
                    start=requestdata["fromdate"]
                    end=requestdata["todate"]
                    if (not requestdata['api']):
                        start=start.split('-')
                        end=end.split('-')
                        start=start[2]+'-'+start[1]+'-'+start[0]
                        end=end[2]+'-'+end[1]+'-'+end[0]
                    try:
                        start=datetime.strptime(start,'%Y-%m-%d')
                        end=datetime.strptime(end,'%Y-%m-%d')
                    except ValueError:
                        res['errMsg'] = "Invalid Date Format, date should be in YYYY-MM-DD"
                        return jsonify(res)
                    end += timedelta(days=1)
                    query={'executedtime':{"$gte": start, "$lte": end}}
                if 'executionid' in requestdata and valid_objectid(requestdata['executionid']):
                    query['executionid']=ObjectId(requestdata['executionid'])
                elif 'executionid' in requestdata:
                    res['errMsg'] = "Invalid Execution Id"
                    return jsonify(res)
                if 'status' in requestdata and requestdata['status'].lower() in status_dict:
                    query['status']=status_dict[requestdata['status'].strip().lower()]
                elif 'status' in requestdata:
                    res['errMsg'] = "Invalid Status"
                    return jsonify(res)
                if 'modifiedby' in requestdata:
                    query['modifiedby']=ObjectId(requestdata['modifiedby'])
                LOB=requestdata["LOB"]
                report = dbsession.reports.find(query,{"testscenarioid":1,"status":1,"overallstatus":1,"modifiedby":1})
                res['rows']=arr
                for i in report:
                    details = {}
                    scenarioid = i["testscenarioid"]
                    status = i["status"]
                    report = i["overallstatus"]
                    starttime = i["overallstatus"]["StartTime"].split(".")[0]
                    endtime = i["overallstatus"]["EndTime"].split(".")[0]
                    modifiedby = i["modifiedby"]
                    details["testresult"] = status
                    details["teststarttime"] = starttime
                    details["testendtime"] = endtime
                    userdetails = list(dbsession.users.find({"_id":modifiedby},{"name":1}))
                    if len(userdetails)>0:
                        username = userdetails[0]["name"]
                        details["username"]= username
                    else:
                        details["username"] = modifiedby

                    scenariodetails = list(dbsession.testscenarios.find({"_id":scenarioid},{"name":1,"projectid":1}))
                    scenarioname = scenariodetails[0]["name"]
                    projectid = scenariodetails[0]["projectid"]
                    details["testcasename"] = scenarioname

                    projectdetails = list(dbsession.projects.find({"_id":projectid},{"name":1,"type":1}))
                    projectname = projectdetails[0]["name"]
                    details["applicationname"] = projectname
                    projecttypeid = projectdetails[0]["type"]

                    projecttypedetails = list(dbsession.projecttypekeywords.find({"_id":projecttypeid},{"name":1}))
                    technology = projecttypedetails[0]["name"]
                    details["technology"] = 'Avo Assure'
                    details["lob"] = LOB
                    arr.append(details)
                    res['rows']=arr
                if len(arr)==0:
                    res['errMsg']='No Records for the given Parameters'
            else:
                app.logger.warn('Empty data received. report.')
                res['errMsg']='Invalid Request : Empty Parameter not allowed'
        except Exception as getmetricsexc:
            if isinstance(getmetricsexc,KeyError):
                res['errMsg']='Invalid Request : Parameter missing'
            servicesException("getExecution_metrics_API", getmetricsexc, True)
        return jsonify(res)

    #fetching the report by executionId - For synchronous Execution
    @app.route('/reports/getDevopsReport_API',methods=['POST'])
    def getDevopsReport_API():
        res={'rows':'fail','errMsg':''}
        errMsgVal=''
        errMsg='Invalid '
        errIds=[]
        finalQuery=[]
        correctScenarios=[]
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getDevopsReport_API")
            if not isemptyrequest(requestdata) and valid_objectid(requestdata['executionId']):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                filter1 = {"executionid":ObjectId(requestdata["executionId"])}
                if("scenarioIds" in requestdata):
                    scenarioIds = dbsession.reports.distinct("testscenarioid", filter1)
                    for scenId in requestdata["scenarioIds"]:
                        if len(scenId.strip())==0:
                            continue
                        try:
                            if ObjectId(scenId) not in scenarioIds:
                                errIds.append(str(scenId))
                            else:
                                correctScenarios.append(ObjectId(scenId))
                        except:
                            errIds.append(str(scenId))
                    if len(correctScenarios) != 0 or len(errIds) != 0:
                        filter1["testscenarioid"] = {"$in":correctScenarios}

                query = dbsession.reports.aggregate([
                    {'$match':{'testscenarioid':{"$in":correctScenarios},"executionid":ObjectId(requestdata["executionId"])}},
                    { '$lookup':{
                            'from':'testscenarios',
                            'let':{'testscenarioid':'$testscenarioid'},
                            'pipeline':[
                                { '$match': { '$expr': { '$eq': ['$_id', '$$testscenarioid']}}}
                            ],
                            'as':'testscenarios'
                        }
                    },
                    { '$lookup':{
                            'from':'executions',
                            'let':{'excid':'$executionid'},
                            'pipeline':[
                                { '$match': { '$expr': { '$eq': ['$_id', '$$excid']}}},
                                { '$lookup': {
                                    'from': 'testsuites',
                                    'let': { 'tsid': {'$arrayElemAt':['$parent',0]}},
                                    'pipeline': [
                                        { '$match': { '$expr': { '$eq': ['$_id', '$$tsid'] }}},
                                        { '$lookup': {
                                            'from': 'projects',
                                            'let': {'cycleid':'$cycleid'},
                                            'pipeline':[
                                                { "$unwind":"$releases"},
                                                { "$unwind":"$releases.cycles"},
                                                { "$match": { '$expr': { '$eq': ['$releases.cycles._id', '$$cycleid']}}},
                                                { "$project":{'_id':1,'releases':1,'domain':1,'name':1}}
                                            ],
                                            'as' : 'proj' 
                                            }
                                        }
                                    ],
                                    'as': 'testsuites'
                                }},
                                {'$project': {'projects':{'$arrayElemAt':[{'$arrayElemAt':['$testsuites.proj',0]},0]},'mindmapid':{'$arrayElemAt':['$testsuites.mindmapid',0]},'cycleid':{'$arrayElemAt':['$testsuites.cycleid',0]},'name':{'$arrayElemAt':['$testsuites.name',0]},'_id':0}}
                            ],
                            'as':'executions'
                        }         
                    },
                    # { '$lookup': {
                    #         'from': 'reportitems',
                    #         'let': { 'pid': '$reportitems' },
                    #         'pipeline': [
                    #             { '$match': { '$expr': { '$in': ['$_id', '$$pid'] } } },
                    #             {'$unwind': '$rows'},
                    #             { '$replaceRoot': { 'newRoot': '$rows' } }
                    #         ],
                    #         'as':'rows'
                    #     }
                    # },
                    {'$project':{
                            # 'rows':1,
                            'executedtime':1,
                            'overallstatus':1,
                            'cycleid':{'$arrayElemAt':['$executions.cycleid',0]},
                            'testsuitename':{'$arrayElemAt':['$executions.name',0]},
                            'mindmapid':{'$arrayElemAt':['$executions.mindmapid',0]},
                            'projects':{'$arrayElemAt':['$executions.projects',0]},
                            'testscenarioname':{'$arrayElemAt':['$testscenarios.name',0]},
                            'testscenarioid':{'$arrayElemAt':['$testscenarios._id',0]},
                            'executionid':1
                        }
                    }
                ])
                finalQuery=[]
                for reportobj in list(query):
                    prjobj = reportobj['projects']
                    data={
                        'report': {
                            # "rows":reportobj["rows"],
                            "overallstatus":reportobj["overallstatus"]},
                        'testscenarioid': reportobj["testscenarioid"],
                        'testscenarioname': reportobj["testscenarioname"],
                        'domainname': prjobj["domain"],
                        'projectname': prjobj["name"],
                        'reportid': reportobj["_id"],
                        'releasename': prjobj["releases"]["name"],
                        'cyclename': prjobj["releases"]["cycles"]["name"],
                        'moduleid': reportobj["mindmapid"],
                        'testsuitename': reportobj["testsuitename"]
                    }
                    finalQuery.append(data)
                res["rows"] = finalQuery
                if len(errIds) != 0:
                    res["errMsg"] = errMsg+'Scenario Id(s): '+(','.join(errIds))
            else:
                app.logger.warn('Empty data received. report.')
                res["errMsg"] = "Invalid Execution ID"
        except Exception as getreportexc:
            if errMsgVal:
                res['errMsg']=errMsg+'Execution Id: '+errMsgVal
            servicesException("getReport_API", getreportexc, True)
        return flask.Response(flask.json.dumps(res), mimetype="application/json")


# END OF REPORTS
