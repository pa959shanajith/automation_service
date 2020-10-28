################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from bson.objectid import ObjectId
import json
from datetime import datetime
uniq = 10000

def generate_id():
    global uniq
    uniq += 1
    return uniq

def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

    # API to get the project type name using the ProjectID
    @app.route('/neurongraphs/getData',methods=['POST'])
    def getNeuronGraphsData():
        app.logger.debug("Inside getNeuronGraphsData")
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            domain_dict = {}
            ptype = {}
            nodes = []
            links = []
            counter = 0
            ptypeall = list(dbsession["projecttypekeywords"].find({}, {"_id":1,"name":1}))
            for e in ptypeall: ptype[e["_id"]] = e["name"]
            prj_data_needed = {"name":1,"releases.name":1,"releases._id":1,"releases.cycles.name":1,"releases.cycles._id":1,"domain":1,"type":1}
            project_id = dbsession["users"].find_one({"_id":ObjectId(requestdata['user_id'])}, {"_id":1,"projects":1})["projects"]
            dprc_list = list(dbsession["projects"].find({"_id":{"$in":project_id}}, prj_data_needed))
            #dprc_list = list(dbsession["projects"].find({}, prj_data_needed))
            cycle_ids=[]
            for p in dprc_list:
                if p["domain"] in domain_dict:
                    domain_id = domain_dict[p["domain"]]
                else:
                    domain_id = generate_id()
                    nodes.append({'id':str(domain_id),"idx":counter,'type':"Domain","name":p["domain"],"attributes":{"Name":p['domain']}})
                    counter+=1
                    domain_dict[p["domain"]] = domain_id
                nodes.append({'id':str(p["_id"]),"idx":counter,'type':"Project","name":p["name"],"attributes":{"Name":p['name'], "Type": ptype[p["type"]]}})
                links.append({"start":str(domain_id),"end":str(p["_id"])})
                counter+=1
                for r in p['releases']:
                    rel_id = generate_id()
                    nodes.append({'id':str(rel_id),"idx":counter,'type':"Release","name":r["name"],"attributes":{"Name":r['name']}})
                    links.append({"start":str(p["_id"]),"end":str(rel_id)})
                    counter+=1
                    for c in r['cycles']:
                        nodes.append({'id':str(c["_id"]),"idx":counter,'type':"Cycle","name":c["name"],"attributes":{"Name":c['name']}})
                        links.append({"start":str(rel_id),"end":str(c["_id"])})
                        cycle_ids.append(c["_id"])
                        counter+=1
            testsuite_data_needed = {"name":1,"testscenarioids":1,"mindmapid":1,"cycleid":1,"versionnumber":1,"conditioncheck":1,"getparampaths":1}
            testsuites=list(dbsession["testsuites"].find({"cycleid":{"$in":cycle_ids}}, testsuite_data_needed))
            # testsuites=list(dbsession["testsuites"].find({}, testsuite_data_needed))
            ts_list=[]
            for t in testsuites:
                #attributes = json.loads(json.dumps(t))
                attributes = t
                attributes["Name"] = attributes["name"]
                links.append({"start":str(t["cycleid"]),"end":str(t["_id"])})
                nodes.append({'id':str(t["_id"]),"idx":counter,'type':"TestSuite","name":t["name"],"attributes":attributes})
                for ts in t["testscenarioids"]:
                    links.append({"start":str(t["_id"]),"end":str(ts)})
                    ts_list.append(ts)
                counter+=1
                del attributes["_id"]
                del attributes["name"]
            testsuites=[]

            testscenarios=list(dbsession["testscenarios"].find({"_id":{"$in":ts_list}},{"name":1,"testcaseids":1,"testcases":1}))
            # testscenarios=list(dbsession["testscenarios"].find({},{"name":1,"testcaseids":1,"testcases":1}))
            testcases_list=[]
            for ts in testscenarios:
                attributes={
                    "Name": ts["name"]
                }
                nodes.append({'id':str(ts["_id"]),"idx":counter,'type':"TestScenario","name":ts["name"],"attributes":attributes})
                counter+=1
                key="testcaseids"
                if key not in ts:
                    key="testcases"
                for tc in ts[key]:
                    testcases_list.append(tc)
                    links.append({"start":str(ts["_id"]),"end":str(tc)})
            testscenarios=[]

            testcases=list(dbsession["testcases"].find({"_id":{"$in":testcases_list}},{"name":1,"screenid":1}))
            # testcases=list(dbsession["testcases"].find({},{"name":1,"screenid":1}))
            screen_list=[]
            for tc in testcases:
                attributes={
                    "Name": tc["name"],
                }
                screen_list.append(tc['screenid'])
                nodes.append({'id':tc["_id"],"idx":counter,'type':"TestCase","name":tc["name"],"attributes":attributes})
                links.append({"start":str(tc["_id"]),"end":str(tc['screenid'])})
                counter+=1
            testcases=[]

            screens=list(dbsession["screens"].find({"_id":{"$in":screen_list}},{"name":1}))
            for s in screens:
                attributes={
                    "Name": s["name"],
                }
                nodes.append({'id':s["_id"],"idx":counter,'type':"Screen","name":s["name"],"attributes":attributes})
                # links.append({"start":str(tc["_id"]),"end":str(tc['screenid'])})
                counter+=1
            screens=[]
            app.logger.debug("Executed getNeuronGraphsData")
            res={"nodes":nodes,"links":links}
        except Exception as e:
            servicesException("getNeuronGraphsData", e, True)
        return jsonify(res)
    #fetching the reports for NG
    @app.route('/neurongraphs/getReportNG',methods=['POST'])
    def getReportNG():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getReport. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                 if(requestdata["query"] == 'getReportNG'):
                    queryresult1 = list(dbsession.executions.find({"parent":ObjectId(requestdata["suiteId"])},{"_id":1,"status":1}))
                    # scenarioid = queryresult1['testscenarioid']
                    for execution in queryresult1:
                        #execution['reports'] = list(dbsession.reports.find({"executionid":queryresult1['_id']},{"_id":1}))
                        execution['reports'] = list(dbsession.reports.find({"executionid":ObjectId(execution['_id'])},{"_id":1}))
                        for reportid in execution['reports']:
                            reportid['jiraId'] = list(dbsession.thirdpartyintegration.find({"reportid":reportid["_id"],"type":"JIRA"},{"_id":0,"defectid":1}))
                    # queryresult1.update(queryresult2)
                    #queryresult3 = dbsession.projects.find_one({"_id":queryresult2['projectid']},{"domain":1,"_id":0})
                    # queryresult1.update(queryresult3)
                    # queryresult1['testscenarioid'] = scenarioid
                    # queryresult.append(queryresult1)
                    res= {"rows":queryresult1}
                    #app.logger.warn(res)
            else:
                app.logger.warn('Empty data received. report.')
        except Exception as getreportexc:
            servicesException("getReport_NG",getreportexc)
        return res

    #fetching the Execution status for NG
    @app.route('/neurongraphs/getReportExecutionStatus_NG',methods=['POST'])
    def getReportExecutionStatusNG():
        app.logger.debug("Inside getReportExecutionStatus_NG")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                queryresult = list(dbsession.executions.find({"parent":ObjectId(requestdata["suiteID"])}))
                res= {"rows":queryresult}
            else:
                app.logger.warn('Empty data received. report suites details execution.')
        except Exception as getsuitedetailsexc:
            servicesException("getReportExecutionStatus_NG",getsuitedetailsexc)
        return jsonify(res)


