################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *

def LoadServices(app, redissession, n68session):
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
                    queryresult1=n68session.users.find_one({"_id": ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
                    queryresult=list(n68session.projects.find({"_id":{"$in":queryresult1["projects"]}},{"name":1,"releases":1}))
                    res= {"rows":queryresult}
                elif(requestdata["query"] == 'getAlltestSuites'):
                    queryresult=list(n68session.testsuites.find({"cycleid": ObjectId(requestdata["id"])},{"_id":1,"name":1}))
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
                queryresult=list(n68session.executions.find({"parent":ObjectId(requestdata["suiteid"])},{"_id":1,"starttime":1,"endtime":1,"status":1}))
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
                    queryresult = list(n68session.reports.find({"executionid":ObjectId(requestdata["executionid"])},{"_id":1,"executionid":1,"executedon":1,"comments":1,"executedtime":1,"modifiedby":1,"modifiedbyrole":1,"modifiedon":1,"status":1,"testscenarioid":1}))
                    res= {"rows":queryresult}
                elif(requestdata["query"] == 'scenarioname'):
                    queryresult = list(n68session.testscenarios.find({"_id":ObjectId(requestdata["scenarioid"])},{"name":1}))
                    res= {"rows":queryresult}
            else:
                app.logger.warn('Empty data received. report status of scenarios.')
        except Exception as getreportstatusexc:
            servicesException("reportStatusScenarios_ICE",getreportstatusexc)
        return jsonify(res)


    #fetching the reports
    @app.route('/reports/getReport_Nineteen68',methods=['POST'])
    def getReport_Nineteen68():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getReport_Nineteen68. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'projectsUnderDomain'):
                    queryresult1 = n68session.reports.find_one({"_id":ObjectId(requestdata["reportid"])},{"executedtime":1,"report":1,"testscenarioid":1})
                    # scenarioid = queryresult1['testscenarioid']
                    queryresult2 = n68session.testscenarios.find_one({"_id":queryresult1['testscenarioid']},{"name":1,"projectid":1,"_id":0})
                    # queryresult1.update(queryresult2)
                    queryresult3 = n68session.projects.find_one({"_id":queryresult2['projectid']},{"domain":1,"_id":0})
                    # queryresult1.update(queryresult3)
                    # queryresult1['testscenarioid'] = scenarioid
                    # queryresult.append(queryresult1)
                    query={
                        'report': queryresult1["report"],
                        'executedtime': queryresult1["executedtime"],
                        'testscenarioid': queryresult1["testscenarioid"],
                        'name': queryresult2["name"],
                        'projectid': queryresult2["projectid"],
                        'domain': queryresult3["domain"]
                        }
                    res= {"rows":query}
            else:
                app.logger.warn('Empty data received. report.')
        except Exception as getreportexc:
            servicesException("getReport_Nineteen68",getreportexc)
        return res


    #update jira defect id in report data
    @app.route('/reports/updateReportData',methods=['POST'])
    def updateReportData():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateReportData.")
            if not isemptyrequest(requestdata):
                queryresult = n68session.reports.find({"_id":ObjectId(requestdata["reportid"])},{"report":1})
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
                    queryresult = n68session.reports.update({"_id":ObjectId(requestdata["reportid"])},{"$set":{"report":report}})
                    res={'rows':'Success'}
        except Exception as updatereportdataexc:
            app.logger.debug(updatereportdataexc)
            servicesException("updateReportData",updatereportdataexc)
        return jsonify(res)
        
    #fetching the report by executionId
    @app.route('/reports/get_Nineteen68Report',methods=['POST'])
    def get_Nineteen68Report():
        res={'rows':'fail'}
        finalQuery=[]
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside get_Nineteen68Report. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'get_Nineteen68Report'):
                    if("scenarioIds" in requestdata):
                        queryresult1 = n68session.reports.find({"executionid":ObjectId(requestdata["executionId"]),"testscenarioid":{"$in":[ObjectId(i) for i in requestdata["scenarioIds"]]}})
                    else:
                        queryresult1 = n68session.reports.find({"executionid":ObjectId(requestdata["executionId"])})
                    queryresult4 = n68session.executions.find_one({"_id": ObjectId(requestdata["executionId"])})
                    parent = queryresult4["parent"]
                    for execData in queryresult1:
                        queryresult2 = n68session.testscenarios.find_one({"_id":execData["testscenarioid"]})#,{"name":1,"projectid":1,"_id":0})
                        queryresult3 = n68session.projects.find_one({"_id":queryresult2["projectid"]})#,{"domain":1,"_id":0})
                        for obj in parent:
                            app.logger.debug("N68 OBJ IS"+str(obj))
                            queryresult5 = n68session.testsuites.find_one({"_id":obj})
                            if execData["testscenarioid"] in queryresult5["testscenarioids"]:
                                queryresult6 = n68session.mindmaps.find_one({"_id":queryresult5["mindmapid"]})
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
                            'moduleId': queryresult6["_id"],
                            'moduleName': queryresult6["name"]
                        }
                        finalQuery.append(query)
                    res["rows"] = finalQuery
            else:
                app.logger.warn('Empty data received. report.')
        except Exception as getreportexc:
            servicesException("get_Nineteen68Report", getreportexc, True)
        return jsonify(res)

# END OF REPORTS
