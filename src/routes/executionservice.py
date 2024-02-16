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
from pymongo import UpdateOne

query = {'delete_flag': False}

def LoadServices(app, redissession, client ,getClientName):
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                app.logger.info("Inside readTestSuite_ICE. Query: " + param)
                if(param == 'gettestsuite'):
                    mindmapid = ObjectId(requestdata['mindmapid'])
                    cycleid = ObjectId(requestdata['cycleid'])
                    filterquery = {"conditioncheck":1,"getparampaths":1,"donotexecute":1,"testscenarioids":1,"accessibilityParameters":1}
                    testsuite = dbsession.testsuites.find_one({"cycleid":cycleid, "mindmapid":mindmapid, "deleted":query['delete_flag']}, filterquery)
                    create_suite = testsuite is None
                    mindmaps = dbsession.mindmaps.find_one({"_id": mindmapid, "deleted":query['delete_flag']})
                    batchinfo = dbsession.tasks.find_one({"nodeid":mindmapid, "cycleid":cycleid},{'batchname': 1,'_id':0})
                    batchname=''
                    if(batchinfo != None and 'batchname' in batchinfo):
                        batchname = batchinfo['batchname']
                    
                    testscenarioids = [i["_id"] for i in mindmaps["testscenarios"]]
                    tsclen = len(testscenarioids)
                    createdby = ObjectId(requestdata['createdby'])
                    createdbyrole = ObjectId(requestdata['createdbyrole'])
                    querydata = {}
                    querydata["name"] = mindmaps["name"]
                    querydata["batchname"] = batchname
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
                        querydata["accessibilityParameters"] = []
                        testsuiteid = dbsession.testsuites.insert(querydata)
                    else:
                        testsuiteid = testsuite["_id"]
                        testscenariods_ts = testsuite["testscenarioids"]
                        getparampaths_ts = testsuite["getparampaths"]
                        donotexecute_ts = testsuite["donotexecute"]
                        conditioncheck_ts = testsuite["conditioncheck"]
                        accessibilityParameters_ts = testsuite["accessibilityParameters"] if "accessibilityParameters" in testsuite else []
                        getparampaths = []
                        conditioncheck = []
                        donotexecute = []
                        for i in range(tsclen):
                            index = -1
                            if testscenarioids[i] in testscenariods_ts:
                                index = testscenariods_ts.index(testscenarioids[i])
                            if index != -1:
                                if (getparampaths_ts[index].strip() == ''): getparampaths.append('')
                                else: getparampaths.append(getparampaths_ts[index])
                                if conditioncheck_ts is not None: conditioncheck.append(conditioncheck_ts[index])
                                if donotexecute_ts is not None: donotexecute.append(donotexecute_ts[index])
                                testscenariods_ts[index] = -1 # Visited this scenario once already
                            else:
                                getparampaths.append('')
                                conditioncheck.append(0)
                                donotexecute.append(1)
                        querydata["conditioncheck"] = conditioncheck
                        querydata["donotexecute"] = donotexecute
                        querydata["getparampaths"] = getparampaths
                        querydata["accessibilityParameters"] = accessibilityParameters_ts
                        dbsession.testsuites.update_one({"_id": testsuiteid, "deleted": query['delete_flag']}, {'$set': querydata})

                    res['rows'] = {
                        "testsuiteid": testsuiteid, "conditioncheck": querydata["conditioncheck"],
                        "donotexecute": querydata["donotexecute"], "getparampaths": querydata["getparampaths"],
                        "testscenarioids": testscenarioids, "name": querydata["name"], "batchname": querydata["batchname"], "accessibilityParameters": querydata["accessibilityParameters"]
                    }

                elif(param == 'gettestscenario'):
                    proj_typ = {}
                    tsc_map = {}
                    prj_map = {}
                    proj_arr = []
                    projectTypes = list(dbsession.projecttypekeywords.find({}, {"name": 1}))
                    for tp in projectTypes:
                        proj_typ[tp["_id"]] = tp["name"]
                    testscenarioids = [ObjectId(i) for i in requestdata["testscenarioids"]]
                    testscenarios = list(dbsession.testscenarios.find({"_id": {"$in": testscenarioids}, "deleted":query['delete_flag']}, {"name": 1, "projectid": 1}))
                    for tsc in testscenarios:
                        proj_arr.append(ObjectId(tsc["projectid"]))
                    projData = list(dbsession.projects.find({"_id": {"$in": proj_arr}}, {"name": 1, "type": 1}))
                    for prj in projData:
                        prj_map[prj["_id"]] = {"name":prj["name"],"type":prj["type"]}
                    for i,tsc in enumerate(testscenarios):
                        tsc_map[tsc["_id"]] = [tsc["name"], prj_map[tsc["projectid"]]["name"],proj_typ[prj_map[tsc["projectid"]]["type"]]]
                    testscenarionames = []
                    projectnames = []
                    apptype = []
                    for tsc in testscenarioids:
                        if tsc in tsc_map:
                            testscenarionames.append(tsc_map[tsc][0])
                            projectnames.append(tsc_map[tsc][1])
                            apptype.append(tsc_map[tsc][2])
                        else:
                            testscenarionames.append('N/A')
                            projectnames.append('N/A')
                            apptype.append('N/A')
                    res['rows'] = {"testscenarionames": testscenarionames, "projectnames": projectnames, "apptypes": apptype}
                app.logger.info("Executed readTestSuite_ICE. Query: " + param)
            else:
                app.logger.warn('Empty data received. read testsuite.')
        except Exception as e:
            app.logger.info("error : " + e)
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                testsuiteid = ObjectId(requestdata['testsuiteid'])
                querydata = requestdata
                del querydata["testsuiteid"]
                del querydata["query"]
                querydata["modifiedon"]= datetime.now()
                querydata["testscenarioids"] = [ObjectId(i) for i in requestdata['testscenarioids']]
                if "accessibilityParameters" in querydata:
                    querydata["accessibilityParameters"] = [i for i in querydata["accessibilityParameters"] if i is not None]
                else:
                    querydata["accessibilityParameters"] = []
                dbsession.testsuites.update_one({"_id": testsuiteid}, {"$set":querydata})
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                if param == 'testcasedetails' and valid_objectid(requestdata['id']):
                    tsc = dbsession.testscenarios.find_one({"_id": ObjectId(requestdata['id']),"deleted":query['delete_flag']},{"testcaseids":1})
                    if tsc is not None:
                        testcase=[]
                        testcases = dbsession.testcases.find({"_id": {"$in": tsc["testcaseids"]},"deleted":query['delete_flag']},{"name":1,"versionnumber":1,"screenid":1,"datatables":1})
                        scids = {}
                        dts_data = {}
                        tcdict = {}
                        for tc in testcases: tcdict[tc['_id']] = tc
                        for i in tsc['testcaseids']:
                            tc = tcdict[i]
                            scid = tc["screenid"]
                            if scid not in scids:
                                scids[scid] = dbsession.screens.find_one({"_id":scid})['name']
                            tc["screenname"] = scids[scid]
                            dtnames = tc.get('datatables', [])
                            if 'dtparam' in requestdata:
                                dtp = requestdata['dtparam']
                                if len(dtp) > 0 and dtp[0] not in dtnames: dtnames.append(dtp[0])
                            if len(dtnames) > 0:
                                dts = []
                                dts_to_fetch = [i for i in dtnames if i not in dts_data]
                                dtdet = dbsession.datatables.find({"name": {'$in': dts_to_fetch}})
                                for dt in dtdet: dts_data[dt['name']] = dt['datatable']
                                for dt in dtnames: 
                                    if dt in dts_data:
                                        dts.append({dt: dts_data[dt]})
                                tc['datatables'] = dts
                            testcase.append(tc)
                        res["rows"] = testcase
                    if 'userid' in requestdata:    # Update the Counter
                        counterupdator(dbsession, 'testscenarios', ObjectId(requestdata['userid']), 1)

                elif param == 'insertintoexecution':
                    starttime = datetime.now()
                    batchid = ObjectId() if requestdata["batchid"] == "generate" else ObjectId(requestdata["batchid"])
                    tsuids = requestdata['testsuiteids']
                    execids = requestdata['executionids']
                    batchname = '' if 'batchname' not in requestdata else requestdata['batchname']
                    smart = False if 'smart' not in requestdata else requestdata['smart']
                    for tsuid in tsuids:
                        if execids[tsuid] is None:
                            insertquery = {"batchid": batchid,"batchname": batchname,"smart":smart,"parent": [ObjectId(tsuid)],
                                "configuration": {}, "executedby": ObjectId(requestdata['executedby']),
                                "status": "queued", "version":requestdata['version'], "endtime": None, "starttime": starttime}
                            if('configurekey' in requestdata and requestdata['configurekey']):
                                insertquery['configurekey'] = requestdata['configurekey']
                                insertquery['executionListId'] = requestdata['executionListId']
                                insertquery['projectId'] = requestdata['projectId']
                                insertquery['releaseName'] = requestdata['releaseName']
                                insertquery['cycleId'] = requestdata['cycleId']

                            execid = str(dbsession.executions.insert(insertquery))
                            execids[tsuid] = execid
                    res["rows"] = {"batchid": str(batchid), "execids": execids}
                elif param  == 'updateintoexecution':
                    TF = '%Y-%m-%d %H:%M:%S'
                    if 'starttime' in requestdata:
                        start_t = datetime.strptime(requestdata['starttime'], TF)
                        for exec_id in requestdata['executionids']:
                            dbsession.executions.update({"_id":ObjectId(exec_id), "status":"queued"}, {'$set': {"status":'inprogress',"starttime":start_t}})
                    else:
                        end_t = datetime.strptime(requestdata['endtime'], TF) if 'endtime' in requestdata else datetime.now()
                        updt_args = {"endtime":end_t}
                        if "status" in requestdata: updt_args["status"]=requestdata['status']
                        for exec_id in requestdata['executionids']:
                            dbsession.executions.update({"_id":ObjectId(exec_id)}, {'$set': updt_args})
                    res["rows"] = True

                elif param == 'insertreportquery':
                    modifiedon = datetime.now()
                    report = json.loads(requestdata['report'])
                    rows = report['rows']
                    overallstatus = report['overallstatus']
                    # limit = 15000
                    # reportitems = []
                    # ind=1
                    # x=0
                    # while True:
                    #     reportitems.append({'index':ind,'rows':rows[x:x+limit]})
                    #     x+=limit
                    #     ind+=1
                    #     if x>=len(rows):
                    #         break
                    # ritems = dbsession.reportitems.insert_many(reportitems)

                    querydata = {
                        "executionid": ObjectId(requestdata['executionid']),
                        "testscenarioid": ObjectId(requestdata['testscenarioid']),
                        "status": requestdata['status'],
                        "executedtime": modifiedon,
                        "executedon": requestdata['browser'],
                        "overallstatus": overallstatus,
                        "modifiedon": modifiedon,
                        "modifiedby": ObjectId(requestdata['modifiedby']),
                        "modifiedbyrole": ObjectId(requestdata['modifiedbyrole']),
                        "reportitems": []  #Modified to support latest changes
                    }
                    res["rows"] = str(dbsession.reports.insert(querydata))


                    # Storing the reportitems after the reports to get the report id
                    # Updated
                    for item in rows:
                        item['scenario_id'] = requestdata['testscenarioid']
                        item['execution_ids'] = requestdata['executionid']
                        item['reportid'] = ObjectId(res["rows"])
                    ritems = dbsession.reportitems.insert_many(rows)

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
            missed_executions = []
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)      
                dbsession=client[clientName]
                if(param == 'insertscheduledata'):
                    for tscos in requestdata["scenarios"]:
                        for tsco in tscos: tsco["scenarioId"] = ObjectId(tsco["scenarioId"])
                    invokinguser = requestdata["scheduledby"]
                    scheduledby = {"invokinguser":ObjectId(invokinguser["invokinguser"]),"invokingusername":invokinguser["invokingusername"],"invokinguserrole":invokinguser["invokinguserrole"]}
                    if "status" in requestdata:
                        status = requestdata["status"]
                    else:
                        status = "scheduled"
                    if "recurringPattern" in requestdata:
                        recurringpattern = requestdata["recurringPattern"]
                    else:
                        recurringpattern = "One Time"
                    if "recurringStringOnHover" in requestdata:
                        recurringstringonhover = requestdata["recurringStringOnHover"]
                    else:
                        recurringstringonhover = "One Time"
                    if requestdata['parentId'] != 0:	
                        parentid = ObjectId(requestdata['parentId'])	
                    else:	
                        parentid = ObjectId()
                    if "scheduleThrough" in requestdata:
                        schedulethrough = requestdata["scheduleThrough"]
                    else:
                        schedulethrough = "client"
                    dataquery = {
                        "scheduledon": datetime.fromtimestamp(int(requestdata['timestamp'])/1000,pytz.UTC),
                        "executeon": requestdata["executeon"],
                        "executemode": requestdata["executemode"],
                        "target": requestdata["targetaddress"],
                        "scenariodetails": requestdata["scenarios"],
                        "scenarioFlag": requestdata["scenarioFlag"],
                        "status": status,
                        "testsuiteids": [ObjectId(i) for i in requestdata['testsuiteIds']],
                        "scheduledby": scheduledby,
                        "poolid": ObjectId(requestdata["poolid"]),
                        "scheduletype": requestdata["scheduleType"],
                        "recurringpattern": recurringpattern,
                        "time": requestdata["time"],
                        "recurringstringonhover": recurringstringonhover,
                        "parentid": parentid,
                        "startdate": datetime.fromtimestamp(int(requestdata['startDate'])/1000,pytz.UTC),
                        "configurekey": requestdata["configureKey"],
                        "configurename": requestdata["configureName"],
                        "endafter": requestdata["endAfter"],
                        "schedulethrough": schedulethrough
                    }
                    if "smartid" in requestdata: dataquery["smartid"] = uuid.UUID(requestdata["smartid"])
                    scheduleid = dbsession.scheduledexecutions.insert(dataquery)
                    res["rows"] = {"id": scheduleid}

                elif(param == 'updatescheduledstatus'):
                    updatequery = { "status": requestdata["schedulestatus"] }
                    if "batchid" in requestdata: updatequery["batchid"] = ObjectId(requestdata["batchid"])
                    dbsession.scheduledexecutions.update({"_id":ObjectId(requestdata['scheduleid'])},{"$set": updatequery})
                    res["rows"] = "success"

                elif(param == 'getscheduleagendajobs'):
                    findquery = {}
                    if "scheduleid" in requestdata: findquery["name"] = requestdata["scheduleid"]
                    res["rows"] = list(dbsession.agendaJobs.find(findquery))

                elif(param == 'cancelagendajobs'):
                    findquery = {}
                    if "scheduleid" in requestdata: findquery["name"] = requestdata["scheduleid"]
                    res["rows"] = list(dbsession.agendaJobs.remove(findquery))

                elif(param == 'getscheduledata'):
                    findquery = {}
                    if "scheduleid" in requestdata: findquery["_id"] = ObjectId(requestdata["scheduleid"])
                    if "status" in requestdata: findquery["status"] = requestdata["status"]
                    if "parentid" in requestdata: findquery["parentid"] = ObjectId(requestdata["parentid"])
                    res["rows"] = list(dbsession.scheduledexecutions.find(findquery))

                elif(param == 'getallscheduledata'):
                    prjtypes = dbsession.projecttypekeywords.find({}, {"name": 1})
                    ptmap = {}
                    for pt in prjtypes: ptmap[pt["_id"]] = pt["name"]
                    projects = dbsession.projects.find({}, {"type": 1})
                    prjmap = {}
                    for prj in projects: prjmap[prj["_id"]] = ptmap[prj["type"]]
                    tsuites = dbsession.testsuites.find({}, {"name": 1})
                    tsumap = {}
                    for tsu in tsuites: tsumap[tsu["_id"]] = tsu["name"]
                    tscos = dbsession.testscenarios.find({}, {"projectid": 1})
                    tscomap = {}
                    for tsco in tscos: tscomap[tsco["_id"]] = prjmap[tsco["projectid"]] if tsco["projectid"] in prjmap else "-"
                    schedules = list(dbsession.scheduledexecutions.find({"configurekey": requestdata["configKey"]}))
                    poollist={}
                    pool = list(dbsession.icepools.find({}, {"poolname": 1}))
                    for pid in pool: poollist[pid['_id']] = pid['poolname']
                    for sch in schedules:
                        if "poolid" in sch and sch["poolid"] in poollist: 
                            sch["poolname"]=poollist[sch["poolid"]]
                        if "recurringstringonhover" in sch and sch["recurringstringonhover"] != "One Time" and sch["status"] != "recurring" and "*" not in sch["recurringpattern"]:
                            if "parentid" in sch:
                                created_date = list(dbsession.scheduledexecutions.find({"_id": sch["parentid"]}))
                                if len(created_date) > 0:
                                    if "startdate" in created_date[0]:
                                        sch["createddate"] = created_date[0]['startdate']
                                    else:
                                        sch["createddate"] = created_date[0]['scheduledon']
                            else:
                                if "startdate" in sch:
                                    sch["createddate"] = sch['startdate']
                                else:
                                    sch["createddate"] = sch['scheduledon']
                        elif "recurringpattern" in sch and "*" in sch["recurringpattern"]:
                            if "startdate" in sch:
                                sch["createddate"] = sch['startdate']
                            else:
                                sch["createddate"] = sch['scheduledon']
                        elif "recurringpattern" in sch and sch["recurringpattern"] == "One Time":
                            if "startdate" in sch:
                                sch["createddate"] = sch['startdate']
                            else:
                                sch["createddate"] = sch['scheduledon']
                        testsuitenames = []
                        for tsuid in sch["testsuiteids"]: testsuitenames.append(tsumap[tsuid] if tsuid in tsumap else "")
                        sch["testsuitenames"] = testsuitenames
                        if sch['scheduledon']:
                            if sch["status"] == "scheduled" and datetime.utcnow() - sch['scheduledon'] >= timedelta(days=3):
                                missed_executions.append(UpdateOne({"_id":sch['_id']},{"$set":{"status":"Missed"}}))
                                sch["status"] = "Missed"
                            elif sch["status"] == "inprogress" and datetime.utcnow() - sch['scheduledon'] >= timedelta(days=15):
                                missed_executions.append(UpdateOne({"_id":sch['_id']},{"$set":{"status":"Failed"}}))
                                sch["status"] = "Failed"
                        if sch["status"] == "Failed 01": sch["status"] = "Missed"
                        elif sch["status"] == "Failed 02": sch["status"] = "Failed"
                        for tscos in sch["scenariodetails"]:
                            if type(tscos) == dict: break
                            for tsco in tscos: tsco["appType"] = tscomap[tsco["scenarioId"]]
                    res["rows"] = schedules
                    if len(missed_executions) > 0: dbsession.scheduledexecutions.bulk_write(missed_executions)
                    
                elif(param == 'gettestsuiteproject'):
                    testsuiteids = [ObjectId(i) for i in requestdata["testsuiteids"]]
                    testsuites = list(dbsession.testsuites.find({"_id": { "$in": testsuiteids}},
                        {"name": 1, "cycleid": 1, "versionnumber": 1}))
                    testsuitemap = {}
                    for tsu in testsuites: testsuitemap[str(tsu["_id"])] = tsu
                    cycleid = ObjectId(testsuites[0]["cycleid"])
                    project = dbsession.projects.find_one({"releases.cycles._id": cycleid}, {"name": 1, "domain": 1, "releases": 1, "type": 1})
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
                    project["type"] = dbsession.projecttypekeywords.find_one({"_id": project["type"]}, {"name": 1})["name"]
                    res["rows"] = { "suitemap": testsuitemap, "project": project }

                elif(param == 'checkscheduleddetails'):
                    timelist = requestdata["scheduledatetime"]
                    flag = -1
                    for i in range(len(timelist)):
                        timestamp =  datetime.fromtimestamp(int(timelist[i])/1000,pytz.UTC)
                        address = requestdata["targetaddress"][i]
                        count = dbsession.scheduledexecutions.find({"scheduledon": timestamp, "status": "scheduled", "target": address}).count()
                        if count > 0:
                            flag = i
                            break
                    res["rows"] = flag

                elif(param == 'checkrecurringscheduleddetails'):
                    timelist = requestdata["scheduledatetime"]
                    flag = -1
                    for i in range(len(timelist)):
                        time =  timelist[i]
                        address = requestdata["targetaddress"][i]
                        count = dbsession.scheduledexecutions.find({"time": time, "status": "recurring", "target": address}).count()
                        if count > 0:
                            flag = i
                            break
                    res["rows"] = flag

                elif(param == 'getallscheduledataondate'):
                    prjtypes = dbsession.projecttypekeywords.find({}, {"name": 1})
                    ptmap = {}
                    for pt in prjtypes: ptmap[pt["_id"]] = pt["name"]
                    projects = dbsession.projects.find({}, {"type": 1})
                    prjmap = {}
                    for prj in projects: prjmap[prj["_id"]] = ptmap[prj["type"]]
                    tsuites = dbsession.testsuites.find({}, {"name": 1})
                    tsumap = {}
                    for tsu in tsuites: tsumap[tsu["_id"]] = tsu["name"]
                    tscos = dbsession.testscenarios.find({}, {"projectid": 1})
                    tscomap = {}
                    for tsco in tscos: tscomap[tsco["_id"]] = prjmap[tsco["projectid"]] if tsco["projectid"] in prjmap else "-"
                    scheduledon = datetime.fromtimestamp(int(requestdata['scheduledDate'])/1000)
                    scheduledon = scheduledon.replace(tzinfo=None)
                    schedules = list(dbsession.scheduledexecutions.find({"$and": [{"scheduledon":scheduledon}, {"configurekey": requestdata["configKey"]}]}))
                    poollist={}
                    pool = list(dbsession.icepools.find({}, {"poolname": 1}))
                    for pid in pool: poollist[pid['_id']] = pid['poolname']
                    for sch in schedules:
                        if "poolid" in sch and sch["poolid"] in poollist: 
                            sch["poolname"]=poollist[sch["poolid"]]
                        if "recurringstringonhover" in sch and sch["recurringstringonhover"] != "One Time" and sch["status"] != "recurring" and "*" not in sch["recurringpattern"]:
                            if "parentid" in sch:
                                created_date = list(dbsession.scheduledexecutions.find({"_id": sch["parentid"]}))
                                if len(created_date) > 0:
                                    if "startdate" in created_date[0]:
                                        sch["createddate"] = created_date[0]['startdate']
                                    else:
                                        sch["createddate"] = created_date[0]['scheduledon']
                            else:
                                if "startdate" in sch:
                                    sch["createddate"] = sch['startdate']
                                else:
                                    sch["createddate"] = sch['scheduledon']
                        elif "recurringpattern" in sch and "*" in sch["recurringpattern"]:
                            if "startdate" in sch:
                                sch["createddate"] = sch['startdate']
                            else:
                                sch["createddate"] = sch['scheduledon']
                        elif "recurringpattern" in sch and sch["recurringpattern"] == "One Time":
                            if "startdate" in sch:
                                sch["createddate"] = sch['startdate']
                            else:
                                sch["createddate"] = sch['scheduledon']
                        testsuitenames = []
                        for tsuid in sch["testsuiteids"]: testsuitenames.append(tsumap[tsuid] if tsuid in tsumap else "")
                        sch["testsuitenames"] = testsuitenames
                        if sch['scheduledon']:
                            if sch["status"] == "scheduled" and datetime.utcnow() - sch['scheduledon'] >= timedelta(days=3):
                                missed_executions.append(UpdateOne({"_id":sch['_id']},{"$set":{"status":"Missed"}}))
                                sch["status"] = "Missed"
                            elif sch["status"] == "inprogress" and datetime.utcnow() - sch['scheduledon'] >= timedelta(days=15):
                                missed_executions.append(UpdateOne({"_id":sch['_id']},{"$set":{"status":"Failed"}}))
                                sch["status"] = "Failed"
                        if sch["status"] == "Failed 01": sch["status"] = "Missed"
                        elif sch["status"] == "Failed 02": sch["status"] = "Failed"
                        for tscos in sch["scenariodetails"]:
                            if type(tscos) == dict: break
                            for tsco in tscos: tsco["appType"] = tscomap[tsco["scenarioId"]]
                    res["rows"] = schedules
                    if len(missed_executions) > 0: dbsession.scheduledexecutions.bulk_write(missed_executions)
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                screenids = [ObjectId(i) for i in requestdata['screenids']]
                screens = list(dbsession.screens.find({"_id": {"$in": screenids},
                    "deleted":query['delete_flag']},{"name":1,"projectid":1}))
                prjset = set()
                screenmap = {}
                prjmap = {}
                for scr in screens:
                    screenmap[scr["_id"]] = scr
                    prjset.add(scr["projectid"])
                projects = list(dbsession.projects.find({"_id": {"$in": list(prjset)}},{"name":1}))
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
            clientName=getClientName(requestdata)         
            dbsession=client[clientName]
            scenario_ids=[]
            screenid=[]
            testcaseid=[]
            screens=[]
            counter=0
            for i in requestdata["scenario_ids"]:
                scenario_ids.append(ObjectId(i))
            testcaseids=list(dbsession.testscenarios.find({"_id":{"$in":scenario_ids}},{"testcaseids":1}))
            for i in testcaseids:
                for j in i["testcaseids"]:
                    testcaseid.append(j)
            testcases=list(dbsession.testcases.find({"_id":{"$in":testcaseid}},{"screenid":1,"_id":1,"modifiedon":1}))
            for i in testcases:
                screenid.append(i["screenid"])
                screens.append(dbsession.screens.find_one({"_id":i["screenid"]},{"modifiedon":1}))
            for i in testcaseid:
                query=list(dbsession.tasks.find({"nodeid":i},{"history":1}).sort("createdon",-1).limit(1))
                if(len(query[0]["history"])>0):
                    date=query[0]["history"][-1]["modifiedOn"]
                    if isinstance(date, str):
                        try:
                            date = datetime.strptime(date.split(' ')[0], "%d/%m/%Y,%H:%M:%S")
                        except:
                            date = datetime.strptime(date, "%d/%m/%Y,%H:%M:%S")
                    if query[0]["history"][-1]["status"] == "complete" and testcases[counter]['modifiedon']>=date:
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
                query=list(dbsession.tasks.find({"nodeid":i},{"history":1}).sort("createdon",-1).limit(1))
                if(len(query[0]["history"])>0):
                    date=query[0]["history"][-1]["modifiedOn"]
                    if isinstance(date, str):
                        try:
                            date = datetime.strptime(date.split(' ')[0], "%d/%m/%Y,%H:%M:%S")
                        except:
                            date = datetime.strptime(date, "%d/%m/%Y,%H:%M:%S")
                    if query[0]["history"][-1]["status"] == "complete" and screens[counter]['modifiedon']>=date:
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
                tasks=list(dbsession.tasks.find({"nodeid":{"$in":testcaseid},"status":{"$ne":"complete"}},{"status":1}))
                tasks1=list(dbsession.tasks.find({"nodeid":{"$in":screenid},"status":{"$ne":"complete"}},{"status":1}))
                res={'rows':len(tasks)+len(tasks1)}
            return jsonify(res)
        except Exception as getalltaskssexc:
            servicesException("checkApproval",getalltaskssexc, True)
            return jsonify(res)