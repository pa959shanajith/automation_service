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
                if(param == 'testsuitecheck'):
                    res["rows"]=list(n68session.testsuites.find({"mindmapid":ObjectId(requestdata["mindmapid"]),
                        "cycleid":ObjectId(requestdata["cycleid"]),"deleted":query['delete_flag']}))

                elif(param == 'testcasesteps'):
                    getparampaths=[]
                    conditioncheck = []
                    donotexecute = []
                    #history=createHistory("create","testsuites",requestdata)
                    createdon = datetime.now()
                    mindmaps = n68session.mindmaps.find_one({"_id":ObjectId(requestdata["mindmapid"])})
                    tsidlen = len([i["_id"] for i in mindmaps["testscenarios"]])
                    for i in range(0,tsidlen):
                        getparampaths.append(' ')
                        conditioncheck.append(0)
                        donotexecute.append(1)
                    querydata = {}
                    querydata["mindmapid"] = ObjectId(requestdata['mindmapid'])
                    querydata["cycleid"] = ObjectId(requestdata['cycleid'])
                    querydata["name"] = requestdata['name']
                    querydata["versionnumber"] = mindmaps['versionnumber']
                    querydata["createdby"] = ObjectId(requestdata['createdby'])
                    querydata["createdbyrole"] = ObjectId(requestdata['createdby'])
                    querydata["createdon"] = createdon
                    querydata["donotexecute"] = donotexecute
                    querydata["getparampaths"] = getparampaths
                    querydata["conditioncheck"] = conditioncheck
                    querydata["modifiedby"] = ObjectId(requestdata['createdby'])
                    querydata["modifiedbyrole"] = ObjectId(requestdata['createdby'])
                    querydata["modifiedon"] = createdon
                    querydata["deleted"] = requestdata['deleted']
                    querydata["testscenarioids"] = [i["_id"] for i in mindmaps["testscenarios"]]
                    if requestdata['name']=='testsuitename':
                        querydata['name'] = mindmaps['name']

                    res["rows"] = str(n68session.testsuites.insert(querydata))

                elif(param == 'updatescenarioinnsuite'):
                    testsuites = n68session.testsuites.find_one({"mindmapid":ObjectId(requestdata["mindmapid"])
                    ,"cycleid":ObjectId(requestdata["cycleid"])})
                    mindmaps = n68session.mindmaps.find_one({"_id":ObjectId(requestdata["mindmapid"])})
                    getparampaths1 = []
                    conditioncheck1 = []
                    donotexecute1 = []

                    testscenariodslist_new = [i["_id"] for i in mindmaps["testscenarios"]]
                    versionnumber = mindmaps["versionnumber"]
                    testscenariodslist = testsuites["testscenarioids"]
                    getparampaths = testsuites["getparampaths"]
                    donotexecute = testsuites["donotexecute"]
                    conditioncheck = testsuites["conditioncheck"]
                    for i in range(0,len(testscenariodslist_new)):
                        if testscenariodslist_new[i] in testscenariodslist:
                            index = testscenariodslist.index(testscenariodslist_new[i])
                            if index != -1 and i < len(testscenariodslist_new):
                                if (getparampaths[index] == '' or getparampaths[index] == ' '):
                                    getparampaths1.append(' ')
                                else:
                                    getparampaths1.append(getparampaths[index])

                                if conditioncheck!= None:
                                    conditioncheck1.append(conditioncheck[index])

                                if donotexecute != None:
                                    donotexecute1.append(donotexecute[index])
                                #fix for repeating scenario case
                                testscenariodslist[index]=-1

                            else:
                                getparampaths1.append(' ')
                                conditioncheck1.append(0)
                                donotexecute1.append(1)
                        else:
                                getparampaths1.append(' ')
                                conditioncheck1.append(0)
                                donotexecute1.append(1)

                    #modifiedon = datetime.now()
                    querydata ={}
                    querydata["conditioncheck"] = conditioncheck1
                    querydata["donotexecute"] = donotexecute1
                    querydata["getparampaths"] = getparampaths1
                    querydata["testscenarioids"] = [ObjectId(i) for i in testscenariodslist_new]
                    querydata["modifiedby"] = ObjectId(requestdata["modifiedby"])
                    querydata["modifiedbyrole"] = ObjectId(requestdata["modifiedbyrole"])
                    querydata["modifiedon"] = datetime.now()
                    querydata["name"] = mindmaps["name"]

                    #if requestdata['name']=='testsuitename':
                    #querydata['name'] = n68session.mindmaps.find_one({"_id":ObjectId(requestdata["mindmapid"])},{"name":1,"_id":0})['name']
                    n68session.testsuites.update_one({"mindmapid":ObjectId(requestdata["mindmapid"]), "cycleid":ObjectId(requestdata["cycleid"]),
                        "deleted":query['delete_flag'],"versionnumber":versionnumber},{'$set':querydata})
                    res={'rows':'Success'}

                elif(param == 'testcasename'):
                    res["rows"] = list(n68session.testscenarios.find({"_id":ObjectId(requestdata["id"]),"deleted":query['delete_flag']},
                    {"name":1,"projectid":1}))

                elif(param == 'projectname'):
                    res["rows"] = list(n68session.projects.find({"_id":ObjectId(requestdata["id"])}, {"name":1}))

                elif(param == 'readTestSuite_ICE'):
                    querydata ={}
                    querydata["conditioncheck"] = 1
                    querydata["donotexecute"] = 1
                    querydata["getparampaths"] = 1
                    querydata["testscenarioids"] = 1
                    querydata["name"] = 1
                    querydata['_id'] = 0
                    if requestdata['testsuitename']=='testsuitename':
                        requestdata['testsuitename'] = n68session.mindmaps.find_one({"_id":ObjectId(requestdata["mindmapid"])},{"name":1,"_id":0})['name']
                    res['rows'] = list(n68session.testsuites.find({"mindmapid":ObjectId(requestdata["mindmapid"]),"name":requestdata["testsuitename"],
                    "cycleid":ObjectId(requestdata["cycleid"]),"deleted":query['delete_flag'],"versionnumber":float(requestdata["versionnumber"])},querydata))

                elif(param == 'gettestsuite'):
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
            else:
                app.logger.warn('Empty data received. update testsuite.')
            app.logger.debug("Executed updateTestSuite_ICE. Query: " + param)
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
                app.logger.debug("Executed ExecuteTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. execute testsuite.')
                return jsonify(res)
        except Exception as execuitetestsuiteexc:
            servicesException("ExecuteTestSuite_ICE", execuitetestsuiteexc, True)
        return jsonify(res)

    @app.route('/suite/ExecuteTestSuite_ICE1',methods=['POST'])
    def ExecuteTestSuite_ICE1() :
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata['query'] == 'testcaseid'):
                    res["rows"] = list(n68session.testscenarios.find({"_id":ObjectId(requestdata['id']),"deleted":query['delete_flag']},{"testcaseids":1}))
                    userid=ObjectId(requestdata['userid']) if 'userid' in requestdata else ""
                    global scenarioscounter
                    scenarioscounter = scenarioscounter + 1
                    counterupdator(n68session,'testscenarios',userid,scenarioscounter)
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'testcasesteps'):
                    res["rows"] = list(n68session.testcases.find({"_id":ObjectId(requestdata['id']),"deleted":query['delete_flag']},{"screenid":1,'versionnumber':1,'name':1}))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'getscreendataquery'):
                    res["rows"] = list(n68session.dataobjects.find({"parent":ObjectId(requestdata['id']),"deleted":query['delete_flag']}))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'testcasestepsquery'):
                    res["rows"] =list( n68session.testcases.find({"_id":ObjectId(requestdata['id']),"deleted":query['delete_flag']},{"steps":1,"name":1}))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'insertreportquery'):
                    modifiedon = datetime.now()
                    querydata = {}
                    querydata["executedon"] = requestdata['browser']
                    querydata["executionid"] = ObjectId(requestdata['executionid'])
                    querydata["cycleid"] = ObjectId(requestdata['cycleid'])
                    querydata["testscenarioid"] = ObjectId(requestdata['testscenarioid'])
                    #querydata["testsuiteid"] = ObjectId(requestdata['testsuiteid'])
                    querydata["status"] = requestdata['status']
                    querydata["executedtime"] = modifiedon
                    querydata["modifiedon"] = modifiedon
                    querydata["modifiedby"] = ObjectId(requestdata['modifiedby'])
                    querydata["modifiedbyrole"] = ObjectId(requestdata['modifiedby'])
                    querydata["report"] = json.loads(requestdata['report'])


                    res["rows"] = str(n68session.reports.insert(querydata))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'inserintotexecutionquery'):
                    starttime = datetime.now()
                    t_arr = []
                    for i in requestdata['testsuiteids']:
                        testsuiteid = (n68session.testsuites.find_one({"mindmapid":ObjectId(i),"cycleid":ObjectId(requestdata["cycleid"])},{"$set":"_id"}))
                        t_arr.append(testsuiteid['_id'])

                    res["rows"] = str(n68session.executions.insert({"parent": t_arr, "configuration": {},
                    "endtime": None, "executedby": ObjectId(requestdata['executedby']), "status": requestdata['status'],
                    "starttime": starttime}))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))

                elif(requestdata['query'] == 'updateintotexecutionquery'):
                    endtime = datetime.now()
                    #testsuiteid = (n68session.testsuites.find_one({"mindmapid":ObjectId(requestdata["testsuiteid"]),"cycleid":ObjectId(requestdata["cycleid"])},{"$set":"_id"}))
                    res["rows"] = list(n68session.executions.update({"_id":ObjectId(requestdata['executionid'])},{'$set': {"status":requestdata['status'],"endtime":endtime}
                    #'$addToSet':{"parent":testsuiteid['_id']}
                    }))
                    app.logger.debug("Executed ExecuteTestSuite_ICE. Query: "+str(requestdata["query"]))
                else:
                    return jsonify(res)
            else:
                app.logger.warn('Empty data received. execute testsuite.')
                return jsonify(res)
            return jsonify(res)
        except Exception as execuitetestsuiteexc:
            servicesException("ExecuteTestSuite_ICE", execuitetestsuiteexc, True)
            return jsonify(res)

################################################################################
# END OF EXECUTION
################################################################################

    @app.route('/suite/ScheduleTestSuite_ICE',methods=['POST'])
    def ScheduleTestSuite_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            param = str(requestdata['query'])
            app.logger.debug("Inside ScheduleTestSuite_ICE. Query: " + param)
            if not isemptyrequest(requestdata):
                if(param == 'insertscheduledata'):
                    requestdata1={}
                    scheduleTime=requestdata['scheduledatetime']
                    requestdata1["scheduledon"] = datetime.fromtimestamp(int(scheduleTime)/1000,pytz.UTC)
                    requestdata1["target"]=requestdata["clientipaddress"]
                    requestdata1["scheduledby"]=ObjectId(requestdata['userid'])
                    testsuiteids_list = [ObjectId(i) for i in requestdata['testsuiteids']]
                    requestdata1["testsuiteids"]=testsuiteids_list
                    requestdata1["scenariodetails"]=json.loads(requestdata["scenariodetails"])
                    requestdata1["status"]=requestdata["schedulestatus"]
                    requestdata1["executeon"]=requestdata["browserlist"]
                    requestdata1["cycleid"]=ObjectId(requestdata["cycleid"])
                    # requestdata1["testsuiteids"]=requestdata["testsuiteids"]
                    res["rows"] =  n68session.scheduledexecutions.insert(requestdata1)

                elif(param == 'updatescheduledstatus'):
                    n68session.scheduledexecutions.update({"_id":ObjectId(requestdata['scheduleid'])},{"$set":{"status":requestdata["schedulestatus"]}})
                    res["rows"] = "success"

                elif(param == 'getscheduledata'):
                    findquery = {}
                    if "status" in requestdata: findquery["status"] = requestdata["status"]
                    if "scheduleid" in requestdata: findquery["_id"] = ObjectId(requestdata["scheduleid"])
                    res["rows"] = list(n68session.scheduledexecutions.find(findquery))

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
            else:
                app.logger.warn('Empty data received. schedule testsuite.')
            app.logger.debug("Executed ScheduleTestSuite_ICE. Query: " + param)
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
            else:
                app.logger.warn('Empty data received. getting testcases from scenarios.')
            app.logger.debug("Executed getTestcaseDetailsForScenario_ICE")
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

