################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime
from pymongo import InsertOne


def LoadServices(app, redissession, dbsession):
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
                    res= {"rows":queryresult}
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
                queryresult=list(dbsession.executions.find({"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1,"version":1}))
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
                if(requestdata["query"] == 'executiondetails'):
                    queryresult = list(dbsession.reports.find({"executionid":ObjectId(requestdata["executionid"])},{"_id":1,"executionid":1,"executedon":1,"comments":1,"executedtime":1,"modifiedby":1,"modifiedbyrole":1,"modifiedon":1,"status":1,"testscenarioid":1}))
                    if len(queryresult) > 0:
                        r_scids = list(set([i["testscenarioid"] for i in queryresult]))
                        scos = dbsession.testscenarios.find({"_id": {"$in": r_scids}},{"name":1})
                        scidmap = {}
                        for sco in scos:
                            scidmap[sco["_id"]] = sco["name"]
                        for rep in queryresult:
                            rep["testscenarioname"] = scidmap.get(rep["testscenarioid"], '')
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
                query = dbsession.reports.aggregate([
                    {'$match':{'_id':ObjectId(requestdata["reportid"])}},
                    { '$lookup':{
                            'from':'testscenarios',
                            'let':{'testscenarioid':'$testscenarioid'},
                            'pipeline':[
                                { '$match': { '$expr': { '$eq': ['$_id', '$$testscenarioid']}}},
                                { '$lookup': {
                                            'from':'projects',
                                            'let':{'projectid':'$projectid'},
                                            'pipeline':[{ '$match': { '$expr': { '$eq': ['$_id', '$$projectid']}}}],
                                            'as':'project'
                                    }
                                },
                                { '$project':{'name':1,'projects':{'_id':{'$arrayElemAt':['$project._id',0]},'domain':{'$arrayElemAt':['$project.domain',0]},'name':{'$arrayElemAt':['$project.name',0]},'releases':{'$arrayElemAt':['$project.releases',0]}}}}
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
                                    ],
                                    'as': 'testsuites'
                                }},
                                {'$project': {'cycleid':{'$arrayElemAt':['$testsuites.cycleid',0]},'name':{'$arrayElemAt':['$testsuites.name',0]},'_id':0}}
                            ],
                            'as':'executions'
                        }         
                    },
                    { '$lookup': {
                            'from': 'reportitems',
                            'let': { 'pid': '$reportitems' },
                            'pipeline': [
                                { '$match': { '$expr': { '$in': ['$_id', '$$pid'] } } },
                                {'$unwind': '$rows'},
                                { '$replaceRoot': { 'newRoot': '$rows' } }
                            ],
                            'as':'rows'
                        }
                    },
                    {'$project':{
                            'rows':1,
                            'executedtime':1,
                            'overallstatus':1,
                            'projects':{'$arrayElemAt':['$testscenarios.projects',0]},
                            'cycleid':{'$arrayElemAt':['$executions.cycleid',0]},
                            'testsuitename':{'$arrayElemAt':['$executions.name',0]},
                            'testscenarioname':{'$arrayElemAt':['$testscenarios.name',0]},
                            'testscenarioid':{'$arrayElemAt':['$testscenarios._id',0]},
                            'executionid':1
                        }
                    }
                ])
                reportobj = list(query)
                #reportobj = dbsession.reports.find_one({"_id":ObjectId(requestdata["reportid"])},{"executedtime":1,"report":1,"testscenarioid":1,"executionid":1})
                if len(reportobj) == 0:
                    res['rows'] = []
                    return res
                reportobj=reportobj[0]
                reportData = {"rows":reportobj["rows"],"overallstatus":reportobj["overallstatus"]}
                prjobj = reportobj['projects']
                # scenarioname = dbsession.testscenarios.find_one({"_id":reportobj['testscenarioid']},{"name":1,"_id":0})["name"]
                # suiteid = dbsession.executions.find_one({"_id":reportobj['executionid']},{"parent":1,"version":1,"_id":0})
                # suiteobj = dbsession.testsuites.find_one({"_id":suiteid["parent"][0]},{"name":1,"cycleid":1,"_id":0})
                # cycleid = suiteobj['cycleid']
                # prjobj = dbsession.projects.find_one({"releases.cycles._id":cycleid},{"domain":1,"name":1,"releases":1})
                query = {
                    'report': reportData,
                    'executionid': reportobj['executionid'],
                    'executedtime': reportobj["executedtime"],
                    'testscenarioid': reportobj["testscenarioid"],
                    'testscenarioname': reportobj["testscenarioname"],
                    'testsuitename': reportobj["testsuitename"],
                    'projectid': prjobj["_id"],
                    'domainname': prjobj["domain"],
                    'projectname': prjobj["name"]
                }
                found = False
                for rel in prjobj["releases"]:
                    for cyc in rel["cycles"]:
                        if cyc["_id"] == reportobj['cycleid']:
                            query["releasename"] = rel["name"]
                            query["cyclename"] = cyc["name"]
                            found = True
                            break
                    if found: break
                res= {"rows":query}
            else:
                app.logger.warn('Empty data received. report.')
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
                queryresult = dbsession.reports.find({"_id":ObjectId(requestdata["reportid"])},{"report":1})
                report = queryresult[0]['report']
                report_rows = report['rows']
                row = None
                for obj in report_rows:
                    if obj['id']==int(requestdata['slno']):
                        row = obj
                    if "'" in obj['StepDescription']:
                        obj['StepDescription'] = obj['StepDescription'].replace("'",'"')
                if(row!=None):
                    row.update({'jira_defect_id':str(requestdata['defectid'])})
                    report['rows']=report_rows
                    queryresult = dbsession.reports.update({"_id":ObjectId(requestdata["reportid"])},{"$set":{"report":report}})
                    dbsession.thirdpartyintegration.insert_one({
                        "type":"JIRA",
                        "reportid":requestdata["reportid"],
                        "defectid":requestdata['defectid'],
                        "stepDetails":{
                                "stepid": row["id"],
                                "stepdescription": row["StepDescription"].replace('""',"'"),
                                "Keyword": row["Keyword"]
                            }
                        })
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
                errMsgVal=str(requestdata["executionId"])
                tsuite = dbsession.executions.find_one({"_id": ObjectId(requestdata["executionId"])})["parent"]
                errMsgVal=''
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
                queryresult1 = dbsession.reports.find(filter1)
                cycleid_dict = {}
                for reportobj in queryresult1:
                    tscid = reportobj["testscenarioid"]
                    tsc = dbsession.testscenarios.find_one({"_id":tscid},{"name":1,"projectid":1,"_id":0})
                    tsuobj = {}
                    for tsuid in tsuite:
                        tsuobj_t = dbsession.testsuites.find_one({"_id":tsuid, "testscenarioids": tscid})
                        if tsuobj_t:
                            tsuobj = tsuobj_t
                            break
                    prjobj = dbsession.projects.find_one({"_id":tsc["projectid"]},{"domain":1,"name":1,"releases":1,"_id":0})
                    release_name = prjobj["releases"][0]["name"]
                    cycle_name = prjobj["releases"][0]["cycles"][0]["name"]
                    cycleid = tsuobj.get('cycleid', None)
                    if cycleid:
                        if cycleid not in cycleid_dict:
                            found = False
                            for rel in prjobj["releases"]:
                                for cyc in rel["cycles"]:
                                    if cyc["_id"] == cycleid:
                                        found = (rel["name"], cyc["name"])
                                        break
                                if found:
                                    cycleid_dict[cycleid] = found
                                    break
                        if cycleid in cycleid_dict:
                            release_name, cycle_name = cycleid_dict[cycleid]
                    query={
                        'report': reportobj["report"],
                        'testscenarioid': tscid,
                        'testscenarioname': tsc["name"],
                        'domainname': prjobj["domain"],
                        'projectname': prjobj["name"],
                        'reportid': reportobj["_id"],
                        'releasename': release_name,
                        'cyclename': cycle_name,
                        'moduleid': tsuobj.get("mindmapid", None),
                        'testsuitename': tsuobj.get("name", None)
                    }
                    finalQuery.append(query)
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
        return jsonify(res)

    @app.route('/reports/getAccessibilityTestingData_ICE',methods=['POST'])
    def getAccessibilityData_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata["query"])
            app.logger.debug("Inside getAccessibilityTestingData_ICE. Query: " + param)
            accessibility_reports = dbsession.accessibilityreports
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
                report = dbsession.reports.find(query,{"testscenarioid":1,"status":1,"report":1,"modifiedby":1})
                res['rows']=arr
                for i in report:
                    details = {}
                    scenarioid = i["testscenarioid"]
                    status = i["status"]
                    report = i["report"]["overallstatus"]
                    starttime = i["report"]["overallstatus"][0]["StartTime"].split(".")[0]
                    endtime = i["report"]["overallstatus"][0]["EndTime"].split(".")[0]
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
# END OF REPORTS
