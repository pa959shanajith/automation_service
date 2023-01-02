################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from copy import copy, deepcopy
from bson.objectid import ObjectId
import json
from datetime import datetime
from Crypto.Cipher import AES
import codecs
from pymongo import InsertOne
from bson import json_util
from bson.json_util import loads


def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

    def getScrapeData(hex_data):
        try:
            key = "".join(['N','i','n','e','e','t','e','e','n','6','8','@','S','e',
                'c','u','r','e','S','c','r','a','p','e','D','a','t','a','P','a','t','h'])
            data = codecs.decode(hex_data, 'hex')
            aes = AES.new(key.encode("utf-8"), AES.MODE_CBC, b'0'*16)
            data = aes.decrypt(data).decode('utf-8')
            return data[0:-ord(data[-1])]
        except:
            return hex_data

    def adddataobjects(pid, d):
        if len(d) == 0: return False
        req = []
        temp_set=set()
        n_list=[]
        queryresult=None
        for i in d:
            t1=tuple(sorted(i.items()))
            if t1 not in temp_set:
                temp_set.add(t1)
                n_list.append(i)
        for row in n_list:
            if(row['tag']!="GuiMenu"):
                if type(row) == str and len(row) == 0: continue
                if "custname" not in row: row["custname"] = "object"+str(row["_id"])
                row["parent"] = [pid]
                req.append(InsertOne(row))
        if req:
            dbsession.dataobjects.bulk_write(req)
            queryresult=list(dbsession.dataobjects.find({"parent":pid},{"custname":1,"_id":1,"parent":1}))
        else: return pid
        return queryresult

    def createdataobjects(scrid, objs):
        custnameToAdd = []
        obj = objs['scrapedata']['view']
        if(obj!=[]):
            for i in range(len(obj)):
                so = obj[i]
                if so["apptype"] == "WEB":
                    ob=[]
                    if 'xpath' in so:
                        obn = so['xpath'] 
                    else:
                        obn = ""
                    dodata = {
                        "custname": so["custname"],
                        "xpath": obn
                    }
                    if obn.strip() == '' :
                        custnameToAdd.append(dodata)
                    legend = ['id', 'name', 'tag', 'left', 'top', 'height', 'width', 'text', 'class']
                    for i in obn.split(';'): ob.append(getScrapeData(i))
                    ob = ";".join(ob).split(';')
                    ob = ob[1:2] + ob[3:]
                    if len(ob) < 4:
                        custnameToAdd.append(dodata)
                        continue
                    elif len(ob) == 4: legend = legend[:4]
                    elif len(ob) == 8: del legend[3]
                    elif len(ob) == 11: dodata["tag"] = ob[-1]
                    try:
                        for i in range(len(legend)):
                            if (i>=4 and i<=7):
                                if ob[i].isnumeric(): dodata[legend[i]] = int(ob[i])
                            else:
                                if (ob[i] != "null") and (legend[i] not in dodata): dodata[legend[i]] = ob[i]
                    except: pass
                    gettag = {"btn":"button","txtbox":"input","lnk":"a","radiobtn":"radiobutton","select":"select","chkbox":"checkbox","lst":"list","tab":"tab","tree":"tree","dtp":"datepicker","tbl":"table","elmnt":"label"}
                    tag = so["custname"].split("_")[-1]
                    if tag in gettag: dodata["tag"] = gettag[tag]
                    if "class" in dodata: dodata["class"] = dodata["class"].split("[")[0]
                    dodata["url"] = so["url"] if 'url' in so else ""
                    dodata["cord"] = so["cord"] if "cord" in so else ""
                elif so["apptype"] == "SAP":
                    if so["tag"]=="GuiOkCodeField": so["tag"]="input"
                    if so["tag"]=="GuiSimpleContainer": so["tag"]="scontainer"
                    if so["tag"]=="GuiLabel": so["tag"]="label"
                    dodata = {
                        'xpath': so['xpath'],
                        'id': so['id'],
                        'text': so['text'].split("  ")[0],
                        'tag': so['tag'],
                        'custname': so['custname'],
                        'left': so['left'],
                        'top': so['top'],
                        'height': so['height'],
                        'width': so['width']
                    }
                elif so["apptype"] == "OEBS":
                    if so['hiddentag']=="No": so['hiddentag']="False"
                    if so['custname']=="":so['custname']=so['tag']+"_elmnt"
                    dodata = {
                        'xpath': so['xpath'],
                        'id': so['id'],
                        'text': so['text'].split("  ")[0],
                        "url":"Oracle Applications - EBSDB",
                        'tag': so['tag'],
                        'hiddentag' : so['hiddentag'],
                        'custname': so['custname'],
                        'left': so['y_coor'],
                        'top': so['x_coor'],
                        'height': so['height'],
                        'width': so['width']
                    }
                custnameToAdd.append(dodata)
            res = adddataobjects(scrid, custnameToAdd)
            return res
        else:
            return scrid

    # API to get the project type name using the ProjectID
    @app.route('/create_ice/getProjectType',methods=['POST'])
    def getProjectType():
        app.logger.debug("Inside getProjectType")
        res={'rows':'fail'}
        try:
           requestdata=json.loads(request.data)
           if not isemptyrequest(requestdata):
                projectid=requestdata['projectid']
                dbconn=dbsession["projects"]
                getProjectType=list(dbconn.find({"_id":ObjectId(projectid)},{"type":1,"releases.name":1,"releases.cycles.name":1,"releases.cycles._id":1,"domain":1}))
                dbconn=dbsession["projecttypekeywords"]
                getProjectTypeName= list(dbconn.find({"_id":ObjectId(getProjectType[0]["type"])},{"name":1}))
                res={'rows':getProjectType,'projecttype':getProjectTypeName}
           else:
                app.logger.warn("Empty data received. getProjectType")
        except Exception as e:
            servicesException("getProjectType", e, True)
        return jsonify(res)

    #API to get ProjectID and Names of project assigned to particular user
    @app.route('/create_ice/getProjectIDs',methods=['POST'])
    def getProjectIDs():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getProjectIDs. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if len(projecttype_names)==0:
                    result=list(dbsession.projecttypekeywords.find({},{"_id":1,"name":1}))
                    for p in result:
                        projecttype_names[str(p["_id"])]=p["name"]
                prjDetails={
                    'projectId':[],
                    'projectName':[],
                    'appType':[],
                    'appTypeName':[],
                    'releases':[],
                    'cycles':{},
                    'projecttypes':projecttype_names,
                    'domains':[]
                }
                if 'userrole' in requestdata and requestdata['userrole'] == "Test Manager":
                    dbconn=dbsession["projects"]
                    projectIDResult=list(dbconn.find({},{"_id":1}))
                else:
                    userid=requestdata['userid']
                    dbconn=dbsession["users"]
                    projectIDResult=list(dbconn.find({"_id":ObjectId(userid)},{"projects":1}))
                if(len(projectIDResult)!=0):
                    dbconn=dbsession["mindmaps"]
                    prjids=[]
                    if "projects" in projectIDResult[0]:
                        for pid in projectIDResult[0]["projects"]:
                            prjids.append(str(pid))
                    else:
                        for pid in projectIDResult:
                            prjids.append(str(pid["_id"]))
                    if(requestdata['query'] == 'emptyflag'):
                        # Check this flag
                        modulequeryresult=dbconn.distinct('projectid')
                        modpids=[]
                        emppid=[]
                        for row in modulequeryresult[0]:
                            modpids.append(str(row['projectid']))
                        for pid in prjids:
                            if pid not in modpids:
                                emppid.append(pid)
                        prjids=emppid
                    for pid in prjids:
                        dbconn=dbsession["projects"]
                        prjDetail=list(dbconn.find({"_id":ObjectId(pid)},{"_id":1,"name":1,"type":1,"domain":1,"releases.name":1,"releases.cycles.name":1,"releases.cycles._id":1}))
                        if(len(prjDetail)!=0):
                            prjDetails['projectId'].append(str(prjDetail[0]['_id']))
                            prjDetails['projectName'].append(prjDetail[0]['name'])
                            prjDetails['appType'].append(str(prjDetail[0]['type']))
                            prjDetails['appTypeName'].append(projecttype_names[str(prjDetail[0]['type'])])
                            prjDetails['releases'].append(prjDetail[0]["releases"])
                            prjDetails['domains'].append(prjDetail[0]["domain"])
                            for rel in prjDetail[0]["releases"]:
                                for cyc in rel['cycles']:
                                    prjDetails['cycles'][str(cyc['_id'])]=[str(cyc['_id']),rel['name'],cyc['name'],]


                res={'rows':prjDetails}
            else:
                app.logger.warn("Empty data received. getProjectIDs")
        except Exception as e:
            servicesException("getProjectIDs", e, True)
        return jsonify(res)

    @app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
    def updateScreenname_ICE():
        app.logger.debug("Inside updateScreenname_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            modifiedon=datetime.now()
            screenname = requestdata['screenname']
            projectid = requestdata['projectid']
            screenid = getScreenID(screenname,projectid)
            if(screenid==None):
                queryresult=dbsession.screens.insert_one({"name":requestdata['screenname'],"projectid":ObjectId(requestdata['projectid']),"versionnumber":requestdata['versionnumber'],"parent":[],"createdby":ObjectId(requestdata['createdby']),"createdon":modifiedon,"createdbyrole":ObjectId(requestdata['createdbyrole']),"modifiedby":ObjectId(requestdata['modifiedby']),"modifiedon":modifiedon,"modifiedbyrole":ObjectId(requestdata['modifiedbyrole']),"deleted":requestdata['deleted'],"createdthrough":requestdata['createdthrough'],"screenshot":requestdata['screenshot'],"scrapedurl":requestdata['scrapedurl']}).inserted_id
                result = createdataobjects(queryresult,requestdata)
            else:
                result = createdataobjects(screenid,requestdata)
            res={'rows':result}
        except Exception as e:
            servicesException("updateScreenname_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
    def updateTestcasename_ICE():
        app.logger.debug("Inside updateTestcasename_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                modifiedon=datetime.now()
                screenid = requestdata['screenid']
                testcasename = requestdata['testcasename']
                testcaseid = getTestcaseID(screenid,testcasename)
                if(testcaseid==None):
                    data1=requestdata['dataobjects']
                    data2=requestdata['steps']
                    for i in range(len(data1)):
                        for j in range(len(data2)):
                            if(data2[j]['custname']==data1[i]['custname']):
                                data2[j]['custname']=ObjectId(data1[i]['_id'])
                    queryresult=dbsession.testcases.insert_one({"name":requestdata['testcasename'],"screenid":ObjectId(requestdata['screenid']),"versionnumber":requestdata['versionnumber'],"createdby":ObjectId(requestdata['createdby']),"createdon":modifiedon,"createdbyrole":ObjectId(requestdata['createdbyrole']),"modifiedby":ObjectId(requestdata['modifiedby']),"modifiedon":modifiedon,"modifiedbyrole":ObjectId(requestdata['modifiedbyrole']),"deleted":requestdata['deleted'],"steps":data2,"parent":requestdata["parent"]})
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateTestcasename_ICE")
        except Exception as e:
            servicesException("updateTestcasename_ICE",e)
        return jsonify(res)


    # New API for getting Module Details.
    @app.route('/mindmap/getModules', methods=['POST'])
    def getModules():
        res = {'rows': 'fail'}
        try:
            requestdata = json.loads(request.data)
            tab = requestdata['tab']
            app.logger.debug("Inside getModules. Query: " +
                             str(requestdata["name"]))
            if "query" in requestdata and requestdata["query"]=="modLength":
                queryresult=list(dbsession.mindmaps.find({'projectid':ObjectId(requestdata["projectid"])}))
            if 'moduleid' in requestdata and requestdata['moduleid'] != None:
                moduleMap = []
                for modId in requestdata["moduleid"]:
                    if type(requestdata["moduleid"]) == str:
                        modId = requestdata["moduleid"]
                    mindmapdata = dbsession.mindmaps.find_one({"_id": ObjectId(modId)}, {
                                                            "testscenarios": 1, "_id": 1, "name": 1, "projectid": 1, "type": 1, "versionnumber": 1})
                    mindmaptype = mindmapdata["type"]
                    scenarioids = []
                    screenids = []
                    testcaseids = []
                    taskids = []
                    cycleid = requestdata['cycleid']
                    # Preparing data for fetching details of screens,testcases and scenarios
                    if "testscenarios" in mindmapdata:
                        for ts in mindmapdata["testscenarios"]:
                            if ts:
                                if "_id" in ts:
                                    if ts["_id"] not in scenarioids:
                                        scenarioids.append(ts["_id"])
                                    if "screens" in ts:
                                        for sc in ts["screens"]:
                                            if sc:                                     
                                                if sc["_id"] not in screenids:
                                                    screenids.append(sc["_id"])
                                                if "testcases" in sc:
                                                    for tc in sc["testcases"]:
                                                        if tc not in testcaseids:
                                                            testcaseids.append(tc)

                    # Preparing data for fetching tasks based on nodeid
                    taskids.extend(scenarioids)
                    taskids.extend(screenids)
                    taskids.extend(testcaseids)
                    taskids.append(ObjectId(modId))
                    taskdetails = list(dbsession.tasks.find(
                        {"nodeid": {"$in": taskids}}))

                    scenariodetails = list(dbsession.testscenarios.find(
                        {"_id": {"$in": scenarioids}}, {"_id": 1, "name": 1, "parent": 1}))
                    screendetails = list(dbsession.screens.find(
                        {"_id": {"$in": screenids}}, {"_id": 1, "name": 1, "parent": 1}))
                    testcasedetails = list(dbsession.testcases.find(
                        {"_id": {"$in": testcaseids}}, {"_id": 1, "name": 1, "parent": 1}))
                    moduledata = {}
                    scenariodata = {}
                    screendata = {}
                    testcasedata = {}
                
                    data_dict = {'testscenarios': scenariodata,
                                'screens': screendata,
                                'testcases': testcasedata,
                                'testsuites': moduledata}
                    assignTab = False
                    if tab == "tabAssign":
                        assignTab = True
                        for t in taskdetails:
                            if assignTab and (mindmaptype == "endtoend" or t['nodetype'] == "screens" or t['nodetype'] == "testcases" or cycleid == str(t['cycleid'])):
                                data_dict[t['nodetype']][t['nodeid']] = {'task': t}
                    else:
                        for t in taskdetails:
                            data_dict[t['nodetype']][t['nodeid']] = {
                                'taskexists': t}

                    for ts in scenariodetails:
                        if ts["_id"] in scenariodata:
                            scenariodata[ts["_id"]]['name'] = ts["name"]
                            app.logger.debug("Inside ts. Query: " +
                            str(ts["name"]))
                            scenariodata[ts["_id"]]['reuse'] = True if len(
                                ts["parent"]) > 1 else False
                        else:
                            scenariodata[ts["_id"]] = {
                                'name': ts["name"],
                                'reuse': True if len(ts["parent"]) > 1 else False
                            }

                    for sc in screendetails:
                        if sc["_id"] in screendata:
                            screendata[sc["_id"]]['name'] = sc["name"]
                            screendata[sc["_id"]]['reuse'] = True if len(
                                sc["parent"]) > 1 else False
                        else:
                            screendata[sc["_id"]] = {
                                "name": sc["name"],
                                "reuse": True if len(sc["parent"]) > 1 else False
                            }
                    for tc in testcasedetails:
                        if tc["_id"] in testcasedata:
                            testcasedata[tc["_id"]]['name'] = tc["name"]
                            testcasedata[tc["_id"]
                                        ]['reuse'] = True if tc["parent"] > 1 else False

                        else:
                            testcasedata[tc["_id"]] = {
                                "name": tc["name"],
                                "reuse": True if tc["parent"] > 1 else False
                            }
                    finaldata = {}
                    finaldata["name"] = mindmapdata["name"]
                    finaldata["_id"] = mindmapdata["_id"]
                    finaldata["projectID"] = mindmapdata["projectid"]
                    finaldata["type"] = "modules"
                    finaldata["childIndex"] = 0
                    finaldata["state"] = "saved"
                    finaldata["versionnumber"] = mindmapdata["versionnumber"]
                    finaldata["children"] = []
                    finaldata["completeFlow"] = True
                    finaldata["type"] = "modules" if mindmaptype == "basic" else "endtoend"
                    if mindmapdata["_id"] in moduledata and 'task' in moduledata[mindmapdata["_id"]] and moduledata[mindmapdata["_id"]]["task"]["status"] != 'complete':
                        finaldata["task"] = moduledata[mindmapdata["_id"]]["task"]
                    else:
                        finaldata["task"] = None
                    # finaldata["task"]=moduledata[mindmapdata["_id"]]["task"] if mindmapdata["_id"] in moduledata and 'task' in moduledata[mindmapdata["_id"]] else None
                    finaldata["taskexists"] = moduledata[mindmapdata["_id"]
                                                        ]["taskexists"] if mindmapdata["_id"] in moduledata and 'taskexists' in moduledata[mindmapdata["_id"]] else None

                    projectid = mindmapdata["projectid"]

                    # Preparing final data in format needed
                    if len(mindmapdata["testscenarios"]) == 0:
                        finaldata["completeFlow"] = False
                    i = 1                    
                    if "testscenarios" in mindmapdata:
                        for ts in mindmapdata["testscenarios"]:
                            if ts:
                                finalscenariodata = {}
                                finalscenariodata["projectID"] = projectid
                                finalscenariodata["_id"] = ts["_id"]
                                finalscenariodata["name"] = scenariodata[ts["_id"]]["name"]
                                finalscenariodata["type"] = "scenarios"
                                finalscenariodata["childIndex"] = i
                                finalscenariodata["children"] = []
                                finalscenariodata["state"] = "saved"
                                finalscenariodata["reuse"] = scenariodata[ts["_id"]]["reuse"]
                                if 'task' in scenariodata[ts["_id"]] and scenariodata[ts["_id"]]["task"]["status"] != "complete":
                                    finalscenariodata["task"] = scenariodata[ts["_id"]]['task']
                                else:
                                    finalscenariodata["task"] = None
                                finalscenariodata["taskexists"] = scenariodata[ts["_id"]]['taskexists'] if 'taskexists' in scenariodata[ts["_id"]
                                                                                                                                        ] and scenariodata[ts["_id"]]["taskexists"]["status"] != "complete" else None
                                i = i+1
                                if "screens" in ts:
                                    if len(ts["screens"]) == 0 and mindmaptype == "basic":
                                        finaldata["completeFlow"] = False
                                    j = 1 
                                    for sc in ts["screens"]:
                                        if sc:                                            
                                            finalscreendata = {}
                                            finalscreendata["projectID"] = projectid
                                            finalscreendata["_id"] = sc["_id"]
                                            finalscreendata["name"] = screendata[sc["_id"]]["name"]
                                            finalscreendata["type"] = "screens"
                                            finalscreendata["childIndex"] = j
                                            finalscreendata["children"] = []
                                            finalscreendata["reuse"] = screendata[sc["_id"]]["reuse"]
                                            finalscreendata["state"] = "saved"
                                            if 'task' in screendata[sc["_id"]] and screendata[sc["_id"]]['task']["status"] != "complete":
                                                finalscreendata["task"] = screendata[sc["_id"]]['task']
                                            else:
                                                finalscreendata["task"] = None
                                            finalscreendata["taskexists"] = screendata[sc["_id"]]['taskexists'] if 'taskexists' in screendata[sc["_id"]
                                                                                                                                            ] and screendata[sc["_id"]]["taskexists"]["status"] != "complete" else None
                                            j = j+1
                                            if "testcases" in sc:
                                                if len(sc["testcases"]) == 0 and mindmaptype == "basic":
                                                    finaldata["completeFlow"] = False
                                                k = 1
                                                for tc in sc["testcases"]:
                                                    if tc:                                                   
                                                        finaltestcasedata = {}
                                                        finaltestcasedata["projectID"] = projectid
                                                        finaltestcasedata["_id"] = tc
                                                        finaltestcasedata["name"] = testcasedata[tc]["name"]
                                                        finaltestcasedata["type"] = "testcases"
                                                        finaltestcasedata["childIndex"] = k
                                                        finaltestcasedata["children"] = []
                                                        finaltestcasedata["reuse"] = testcasedata[tc]["reuse"]
                                                        finaltestcasedata["state"] = "saved"
                                                        if 'task' in testcasedata[tc] and testcasedata[tc]['task']['status'] != 'complete':
                                                            finaltestcasedata["task"] = testcasedata[tc]['task']
                                                        else:
                                                            finaltestcasedata["task"] = None
                                                        finaltestcasedata["taskexists"] = testcasedata[tc]['taskexists'] if 'taskexists' in testcasedata[
                                                            tc] and testcasedata[tc]['taskexists']['status'] != 'complete' else None
                                                        k = k+1
                                                        finalscreendata["children"].append(
                                                            finaltestcasedata)
                                            finalscenariodata["children"].append(
                                                finalscreendata)
                                finaldata["children"].append(finalscenariodata)
                        moduleMap.append(finaldata)
                    res = {'rows': moduleMap if len(moduleMap)>1 else moduleMap[0]}
                    if type(requestdata["moduleid"]) == str:
                        break
            else:
                findquery = {"projectid": ObjectId(requestdata["projectid"])}
                if tab == "tabCreate":
                    findquery["type"] = "basic"
                queryresult = list(dbsession.mindmaps.find(
                    findquery, {"name": 1, "_id": 1, "type": 1}))
                res = {'rows': queryresult}
        except Exception as e:
            servicesException("getModules", e, True)
        return jsonify(res)


    @app.route('/plugins/getTasksJSON',methods=['POST'])
    def getTasksJSON():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getTasksJSON.")
            if not isemptyrequest(requestdata):
                userid=requestdata["userid"]
                tasks=list(dbsession.tasks.find({"assignedto":ObjectId(userid)}))
                res={'rows':tasks}
            else:
                app.logger.warn("Empty data received. getTasksJSON")
        except Exception as e:
            servicesException("getTasksJSON", e, True)
        return jsonify(res)

    @app.route('/plugins/updateAccessibilitySelection',methods=['POST'])
    def updateAccessibilitySelection():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateAccessibilitySelection.")
            if not isemptyrequest(requestdata):
                taskid=requestdata["taskId"]
                dbsession.tasks.update_one({"_id":ObjectId(taskid)},{'$set':{"accessibilityparameters":requestdata["accessibilityParameters"]}})
                res={'rows':"success"}
            else:
                app.logger.warn("Empty data received. updateAccessibilitySelection")
        except Exception as e:
            servicesException("updateAccessibilitySelection", e, True)
        return jsonify(res)

    @app.route('/mindmap/getScenarios',methods=['POST'])
    def getScenarios():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScenarios.")
            if not isemptyrequest(requestdata):
                moduleid=requestdata["moduleid"]
                moduledetails=list(dbsession.mindmaps.find({"_id":ObjectId(moduleid)},{"testscenarios":1}))
                scenarioids=[]
                for mod in moduledetails:
                    if "testscenarios" in mod:
                        for sce in mod["testscenarios"]:
                            scenarioids.append(ObjectId(sce["_id"]))
                scenarioslist=list(dbsession.testscenarios.find({"_id":{"$in":scenarioids}},{"name":1}))
                res={'rows':scenarioslist}
            else:
                app.logger.warn("Empty data received. getScenarios")
        except Exception as e:
            servicesException("getScenarios", e, True)
        return jsonify(res)

    # API to Save Data
    @app.route('/create_ice/saveMindmap',methods=['POST'])
    def saveMindmap():
        app.logger.debug("Inside saveMindmap")
        res={'rows':'fail','error':'Failed to save structure.'}
        try:
            requestdata=json.loads(request.data)
            requestdata=requestdata["data"]
            projectid=requestdata['projectid']
            createdby=requestdata['userid']
            createdbyrole=requestdata['userroleid']
            versionnumber=requestdata['versionnumber']
            createdthrough=requestdata['createdthrough']
            module_type="basic"
            error=checkReuse(requestdata)
            currentmoduleid=None
            if error is None:
                for moduledata in requestdata['testsuiteDetails']:
                    if moduledata["testsuiteId"] is None:
                        currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,module_type)
                    else:
                        if moduledata['state']=="renamed":
                            updateModuleName(moduledata['testsuiteName'],projectid,moduledata["testsuiteId"],createdby,createdbyrole)
                        currentmoduleid=moduledata['testsuiteId']
                    idsforModule=[]
                    for scenariodata in moduledata['testscenarioDetails']:
                        testcaseidsforscenario=[]
                        if scenariodata['testscenarioid'] is None:
                            currentscenarioid=saveTestScenario(projectid,scenariodata['testscenarioName'],versionnumber,createdby,createdbyrole,currentmoduleid)
                        else:
                            if scenariodata['state']=="renamed":
                                updateScenarioName(scenariodata['testscenarioName'],projectid,scenariodata['testscenarioid'],createdby,createdbyrole)
                            currentscenarioid=scenariodata['testscenarioid']
                        iddata1={"_id":ObjectId(currentscenarioid),"screens":[]}
                        for screendata in scenariodata['screenDetails']:
                            if screendata["screenid"] is None:
                                if "newreuse" in screendata:
                                    currentscreenid=getScreenID(screendata["screenName"],projectid)
                                    updateparent("screens",currentscreenid,currentscenarioid,"add")
                                else:
                                    currentscreenid=saveScreen(projectid,screendata["screenName"],versionnumber,createdby,createdbyrole,currentscenarioid)
                            else:
                                if screendata["state"]=="renamed":
                                    updateScreenName(screendata['screenName'],projectid,screendata['screenid'],createdby,createdbyrole)
                                currentscreenid=screendata["screenid"]
                                if "reuse" in screendata and screendata["reuse"]:
                                    updateScreenAndTestcase(currentscreenid,createdby,createdbyrole)
                                    updateparent("screens",currentscreenid,currentscenarioid,"add")
                            iddata2={"_id":ObjectId(currentscreenid),"testcases":[]}
                            for testcasedata in screendata['testcaseDetails']:
                                if testcasedata["testcaseid"] is None:
                                    if "newreuse" in testcasedata:
                                        currenttestcaseid=getTestcaseID(currentscreenid,testcasedata['testcaseName'])
                                        updateparent("testcases",currenttestcaseid,currentscreenid,"add")
                                    else:
                                        currenttestcaseid=saveTestcase(currentscreenid,testcasedata['testcaseName'],versionnumber,createdby,createdbyrole)
                                else:
                                    if testcasedata['state']=="renamed":
                                        updateTestcaseName(testcasedata['testcaseName'],projectid,testcasedata['testcaseid'],createdby,createdbyrole)
                                    currenttestcaseid=testcasedata['testcaseid']
                                    if "reuse" in testcasedata and testcasedata["reuse"]:
                                        updateparent("testcases",currenttestcaseid,currentscreenid,"add")
                                testcaseidsforscenario.append(ObjectId(currenttestcaseid))
                                iddata2["testcases"].append(ObjectId(currenttestcaseid))
                            iddata1["screens"].append(iddata2)
                        idsforModule.append(iddata1)
                        updateTestcaseIDsInScenario(currentscenarioid,testcaseidsforscenario)
                    updateTestScenariosInModule(currentmoduleid,idsforModule)
                scenarioInfo = []
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios":
                        scenarioName, parents = updateScenarioMindmap(node[0],node[2])
                        if parents:
                            scenarioInfo.append({"nodeid" : node[0], "scenarioName": scenarioName, "parents":parents })
                    else:
                        updateparent(node[1],node[0],node[2],"delete")
                if scenarioInfo:
                    res = {'rows' : {"currentmoduleid" : currentmoduleid , "scenarioInfo" :scenarioInfo}}
                else:
                    res={'rows':currentmoduleid}
            else:
                res={'rows':'reuseerror',"error":error}
        except Exception as e:
            servicesException("saveMindmap", e, True)
        return jsonify(res)

    def saveTestSuite(projectid,modulename,versionnumber,createdthrough,createdby,createdbyrole,moduletype,testscenarios=[]):
        app.logger.debug("Inside saveTestSuite.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":modulename,
        "versionnumber":versionnumber,
        "createdon":createdon,
        "createdthrough":createdthrough,
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole),
        "deleted":False,
        "modifiedby": ObjectId(createdby),
        "modifiedon": createdon,
        "modifiedbyrole": ObjectId(createdbyrole),
        "type": moduletype,
        "testscenarios":[]
        }
        queryresult=dbsession.mindmaps.insert_one(data).inserted_id
        return queryresult

    def saveTestScenario(projectid,testscenarioname,versionnumber,createdby,createdbyrole,moduleid,testcaseids=[]):
        app.logger.debug("Inside saveTestScenario.")
        createdon = datetime.now()
        data={
            "name":testscenarioname,
            "projectid":ObjectId(projectid),
            "parent":[ObjectId(moduleid)] ,
            "versionnumber":versionnumber,
            "createdby":ObjectId(createdby),
            "createdbyrole":ObjectId(createdbyrole),
            "createdon":createdon,
            "deleted":False,
            "modifiedby":ObjectId(createdby),
            "modifiedbyrole":ObjectId(createdbyrole),
            "modifiedon":createdon,
            "testcaseids":testcaseids
        }
        queryresult=dbsession.testscenarios.insert_one(data).inserted_id
        return queryresult

    def saveScreen(projectid,screenname,versionnumber,createdby,createdbyrole,scenarioid):
        app.logger.debug("Inside saveScreen.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":screenname,
        "versionnumber":versionnumber,
        "parent":[ObjectId(scenarioid)], 
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole),
        "createdon":createdon,
        "deleted":False,
        "modifiedby":ObjectId(createdby),
        "modifiedbyrole":ObjectId(createdbyrole),
        "modifiedon":createdon,
        "screenshot":"",
        "scrapedurl":""
        }
        queryresult=dbsession.screens.insert_one(data).inserted_id
        return queryresult

    def saveTestcase(screenid,testcasename,versionnumber,createdby,createdbyrole):
        app.logger.debug("Inside saveTestcase.")
        createdon = datetime.now()
        data={
            "screenid": ObjectId(screenid),
            "name":testcasename,
            "versionnumber":versionnumber,
            "createdby": ObjectId(createdby),
            "createdbyrole": ObjectId(createdbyrole),
            "createdon": createdon,
            "modifiedby": ObjectId(createdby),
            "modifiedbyrole": ObjectId(createdbyrole),
            "modifiedon":createdon,
            "steps":[],
            "parent":1,
            "deleted":False
        }
        queryresult=dbsession.testcases.insert_one(data).inserted_id
        return queryresult



    # API to Save Data of Genius
    @app.route('/create_ice/saveGeniusMindmap',methods=['POST'])
    def saveGeniusMindmap():
        app.logger.debug("Inside saveGeniusMindmap")
        res={'rows':'fail','error':'Failed to save structure.'}
        try:
            requestdata=json.loads(request.data)
            requestdata=requestdata["data"]
            projectid=requestdata['projectid']
            # testcasename = "Tc_"+projectid
            createdby=requestdata['userid']
            createdbyrole=requestdata['userroleid']
            versionnumber=requestdata['versionnumber']
            createdthrough=requestdata['createdthrough']
            module_type="basic"
            error=checkReuse(requestdata)
            currentmoduleid=None
            if error is None:
                for moduledata in requestdata['testsuiteDetails']:
                    if moduledata["testsuiteId"] is None:
                        currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,module_type)
                    else:
                        if moduledata['state']=="renamed":
                            updateModuleName(moduledata['testsuiteName'],projectid,moduledata["testsuiteId"],createdby,createdbyrole)
                        currentmoduleid=moduledata['testsuiteId']
                    idsforModule=[]
                    for scenariodata in moduledata['testscenarioDetails']:
                        testcaseidsforscenario=[]
                        if scenariodata['testscenarioid'] is None:
                            currentscenarioid=saveTestScenario(projectid,scenariodata['testscenarioName'],versionnumber,createdby,createdbyrole,currentmoduleid)
                        else:
                            if scenariodata['state']=="renamed":
                                updateScenarioName(scenariodata['testscenarioName'],projectid,scenariodata['testscenarioid'],createdby,createdbyrole)
                            currentscenarioid=scenariodata['testscenarioid']
                        iddata1={"_id":ObjectId(currentscenarioid),"screens":[]}
                        for screendata in scenariodata['screenDetails']:
                            if screendata["screenid"] is None:
                                if "newreuse" in screendata:
                                    currentscreenid=getScreenID(screendata["screenName"],projectid)
                                    updateparent("screens",currentscreenid,currentscenarioid,"add")
                                else:
                                    currentscreenid=saveScreen(projectid,screendata["screenName"],versionnumber,createdby,createdbyrole,currentscenarioid)
                            else:
                                if screendata["state"]=="renamed":
                                    updateScreenName(screendata['screenName'],projectid,screendata['screenid'],createdby,createdbyrole)
                                currentscreenid=screendata["screenid"]
                                if "reuse" in screendata and screendata["reuse"]:
                                    updateScreenAndTestcase(currentscreenid,createdby,createdbyrole)
                                    updateparent("screens",currentscreenid,currentscenarioid,"add")
                            iddata2={"_id":ObjectId(currentscreenid),"testcases":[]}
                            for testcasedata in screendata['testcaseDetails']:
                                if testcasedata["testcaseid"] is None:
                                    if "newreuse" in testcasedata:
                                        currenttestcaseid=getTestcaseID(currentscreenid,testcasedata['testcaseName'])
                                        updateparent("testcases",currenttestcaseid,currentscreenid,"add")
                                    else:
                                        currenttestcaseid=saveTestcase(currentscreenid,testcasedata['testcaseName'],versionnumber,createdby,createdbyrole)
                                else:
                                    if testcasedata['state']=="renamed":
                                        updateTestcaseName(testcasedata['testcaseName'],projectid,testcasedata['testcaseid'],createdby,createdbyrole)
                                    currenttestcaseid=testcasedata['testcaseid']
                                    if "reuse" in testcasedata and testcasedata["reuse"]:
                                        updateparent("testcases",currenttestcaseid,currentscreenid,"add")
                                testcaseidsforscenario.append(ObjectId(currenttestcaseid))
                                iddata2["testcases"].append(ObjectId(currenttestcaseid))
                            iddata1["screens"].append(iddata2)
                        idsforModule.append(iddata1)
                        updateTestcaseIDsInScenario(currentscenarioid,testcaseidsforscenario)
                    updateTestScenariosInModule(currentmoduleid,idsforModule)
                scenarioInfo = []
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios":
                        scenarioName, parents = updateScenarioMindmap(node[0],node[2])
                        if parents:
                            scenarioInfo.append({"nodeid" : node[0], "scenarioName": scenarioName, "parents":parents })
                    else:
                        updateparent(node[1],node[0],node[2],"delete")
                if scenarioInfo:
                    res = {'rows' : {"currentmoduleid" : currentmoduleid , "scenarioInfo" :scenarioInfo}}
                else:
                    res={'rows':currentmoduleid}
            else:
                res={'rows':'reuseerror',"error":error}
        except Exception as e:
            servicesException("saveGeniusMindmap", e, True)
        return jsonify(res)

    def saveTestSuite(projectid,modulename,versionnumber,createdthrough,createdby,createdbyrole,moduletype,testscenarios=[]):
        app.logger.debug("Inside saveTestSuite.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":modulename,
        "versionnumber":versionnumber,
        "createdon":createdon,
        "createdthrough":createdthrough,
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole),
        "deleted":False,
        "modifiedby": ObjectId(createdby),
        "modifiedon": createdon,
        "modifiedbyrole": ObjectId(createdbyrole),
        "type": moduletype,
        "testscenarios":[]
        }
        queryresult=dbsession.mindmaps.insert_one(data).inserted_id
        return queryresult

    def saveTestScenario(projectid,testscenarioname,versionnumber,createdby,createdbyrole,moduleid,testcaseids=[]):
        app.logger.debug("Inside saveTestScenario.")
        createdon = datetime.now()
        data={
            "name":testscenarioname,
            "projectid":ObjectId(projectid),
            "parent":[ObjectId(moduleid)] ,
            "versionnumber":versionnumber,
            "createdby":ObjectId(createdby),
            "createdbyrole":ObjectId(createdbyrole),
            "createdon":createdon,
            "deleted":False,
            "modifiedby":ObjectId(createdby),
            "modifiedbyrole":ObjectId(createdbyrole),
            "modifiedon":createdon,
            "testcaseids":testcaseids
        }
        queryresult=dbsession.testscenarios.insert_one(data).inserted_id
        return queryresult

    def saveScreen(projectid,screenname,versionnumber,createdby,createdbyrole,scenarioid):
        app.logger.debug("Inside saveScreen.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":screenname,
        "versionnumber":versionnumber,
        "parent":[ObjectId(scenarioid)], 
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole),
        "createdon":createdon,
        "deleted":False,
        "modifiedby":ObjectId(createdby),
        "modifiedbyrole":ObjectId(createdbyrole),
        "modifiedon":createdon,
        "screenshot":"",
        "scrapedurl":""
        }
        queryresult=dbsession.screens.insert_one(data).inserted_id
        return queryresult

    def saveTestcase(screenid,testcasename,versionnumber,createdby,createdbyrole):
        app.logger.debug("Inside saveTestcase.")
        createdon = datetime.now()
        data={
            "screenid": ObjectId(screenid),
            "name":testcasename,
            "versionnumber":versionnumber,
            "createdby": ObjectId(createdby),
            "createdbyrole": ObjectId(createdbyrole),
            "createdon": createdon,
            "modifiedby": ObjectId(createdby),
            "modifiedbyrole": ObjectId(createdbyrole),
            "modifiedon":createdon,
            "steps":[],
            "parent":1,
            "deleted":False
        }
        queryresult=dbsession.testcases.insert_one(data).inserted_id
        return queryresult

    @app.route('/mindmap/manageTask',methods=['POST'])
    def manageTaskDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action=requestdata["action"]
            del requestdata["action"]
            if not isemptyrequest(requestdata):

                if action == "modify":
                    tasks_update=requestdata["update"]
                    tasks_remove=requestdata["delete"]
                    for i in tasks_update:
                        i["assignedtime"]=datetime.now()
                        if i['startdate'].find('-') > -1:
                            i["startdate"]=datetime.strptime(i["startdate"],"%d-%m-%Y")
                        if i['enddate'].find('-') > -1:
                            i["enddate"]=datetime.strptime(i["enddate"],"%d-%m-%Y")
                        dbsession.tasks.update({"_id":ObjectId(i["_id"]),"cycleid":ObjectId(i["cycleid"])},{"$set":{"assignedtime":i["assignedtime"],"startdate":i["startdate"],"enddate":i["enddate"],"assignedto":ObjectId(i["assignedto"]),"reviewer":ObjectId(i["reviewer"]),"status":i["status"],"reestimation":i["reestimation"],"complexity":i["complexity"],"history":i["history"],"details":i["details"]}})
                    tasks_insert=requestdata["insert"]
                    for i in tasks_insert:
                        i["startdate"]=datetime.strptime(i["startdate"],"%d-%m-%Y")
                        i["enddate"]=datetime.strptime(i["enddate"],"%d-%m-%Y")
                        i["assignedtime"]=datetime.now()
                        i["createdon"]=datetime.now()
                        i["owner"]=ObjectId(i["owner"])
                        i['cycleid']=ObjectId(i["cycleid"])
                        i["assignedto"]=ObjectId(i["assignedto"])
                        i["nodeid"]=ObjectId(i["nodeid"])
                        i['rules'] = []
                        if i["parent"] != "":
                            i["parent"]=ObjectId(i["parent"])
                        i["reviewer"]=ObjectId(i["reviewer"])
                        i["projectid"]=ObjectId(i["projectid"])
                        if i['details']=='':
                            i['details']=i['tasktype']+" "+i['nodetype']+" "+i['name']
                    if len(tasks_insert)>0:
                        dbsession.tasks.insert_many(tasks_insert)
                    if len(tasks_remove)>0:
                        tasks_remove=[ObjectId(t) for t in tasks_remove]
                        dbsession.tasks.delete_many({"_id":{"$in":tasks_remove}})
                    res={"rows":"success"}
                elif action=="updatestatus":
                    status=requestdata['status']
                    dbsession.tasks.update({"_id":ObjectId(requestdata["id"])},{"$set":{"status":status}})
                    res={"rows":"success"}
                elif action=="updatetaskstatus":  
                    task=dbsession.tasks.find_one({"_id":ObjectId(requestdata["id"])})
                    history=[]
                    status=assignedto=owner=reviewer=''
                    if requestdata["status"] == "underReview":
                        status="complete"
                        assignedto=''
                        owner=task["owner"]
                        reviewer=task["reviewer"]
                        # dbsession.tasks.update({"_id":ObjectId(requestdata["id"])},{"$set":{"status":status,"history":history,"assignedto":''}})
                    elif (requestdata["status"] == "inprogress" or requestdata["status"] == "assigned" or requestdata["status"] == "reassigned") and task['reviewer'] != "select reviewer":
                        status="underReview"
                        assignedto=task["reviewer"]
                        owner=task["owner"]
                        reviewer=task["reviewer"]
                        # dbsession.tasks.update({"_id":ObjectId(requestdata["id"])},{"$set":{"status":status,"history":history,"assignedto":task["reviewer"]}})
                    elif (requestdata["status"] == "reassign"):
                        status="reassigned"
                        assignedto=task["owner"]
                        owner=task["owner"]
                        reviewer=task["reviewer"]
                    requestdata["history"]["status"]=status
                    if(len(task["history"])==0):
                        requestdata["history"]["userid"]=ObjectId(requestdata["history"]["userid"])
                        history=[requestdata["history"]]
                    else:
                        history=task["history"]
                        requestdata["history"]["userid"]=ObjectId(requestdata["history"]["userid"])
                        history.append(requestdata["history"])
                    dbsession.tasks.update({"_id":ObjectId(requestdata["id"])},{"$set":{"status":status,"history":history,"assignedto":assignedto,"owner":owner,"reviewer":reviewer}})
                    res={"rows":"success"}
                elif action == "delete":
                    dbsession.tasks.delete({"_id":ObjectId(requestdata["id"]),"cycle":ObjectId(requestdata["cycleid"])})
                    res={"rows":"success"}
            else:
                app.logger.warn('Empty data received. manage users.')
        except Exception as e:
            servicesException("manageTaskDetails", e, True)
        return jsonify(res)

    def checkReuse(requestdata):
        scenarionames=set()
        # screennameset=set()
        screen_testcase={}
        error=None
        projectid=projectid=requestdata['projectid']
        for moduledata in requestdata['testsuiteDetails']:
            if moduledata['testsuiteId'] is None:
                # If the the Module does not have an ID then we will check if the target name has conflict.
                if checkModuleNameExists(moduledata["testsuiteName"],projectid):
                    error="A project cannot have similar module name"
                    break
                else:
                    moduledata['state']="renamed"
            else:
                # If the the Module has an ID then we will check if the target name has conflict if not then rename will be allowed.
                name=getModuleName(moduledata['testsuiteId'])
                if name!=moduledata["testsuiteName"]:
                    if checkModuleNameExists(moduledata["testsuiteName"],projectid):
                        error="Module cannot be renamed to an existing module name"
                        break
                    else:
                        moduledata['state']="renamed"
            for scenariodata in moduledata['testscenarioDetails']:
                # This check for similar scenario name within the same module.
                if scenariodata['testscenarioName'] in scenarionames:
                    error="A project cannot have similar scenario names: "+scenariodata['testscenarioName']
                    break
                else:
                    scenarionames.add(scenariodata['testscenarioName'])

                # If the the Scenario does not have an ID then we will check if the target name has conflict.
                if scenariodata['testscenarioid'] is None:
                    if checkScenarioNameExists(projectid,scenariodata['testscenarioName']):
                        error="A project cannot have similar scenario names: change "+scenariodata['testscenarioName']+" name"
                        break
                else:
                    # If the the Scenario has an ID then we will check if the target name has conflict if not then rename will be allowed.
                    scenarioname=getScenarioName(scenariodata['testscenarioid'])
                    if scenarioname!=scenariodata['testscenarioName']:
                        if checkScenarioNameExists(projectid,scenariodata['testscenarioName']):
                            error="A project cannot have similar scenario names: change "+scenariodata['testscenarioName']+" name"
                            break
                        else:
                            scenariodata['state']="renamed"
                for screendata in scenariodata['screenDetails']:
                    
                    if screendata["screenid"] is None:
                        # If ScreenID is none then we will check if a screen with that name exists then we will give this screen the ID of the existing screen else it will be None only.
                        screendata["screenid"]=getScreenID(screendata["screenName"],projectid)
                        if screendata["screenid"] is not None:
                            screendata["reuse"]=True
                        elif screendata["screenName"] in screen_testcase:
                            screendata["newreuse"]=True
                        else:
                            screendata["reuse"]=False
                    else:
                        screenname = getScreenName(screendata["screenid"])
                        if screenname != screendata["screenName"]:
                            if checkScreenNameExists(screendata["screenName"], projectid):
                                error = "Cannot rename screen to an existing screen name: " + screendata["screenName"]
                                break
                            else:
                                screendata['state']="renamed"
                    if screendata["screenName"] not in screen_testcase:
                        screen_testcase[screendata["screenName"]]=set()
                        for testcasedata in screendata['testcaseDetails']:
                            if testcasedata["testcaseName"] not in screen_testcase[screendata["screenName"]]:
                                screen_testcase[screendata["screenName"]].add(testcasedata["testcaseName"])
                            else:
                                testcasedata["newreuse"]=True
                    else:
                        for testcasedata in screendata['testcaseDetails']:
                            if testcasedata["testcaseName"] not in screen_testcase[screendata["screenName"]]:
                                screen_testcase[screendata["screenName"]].add(testcasedata["testcaseName"])
                            else:
                                testcasedata["newreuse"]=True
                    # Checking of Reuse in Testcases is done only when the screen has a valid ID.

                    if screendata["screenid"] is not None:
                        for testcasedata in screendata['testcaseDetails']:
                            if testcasedata['testcaseid'] is None:
                                testcasedata['testcaseid']=getTestcaseID(screendata["screenid"],testcasedata["testcaseName"])
                                if testcasedata["testcaseid"] is not None:
                                    testcasedata["reuse"]=True
                                else:
                                    testcasedata["reuse"]=False
                            else:
                                testcasename=getTestcaseName(testcasedata['testcaseid'])
                                if testcasename!= testcasedata["testcaseName"]:
                                    testcaseid=getTestcaseID(screendata["screenid"],testcasedata["testcaseName"])
                                    if testcaseid is not None:
                                        updateparent('testcases',testcasedata['testcaseid'],screendata["screenid"],'delete')
                                        testcasedata['testcaseid']=testcaseid
                                        testcasedata["reuse"]=True
                                    else:
                                        testcasedata["state"]="renamed"
                                        testcasedata["reuse"]=False
        if error is None:
            return None
        else:
            return error

    def checkModuleNameExists(name,projectid):
        res=list(dbsession.mindmaps.find({"projectid":ObjectId(projectid),"name":name},{"_id":1}))
        if len(res)>0:
            return True
        else:
            return False

    def checkScreenNameExists(name,projectid):
        res = list(dbsession.screens.find({"projectid": ObjectId(projectid), "name": name}, {"_id": 1}))
        if len(res) > 0:
            return True
        else:
            return False
    @app.route('/mindmap/deleteScenarioETE',methods=['POST'])
    def deleteScenarioETE():
        app.logger.debug("Inside deleteScenarioETE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            scenarioid = requestdata['scenarioIds'][0]
            parentid=requestdata['parentIds'][0]
            module=list(dbsession.mindmaps.find({'_id': ObjectId(parentid)}))
            for module in  module:
                tempModule=module
                testscenarios=[]
                for scenario in tempModule['testscenarios']:
                    tempScenario=scenario
                    if "_id" in tempScenario:
                        if scenario["_id"]==ObjectId(scenarioid):                           
                            testscenarioparent=list(dbsession.testscenarios.find({'_id':tempScenario["_id"]},{"parent":1}))
                            for testscenarioparent in testscenarioparent:
                                temptestscenarioparent=testscenarioparent
                                parentList=[]
                                for parent in temptestscenarioparent['parent']:
                                    try:
                                       temptestscenarioparent['parent'].remove(tempModule['_id'])
                                       break
                                    except:
                                        pass                             
                                parentList.append(temptestscenarioparent['parent'])
                                parentLists=parentList[0]
                                dbsession.testscenarios.update_many({'_id':tempScenario["_id"]},{'$set' : {'parent':parentLists}})                               
                            del tempScenario["_id"]
                            break                                            
                testscenarios.append(tempModule['testscenarios'])
                testscenarios= testscenarios[0]                   
                dbsession.mindmaps.update_one({'_id' : tempModule['_id']},  {'$set' : {'testscenarios':testscenarios}})             
                res= {'rows' : 'success'}
        except Exception as e:
            servicesException("deleteScenarioETE", e, True)
        return jsonify(res)           
   

    @app.route('/mindmap/deleteScenario',methods=['POST'])
    def deleteScenario():
        app.logger.debug("Inside deleteScenario")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            scenarioids = requestdata['scenarioIds']
            testcaseids=requestdata['testcaseIds']
            screenids=requestdata['screenIds']
            if len(scenarioids)>0:
                for screenid in screenids:
                    screenObjects=list(dbsession.screens.find({"_id":ObjectId(screenid)},{"parent":1}))
                    if len(screenObjects)==0:
                        continue
                    screenlist = screenObjects[0]['parent']
                    parentScreens = list(dbsession.mindmaps.find({'testscenarios._id'  : {'$in':screenlist}}))                                
                    for mod in parentScreens:                                                                               
                        testscenarios1=[]
                        tempModule1=mod
                        for scen in tempModule1['testscenarios']:
                            tempScenario1=scen
                            if len(tempScenario1)>0:
                                if tempScenario1["screens"]:
                                    for scrn in tempScenario1["screens"]:
                                        if "_id" in scrn:
                                            if scrn["_id"]==ObjectId(screenid):
                                                dataObjects=list(dbsession.dataobjects.find({"parent":ObjectId(screenid)},{"parent":1}))
                                                if len(dataObjects)==0:
                                                   del scrn["_id"]                                                   
                                                else:                                                    
                                                    dataObjectslist = dataObjects[0]['parent']
                                                    if len(dataObjectslist)==1:
                                                        dbsession.dataobjects.delete_many({'parent':ObjectId(screenid)})
                                                    else:
                                                        dbsession.dataobjects.update_many({'parent':ObjectId(screenid)},{"$pull": {"parent": ObjectId(screenid)}})
                                                    del scrn["_id"]
                                                dbsession.screens.delete_many({'_id': ObjectId(screenid)})                                                
                                                if "testcases" in scrn:
                                                    for testcase in scrn["testcases"]:
                                                        dbsession.testcases.delete_many({'_id': testcase})
                                                        dbsession.testscenarios.update_many({'_id':scen["_id"]},{"$pull": {"testcaseids": testcase}})
                                                    del scrn["testcases"]                                        
                        testscenarios1.append(tempModule1['testscenarios']) 
                        testscenario1= testscenarios1[0]                               
                        dbsession.mindmaps.update_one({'_id' : tempModule1['_id']},  {'$set' : {'testscenarios':testscenario1}})
                for scenarioid in scenarioids:
                # finding the parent list of the scenario
                    scenarioObjects=list(dbsession.testscenarios.find({"_id":ObjectId(scenarioid)},{"parent":1}))
                    if len(scenarioObjects)==0:
                        continue
                    parentlist = scenarioObjects[0]['parent']
                    parentModules = list(dbsession.mindmaps.find({'_id' : {'$in':parentlist}}))                                        
                    for module in parentModules:
                        testscenarios=[]
                        tempmodule=module
                        if  len(tempmodule['testscenarios'])>0:                      
                            for scenario in tempmodule['testscenarios']:
                                if "_id" in  scenario:           
                                    if scenario["_id"]==ObjectId(scenarioid):
                                        del scenario["_id"]                                                                
                                        del scenario["screens"]                                                                   
                        testscenarios.append(tempmodule['testscenarios'])
                        testscenario=testscenarios[0]                    
                        dbsession.mindmaps.update_one({'_id' : tempmodule['_id']},  {'$set' : {'testscenarios':testscenario}})
                        dbsession.testsuites.update_one({'name':tempmodule['name']},{"$pull": {"testscenarioids":ObjectId(scenarioid)}})
                    
                
                dbsession.testscenarios.delete_many({'_id': ObjectId(scenarioid)})
                for screenid in screenids:
                    dbsession.screens.delete_many({'_id': ObjectId(screenid)})
                for testcaseid in testcaseids:
                    dbsession.testcases.delete_many({'_id': ObjectId(testcaseid)}) 


            elif len(screenids)>0:
                    for screenid in screenids:
                
                        screenObjects=list(dbsession.screens.find({"_id":ObjectId(screenid)},{"parent":1}))
                        if len(screenObjects)==0:
                            continue
                        screenlist = screenObjects[0]['parent']
                        parentModules = list(dbsession.mindmaps.find({'testscenarios._id'  : {'$in':screenlist}}))
                        
                
                        for module in parentModules:
                            testscenarios=[]
                            tempModule=module
                            for scenario in tempModule['testscenarios']:
                                tempScenario=scenario
                                if len(scenario)>0:
                                    for screen in tempScenario["screens"]:
                                        if "_id" in screen:
                                            if screen["_id"]==ObjectId(screenid):
                                                dataObjects=list(dbsession.dataobjects.find({"parent":ObjectId(screenid)},{"parent":1}))
                                                if len(dataObjects)==0:
                                                   del screen["_id"]                                                                                                     
                                                else:
                                                    dataObjectslist = dataObjects[0]['parent']
                                                    if len(dataObjectslist)==1:
                                                        dbsession.dataobjects.delete_many({'parent':ObjectId(screenid)})
                                                    else:
                                                        dbsession.dataobjects.update_many({'parent':ObjectId(screenid)},{"$pull": {"parent":ObjectId(screenid)}})
                                                    del screen["_id"]
                                                if "testcases" in screen:
                                                    for testcase in screen["testcases"]:
                                                        dbsession.testcases.delete_many({'_id': testcase})
                                                        dbsession.testscenarios.update_many({'_id':scenario["_id"]},{"$pull": {"testcaseids": testcase}})
                                                    del screen["testcases"]                                            
                            testscenarios.append(tempModule['testscenarios'])
                            testscenario=testscenarios[0]
                            dbsession.mindmaps.update_one({'_id' : tempModule['_id']},  {'$set' : {'testscenarios':testscenario}})
                    dbsession.screens.delete_many({'_id': ObjectId(screenid)})
                    for testcaseid in testcaseids:
                        dbsession.testcases.delete_many({'_id': ObjectId(testcaseid)}) 
                                                      


            elif len(testcaseids)>0:
                
                for testcaseid in testcaseids:
                    # finding the parent list of the scenario
                            testcaseObjects=list(dbsession.testcases.find({"_id":ObjectId(testcaseid)},{"screenid":1}))
                            if len(testcaseObjects)==0:
                                continue
                            testcaseslist = []
                            testcaseslist.append(testcaseObjects[0]['screenid'])
                            parentTestcases = list(dbsession.mindmaps.find({'testscenarios.screens._id'  : {'$in':testcaseslist}}))
                            for module in parentTestcases:
                                testscenarios=[]
                                for scenario in module['testscenarios']:  
                                    tempScenario=scenario 
                                    dbsession.testscenarios.update_many({'_id':scenario["_id"]},{"$pull": {"testcaseids": ObjectId(testcaseid)}})
                                    for screen in tempScenario["screens"]:
                                        try:
                                             screen["testcases"].remove(ObjectId(testcaseid))
                                        except:
                                            pass

                                    testscenarios.append(tempScenario)
                                dbsession.mindmaps.update_one({'_id' : module['_id']},  {'$set' : {'testscenarios':testscenarios}})
                dbsession.testcases.delete_many({'_id': ObjectId(testcaseid)}) 
            res= {'rows' : 'success'}
        except Exception as e:
            servicesException("deleteScenario", e, True)
        return jsonify(res)


    def updateScenarioMindmap(scenarioid,parentid):
        scenarioList=list(dbsession.testscenarios.find({"_id":ObjectId(scenarioid)}))
        if len(scenarioList) == 0:
            return "",[]
        oldParentList=scenarioList[0]['parent']
        newParentList=[]
        if len(oldParentList) == 1 and ObjectId(parentid) in oldParentList:
            dbsession.testscenarios.delete_many({'_id' : ObjectId(scenarioid)})
            return "",[]
        else:
            # delete this parent and send all other parents names back
            flag=False
            for pid in oldParentList:
                if flag or str(pid)!=parentid:
                    newParentList.append(pid)
                else:
                    flag=True
            dbsession.testscenarios.update_one({'_id':ObjectId(scenarioid)},{'$set':{'parent':newParentList}})
            parentsNameList=[]
            #finding the name of the parent Modules
            pNameObject = list(dbsession.mindmaps.find({'_id' : {'$in':newParentList}}, {'name':1}))
            for pName in pNameObject:
                parentsNameList.append(pName['name'])
            return scenarioList[0]['name'], parentsNameList

    def updateScenarioMindmapETE(scenarioid,parentid):
        scenarioList=list(dbsession.testscenarios.find({"_id":ObjectId(scenarioid)},{"parent":1}))
        if len(scenarioList) == 0:
            return
        oldParentList=scenarioList[0]['parent']
        if len(oldParentList) == 1 and ObjectId(parentid) in oldParentList:
            dbsession.testscenarios.delete_many({'_id' : ObjectId(scenarioid)})
        else:
            newParentList=[]
            flag=False
            for pid in oldParentList:
                if flag or str(pid)!=parentid:
                    newParentList.append(pid)
                else:
                    flag=True
            dbsession.testscenarios.update_one({'_id':ObjectId(scenarioid)},{'$set':{'parent':newParentList}})
    
    def updateparent(type,nodeid,parentid,action):
        if action=="add":
            if type=="scenarios":
                parentlist=list(dbsession.testscenarios.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist.append(ObjectId(parentid))
                dbsession.testscenarios.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
            elif type=="screens":
                parentlist=list(dbsession.screens.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist.append(ObjectId(parentid))
                dbsession.screens.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
            elif type=="testcases":
                parentlist=list(dbsession.testcases.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist+=1
                dbsession.testcases.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
        elif action=="delete":
            if type=="scenarios":
                parentlist=list(dbsession.testscenarios.find({"_id":ObjectId(nodeid)},{"parent":1}))
                oldparentlist=parentlist[0]['parent']
                newparentlist=[]
                flag=False
                for pid in oldparentlist:
                    if flag or str(pid)!=parentid:
                        newparentlist.append(pid)
                    else:
                        flag=True
                dbsession.testscenarios.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':newparentlist}})
            elif type=="screens":
                parentlist=list(dbsession.screens.find({"_id":ObjectId(nodeid)},{"parent":1}))
                oldparentlist=parentlist[0]['parent']
                newparentlist=[]
                flag=False
                for pid in oldparentlist:
                    if flag or str(pid)!=parentid:
                        newparentlist.append(pid)
                    else:
                        flag=True
                dbsession.screens.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':newparentlist}})
            elif type=="testcases":
                parentlist=list(dbsession.testcases.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist-=1
                dbsession.testcases.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})

        
    def updateTestcaseIDsInScenario(currentscenarioid,testcaseidsforscenario):
        dbsession.testscenarios.update_one({'_id':ObjectId(currentscenarioid)},{'$set':{'testcaseids':testcaseidsforscenario}})
        return

    def updateTestScenariosInModule(currentmoduleid,idsforModule):
        dbsession.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':idsforModule}})
        return

    def updateScreenAndTestcase(screenid,createdby,createdbyrole):
        createdon = datetime.now()
        dbsession.screens.update_one({"_id":ObjectId(screenid)},{'$set':{"createdby":ObjectId(createdby),"createdbyrole":ObjectId(createdbyrole),"createdon":createdon,"modifiedby":ObjectId(createdby),"modifiedbyrole":ObjectId(createdbyrole),"modifiedon":createdon}})
        dbsession.testcases.update_one({"screenid":ObjectId(screenid)},{'$set':{"createdby":ObjectId(createdby),"createdbyrole":ObjectId(createdbyrole),"createdon":createdon,"modifiedby":ObjectId(createdby),"modifiedbyrole":ObjectId(createdbyrole),"modifiedon":createdon}})
        return

    @app.route('/mindmap/getScreens',methods=['POST'])
    def getScreens():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScreens.")
            if not isemptyrequest(requestdata):
                projectid=ObjectId(requestdata["projectid"])
                screendetails=list(dbsession.screens.find({"projectid":projectid},{"_id":1,"name":1,"parent":1}))
                screenids = [scr["_id"] for scr in screendetails]
                testcasedetails=list(dbsession.testcases.find({"screenid":{"$in":screenids}},{"_id":1,"name":1,"parent":1,"screenid":1}))
                res={'rows':{'screenList':screendetails,'testCaseList':testcasedetails}}
            else:
                app.logger.warn("Empty data received. getScreens")
        except Exception as e:
            servicesException("getScreens", e, True)
        return jsonify(res)

    def checkScenarioNameExists(projectid,name):
        res=list(dbsession.testscenarios.find({"projectid":ObjectId(projectid),"name":name},{"_id":1}))
        if len(res)>0:
            return True
        else:
            return False

    @app.route('/create_ice/saveMindmapE2E',methods=['POST'])
    def saveMindmapEndtoEnd():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            requestdata=requestdata["data"]
            app.logger.debug("Inside saveMindmapE2E.")
            if not isemptyrequest(requestdata):
                projectid=requestdata['projectid']

                userid=requestdata['userid']
                userroleid=requestdata['userroleid']
                versionnumber=requestdata['versionnumber']
                createdthrough=requestdata['createdthrough']
                type="endtoend"

                scenarioids=[]
                error=None
                currentmoduleid=None
                for moduledata in requestdata['testsuiteDetails']:
                    if moduledata['testsuiteId'] is None:
                        if( checkModuleNameExists(moduledata["testsuiteName"],projectid) ):
                            error="Module name cannot be reused"
                            break
                        else:
                            currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,userid,userroleid,type)
                    else:
                        oldModulename=getModuleName(moduledata['testsuiteId'])
                        if oldModulename!=moduledata["testsuiteName"]:
                            if( checkModuleNameExists(moduledata["testsuiteName"],projectid) ):
                                error="Module name cannot be reused"
                                break
                            else:
                                updateModuleName(moduledata["testsuiteName"],projectid,moduledata['testsuiteId'],userid,userroleid)
                        currentmoduleid=moduledata['testsuiteId']
                    for scenariodata in moduledata['testscenarioDetails']:
                        if scenariodata["state"]=="created":
                            if( checkScenarioIDexists(scenariodata["testscenarioName"],scenariodata["testscenarioid"]) ):
                                scenarioids.append({"_id":ObjectId(scenariodata["testscenarioid"]),"screens":[]})
                                updateparent("scenarios",scenariodata["testscenarioid"],currentmoduleid,"add")
                            else:
                                error="fail"
                                break
                        else:
                            scenarioids.append({"_id":ObjectId(scenariodata["testscenarioid"]),"screens":[]})
                if currentmoduleid is not None:
                    updateTestScenariosInModule(currentmoduleid,scenarioids)
                    # dbsession.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':scenarioids}})
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios" :
                        updateScenarioMindmapETE(node[0],node[2])
                    else:
                        updateparent(node[1],node[0],node[2],"delete")
                if error==None:
                    res={'rows':currentmoduleid}
                else:
                    res={'rows':'fail',"error":error}
            else:
                app.logger.warn("Empty data received. saveMindmapE2E")
        except Exception as e:
            servicesException("saveMindmapE2E", e, True)
        return jsonify(res)

    def checkScenarioIDexists(name,id):
        res=list(dbsession.testscenarios.find({"_id":ObjectId(id),"name":name,"deleted":False},{"_id":1}))
        if len(res)==1:
            return True
        else:
            return False

    def updateModuleName(modulename,projectid,moduleid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.mindmaps.update_one({"_id":ObjectId(moduleid)},{"$set":{"name":modulename,"modifiedby":userid,"modifedon":modifiedon,"modifiedbyrole":userroleid}})
        return

    def updateScenarioName(scenarioname,projectid,scenarioid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.testscenarios.update_one({"_id":ObjectId(scenarioid)},{"$set":{"name":scenarioname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateScreenName(screenname,projectid,screenid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.screens.update_one({"_id":ObjectId(screenid)},{"$set":{"name":screenname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateTestcaseName(testcasename,projectid,testcaseid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.testcases.update_one({"_id":ObjectId(testcaseid)},{"$set":{"name":testcasename,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def getModuleName(moduleid):
        modulename=list(dbsession.mindmaps.find({"_id":ObjectId(moduleid),"deleted":False},{"name":1}))
        if len(modulename)!=0:
            res=modulename[0]["name"]
        else:
            res=None
        return res
    
    def getScenarioName(scenarioid):
        scenarioname=list(dbsession.testscenarios.find({"_id":ObjectId(scenarioid),"deleted":False},{"name":1}))
        if len(scenarioname)!=0:
            res=scenarioname[0]["name"]
        else:
            res=None
        return res

    def getScreenName(screenid):
        screename=list(dbsession.screens.find({"_id":ObjectId(screenid),"deleted":False},{"name":1}))
        if len(screename)!=0:
            res=screename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseName(testcaseid):
        testcasename=list(dbsession.testcases.find({"_id":ObjectId(testcaseid),"deleted":False},{"name":1}))
        if len(testcasename)!=0:
            res=testcasename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseID(screenid,testcasename):
        testcaseid = list(dbsession.testcases.find({"screenid": ObjectId(screenid),"name": testcasename,"deleted": False}, {"_id": 1}))
        if len(testcaseid) != 0:
            res = str(testcaseid[0]["_id"])
        else:
            res = None
        return res

    def getScreenID(screenname,projectid):
        screenname=list(dbsession.screens.find({"projectid":ObjectId(projectid),"name":screenname,"deleted":False},{"_id":1}))
        if len(screenname)==1:
            return str(screenname[0]["_id"])
        else:   
            return None


    @app.route('/mindmap/exportMindmap', methods=['POST'])
    def exportMindmap():
        res = {'rows': 'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside exportMindmap.")
            if not isemptyrequest(requestdata):
                if (requestdata['query'] == 'exportMindmap'):
                    if type(requestdata['mindmapId']) == str:
                        mindmapid=[]
                        mindmapid.append(ObjectId(requestdata["mindmapId"]))
                    else:
                        mindmapid = [ObjectId(i) for i in requestdata['mindmapId']]                                                
                    queryresult=mindmapid                                        
                    projectid=list(dbsession.mindmaps.find({"_id":mindmapid[0]},{"projectid":1}))
                    projecttype=dbsession.projects.find({"_id":ObjectId(projectid[0]["projectid"])},{"type":1})
                    getProjectTypeName= list(dbsession.projecttypekeywords.find({"_id":ObjectId(projecttype[0]["type"])},{"name":1}))
                    projectAppType={"apptype":""}
                    projectId={"projectid":""}
                    projectId["projectid"]=projectid[0]["projectid"]
                    projectAppType["apptype"]=getProjectTypeName[0]["name"]
                    queryresult.append(projectAppType)
                    queryresult.append(projectId)
                    if queryresult:
                        res = {'rows': mindmapid}
            else:
                app.logger.warn('Empty data received while exporting mindmap')
        except Exception as exportmindmapexc:
            servicesException("exportMindmap", exportmindmapexc, True)
        return jsonify(json.loads(json_util.dumps(res)))
    

    def update_scenarios(scenarios):
        #converting all strings to ObjectIds
        for i in scenarios:
            i['_id'] = ObjectId(i['_id'])
            if 'screens' in i:
                for j in i['screens']:
                    j['_id'] = ObjectId(j['_id'])
                    if 'testcases' in j:
                        testcases =[]
                        for k in j['testcases']:
                            testcases.append(ObjectId(k))
                        j['testcases'] = testcases


    @app.route('/mindmap/importMindmap', methods=['POST'])
    def importMindmap():
        res = {'rows': 'fail'}
        try:
            app.logger.debug("Inside importMindmap.Request: "+str(request))
            # requestdata = json.loads(request.data)
            requestdata = loads(request.data)
            app.logger.debug("Inside importMindmap."+str(requestdata))
            if not isemptyrequest(requestdata):
                createdModuleList = []
                screenNames=[]
                scenarioIds=[]
                testcaseNames=[]                
                for moduleObj in requestdata['mindmap']:
                    if type(moduleObj)==dict:
                        continue                                       
                    mindmapdata=list(dbsession.mindmaps.find({'_id':moduleObj}))  
                    moduledataList=[]                    
                    for module in mindmapdata:                        
                        mindmapData=list(dbsession.mindmaps.find({'_id':module["_id"]},{"_id":1,"createdby":1,"createdbyrole":1,"createdon":1,"createdthrough":1,"deleted":1,"modifiedby":1,"modifiedbyrole":1,"modifiedon":1,"name":1,"projectid":1,"type":1,"versionnumber":1,"testscenarios":1}))
                        tscList=[]
                        if "testscenarios" in module:
                            for testscenarios in module["testscenarios"]:
                                if "_id" in testscenarios:
                                    testscenarioData=list(dbsession.testscenarios.find({'_id':testscenarios["_id"]}))
                                    if len(testscenarioData)>0:
                                        tsc=testscenarioData[0]
                                        tsc["screens"]=[]
                                        if "screens" in testscenarios:
                                            for screens in testscenarios["screens"]:
                                                if "_id" in screens:
                                                    screenData=list(dbsession.screens.find({'_id':screens["_id"]}))
                                                    if len(screenData)>0:
                                                        scr=screenData[0]                                                                        
                                                        scr["testcases"]=[]
                                                        if "testcases" in screens:                               
                                                            for testcase in screens["testcases"]:
                                                                if testcase:
                                                                    testcaseData=list(dbsession.testcases.find({'_id':testcase}))
                                                                    if len(testcaseData)>0:
                                                                        scr["testcases"].append(testcaseData[0])
                                                            tsc["screens"].append(scr)                                                                                                                    
                                            tscList.append(tsc)                                                
                            mindmapData[0]["testscenarios"]=tscList
                    moduledataList.append(mindmapData[0])
                    # del moduledataList[0]['projectid']
                    projectid = requestdata['mindmap'][-1]["projectid"]
                    moduledataList[0]['projectid']=requestdata['mindmap'][-1]["projectid"]
                    createdby = moduledataList[0]['createdby']
                    createdbyrole = moduledataList[0]['createdbyrole']
                    del moduledataList[0]['_id']
                    versionnumber = moduledataList[0]['versionnumber']
                    if (requestdata['query'] == 'importMindmap'):
                            app.logger.debug("Inside importMindmap.")
                            moduledataList[0]['projectid'] = ObjectId(
                               moduledataList[0]['projectid'])
                            moduleObjCopy = deepcopy(moduledataList[0])
                            moduleObjCopy["createdon"]= datetime.now()
                            moduleObjCopy["createdthrough"]=moduledataList[0]['createdthrough']
                            createdthrough=moduleObjCopy["createdthrough"]
                            moduleObjCopy["createdby"]=ObjectId(createdby)
                            moduleObjCopy["createdbyrole"]=ObjectId(createdbyrole)
                            moduleObjCopy["deleted"]=False
                            moduleObjCopy["modifiedby"]= ObjectId(createdby)
                            moduleObjCopy["modifiedon"] = datetime.now()
                            moduleObjCopy["modifiedbyrole"]= ObjectId(createdbyrole)
                            moduleObjCopy["type"]= moduledataList[0]['type']
                            moduleObjCopy["testscenarios"]= []
                            module_type= moduleObjCopy["type"]                          
                            queryresult = dbsession.mindmaps.insert_one(
                                moduleObjCopy)
                            result = dbsession.mindmaps.find_one(
                            {"_id": queryresult.inserted_id}, {"_id": 1})
                            createdModuleList.append(queryresult.inserted_id)
                            scenarioList = moduledataList[0]['testscenarios']                            
                            currentmoduleid = queryresult.inserted_id
                            idsforModule = []
                            for scenariodata in scenarioList:
                                testcaseidsforscenario = []
                                currentscenarioid = saveTestScenario(
                                    projectid, scenariodata['name'], versionnumber, createdby, createdbyrole, currentmoduleid)
                                scenarioIds.append(ObjectId(
                                    currentscenarioid))
                                iddata1 = {"_id": ObjectId(
                                    currentscenarioid), "screens": []}
                                for screendata in scenariodata['screens']:
                                    if '_id' in screendata:
                                        del screendata['_id']
                                    if 'parent' in screendata:
                                        del screendata['parent']
                                    if 'name' in screendata:
                                        if screendata['name'] in screenNames:
                                            screenId=list(dbsession.screens.find({'name':screendata['name'],'parent':{'$in':scenarioIds},'projectid':ObjectId(projectid)},{"id":1}))                                            
                                            currentscreenid=screenId[0]['_id']
                                            queryresult=dbsession.screens.update_many({'_id':ObjectId(currentscreenid)},{"$push":{'parent':ObjectId(currentscenarioid)}})
                                        else:
                                            screenNames.append(screendata['name'])
                                            currentscreenid = saveScreen(
                                                        projectid, screendata["name"], versionnumber, createdby, createdbyrole, currentscenarioid)
                                            queryresult=dbsession.screens.update_many({'_id':ObjectId(currentscreenid),'versionnumber':versionnumber},
                                                        {'$set':{'modifiedby':ObjectId(createdby),'modifiedbyrole':ObjectId(createdbyrole),'screenshot':screendata['screenshot'] if ('screenshot' in screendata) else "" ,'orderlist': screendata['orderlist'] if ('orderlist' in screendata) else [],'scrapedurl':screendata['scrapedurl'] if ('scrapedurl' in screendata) else "" ,"modifiedon" : datetime.now()}}).matched_count
                                            if 'orderlist' in screendata:
                                                orderlistids=[]
                                                for i in screendata['orderlist']:
                                                    orderlistids.append(ObjectId(i))
                                                queryresult=dbsession.dataobjects.update_many({'_id':{'$in':orderlistids}},{"$push":{'parent':ObjectId(currentscreenid)}})
                                        iddata2 = {"_id": ObjectId(
                                            currentscreenid), "testcases": []}
                                        for testcasedata in screendata['testcases']:
                                            if 'screenid' in testcasedata:
                                                del testcasedata['screenid']
                                            if 'name' in testcasedata:
                                                if testcasedata['name'] in testcaseNames:
                                                    testcaseId=list(dbsession.testcases.find({'name':testcasedata['name'],'screenid':ObjectId(currentscreenid)},{"id":1}))
                                                    if len(testcaseId)>0:
                                                        currenttestcaseid=testcaseId[0]['_id']
                                                        testcaseParent=list(dbsession.testcases.find({'_id':currenttestcaseid,'screenid':ObjectId(currentscreenid)},{"parent":1}))
                                                        parent=testcaseParent[0]["parent"]
                                                        parentInc=parent+1
                                                        queryresult=dbsession.testcases.update_many({'_id':ObjectId(currenttestcaseid),'screenid':ObjectId(currentscreenid)},{'$set':{"parent":parentInc}})
                                                        testcaseidsforscenario.append(
                                                            ObjectId(currenttestcaseid))
                                                        iddata2["testcases"].append(
                                                            ObjectId(currenttestcaseid))
                                                    else:
                                                        currenttestcaseid = saveTestcase(
                                                                currentscreenid, testcasedata['name'], versionnumber, createdby, createdbyrole)
                                                        queryresult = dbsession.testcases.update_many({'_id':ObjectId(currenttestcaseid),'versionnumber':versionnumber},
                                                                    {'$set':{'modifiedby':ObjectId(createdby),'modifiedbyrole':ObjectId(createdbyrole),"modifiedon" : datetime.now(),'steps':testcasedata['steps'] if ('steps' in testcasedata) else [],'datatables':testcasedata['datatables'] if 'datatables' in testcasedata else []}}).matched_count
                                                        testcaseidsforscenario.append(
                                                            ObjectId(currenttestcaseid))
                                                        iddata2["testcases"].append(
                                                            ObjectId(currenttestcaseid))                                                 
                                                else:
                                                    testcaseNames.append(testcasedata['name'])
                                                    currenttestcaseid = saveTestcase(
                                                                currentscreenid, testcasedata['name'], versionnumber, createdby, createdbyrole)
                                                    queryresult = dbsession.testcases.update_many({'_id':ObjectId(currenttestcaseid),'versionnumber':versionnumber},
                                                                {'$set':{'modifiedby':ObjectId(createdby),'modifiedbyrole':ObjectId(createdbyrole),"modifiedon" : datetime.now(),'steps':testcasedata['steps'] if ('steps' in testcasedata) else [],'datatables':testcasedata['datatables'] if 'datatables' in testcasedata else []}}).matched_count
                                                    testcaseidsforscenario.append(
                                                        ObjectId(currenttestcaseid))
                                                    iddata2["testcases"].append(
                                                        ObjectId(currenttestcaseid))
                                        iddata1["screens"].append(iddata2)
                                idsforModule.append(iddata1)
                                updateTestcaseIDsInScenario(
                                            currentscenarioid, testcaseidsforscenario)
                            updateTestScenariosInModule(currentmoduleid, idsforModule)
                                
                            
                    
                    if queryresult:
                            res = {'rows': createdModuleList}
                
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as importmindmapexc:
            servicesException("importMindmap", importmindmapexc, True)
        return jsonify(res)

    @app.route('/mindmap/gitToMindmap',methods=['POST'])
    def gitToMindmap():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside gitToMindmap.")
            if not isemptyrequest(requestdata):
                if (requestdata['query'] == 'gitToMindmap'):
                    mindmapid=ObjectId(requestdata['mindmap']['_id'])
                    update_scenarios(requestdata['mindmap']['testscenarios'])
                    #query below can be improved
                    result=dbsession.mindmaps.find_one({"_id":mindmapid})
                    if result != None:
                        queryresult = dbsession.mindmaps.update_one({"_id":mindmapid},{'$set':{"deleted":False,"name":requestdata['mindmap']['name'],"projectid": ObjectId(requestdata['mindmap']['projectid']),"testscenarios":requestdata['mindmap']['testscenarios'],"type":requestdata['mindmap']['type'],"versionnumber":requestdata['mindmap']['versionnumber']}})
                    else:
                        requestdata['mindmap']['_id'] = mindmapid
                        requestdata['mindmap']['projectid'] = ObjectId(requestdata['mindmap']['projectid'])
                        queryresult = dbsession.mindmaps.insert_one(requestdata['mindmap'])
                    result=dbsession.mindmaps.find_one({"_id":mindmapid},{"_id":1})
                    if queryresult:
                        res={'rows':result}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as gitToMindmapexc:
            servicesException("gitToMindmap",gitToMindmapexc, True)
        return jsonify(res)
   
