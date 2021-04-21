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
                    queryresult=list(dbsession.testsuites.find({"cycleid": ObjectId(requestdata["id"])},{"_id":1,"name":1}))
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
                queryresult=list(dbsession.executions.find({"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1}))
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
                    res= {"rows":queryresult}
                elif(requestdata["query"] == 'scenarioname'):
                    queryresult = list(dbsession.testscenarios.find({"_id":ObjectId(requestdata["scenarioid"])},{"name":1}))
                    res= {"rows":queryresult}
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
                reportobj = dbsession.reports.find_one({"_id":ObjectId(requestdata["reportid"])},{"executedtime":1,"report":1,"testscenarioid":1,"executionid":1})
                if reportobj is None:
                    res['rows'] = []
                    return res
                scenarioname = dbsession.testscenarios.find_one({"_id":reportobj['testscenarioid']},{"name":1,"_id":0})["name"]
                suiteid = dbsession.executions.find_one({"_id":reportobj['executionid']},{"parent":1,"_id":0})["parent"][0]
                suiteobj = dbsession.testsuites.find_one({"_id":suiteid},{"name":1,"cycleid":1,"_id":0})
                cycleid = suiteobj['cycleid']
                prjobj = dbsession.projects.find_one({"releases.cycles._id":cycleid},{"domain":1,"name":1,"releases":1})
                query = {
                    'report': reportobj["report"],
                    'executionid': reportobj['executionid'],
                    'executedtime': reportobj["executedtime"],
                    'testscenarioid': reportobj["testscenarioid"],
                    'testscenarioname': scenarioname,
                    'testsuitename': suiteobj["name"],
                    'projectid': prjobj["_id"],
                    'domainname': prjobj["domain"],
                    'projectname': prjobj["name"]
                }
                found = False
                for rel in prjobj["releases"]:
                    for cyc in rel["cycles"]:
                        if cyc["_id"] == cycleid:
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
        return res


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
            if not isemptyrequest(requestdata):
                errMsgVal=str(requestdata["executionId"])
                queryresult1 = dbsession.reports.find({"executionid":ObjectId(requestdata["executionId"])})
                queryresult4 = dbsession.executions.find_one({"_id": ObjectId(requestdata["executionId"])})
                parent = queryresult4["parent"]
                errMsgVal=''
                if("scenarioIds" in requestdata):
                    scenarioIds = dbsession.reports.distinct("testscenarioid",{"executionid":ObjectId(requestdata["executionId"])})
                    for scenId in requestdata["scenarioIds"]:
                        if len(scenId.strip())==0:
                            continue
                        try:
                            if ObjectId(scenId) not in scenarioIds:
                                errIds.append(str(scenId))
                            else:
                                correctScenarios.append(ObjectId(scenId))
                        except Exception:
                            errIds.append(str(scenId))
                    if len(correctScenarios) != 0 or len(errIds) != 0:
                        queryresult1 = dbsession.reports.find({"executionid":ObjectId(requestdata["executionId"]),"testscenarioid":{"$in":correctScenarios}})
                for execData in queryresult1:
                    queryresult2 = dbsession.testscenarios.find_one({"_id":execData["testscenarioid"]})#,{"name":1,"projectid":1,"_id":0})
                    queryresult3 = dbsession.projects.find_one({"_id":queryresult2["projectid"]})#,{"domain":1,"_id":0})
                    for obj in parent:
                        queryresult5 = dbsession.testsuites.find_one({"_id":obj})
                        if execData["testscenarioid"] in queryresult5["testscenarioids"]:
                            #queryresult6 = dbsession.mindmaps.find_one({"_id":queryresult5["mindmapid"]})
                            break
                    query={
                        'report': execData["report"],
                        'scenariodId': queryresult2["_id"],
                        'scenarioName': queryresult2["name"],
                        'domainName': queryresult3["domain"],
                        'projectName': queryresult3["name"],
                        'reportId': execData["_id"],
                        'releaseName': queryresult3["releases"][0]["name"],
                        'cycleName': queryresult3["releases"][0]["cycles"][0]["name"],
                        'moduleId': queryresult5["mindmapid"],
                        'moduleName': queryresult5["name"]
                    }
                    finalQuery.append(query)
                res["rows"] = finalQuery
                if len(errIds) != 0:
                    res["errMsg"] = errMsg+'Scenario Id(s): '+(','.join(errIds))
            else:
                app.logger.warn('Empty data received. report.')
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
                    start=datetime.strptime(start,'%Y-%m-%d')
                    end=datetime.strptime(end,'%Y-%m-%d')
                    end += timedelta(days=1)
                    query={'executedtime':{"$gte": start, "$lte": end}}
                if 'executionid' in requestdata:
                    query['executionid']=ObjectId(requestdata['executionid'])
                if 'modifiedby' in requestdata:
                    query['modifiedby']=ObjectId(requestdata['modifiedby'])
                if 'status' in requestdata and requestdata['status'].lower() in status_dict:
                    query['status']=status_dict[requestdata['status'].strip().lower()]
                LOB=requestdata["LOB"]
                report = dbsession.reports.find(query,{"testscenarioid":1,"status":1,"report":1,"modifiedby":1})
                res['rows']=arr
                for i in report:
                    details = {}
                    scenarioid = i["testscenarioid"]
                    status = i["status"]
                    report = i["report"]["overallstatus"]
                    starttime = i["report"]["overallstatus"][0]["StartTime"]
                    endtime = i["report"]["overallstatus"][0]["EndTime"]
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
