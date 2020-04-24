#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      shree.p
#
# Created:     09/10/2019
# Copyright:   (c) shree.p 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------


################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS
################################################################################
#----------DEFAULT METHODS AND IMPORTS-------------------------------
from utils import *
from datetime import datetime, timedelta
import pytz
import time
import uuid

query = {'delete_flag': False}

def LoadServices(app, redissession, n68session):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

    @app.route('/suite/readTestSuite_ICE',methods=['POST'])
    def readTestSuite_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata["query"])
            if not isemptyrequest(requestdata):
                app.logger.info("Inside readTestSuite_ICE. Query: " + param)
                if(param == 'gettestsuite'):
                    mindmapid = ObjectId(requestdata['mindmapid'])
                    cycleid = ObjectId(requestdata['cycleid'])
                    filterquery = {"conditioncheck":1,"getparampaths":1,"donotexecute":1,"testscenarioids":1}
                    testsuite = n68session.testsuites.find_one({"mindmapid":mindmapid, "cycleid":cycleid, "deleted":query['delete_flag']}, filterquery)
                    create_suite = testsuite is None
                    mindmaps = n68session.mindmaps.find_one({"_id": mindmapid, "deleted":query['delete_flag']})
                    testscenarioids = [i["_id"] for i in mindmaps["testscenarios"]]
                    tsclen = len(testscenarioids)
                    createdby = ObjectId(requestdata['createdby'])
                    createdbyrole = ObjectId(requestdata['createdbyrole'])
                    #createdbyrole = n68session.users.find_one({"_id":createdby},{"defaultrole":1})["defaultrole"]
                    querydata = {}
                    querydata["name"] = mindmaps["name"]
                    querydata["modifiedby"] = createdby
                    querydata["modifiedbyrole"] = createdbyrole
                    querydata["modifiedon"] = datetime.now()
                    querydata["testscenarioids"] = testscenarioids

                    if create_suite:
                        querydata["mindmapid"] = mindmaps["_id"]
                        querydata["cycleid"] = cycleid
                        querydata["versionnumber"] = mindmaps["versionnumber"]
                        querydata["conditioncheck"] = [0] * tsclen
                        querydata["createdby"] = querydata["modifiedby"]
                        querydata["createdbyrole"] = querydata["modifiedbyrole"]
                        querydata["createdon"] = querydata["modifiedon"]
                        querydata["deleted"] = mindmaps["deleted"]
                        querydata["donotexecute"] = [1] * tsclen
                        querydata["getparampaths"] = [' '] * tsclen
                        testsuiteid = n68session.testsuites.insert(querydata)
                    else:
                        testsuiteid = testsuite["_id"]
                        testscenariods_ts = testsuite["testscenarioids"]
                        getparampaths_ts = testsuite["getparampaths"]
                        donotexecute_ts = testsuite["donotexecute"]
                        conditioncheck_ts = testsuite["conditioncheck"]
                        getparampaths = []
                        conditioncheck = []
                        donotexecute = []
                        for i in range(tsclen):
                            index = -1
                            if testscenarioids[i] in testscenariods_ts:
                                index = testscenariods_ts.index(testscenarioids[i])
                            if index != -1:
                                if (getparampaths_ts[index].strip() == ''): getparampaths.append(' ')
                                else: getparampaths.append(getparampaths_ts[index])
                                if conditioncheck_ts is not None: conditioncheck.append(conditioncheck_ts[index])
                                if donotexecute_ts is not None: donotexecute.append(donotexecute_ts[index])
                                testscenariods_ts[index] = -1 # Visited this scenario once already
                            else:
                                getparampaths.append(' ')
                                conditioncheck.append(0)
                                donotexecute.append(1)
                        querydata["conditioncheck"] = conditioncheck
                        querydata["donotexecute"] = donotexecute
                        querydata["getparampaths"] = getparampaths
                        n68session.testsuites.update_one({"_id": testsuiteid, "deleted": query['delete_flag']}, {'$set': querydata})

                    res['rows'] = {
                        "testsuiteid": testsuiteid, "conditioncheck": querydata["conditioncheck"],
                        "donotexecute": querydata["donotexecute"], "getparampaths": querydata["getparampaths"],
                        "testscenarioids": testscenarioids, "name": querydata["name"]
                    }

                elif(param == 'gettestscenario'):
                    testscenarioids = [ObjectId(i) for i in requestdata["testscenarioids"]]
                    projects = n68session.projects.find({}, {"name": 1})
                    prj_map = {}
                    for prj in projects:
                        prj_map[prj["_id"]] = prj["name"]
                    testscenarios = n68session.testscenarios.find({"_id": {"$in": testscenarioids}, "deleted":query['delete_flag']}, {"name": 1, "projectid": 1})
                    tsc_map = {}
                    for tsc in testscenarios:
                        tsc_map[tsc["_id"]] = [tsc["name"], prj_map[tsc["projectid"]]]
                    testscenarionames = []
                    projectnames = []
                    for tsc in testscenarioids:
                        if tsc in tsc_map:
                            testscenarionames.append(tsc_map[tsc][0])
                            projectnames.append(tsc_map[tsc][1])
                        else:
                            testscenarionames.append('N/A')
                            projectnames.append('N/A')
                    res['rows'] = {"testscenarionames": testscenarionames, "projectnames": projectnames}
                app.logger.info("Executed readTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. read testsuite.')
        except Exception as e:
            servicesException("readTestSuite_ICE", e, True)
        return jsonify(res)

    @app.route('/suite/updateTestSuite_ICE',methods=['POST'])
    def updateTestSuite_ICE():
        res={'rows':'fail'}
        querydata = {}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata["query"])
            app.logger.debug("Inside updateTestSuite_ICE. Query: " + param)
            if not isemptyrequest(requestdata):
                testsuiteid = ObjectId(requestdata['testsuiteid'])
                querydata = requestdata
                del querydata["testsuiteid"]
                del querydata["query"]
                querydata["modifiedon"]= datetime.now()
                querydata["testscenarioids"] = [ObjectId(i) for i in requestdata['testscenarioids']]
                n68session.testsuites.update_one({"_id": testsuiteid}, {"$set":querydata})
                res={'rows':'Success'}
                app.logger.debug("Executed updateTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. update testsuite.')
        except Exception as updatetestsuiteexc:
            servicesException("updateTestSuite_ICE", updatetestsuiteexc, True)
        return jsonify(res)

    @app.route('/suite/ExecuteTestSuite_ICE',methods=['POST'])
    def ExecuteTestSuite_ICE() :
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            param = str(requestdata["query"])
            app.logger.debug("Inside ExecuteTestSuite_ICE. Query: " + param)
            if not isemptyrequest(requestdata):
                if param == 'testcasedetails':
                    tsc = n68session.testscenarios.find_one({"_id": ObjectId(requestdata['id']),"deleted":query['delete_flag']},{"testcaseids":1})
                    if tsc is not None:
                        testcases = list(n68session.testcases.find({"_id": {"$in": tsc["testcaseids"]},"deleted":query['delete_flag']},{"name":1,"versionnumber":1,"screenid":1}))
                        res["rows"] = testcases
                    if 'userid' in requestdata:    # Update the Counter
                        userid = ObjectId(requestdata['userid'])
                        global scenarioscounter
                        scenarioscounter = scenarioscounter + 1
                        counterupdator(n68session, 'testscenarios', userid, scenarioscounter)

                elif param == 'insertintoexecution':
                    starttime = datetime.now()
                    batchid = ObjectId() if requestdata["batchid"] == "generate" else ObjectId(requestdata["batchid"])
                    tsuids = requestdata['testsuiteids']
                    execids = requestdata['executionids']
                    for tsuid in tsuids:
                        if execids[tsuid] is None:
                            insertquery = {"batchid": batchid, "parent": [ObjectId(tsuid)],
                                "configuration": {}, "executedby": ObjectId(requestdata['executedby']),
                                "status": "inprogress", "endtime": None, "starttime": starttime}
                            execid = str(n68session.executions.insert(insertquery))
                            execids[tsuid] = execid
                    res["rows"] = {"batchid": str(batchid), "execids": execids}
                elif param  == 'updateintoexecution':
                    endtime = datetime.now()
                    for exec_id in requestdata['executionids']:
                        n68session.executions.update({"_id":ObjectId(exec_id)}, {'$set': {"status":requestdata['status'],"endtime":endtime}})
                    res["rows"] = True

                elif param == 'insertreportquery':
                    modifiedon = datetime.now()
                    querydata = {
                        "executionid": ObjectId(requestdata['executionid']),
                        "testscenarioid": ObjectId(requestdata['testscenarioid']),
                        "status": requestdata['status'],
                        "executedtime": modifiedon,
                        "executedon": requestdata['browser'],
                        "modifiedon": modifiedon,
                        "modifiedby": ObjectId(requestdata['modifiedby']),
                        "modifiedbyrole": ObjectId(requestdata['modifiedbyrole']),
                        "report": json.loads(requestdata['report'])
                    }
                    res["rows"] = str(n68session.reports.insert(querydata))

                app.logger.debug("Executed ExecuteTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. execute testsuite.')
        except Exception as execuitetestsuiteexc:
            servicesException("ExecuteTestSuite_ICE", execuitetestsuiteexc, True)
        return jsonify(res)

    @app.route('/suite/ScheduleTestSuite_ICE',methods=['POST'])
    def ScheduleTestSuite_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata['query'])
            app.logger.debug("Inside ScheduleTestSuite_ICE. Query: " + param)
            if not isemptyrequest(requestdata):
                if(param == 'insertscheduledata'):
                    for tscos in requestdata["scenarios"]:
                        for tsco in tscos: tsco["scenarioId"] = ObjectId(tsco["scenarioId"])
                    dataquery = {
                        "scheduledon": datetime.fromtimestamp(int(requestdata['timestamp'])/1000,pytz.UTC),
                        "executeon": requestdata["executeon"],
                        "executemode": requestdata["executemode"],
                        "target": requestdata["targetaddress"],
                        "scenariodetails": requestdata["scenarios"],
                        "status": "scheduled",
                        "testsuiteids": [ObjectId(i) for i in requestdata['testsuiteIds']],
                        "scheduledby": ObjectId(requestdata['userid'])
                    }
                    if "smartid" in requestdata: dataquery["smartid"] = uuid.UUID(requestdata["smartid"])
                    scheduleid = n68session.scheduledexecutions.insert(dataquery)
                    res["rows"] = {"id": scheduleid}

                elif(param == 'updatescheduledstatus'):
                    updatequery = { "status": requestdata["schedulestatus"] }
                    if "batchid" in requestdata: updatequery["batchid"] = ObjectId(requestdata["batchid"])
                    n68session.scheduledexecutions.update({"_id":ObjectId(requestdata['scheduleid'])},{"$set": updatequery})
                    res["rows"] = "success"

                elif(param == 'getscheduledata'):
                    findquery = {}
                    if "status" in requestdata: findquery["status"] = requestdata["status"]
                    if "scheduleid" in requestdata: findquery["_id"] = ObjectId(requestdata["scheduleid"])
                    res["rows"] = list(n68session.scheduledexecutions.find(findquery))

                elif(param == 'getallscheduledata'):
                    prjtypes = n68session.projecttypekeywords.find({}, {"name": 1})
                    ptmap = {}
                    for pt in prjtypes: ptmap[pt["_id"]] = pt["name"]
                    projects = n68session.projects.find({}, {"type": 1})
                    prjmap = {}
                    for prj in projects: prjmap[prj["_id"]] = ptmap[prj["type"]]
                    tsuites = n68session.testsuites.find({}, {"name": 1})
                    tsumap = {}
                    for tsu in tsuites: tsumap[tsu["_id"]] = tsu["name"]
                    tscos = n68session.testscenarios.find({}, {"projectid": 1})
                    tscomap = {}
                    for tsco in tscos: tscomap[tsco["_id"]] = prjmap[tsco["projectid"]] if tsco["projectid"] in prjmap else "-"
                    schedules = list(n68session.scheduledexecutions.find({}))
                    for sch in schedules:
                        sch["testsuitenames"] = [tsumap[tsuid] for tsuid in sch["testsuiteids"]]
                        for tscos in sch["scenariodetails"]:
                            if type(tscos) == dict: break
                            for tsco in tscos: tsco["appType"] = tscomap[tsco["scenarioId"]]
                    res["rows"] = schedules

                elif(param == 'gettestsuiteproject'):
                    testsuiteids = [ObjectId(i) for i in requestdata["testsuiteids"]]
                    testsuites = list(n68session.testsuites.find({"_id": { "$in": testsuiteids}},
                        {"name": 1, "cycleid": 1, "versionnumber": 1}))
                    testsuitemap = {}
                    for tsu in testsuites: testsuitemap[str(tsu["_id"])] = tsu
                    cycleid = ObjectId(testsuites[0]["cycleid"])
                    project = n68session.projects.find_one({"releases.cycles._id": cycleid}, {"name": 1, "domain": 1, "releases": 1, "type": 1})
                    for rel in project["releases"]:
                        for cyc in rel["cycles"]:
                            if cyc["_id"] == cycleid:
                                project["releaseid"] = rel["name"]
                                project["cycleid"] = cycleid
                                project["cyclename"] = cyc["name"]
                                cycleid = None
                                break
                        if cycleid is None: break
                    del project["releases"]
                    project["type"] = n68session.projecttypekeywords.find_one({"_id": project["type"]}, {"name": 1})["name"]
                    res["rows"] = { "suitemap": testsuitemap, "project": project }

                elif(param == 'checkscheduleddetails'):
                    timelist = requestdata["scheduledatetime"]
                    flag = -1
                    for i in range(len(timelist)):
                        timestamp =  datetime.strptime(timelist[i], "%d-%m-%Y %H:%M")
                        address = requestdata["targetaddress"][i]
                        count = n68session.scheduledexecutions.find({"scheduledon": timestamp, "target": address}).count()
                        if count > 0:
                            flag = i
                            break
                    res["rows"] = flag
                app.logger.debug("Executed ScheduleTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. schedule testsuite.')
        except Exception as scheduletestsuiteexc:
            servicesException("ScheduleTestSuite_ICE", scheduletestsuiteexc, True)
        return jsonify(res)

    @app.route('/suite/getTestcaseDetailsForScenario_ICE',methods=['POST'])
    def getTestcaseDetailsForScenario_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getTestcaseDetailsForScenario_ICE")
            if not isemptyrequest(requestdata):
                screenids = [ObjectId(i) for i in requestdata['screenids']]
                screens = list(n68session.screens.find({"_id": {"$in": screenids},
                    "deleted":query['delete_flag']},{"name":1,"projectid":1}))
                prjset = set()
                screenmap = {}
                prjmap = {}
                for scr in screens:
                    screenmap[scr["_id"]] = scr
                    prjset.add(scr["projectid"])
                projects = list(n68session.projects.find({"_id": {"$in": list(prjset)}},{"name":1}))
                for prj in projects: prjmap[prj["_id"]] = prj
                screennames = []
                projectnames = []
                projectids = []
                for scrid in screenids:
                    if scrid in screenmap:
                        scr = screenmap[scrid]
                        screennames.append(scr["name"])
                        projectids.append(scr["projectid"])
                        projectnames.append(prjmap[scr["projectid"]]["name"])
                    else:
                        screennames.append("")
                        projectnames.append("")
                        projectids.append("")
                res["rows"] = {"screennames": screennames, "projectnames": projectnames, "projectids": projectids}
                app.logger.debug("Executed getTestcaseDetailsForScenario_ICE")
            else:
                app.logger.warn('Empty data received. getting testcases from scenarios.')
        except Exception as userrolesexc:
            servicesException("getTestcaseDetailsForScenario_ICE", userrolesexc, True)
        return jsonify(res)

    @app.route('/suite/checkApproval',methods=['POST'])
    def checkApproval():
        app.logger.debug("Inside checkApproval")
        res={'rows':'fail'}
        flag=False
        try:
            requestdata=json.loads(request.data)
            scenario_ids=[]
            screenid=[]
            testcaseid=[]
            screens=[]
            counter=0
            for i in requestdata["scenario_ids"]:
                scenario_ids.append(ObjectId(i))
            testcaseids=list(n68session.testscenarios.find({"_id":{"$in":scenario_ids}},{"testcaseids":1}))
            for i in testcaseids:
                for j in i["testcaseids"]:
                    testcaseid.append(j)
            testcases=list(n68session.testcases.find({"_id":{"$in":testcaseid}},{"screenid":1,"_id":1,"modifiedon":1}))
            for i in testcases:
                screenid.append(i["screenid"])
                screens.append(n68session.screens.find_one({"_id":i["screenid"]},{"modifiedon":1}))
            for i in testcaseid:
                query=list(n68session.tasks.find({"nodeid":i},{"history":1}).sort("createdon",-1).limit(1))
                if(len(query[0]["history"])>0):
                    date=query[0]["history"][-1]["modifiedOn"]
                    if isinstance(date,str) and query[0]["history"][-1]["status"] == "complete" and testcases[counter]['modifiedon']>=datetime.strptime(date,"%d/%m/%Y,%H:%M:%S"):
                        flag=True
                        res={'rows':"Modified"}
                        return jsonify(res)
                    elif isinstance(date,datetime) and query[0]["history"][-1]["status"] == "complete" and testcases[counter]['modifiedon']>=date:
                        flag=True
                        res={'rows':"Modified"}
                        return jsonify(res)
                else:
                    res={'rows':1}
                    return jsonify(res)
                if (query==None):
                    flag=True
                    res={'rows':"No Task"}
                    return jsonify(res)
                counter+=1
            counter=0
            for i in screenid:
                query=list(n68session.tasks.find({"nodeid":i},{"history":1}).sort("createdon",-1).limit(1))
                if(len(query[0]["history"])>0):
                    date=query[0]["history"][-1]["modifiedOn"]
                    if isinstance(date,str) and query[0]["history"][-1]["status"] == "complete" and screens[counter]['modifiedon']>=datetime.strptime(date,"%d/%m/%Y,%H:%M:%S"):
                        flag=True
                        res={'rows':"Modified"}
                        return jsonify(res)
                    elif isinstance(date,datetime) and query[0]["history"][-1]["status"] == "complete" and screens[counter]['modifiedon']>=date:
                        flag=True
                        res={'rows':"Modified"}
                        return jsonify(res)
                else:
                    res={'rows':1}
                    return jsonify(res)
                date=query[0]["history"][0]["modifiedOn"]
                if (query==None):
                    flag=True
                    res={'rows':"No Task"}
                    return jsonify(res)
                counter+=1
            if flag==False:
                tasks=list(n68session.tasks.find({"nodeid":{"$in":testcaseid},"status":{"$ne":"complete"}},{"status":1}))
                tasks1=list(n68session.tasks.find({"nodeid":{"$in":screenid},"status":{"$ne":"complete"}},{"status":1}))
                res={'rows':len(tasks)+len(tasks1)}
            return jsonify(res)
        except Exception as getalltaskssexc:
            servicesException("checkApproval",getalltaskssexc, True)
            return jsonify(res)

