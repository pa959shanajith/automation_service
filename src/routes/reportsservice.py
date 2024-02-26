################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime
from pymongo import InsertOne
from ftplib import FTP
import os
import shutil
import base64
from document_modules.generateAI_module import UserDocument,UserTestcases,AI_Testcases
import requests
from datetime import datetime
from pathlib import Path


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
            # if not isemptyrequest(requestdata):
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            if(requestdata["query"] == 'projects'):
                queryresult1=dbsession.users.find_one({"_id": ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
                queryresult=list(dbsession.projects.find({"_id":{"$in":queryresult1["projects"]}},{"name":1,"releases":1,"type":1,"modifiedby":1,"progressStep":1, 'projectlevelrole':1, "modifiedon":1}))
                modifiedby_ids=[]
                for modifiedId in queryresult:
                    modifiedby_ids.append(ObjectId(modifiedId["modifiedby"]))
                modifiedby_ids=list(set(modifiedby_ids))                  
                queryresult2=list(dbsession.users.find({"_id":{"$in":modifiedby_ids}},{"firstname":1,"lastname":1,"_id":1,"projectlevelrole":1}))                    
                for username in queryresult:
                    for modifiedname in queryresult2:
                        if "projectlevelrole" in modifiedname:
                            for role in modifiedname['projectlevelrole']:
                                if role["_id"] == str(username['_id']):
                                    username['projectlevelrole']= role
                        if modifiedname["_id"] == username["modifiedby"]:
                            username["firstname"]=modifiedname["firstname"]
                            username["lastname"]=modifiedname["lastname"]
                            break
                
                for ids in queryresult: 
                    list_of_modules = list(dbsession.mindmaps.find({"projectid":ids["_id"]}))
                    listofmodules=[]
                    for prj_ids in list_of_modules:
                        listofmodules.append(prj_ids["_id"])
                    if len(list_of_modules) == 0 :
                        progressStep = 0
                    keyDetails =dbsession.configurekeys.find({"executionData.batchInfo.projectId":ids["_id"]}).count()
                    if len(list_of_modules) > 0 and keyDetails == 0 :
                        progressStep = 1
                    executionList=list(dbsession.testsuites.find({"mindmapid":{"$in":listofmodules}},{"_id":1}))
                    if len(list_of_modules) > 0 and keyDetails > 0 and len(executionList) == 0 :
                            progressStep = 2
                    elif len(executionList) > 0:
                            progressStep = 3
                    ids["progressStep"]=progressStep
            
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
                    }},
                    {'$lookup':{
                        'from':"executions",
                        'localField':"_id",
                        'foreignField':"parent",
                        'as':"check"
                        }
                    },
                    {'$project':{
                        '_id':1,
                        'name':1,
                        'type':1,
                        'executionCount':{'$size':'$check'},
                        'lastExecutedtime':{ "$max": "$check.starttime"}
                    }}
                ]))
                # Pagination
                search_key = requestdata['searchKey']
                if search_key:
                    # Perform search within 'configurename' field
                    matching_items = [item for item in queryresult if search_key in item.get('name', '')]
                    total_count = len(matching_items)
                    items_to_paginate = matching_items
                else:
                    # No search term provided, use the entire dataset
                    total_count = len(queryresult)
                    items_to_paginate = queryresult
                pagecount= requestdata['page']
                limit = 10
                startindex = (pagecount - 1) * limit
                end_index = startindex + limit
                pagination_data = items_to_paginate[startindex:end_index]
                total_count = len(items_to_paginate)  
                response = {
                    "data" :pagination_data,
                    "pagination" : {
                        "page" : pagecount,
                        'limit' : limit,
                        'totalcount' : total_count
                    }
                }
                batchresult=list(dbsession.executions.distinct('batchname',{'parent':{'$in':[i['_id'] for i in response['data']]}}))
                batch_data = batchresult[startindex:end_index]
                totalBahtch_count = len(batchresult)  
                batch_response = {
                    "data" :batch_data,
                    "pagination" : {
                        "page" : pagecount,
                        'limit' : limit,
                        'totalcount' : totalBahtch_count
                    }
                }
                res= {"rows":{"modules":response,"batch":batch_response}}
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
                
                # res = queryresult if 'executionListId' in requestdata['data'] else {"modules": testSuiteNames}
                res = {"modules": testSuiteNames}

            # else:
            #     app.logger.warn('Empty data received. report suites details.')
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
                    {'$match':{"executionid":ObjectId(requestdata["executionid"]) }},
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
                # report_items= list(dbsession.reportitems.find({"_id":reports[0]["reportitems"][0]}))

                # Added below query 
                report_items= list(dbsession.reportitems.find({'reportid':reports[0]['_id']}))
                scenarios = list(dbsession.testscenarios.find({"_id":reports[0]["testscenarioid"]}))
                execs = list(dbsession.executions.find({"_id":reports[0]["executionid"]}))
                testsuites = list(dbsession.testsuites.find({"_id":execs[0]["parent"][0]}))
                projs = list(dbsession.projects.find({"releases.cycles._id":testsuites[0]["cycleid"]},{'_id':1,'releases':{'$elemMatch': {"cycles._id":testsuites[0]["cycleid"]}},'domain':1,'name':1}))
                
                for cyc in projs[0]["releases"][0]["cycles"]:
                    if testsuites[0]["cycleid"] == cyc["_id"]:
                        cyclename = cyc["name"]
                        break
                        
                reportData = {"rows":report_items,"overallstatus":reports[0]["overallstatus"]}
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
                # for i in range(llimit,len(report)): # practically should iterate once
                #     a = list(dbsession.reportitems.find({"_id":report[i],"rows.id":slno},{"rows.$":1}))
                #     if(len(a)>0):
                #         report_rows=a[0]['rows']
                #         reportitemsid =a[0]['_id']
                #         break

                a = list(dbsession.reportitems.find({"reportid":queryresult[0]['_id'],"id":slno}))
                report_rows=a[0]
                reportitemsid = a[0]['_id']
                row = None
                obj = report_rows
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
                    queryresult = dbsession.reportitems.replace_one({"_id":reportitemsid,"id":slno},row)
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
                        if len(scenId['testscenarioid'].strip())==0:
                            continue
                        try:
                            if ObjectId(scenId['testscenarioid']) not in scenarioIds:
                                errIds.append(str(scenId['testscenarioid']))
                            else:
                                correctScenarios.append(ObjectId(scenId['testscenarioid']))
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
        
    @app.route('/reports/fetchExecutionDetail', methods=['POST'])
    def fetchExecutionDetail():
        res = {'rows': 'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside fetchExecutionDetail.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                TF = '%Y-%m-%d %H:%M:%S'
                startdate = datetime.strptime(requestdata['startDate'], TF)                
                enddate = datetime.strptime(requestdata['endDate'], TF)            
                if requestdata["prefixRegexProjName"] != "Default":                    
                    projId=list(dbsession.projects.aggregate( [{"$match":{"name": { "$regex":requestdata["prefixRegexProjName"], "$options": 'i' } }} ,
                    {"$group":{"_id":"null","projectids":{"$push":"$_id"}}}]))                    
                elif type(requestdata["ProjName"]) != str:
                    projId=list(dbsession.projects.aggregate( [{"$match":{"name": { "$in":requestdata["ProjName"]} }} ,
                    {"$group":{"_id":"null","projectids":{"$push":"$_id"}}}]))
                else:
                    projId=list(dbsession.projects.aggregate( [{"$match":{"name": requestdata["ProjName"] }} ,
                    {"$group":{"_id":"null","projectids":{"$push":"$_id"}}}])) 
                    
                if len(projId)>0:
                    testsecnarioids=list(dbsession.testscenarios.aggregate([{"$match":{"projectid":{"$in": projId[0]["projectids"]}}},
                    {"$group":{"_id":"null","testscenarioids":{"$push":"$_id"}}}]))
                    if len(testsecnarioids)>0:
                        testsuiteids=list(dbsession.testsuites.aggregate([{"$match":{"testscenarioids": {"$in":testsecnarioids[0]["testscenarioids"]}}},
                        {"$group":{"_id":"null","testsuiteids":{"$push":"$_id"}}}]))
                        if len(testsuiteids)>0:
                            executionids=list(dbsession.executions.aggregate([{"$match":{"starttime": {"$gte":startdate,"$lte": enddate},
                            "parent":{"$in":testsuiteids[0]["testsuiteids"]}}},
                            {"$group":{"_id":"null","executionids":{"$push":"$_id"}}}]))
                            if len(executionids)>0:
                                count=dbsession.reports.find({"executionid": {"$in":executionids[0]["executionids"]}}).count()
                                if count <= 5000:
                                    dbsession.reports.aggregate([{"$match":{"executionid": {"$in":executionids[0]["executionids"]
                                            }}},{"$lookup":{
                                            'from': "testscenarios",
                                            'localField': "testscenarioid",
                                            'foreignField': "_id",
                                            'as': "scenario"}},{"$unwind":"$scenario"},{"$project":{"_id":0,"scenarioid":"$scenario._id","Scenario_Name":"$scenario.name",
                                            "status":"$overallstatus.overallstatus","StartTime":"$overallstatus.StartTime","EndTime":"$overallstatus.EndTime",
                                            "BrowserType":"$overallstatus.browserType"}},{"$out":"scen_exe"}])
                                    dbsession.scen_exe.aggregate([{"$lookup":{
                                            'from': "mindmaps",
                                            'localField': "scenarioid",
                                            'foreignField': "testscenarios._id",
                                            'as': "mindmaps"}},{"$unwind":"$mindmaps"},
                                            {"$group":{"_id":"$mindmaps.name","projectid":{"$first":"$mindmaps.projectid"},"Testscenarios_details":{"$push":
                                            {"Scenario_Name":"$Scenario_Name",
                                            "status":"$status","StartTime":"$StartTime","EndTime":"$EndTime",
                                            "BrowserType":"$BrowserType"}},"passcount":{ "$sum": { "$cond": [ { "$eq": [ "$status", 'Pass' ] }, 1, 0 ] } }}},
                                            {"$project":{"name":"$_id","_id":0,"projectid":1,"passcount":1,"Testscenarios_details":1,"Totalcount":{"$size":"$Testscenarios_details"}}},{"$out":"mod_exe"}
                                            ])
                                    dbsession.projects.aggregate([{"$match":{"_id": { "$in":projId[0]["projectids"]}}},{"$lookup":{
                                            'from': "projecttypekeywords",
                                            'localField': "type",
                                            'foreignField': "_id",
                                            'as': "apptype"}},{"$unwind":"$apptype"},
                                            {"$project":{"projName":"$name","appType":"$apptype.name"}},{"$out":"proj_exe"}
                                            ])
                                    data=list(dbsession.proj_exe.aggregate([{"$lookup":{
                                            'from': "mod_exe",
                                            'localField': "_id",
                                            'foreignField': "projectid",
                                            'as': "Testsuite_Details"}},{"$project":{"_id":0,"Testsuite_Details._id":0,"Testsuite_Details.projectid":0}}]))
                                    dbsession.proj_exe.drop()
                                    dbsession.scen_exe.drop()
                                    dbsession.mod_exe.drop()
                                    if data:
                                            res={'rows':data}
                                else:
                                    res="Execution details exceeded the limit of 5000"
                            else:
                                res="No Exceutions found for the given project during the given startDate and endDate"
                        else:
                            res="No Testsuites found for the given project"
                    else:
                        res="No Testscenarios found for the given project"
                else:
                    res="No Projects found"
                
            else:
                app.logger.warn('Empty data received while fetching execution details')
        except Exception as  fetchExecutionDetailexc:
            dbsession.proj_exe.drop()
            dbsession.scen_exe.drop()
            dbsession.mod_exe.drop()
            servicesException("fetchExecutionDetail",fetchExecutionDetailexc, True)
        return jsonify(res)
    
    @app.route('/reports/fetchExecProfileStatus',methods=['POST'])
    def fetchExecProfileStatus():
        res={'rows':'fail'}
        result = {}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            if 'configurekey' in requestdata:
                configurekey= requestdata['configurekey']
                reports = dbsession.executions.aggregate([{"$match":{"configurekey":configurekey}},{"$group":{"_id":"$executionListId",
                                                                    "modStatus":{"$push":{"_id":"$_id","status":"$status"}},"startDate":{"$first":"$starttime"}}},
                                                                    {'$lookup':{
                                                                                        'from':"reports",
                                                                                        'localField':"modStatus._id",
                                                                                        'foreignField':"executionid",
                                                                                        'as':"reportdata"
                                                                                        }
                                                                                    },
                                                                                    {"$project":{"_id":1,"modStatus":"$modStatus.status","scestatus":"$reportdata.status","startDate":1}},{"$sort":{"startDate":-1}}
                                                                                    ])
            
            else:
                testsuiteid = ObjectId(requestdata['testsuiteid'])
                reports = dbsession.executions.aggregate([
                    {"$match":{"parent":testsuiteid}},
                    {"$project": {
                        "_id":1,
                        "status":1,
                        "starttime": 1
                    }},
                    {"$lookup": {
                        'from':"reports",
                        'localField':"_id",
                        'foreignField':"executionid",
                        'as':"reportdata"
                    }},
                    {"$project":{"_id":1,
                        "modstatus":["$status"],
                        "scestatus":"$reportdata.status",
                        "starttime":1}},
                    {"$sort":{"startDate":-1}}
                ])
            result = list(reports)
            res['rows'] = result
            return jsonify(res)
        except Exception as e:
            servicesException("fetchExecProfileStatus",e)
            res={'rows':'fail'}
        return jsonify(res)    
    

    @app.route('/reports/fetchModSceDetails',methods=['POST'])
    def fetchModSceDetails():
        res={'rows':'fail'}
        result = {}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            # configurekey= requestdata['configurekey']
            if (requestdata["param"] == "modulestatus"):
                executionListId = requestdata['executionListId']
                reports = dbsession.executions.aggregate([{"$match":{"executionListId":executionListId}},
                                                                        {"$project":{"parent":1,"status":1}},{'$lookup':{
                                                                        'from':"testsuites",
                                                                        'localField':"parent",
                                                                        'foreignField':"_id",
                                                                        'as':"testsuites"
                                                                            }
                                                                        },{'$lookup':{
                                                                        'from':"reports",
                                                                        'localField':"_id",
                                                                        'foreignField':"executionid",
                                                                        'as':"reports"
                                                                        } },
                                                                        {"$project":{'modulename':{"$arrayElemAt":["$testsuites.name",0]},"status":1,"scenarioStatus":"$reports.status"}}
                                                                        ])
            elif (requestdata["param"] == "scenarioStatus"): 
                executionid = requestdata['executionId']
                reports=dbsession.reports.aggregate([{"$match":{"executionid":ObjectId(executionid)}},
                                                            {"$project":{"testscenarioid":1,"status":1}},
                                                            {'$lookup':{'from':"testscenarios",
                                                                        'localField':"testscenarioid",
                                                                        'foreignField':"_id",
                                                                        'as':"testscenarios"
                                                                         }
                                                            },{"$project":{'scenarioname':{"$arrayElemAt":["$testscenarios.name",0]},"status":1}}])

            result = list(reports)  
            res['rows'] = result    
            return jsonify(res) 
        except Exception as e:
            servicesException("fetchModSceDetails",e)
            res={'rows':'fail'}
        return jsonify(res)

    #fetching all the reports status
    @app.route('/reports/reportStatusScenario',methods=['POST'])
    def reportStatusScenario():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside reportStatusScenarios_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if(requestdata["query"] == 'executiondetails'):
                    queryresult = []
                    for executionId in requestdata["executionId"]:
                        statusList = []
                        result = list(dbsession.reports.find({"executionid": ObjectId(executionId)}))
                        for element in result:
                            status = { "status": element["status"], "reportId": str(element['_id']), "timeEllapsed": element["overallstatus"]["EllapsedTime"] }
                            statusList.append(status)
                        queryresult.append(statusList)
                    res = {"rows":queryresult}
            else:
                app.logger.warn('Empty data received. report status of scenarios.')
        except Exception as getreportstatusexc:
            servicesException("reportStatusScenarios_ICE",getreportstatusexc)
        return jsonify(res)
    
    def save_file(file_content,target_folder,filename,request_data):
        try:
            pdf_binary_data = bytes(file_content['buffer']['data'])
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            destination_path = os.path.join(target_folder,filename)
            
            with open(destination_path, 'wb') as pdf_file:
                pdf_file.write(pdf_binary_data)
                
            app.logger.info(f"Stored file '{filename}' in folder '{target_folder}'")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the path to server_config.json
            config_path = os.path.join(current_dir, '..','..', 'server_config.json')
            with open(config_path, 'r') as config:
                # Load the JSON data from the config file
                conf = json.load(config)

            # Extract the value for "genAIurl" key from the loaded JSON data
            # addr = conf.get("genAIurl", None)
            addr = "https://aiapidevtest.avoassurecloud.com"
            test_url = addr + '/send_text'
            # files = request_data['file']
            files = {'file': (filename, open(destination_path, 'rb'))}
            data={'instancename':request_data['organization'],'projectname':request_data['project'],'type':request_data['type'],'username':request_data['name']}
            
            response = requests.post(test_url,data=data,files=files,verify = False,timeout=None)
            if response.status_code == 200:
                app.logger.info('generate AI file sent successfully')
                return True
            elif response.status_code == 400:
                app.logger.error('Bad Request')
                return False
            elif response.status_code == 401:
                app.logger.error('Unauthorized user')
                return False
            elif response.status_code == 403:
                app.logger.error('user does not have the necessary permissions to access')
                return False
            elif response.status_code == 404 :
                app.logger.error('Source not found')
                return False
            elif response.status_code == 500 :
                app.logger.error('Internal Server Error')
                return False
            return True        
        except Exception as e:
            app.logger.error(f"Error saving file: {str(e)}")
            return False
            
    @app.route('/upload/generateAIfile', methods=['POST'])
    def upload_file():
        try:
            request_data = request.get_json()

            if 'file' not in request_data or 'originalname' not in request_data['file']:
                return jsonify({'error': 'Invalid request data'}), 400
            
            
                
            filename = request_data['file']['originalname']
            project_name = request_data['project']
            organization_name = request_data['organization']
            home_directory = Path.home()
            app.logger.info("Home Directory:", home_directory)
            base_dir = home_directory + os.sep + 'GenerateAI_temp'
            app.logger.info("Base Dir : ", base_dir)
            target_folder = f'{base_dir}/{organization_name}/{project_name}'

            if save_file(request_data['file'], target_folder, filename,request_data):
                client_name = getClientName(request_data)
                dbsession = client[client_name]

                document_data = UserDocument(
                    project=project_name,
                    orgname=organization_name,
                    name=request_data['name'],
                    # path=os.path.join(target_folder, filename),
                    path=f'{target_folder}/{filename}',
                    uploadedBy=request_data['email'],
                    input_type=request_data['type'],
                    version="1.0"
                )

                data_to_insert = document_data.to_dict()
                insert_result = dbsession.generateAI_temp.insert_one(data_to_insert)

                if insert_result.acknowledged:
                    return jsonify({'rows':'success', 'message': 'File uploaded successfully'}), 200
                else:
                    return jsonify({'rows':'fail','error': 'Data insertion failed'}), 500
            else:
                return jsonify({'rows':'fail','error': 'File upload failed'}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
    
    @app.route('/upload/getallUploadFiles', methods=['POST'])
    def getallfiles():
        try:
            request_data = request.get_json()

            if 'email' not in request_data:
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            fetch_result = list(dbsession.generateAI_temp.find({"uploadedBy":request_data['email']}))

            if len(fetch_result):
                return jsonify({'rows':fetch_result, 'message': 'records found'}), 200
            else:
                return jsonify({'rows':[],'message': 'no records found'}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
    
    @app.route('/generate/testcase', methods=['POST'])
    def generateTestcase():
        try:
            request_data = request.get_json()
            required_fields = ['email', 'name', 'projectname', 'organization', 'generateType']
            if all(field not in request_data and ('generateType' not in request_data or 'typename' not in request_data['generateType']) for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            headers = {
                'Accept': 'application/json',
                'Content-Type':'application/json'
            }
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the path to server_config.json
            config_path = os.path.join(current_dir, '..','..', 'server_config.json')
            with open(config_path, 'r') as config:
                # Load the JSON data from the config file
                conf = json.load(config)

            # Extract the value for "genAIurl" key from the loaded JSON data
            # addr = conf.get("genAIurl", None)
            addr = "https://aiapidevtest.avoassurecloud.com"
            test_url = addr + '/generate_testcase'
           
            data={'generate_type':request_data['generateType'], 'instancename':request_data['organization'],'projectname':request_data['project'],'email':request_data['email'],'username':request_data['name']}
            json_data = json.dumps(data)
            response = requests.post(test_url,headers=headers,data=json_data,verify = False,timeout=None)
            if response.status_code == 200:
                JsonObject = response.json()
                app.logger.info('testcase generated successfully')
                return jsonify({'rows':JsonObject, 'message': 'records found'}), 200
            elif response.status_code == 400:
                app.logger.error('Bad Request')
                return jsonify({'rows':"fail", 'message': 'Bad Request'}), 400
            elif response.status_code == 401:
                app.logger.error('Unauthorized user')
                return jsonify({'rows':"fail", 'message': 'Unauthorized user'}), 401
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

    @app.route('/JSON/userstory', methods=['POST'])
    def getuserstories():
        try:
            request_data = request.get_json()
            required_fields = ['email', 'name','organization']
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            query = {
                "uploadedBy": request_data['email'],
                "name": request_data['name'],
                "organization": request_data['organization'],
                "uploadedTime": {'$exists': True},
                "type":"userstories"
            }
            fetch_result = list(dbsession.generateAI_temp.find(query).sort("uploadedTime",-1).limit(1))

            if len(fetch_result):
                json_file_path = fetch_result[0]['path']
                with open(json_file_path,'r') as file:
                    json_data = file.read()
                return jsonify({'rows':eval(json_data), 'message': 'records found'}), 200
            else:
                return jsonify({'rows':[],'message': 'no records found'}), 200

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
    
    @app.route('/Save/testcases', methods=['POST'])
    def saveTestcases():
        try:
            request_data = request.get_json()
            required_fields = ['email', 'name','organization','projectname','testcase','type']
            if all(field not in request_data for field in required_fields):
                return jsonify({'error': 'Invalid request data'}), 400
            client_name = getClientName(request_data)
            dbsession = client[client_name]
            
            document_testcase = AI_Testcases(
                testcase = request_data['testcase']
            )

            testcase_to_insert = document_testcase.to_dict()
            insert_result = dbsession.AI_Testcases.insert_one(testcase_to_insert)

            if insert_result.acknowledged:
                query = {
                "email": request_data['email'],
                "name": request_data['name'],
                "organization": request_data['organization'],
                "project": request_data['projectname']
                }
                update = {
                    "$push": {
                    "testcases": {
                        "testcase": insert_result.inserted_id,
                        "testcasetype": request_data['type'],
                        "createdAt": datetime.now(),
                        "updatedAt": datetime.now()
                    }
                }
                }
                insert_user_testcase = dbsession.UserTestcases.update_one(query,update,upsert=True)
                if insert_user_testcase.acknowledged:
                   return jsonify({'rows':'success', 'message': 'user and AI testcase saved successfully'}), 200
                    
                else:
                    return jsonify({'rows':'fail','error': 'failed to save user testcase'}), 500
            else:
                return jsonify({'rows':'fail','error': 'Data save or update failed'}), 500

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
    
    @app.route('/download/downloadReport', methods=['POST'])
    def downloadReport():
        try:
            requestdata = request.get_json()
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            executionListId = requestdata['executionListId']
            reportdata = dbsession.executions.aggregate([{"$match":{"executionListId":executionListId}},
                                                                        {"$project":{"parent":1,"status":1, "starttime":1,"endtime":1,"projectId":1,"batchid":1}},{'$lookup':{
                                                                        'from':"testsuites",
                                                                        'localField':"parent",
                                                                        'foreignField':"_id",
                                                                        'as':"testsuites"
                                                                            }
                                                                        },
                                                                        {
                                                                        '$addFields': {'projectId': {'$toObjectId': '$projectId'}}
                                                                        },
                                                                        {'$lookup':{
                                                                        'from':"reports",
                                                                        'localField':"_id",
                                                                        'foreignField':"executionid",
                                                                        'as':"reports"
                                                                        } },
                                                                        {'$lookup':{
                                                                            'from' : "projects",
                                                                            'localField': "projectId",
                                                                            'foreignField': "_id",
                                                                            'as': "projectName"
                                                                        }},
                                                                        {"$project":{'modulename':{"$arrayElemAt":["$testsuites.name",0]},"projectname" : "$projectName.name","status":1,"scenarioStatus":"$reports.status","overallstatusReport":"$reports.overallstatus","starttime":1,"endtime":1,"batchid":1}}
                                                                        ])
            result = list(reportdata)  
            res = {"rows" :result}    
            return jsonify(res)        

        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            return jsonify({'rows':'fail','error': 'Internal server error'}), 500
# END OF REPORTS
