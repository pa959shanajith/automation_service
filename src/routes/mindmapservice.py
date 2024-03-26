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
import subprocess
import shutil
import os
import sys
import platform
import pymongo  


def LoadServices(app, redissession, client ,getClientName):
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

    def adddataobjects(dbsession,pid, d):
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

    def createdataobjects(dbsession,crid, objs):
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
            res = adddataobjects(dbsession,scrid, custnameToAdd)
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
                    'domains':[],
                    'projectlevelrole' : []
                }
                projectlevelrole = list(dbsession.users.find({"_id":ObjectId(requestdata['userid'])},{"projectlevelrole": 1}))

                prjDetails['projectlevelrole'].append(projectlevelrole[0]['projectlevelrole'])

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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            modifiedon=datetime.now()
            screenname = requestdata['screenname']
            projectid = requestdata['projectid']
            screenid = getScreenID(dbsession,screenname,projectid)
            if(screenid==None):
                queryresult=dbsession.screens.insert_one({"name":requestdata['screenname'],"projectid":ObjectId(requestdata['projectid']),"versionnumber":requestdata['versionnumber'],"parent":[],"createdby":ObjectId(requestdata['createdby']),"createdon":modifiedon,"createdbyrole":ObjectId(requestdata['createdbyrole']),"modifiedby":ObjectId(requestdata['modifiedby']),"modifiedon":modifiedon,"modifiedbyrole":ObjectId(requestdata['modifiedbyrole']),"deleted":requestdata['deleted'],"createdthrough":requestdata['createdthrough'],"screenshot":requestdata['screenshot'],"scrapedurl":requestdata['scrapedurl']}).inserted_id
                result = createdataobjects(dbsession,queryresult,requestdata)
            else:
                result = createdataobjects(dbsession,screenid,requestdata)
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                modifiedon=datetime.now()
                screenid = requestdata['screenid']
                testcasename = requestdata['testcasename']
                testcaseid = getTestcaseID(dbsession,screenid,testcasename)
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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            tab = requestdata['tab']
            app.logger.debug("Inside getModules. Query: " +
                             str(requestdata["name"]))
            if "query" in requestdata and requestdata["query"]=="modLength":
                queryresult=list(dbsession.mindmaps.find({'projectid':ObjectId(requestdata["projectid"])},{"_id":1}))
                res = {'rows': queryresult}
            elif 'moduleid' in requestdata and requestdata['moduleid'] != None:
                moduleMap = []
                for modId in requestdata["moduleid"]:
                    if type(requestdata["moduleid"]) == str:
                        modId = requestdata["moduleid"]
                    mindmapdata = dbsession.mindmaps.find_one({"_id": ObjectId(modId)}, {
                                                            "testscenarios": 1, "_id": 1, "name": 1, "projectid": 1, "type": 1, "versionnumber": 1,"currentlyinuse":1,"assignedUser": 1 })
                    projectid = mindmapdata["projectid"]
                    # projectlevelTag= list(dbsession.mindmaps.find({'projectid':projectid},{'testscenarios.tag': 1, 'testscenarios.assigneduser': 1}))
                    # all_tags = []
                    # allusers = []
                    # for entry in projectlevelTag:
                    #     if 'testscenarios' in entry:
                    #         for scenario in entry['testscenarios']:
                    #             if 'tag' in scenario :
                    #                 all_tags.extend(scenario['tag'])
                    #             if 'assigneduser' in scenario:
                    #                 allusers.extend(scenario['assigneduser'])
                    mindmaptype = mindmapdata["type"]
                    scenarioids = []
                    screenids = []
                    tag = []
                    assigneduser = []
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
                                        if "tag" in ts:
                                            if ts["tag"] not in tag:
                                                tag.append(ts["tag"])
                                        if "assigneduser" in ts:
                                            if ts["assigneduser"] not in assigneduser:
                                                assigneduser.append(ts["assigneduser"])
                                        
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
                    taskids.extend(tag)
                    taskids.extend(assigneduser)
                    taskids.extend(screenids)
                    taskids.extend(testcaseids)
                    taskids.append(ObjectId(modId))
                    taskdetails = list(dbsession.tasks.find(
                        {"nodeid": {"$in": taskids}}))

                    scenariodetails = list(dbsession.testscenarios.find(
                        {"_id": {"$in": scenarioids}}, {"_id": 1, "name": 1, "parent": 1, "assigneduser": 1}))

                    testcasedetails = list(dbsession.testcases.aggregate([
                        {'$match': {"_id": {"$in": testcaseids}}},
                        {'$project':{'stepsLen':{ '$cond': { 'if': { '$isArray': "$steps" },
                         'then': { '$size': "$steps" }, 'else': 0}} ,'_id': 1 , 'name': 1,'parent':1}}]))

                    screendetails = list(dbsession.screens.aggregate([
                        {'$match': {"_id": {"$in": screenids}}},
                        {'$project':{'objLen':{ '$cond': { 'if': { '$isArray': "$orderlist" },
                         'then': { '$size': "$orderlist" }, 'else': 0}} ,'_id': 1 , 'name': 1,'parent':1}}]))

                    # Check for ObjectId in screenids but not in screendetails
                    for oid in screenids:
                        if oid not in [item['_id'] for item in screendetails]:
                            dbsession.mindmaps.update_one(
                                {
                                    "_id": mindmapdata["_id"],
                                    "testscenarios.screens._id": oid
                                },
                                {
                                    "$pull": {
                                        "testscenarios.$[scenario].screens": {
                                            "_id": oid
                                        }
                                    }
                                },
                                array_filters=[
                                    {"scenario.screens._id": oid}
                                ]
                            )
                        else:
                            # Check for ObjectId in testcaseids but not in testcasedetails
                            for oidTest in testcaseids:
                                if oidTest not in [item['_id'] for item in testcasedetails]:
                                    if oidTest in sc.get('testcases'):
                                        dbsession.mindmaps.update_one(
                                            {
                                                "_id": mindmapdata["_id"],
                                                "testscenarios.screens._id": sc["_id"]
                                            },
                                            {
                                                "$pull": {
                                                            "testscenarios.$[].screens.$[screen].testcases": oidTest
                                                         }
                                            },
                                            array_filters=[
                                                {"screen._id": sc["_id"]}
                                            ]
                                        )
                                        for it in ts['screens']:
                                            if sc["_id"] == it["_id"]:
                                                if oidTest in it.get('testcases'):
                                                    dbsession.testscenarios.update_one(
                                                        {
                                                            "_id": ts["_id"],
                                                            "testcaseids": oidTest
                                                        },
                                                        {
                                                            "$pull": {
                                                                        "testcaseids": oidTest
                                                                    }
                                                        },
                                                    )

                    # screendetails = list(dbsession.screens.find(
                    #     {"_id": {"$in": screenids}}, {"_id": 1, "name": 1, "parent": 1,"orderlist":1}))
                    # testcasedetails = list(dbsession.testcases.find(
                    #     {"_id": {"$in": testcaseids}}, {"_id": 1, "name": 1, "parent": 1,"steps":1}))
                    moduledata = {}
                    scenariodata = {}
                    screendata = {}
                    testcasedata = {}
                    mindmapdata = dbsession.mindmaps.find_one({"_id": ObjectId(modId)}, {
                                                            "testscenarios": 1, "_id": 1, "name": 1, "projectid": 1, "type": 1, "versionnumber": 1,"currentlyinuse":1})
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
                            screendata[sc["_id"]]['objLen'] = sc["objLen"]
                        else:
                            screendata[sc["_id"]] = {
                                "name": sc["name"],
                                "reuse": True if len(sc["parent"]) > 1 else False,
                                "objLen" : sc["objLen"]
                            }
                    for tc in testcasedetails:
                        if tc["_id"] in testcasedata:
                            testcasedata[tc["_id"]]['name'] = tc["name"]
                            testcasedata[tc["_id"]
                                        ]['reuse'] = True if tc["parent"] > 1 else False
                            testcasedata[tc["_id"]]['stepsLen'] = tc["stepsLen"]

                        else:
                            testcasedata[tc["_id"]] = {
                                "name": tc["name"],
                                "reuse": True if tc["parent"] > 1 else False,
                                "stepsLen": tc["stepsLen"]
                            }
                    finaldata = {}
                    finaldata["name"] = mindmapdata["name"]
                    finaldata["_id"] = mindmapdata["_id"]
                    finaldata["projectID"] = mindmapdata["projectid"]
                    # for tg in mindmapdata["testscenarios"]:
                    #     if "tag" in tg:
                    #         finaldata["tag"] = all_tags
                    #     if "assigneduser" in tg:
                    #         finaldata["assignedUser"] = allusers
                    finaldata["type"] = "modules"
                    finaldata["childIndex"] = 0
                    finaldata["state"] = "saved"
                    finaldata["versionnumber"] = mindmapdata["versionnumber"]
                    finaldata["children"] = []
                    if "currentlyinuse" in mindmapdata:
                        finaldata["currentlyInUse"]=mindmapdata["currentlyinuse"]
                    else:
                        finaldata["currentlyInUse"]= ''
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
                                # for ts in mindmapdata["testscenarios"]:
                                if "tag" in ts:
                                    finalscenariodata["tag"] = ts['tag']
                                if "assigneduser" in ts:
                                    finalscenariodata["assigneduser"] = ts['assigneduser']
                                # finalscenariodata["tag"] = ts["tag"]
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
                                            finalscreendata["objLen"] = screendata[sc["_id"]]["objLen"]
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
                                                        finaltestcasedata["stepsLen"] = testcasedata[tc]["stepsLen"]
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
                query = dbsession.mindmaps.find(
                    findquery, {"name": 1, "_id": 1, "type": 1, "createdon":1, "currentlyinuse" : 1 })
                
                queryresult = list(query.sort([('createdon', pymongo.DESCENDING),('name', pymongo.ASCENDING)]))
            
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            requestdata=requestdata["data"]
            projectid=requestdata['projectid']
            createdby=requestdata['userid']
            username = requestdata['username']
            createdbyrole=requestdata['userroleid']
            versionnumber=requestdata['versionnumber']
            createdthrough=requestdata['createdthrough']
            module_type="basic"
            createdon = datetime.now()
            error=checkReuse(dbsession,requestdata)
            currentmoduleid=None
            if error is None:
                for moduledata in requestdata['testsuiteDetails']:       
                    if moduledata["testsuiteId"] is None:
                        currentmoduleid=saveTestSuite(dbsession,projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,module_type)
                    else:
                        if moduledata['state']=="renamed":
                            updateModuleName(dbsession,moduledata['testsuiteName'],projectid,moduledata["testsuiteId"],createdby,createdbyrole)
                        currentmoduleid=moduledata['testsuiteId']
                    idsforModule=[] 
                    # moduledata["testscenarioDetails"][0]["assigneduser"] = "rakesh_solapure"
                    for scenariodata in moduledata['testscenarioDetails']:
                        assigneduser=''
                        if "assigneduser"  in scenariodata :
                            assigneduser=scenariodata["assigneduser"]
                        # assigneduser = dbsession.testscenarios.find_one({"_id" : ObjectId(scenariodata["testscenarioid"])},{"assignedUser": 1})
                        if assigneduser =="":
                            assigneduser=requestdata['username']
                        # verifyuser = scenariodata["assigneduser"]
                            
                        if assigneduser == requestdata['username']:
                            testcaseidsforscenario=[]
                            if scenariodata['testscenarioid'] is None:
                                currentscenarioid=saveTestScenario(dbsession,projectid,scenariodata['testscenarioName'],versionnumber,createdby,createdbyrole,username,currentmoduleid)
                            else:
                                if scenariodata['state']=="renamed":
                                    updateScenarioName(dbsession,scenariodata['testscenarioName'],projectid,scenariodata['testscenarioid'],createdby,createdbyrole)
                                currentscenarioid=scenariodata['testscenarioid']
                            iddata1={"_id":ObjectId(currentscenarioid),"screens":[],"tag":scenariodata["tag"], "assignedUser" : assigneduser}
                            for screendata in scenariodata['screenDetails']:
                                if screendata["screenid"] is None:
                                    if "newreuse" in screendata:
                                        currentscreenid=getScreenID(dbsession,screendata["screenName"],projectid)
                                        updateparent(dbsession,"screens",currentscreenid,currentscenarioid,"add")
                                    else:
                                        scrapedurl = screendata['scrapedurl'] if 'scrapedurl' in screendata else ""
                                        scrapeinfo = screendata['scrapeinfo'] if 'scrapeinfo' in screendata else "" 
                                        currentscreenid=saveScreen(dbsession,projectid,screendata["screenName"],versionnumber,createdby,createdbyrole,currentscenarioid,scrapedurl,scrapeinfo)
                                else:
                                    if screendata["state"]=="renamed":
                                        updateScreenName(dbsession,screendata['screenName'],projectid,screendata['screenid'],createdby,createdbyrole)
                                    currentscreenid=screendata["screenid"]
                                    if "reuse" in screendata and screendata["reuse"]:
                                        updateScreenAndTestcase(dbsession,currentscreenid,createdby,createdbyrole)
                                        updateparent(dbsession,"screens",currentscreenid,currentscenarioid,"add")
                                iddata2={"_id":ObjectId(currentscreenid),"testcases":[]}
                                for testcasedata in screendata['testcaseDetails']:
                                    if testcasedata["testcaseid"] is None:
                                        if "newreuse" in testcasedata:
                                            currenttestcaseid=getTestcaseID(dbsession,currentscreenid,testcasedata['testcaseName'])
                                            updateparent(dbsession,"testcases",currenttestcaseid,currentscreenid,"add")
                                        else:
                                            steps = testcasedata['steps'] if 'steps' in testcasedata else []
                                            currenttestcaseid=saveTestcase(dbsession,currentscreenid,testcasedata['testcaseName'],versionnumber,createdby,createdbyrole,steps)
                                    else:
                                        if testcasedata['state']=="renamed":
                                            updateTestcaseName(dbsession,testcasedata['testcaseName'],projectid,testcasedata['testcaseid'],createdby,createdbyrole)
                                        currenttestcaseid=testcasedata['testcaseid']
                                        if "reuse" in testcasedata and testcasedata["reuse"]:
                                            updateparent(dbsession,"testcases",currenttestcaseid,currentscreenid,"add")
                                    testcaseidsforscenario.append(ObjectId(currenttestcaseid))
                                    iddata2["testcases"].append(ObjectId(currenttestcaseid))
                                iddata1["screens"].append(iddata2)
                            idsforModule.append(iddata1)
                            updateTestcaseIDsInScenario(dbsession,currentscenarioid,testcaseidsforscenario)
                        else:
                            iddata1=module_data(scenariodata)
                            for data1 in iddata1:
                                idsforModule.append(data1)
                            # updateTestcaseIDsInScenario(dbsession,currentscenarioid,testcaseidsforscenario)
                    updateTestScenariosInModule(dbsession,currentmoduleid,idsforModule) 
                scenarioInfo = []
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios":
                        scenarioName, parents = updateScenarioMindmap(dbsession,node[0],node[2])
                        if parents:
                            scenarioInfo.append({"nodeid" : node[0], "scenarioName": scenarioName, "parents":parents })
                    else:
                        updateparent(dbsession,node[1],node[0],node[2],"delete")
                if scenarioInfo:
                    res = {'rows' : {"currentmoduleid" : currentmoduleid , "scenarioInfo" :scenarioInfo}}
                else:
                    res={'rows':currentmoduleid}
                dbsession.projects.update_one({"_id":ObjectId(projectid), }, {"$set":{"modifiedon": createdon} })
            else:
                res={'rows':'reuseerror',"error":error}
        except Exception as e:
            servicesException("saveMindmap", e, True)
        return jsonify(res)
    @app.route('/design/updateTestSuiteInUseBy', methods=['POST'])
    def updateTestSuiteInUseBy():
        try:
            res={'rows':'fail'}
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]
            testsuitedetail=dbsession.mindmaps.find_one({'_id':ObjectId(requestdata['testsuiteId'])})
            currentlyinuseby=testsuitedetail['currentlyinuse']
            if(currentlyinuseby is not None and requestdata['testsuiteId']==requestdata["oldTestSuiteId"]):
                return
            app.logger.debug("Inside updateTestSuiteInUseBy. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
            
                accessedBy=requestdata['accessedBy']
                if (len(requestdata['testsuiteId'])>0 and requestdata['assignToUser']==True):
                   dbsession.mindmaps.update_one({'_id':ObjectId(requestdata['testsuiteId'])},{"$set":{"currentlyinuse":accessedBy}})
                if (len(requestdata["oldTestSuiteId"])!=0 and requestdata['resetFlag']==True):
                   dbsession.mindmaps.update_one({'_id':ObjectId(requestdata["oldTestSuiteId"])},{"$set":{"currentlyinuse":""}})   
                res={"rows":"Success"}
            else:
                app.logger.warn('Empty data received.')
        except Exception as getscrapedataexc:
            servicesException("getScrapeDataScenarioLevel_ICE",getscrapedataexc, True)
        return jsonify(res)    
    def saveTestSuite(dbsession,projectid,modulename,versionnumber,createdthrough,createdby,createdbyrole,moduletype,testscenarios=[]):
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
        "testscenarios":[],
        "currentlyinuse":""
        }
        queryresult=dbsession.mindmaps.insert_one(data).inserted_id
        return queryresult
    
    def module_data(scenariodata):
        app.logger.debug("Inside module_data")
        iddata1 = []
        screedata = []
        for screendata in scenariodata['screenDetails']:
            screen = {}
            screen["_id"] = ObjectId(screendata['screenid'])
            screen["testcases"] = []
            for screenid in screendata["testcaseDetails"]:
                screen['testcases'].append(ObjectId(screenid['testcaseid']))
            screedata.append(screen)
        iddata1.append({"_id":ObjectId(scenariodata["testscenarioid"]),"screens":screedata,"tag":scenariodata["tag"],"assigneduser":scenariodata["assigneduser"] })
        return iddata1

    def saveTestScenario(dbsession,projectid,testscenarioname,versionnumber,createdby,createdbyrole,username,moduleid,testcaseids=[]):
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
            "testcaseids":testcaseids,
            "assignedUser" : username
        }
        queryresult=dbsession.testscenarios.insert_one(data).inserted_id
        return queryresult

    def saveScreen(dbsession,projectid,screenname,versionnumber,createdby,createdbyrole,scenarioid):
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
        "scrapedurl":"",
        "orderlist" : []
        }
        queryresult=dbsession.screens.insert_one(data).inserted_id
        return queryresult
    @app.route('/design/insertScreen', methods=['POST'])
    def insertScreen():
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]
            createdon = datetime.now()
 
            if requestdata['param']=="create":
            # app.logger.debug("Inside insertScreen. Query: "+str(requestdata["query"]))
                data={
                    "projectid":ObjectId(requestdata['projectid']),
                    "name":requestdata['name'],
                    "versionnumber":requestdata['versionnumber'],
                    # "parent":[ObjectId(requestdata['scenarioid'])],
                    "createdby":ObjectId(requestdata['createdby']),
                    "createdbyrole":ObjectId(requestdata['createdbyrole']),
                    "createdon":createdon,
                    "deleted":False,
                    "parent" : [],
                    "screenids" : [],
                    "modifiedby":ObjectId(requestdata['createdby']),
                    "modifiedbyrole":ObjectId(requestdata['createdbyrole']),
                    "modifiedon":createdon,
                    "screenshot":"",
                    "scrapedurl":"",
                    "orderlist":[],
                    }
                dbsession.elementrepository.insert_one(data).inserted_id
                res = {"rows":"Success"}
            elif requestdata['param']=="update":
                dbsession.elementrepository.update({"_id":ObjectId(requestdata['screenid'])},{"$set":{"name":requestdata['name'],"modifiedby":ObjectId(requestdata['userId']),"modifedon":createdon,"modifiedbyrole":ObjectId(requestdata["roleId"])}})
                res={"rows":"Success"}
        
        except Exception as e:
            servicesException("insertScreen",e, True)
        return jsonify(res)
    
    @app.route('/design/insertRepository', methods=['POST'])
    def insertRepository():
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]
            createdon = datetime.now()
 
            if requestdata['param']=="create":
            # app.logger.debug("Inside insertScreen. Query: "+str(requestdata["query"]))
                data={
                    "projectid":ObjectId(requestdata['projectid']),
                    "name":requestdata['name'],
                    "versionnumber":requestdata['versionnumber'],
                    # "parent":[ObjectId(requestdata['scenarioid'])],
                    "createdby":ObjectId(requestdata['createdby']),
                    "createdbyrole":ObjectId(requestdata['createdbyrole']),
                    "createdon":createdon,
                    "deleted":False,
                    "parent" : [],
                    "modifiedby":ObjectId(requestdata['createdby']),
                    "modifiedbyrole":ObjectId(requestdata['createdbyrole']),
                    "modifiedon":createdon,
                    "screenshot":"",
                    "scrapedurl":"",
                    "orderlist":[],
                    }
                dbsession.elementrepository.insert_one(data).inserted_id
                res = {"rows":"Success"}
            elif requestdata['param']=="update":
                dbsession.elementrepository.update({"_id":ObjectId(requestdata['screenid'])},{"$set":{"name":requestdata['name'],"modifiedby":ObjectId(requestdata['userId']),"modifedon":createdon,"modifiedbyrole":ObjectId(requestdata["roleId"])}})
                res={"rows":"Success"}
        
        except Exception as e:
            servicesException("insertRepository",e, True)
        return jsonify(res)
    def saveTestcase(dbsession,screenid,testcasename,versionnumber,createdby,createdbyrole):
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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            if 'migration' in requestdata:
                migration=requestdata['migration']
            else:
                migration = False
            requestdata=requestdata["data"]
            projectid=requestdata['projectid']
            # testcasename = "Tc_"+projectid
            createdby=requestdata['userid']
            createdbyrole=requestdata['userroleid']
            versionnumber=requestdata['versionnumber']
            createdthrough=requestdata['createdthrough']
            module_type="basic"
            error=checkReuse(dbsession,requestdata)
            currentmoduleid=None
            if error is None:
                for moduledata in requestdata['testsuiteDetails']:
                    if moduledata["testsuiteId"] is None:
                        currentmoduleid=saveTestSuite(dbsession,projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,module_type)
                    else:
                        if moduledata['state']=="renamed":
                            updateModuleName(dbsession,moduledata['testsuiteName'],projectid,moduledata["testsuiteId"],createdby,createdbyrole)
                        currentmoduleid=moduledata['testsuiteId']
                    idsforModule=[]
                    for scenariodata in moduledata['testscenarioDetails']:
                        testcaseidsforscenario=[]
                        if scenariodata['testscenarioid'] is None:
                            currentscenarioid=saveTestScenario(dbsession,projectid,scenariodata['testscenarioName'],versionnumber,createdby,createdbyrole,currentmoduleid)
                        else:
                            if scenariodata['state']=="renamed":
                                updateScenarioName(dbsession,scenariodata['testscenarioName'],projectid,scenariodata['testscenarioid'],createdby,createdbyrole)
                            currentscenarioid=scenariodata['testscenarioid']
                        iddata1={"_id":ObjectId(currentscenarioid),"screens":[]}
                        for screendata in scenariodata['screenDetails']:
                            if screendata["screenid"] is None:
                                if "newreuse" in screendata:
                                    currentscreenid=getScreenID(dbsession,screendata["screenName"],projectid)
                                    updateparent(dbsession,"screens",currentscreenid,currentscenarioid,"add")
                                else:
                                    currentscreenid=saveScreen(dbsession,projectid,screendata["screenName"],versionnumber,createdby,createdbyrole,currentscenarioid)
                            else:
                                if screendata["state"]=="renamed":
                                    updateScreenName(dbsession,screendata['screenName'],projectid,screendata['screenid'],createdby,createdbyrole)
                                currentscreenid=screendata["screenid"]
                                if "reuse" in screendata and screendata["reuse"]:
                                    updateScreenAndTestcase(dbsession,currentscreenid,createdby,createdbyrole)
                                    updateparent(dbsession,"screens",currentscreenid,currentscenarioid,"add")
                            iddata2={"_id":ObjectId(currentscreenid),"testcases":[]}
                            for testcasedata in screendata['testcaseDetails']:
                                if testcasedata["testcaseid"] is None:
                                    if "newreuse" in testcasedata:
                                        currenttestcaseid=getTestcaseID(dbsession,currentscreenid,testcasedata['testcaseName'])
                                        updateparent(dbsession,"testcases",currenttestcaseid,currentscreenid,"add")
                                    else:
                                        currenttestcaseid=saveTestcase(dbsession,currentscreenid,testcasedata['testcaseName'],versionnumber,createdby,createdbyrole)
                                else:
                                    if testcasedata['state']=="renamed":
                                        updateTestcaseName(dbsession,testcasedata['testcaseName'],projectid,testcasedata['testcaseid'],createdby,createdbyrole)
                                    currenttestcaseid=testcasedata['testcaseid']
                                    if "reuse" in testcasedata and testcasedata["reuse"]:
                                        updateparent(dbsession,"testcases",currenttestcaseid,currentscreenid,"add")
                                testcaseidsforscenario.append(ObjectId(currenttestcaseid))
                                iddata2["testcases"].append(ObjectId(currenttestcaseid))
                            iddata1["screens"].append(iddata2)
                        idsforModule.append(iddata1)
                        updateTestcaseIDsInScenario(dbsession,currentscenarioid,testcaseidsforscenario)
                        if (migration == False):
                            updateTestScenariosInModule(dbsession,currentmoduleid,idsforModule)
                        else:
                            updateTestScenariosInModuleMigration(dbsession,currentmoduleid,idsforModule)
                scenarioInfo = []
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios":
                        scenarioName, parents = updateScenarioMindmap(dbsession,node[0],node[2])
                        if parents:
                            scenarioInfo.append({"nodeid" : node[0], "scenarioName": scenarioName, "parents":parents })
                    else:
                        updateparent(dbsession,node[1],node[0],node[2],"delete")
                if scenarioInfo:
                    res = {'rows' : {"currentmoduleid" : currentmoduleid , "scenarioInfo" :scenarioInfo}}
                else:
                    res={'rows':currentmoduleid}
            else:
                res={'rows':'reuseerror',"error":error}
        except Exception as e:
            servicesException("saveGeniusMindmap", e, True)
        return jsonify(res)

    def saveTestSuite(dbsession,projectid,modulename,versionnumber,createdthrough,createdby,createdbyrole,moduletype,testscenarios=[]):
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
        "testscenarios":[],
        "currentlyinuse":""
        }
        queryresult=dbsession.mindmaps.insert_one(data).inserted_id
        return queryresult

    def saveTestScenario(dbsession,projectid,testscenarioname,versionnumber,createdby,createdbyrole,username,moduleid,testcaseids=[]):
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
            "testcaseids":testcaseids,
            "assignedUser": username
        }
        queryresult=dbsession.testscenarios.insert_one(data).inserted_id
        return queryresult

    def saveScreen(dbsession,projectid,screenname,versionnumber,createdby,createdbyrole,scenarioid,*args):
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
        "scrapedurl":args[0] if len(args) > 0 else "",
        "orderlist" : []
        }
        if(len(args) > 1 and args[1] != ""):
            data["scrapeinfo"]=args[1]
        queryresult=dbsession.screens.insert_one(data).inserted_id
        return queryresult

    def saveTestcase(dbsession,screenid,testcasename,versionnumber,createdby,createdbyrole,*args):
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
            "steps":args[0] if len(args) > 0 else [],
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]

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

    def checkReuse(dbsession,requestdata):
        scenarionames=set()
        # screennameset=set()
        screen_testcase={}
        error=None
        projectid=projectid=requestdata['projectid']
        for moduledata in requestdata['testsuiteDetails']:
            if moduledata['testsuiteId'] is None:
                # If the the Module does not have an ID then we will check if the target name has conflict.
                if checkModuleNameExists(dbsession,moduledata["testsuiteName"],projectid):
                    error="A project cannot have similar test suite name"
                    break
                else:
                    moduledata['state']="renamed"
            else:
                # If the the Module has an ID then we will check if the target name has conflict if not then rename will be allowed.
                name=getModuleName(dbsession,moduledata['testsuiteId'])
                if name!=moduledata["testsuiteName"]:
                    if checkModuleNameExists(dbsession,moduledata["testsuiteName"],projectid):
                        error="Test suite cannot be renamed to an existing test suite name"
                        break
                    else:
                        moduledata['state']="renamed"
            for scenariodata in moduledata['testscenarioDetails']:
                # This check for similar scenario name within the same module.
                if scenariodata['testscenarioName'] in scenarionames:
                    error="A project cannot have similar testcase names: "+scenariodata['testscenarioName']
                    break
                else:
                    scenarionames.add(scenariodata['testscenarioName'])

                # If the the Scenario does not have an ID then we will check if the target name has conflict.
                if scenariodata['testscenarioid'] is None:
                    if checkScenarioNameExists(dbsession,projectid,scenariodata['testscenarioName']):
                        error="A project cannot have similar testcase names: change "+scenariodata['testscenarioName']+" name"
                        break
                else:
                    # If the the Scenario has an ID then we will check if the target name has conflict if not then rename will be allowed.
                    scenarioname=getScenarioName(dbsession,scenariodata['testscenarioid'])
                    if scenarioname!=scenariodata['testscenarioName']:
                        if checkScenarioNameExists(dbsession,projectid,scenariodata['testscenarioName']):
                            error="A project cannot have similar testcase names: change "+scenariodata['testscenarioName']+" name"
                            break
                        else:
                            scenariodata['state']="renamed"
                for screendata in scenariodata['screenDetails']:
                    
                    if screendata["screenid"] is None:
                        # If ScreenID is none then we will check if a screen with that name exists then we will give this screen the ID of the existing screen else it will be None only.
                        screendata["screenid"]=getScreenID(dbsession,screendata["screenName"],projectid)
                        if screendata["screenid"] is not None:
                            screendata["reuse"]=True
                        elif screendata["screenName"] in screen_testcase:
                            screendata["newreuse"]=True
                        else:
                            screendata["reuse"]=False
                    else:
                        screenname = getScreenName(dbsession,screendata["screenid"])
                        if screenname != screendata["screenName"]:
                            if checkScreenNameExists(dbsession,screendata["screenName"], projectid):
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
                                testcasedata['testcaseid']=getTestcaseID(dbsession,screendata["screenid"],testcasedata["testcaseName"])
                                if testcasedata["testcaseid"] is not None:
                                    testcasedata["reuse"]=True
                                else:
                                    testcasedata["reuse"]=False
                            else:
                                testcasename=getTestcaseName(dbsession,testcasedata['testcaseid'])
                                if testcasename!= testcasedata["testcaseName"]:
                                    testcaseid=getTestcaseID(dbsession,screendata["screenid"],testcasedata["testcaseName"])
                                    if testcaseid is not None:
                                        updateparent(dbsession,'testcases',testcasedata['testcaseid'],screendata["screenid"],'delete')
                                        testcasedata['testcaseid']=testcaseid
                                        testcasedata["reuse"]=True
                                    else:
                                        testcasedata["state"]="renamed"
                                        testcasedata["reuse"]=False
        if error is None:
            return None
        else:
            return error

    def checkModuleNameExists(dbsession,name,projectid):
        res=list(dbsession.mindmaps.find({"projectid":ObjectId(projectid),"name":name},{"_id":1}))
        if len(res)>0:
            return True
        else:
            return False

    def checkScreenNameExists(dbsession,name,projectid):
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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
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
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
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
                                    finalscreen=[]
                                    for scrn in tempScenario1["screens"]:
                                        if "_id" in scrn:
                                            if scrn["_id"]==ObjectId(screenid):
                                                dataObjects=list(dbsession.dataobjects.find({"parent":ObjectId(screenid)},{"parent":1}))
                                                if len(dataObjects)>0:                                                                                                      
                                                    dataObjectslist = dataObjects[0]['parent']
                                                    if len(dataObjectslist)==1:
                                                        dbsession.dataobjects.delete_many({'parent':ObjectId(screenid)})
                                                    else:
                                                        dbsession.dataobjects.update_many({'parent':ObjectId(screenid)},{"$pull": {"parent": ObjectId(screenid)}})                                                    
                                                dbsession.screens.delete_one({'_id': ObjectId(screenid)})                                                
                                                if "testcases" in scrn:
                                                    for testcase in scrn["testcases"]:
                                                        dbsession.testcases.delete_one({'_id': testcase})
                                                        dbsession.testscenarios.update_one({'_id':scen["_id"]},{"$pull": {"testcaseids": testcase}})                                                   
                                            else:
                                                finalscreen.append(scrn)
                                    tempScenario1["screens"]=finalscreen                                     
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
                                        if "screens" in scenario:                                                                
                                            del scenario["screens"]                                                                   
                        testscenarios.append(tempmodule['testscenarios'])
                        testscenario=testscenarios[0] 
                        testscenario=[i for i in testscenario if i]                   
                        dbsession.mindmaps.update_one({'_id' : tempmodule['_id']},  {'$set' : {'testscenarios':testscenario}})
                        dbsession.testsuites.update_one({'name':tempmodule['name']},{"$pull": {"testscenarioids":ObjectId(scenarioid)}})
                    
                
                    dbsession.testscenarios.delete_one({'_id': ObjectId(scenarioid)})
                for screenid in screenids:
                    dbsession.screens.delete_one({'_id': ObjectId(screenid)})
                for testcaseid in testcaseids:
                    dbsession.testcases.delete_one({'_id': ObjectId(testcaseid)}) 


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
                                    finalscr=[]
                                    for screen in tempScenario["screens"]:
                                        if "_id" in screen:
                                            if screen["_id"]==ObjectId(screenid):
                                                dataObjects=list(dbsession.dataobjects.find({"parent":ObjectId(screenid)},{"parent":1}))
                                                if len(dataObjects)>0:                                                   
                                                    dataObjectslist = dataObjects[0]['parent']
                                                    if len(dataObjectslist)==1:
                                                        dbsession.dataobjects.delete_many({'parent':ObjectId(screenid)})
                                                    else:
                                                        dbsession.dataobjects.update_many({'parent':ObjectId(screenid)},{"$pull": {"parent":ObjectId(screenid)}})                                                    
                                                if "testcases" in screen:
                                                    for testcase in screen["testcases"]:
                                                        dbsession.testcases.delete_one({'_id': testcase})
                                                        dbsession.testscenarios.update_one({'_id':scenario["_id"]},{"$pull": {"testcaseids": testcase}})                                                                                                   
                                            else:
                                                finalscr.append(screen)
                                    tempScenario["screens"]=finalscr                                          
                            testscenarios.append(tempModule['testscenarios'])
                            testscenario=testscenarios[0]
                            dbsession.mindmaps.update_one({'_id' : tempModule['_id']},  {'$set' : {'testscenarios':testscenario}})
                        dbsession.screens.delete_one({'_id': ObjectId(screenid)})
                    for testcaseid in testcaseids:
                        dbsession.testcases.delete_one({'_id': ObjectId(testcaseid)}) 
                                                      


            elif len(testcaseids)>0:
                
                for testcaseid in testcaseids:                    
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
                            dbsession.testscenarios.update_one({'_id':scenario["_id"]},{"$pull": {"testcaseids": ObjectId(testcaseid)}})
                            for screen in tempScenario["screens"]:
                                try:
                                        screen["testcases"].remove(ObjectId(testcaseid))
                                except:
                                    pass

                            testscenarios.append(tempScenario)
                        dbsession.mindmaps.update_one({'_id' : module['_id']},  {'$set' : {'testscenarios':testscenarios}})
                    dbsession.testcases.delete_one({'_id': ObjectId(testcaseid)}) 
            res= {'rows' : 'success'}
        except Exception as e:
            servicesException("deleteScenario", e, True)
        return jsonify(res)
    
    @app.route('/mindmap/deleteElementRepo',methods=['POST'])
    def deleteElementRepo():
        app.logger.debug("Inside deleteElementRepo")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)             
            dbsession=client[clientName]
            repoid=requestdata['repoId']
            elerepo = list(dbsession.elementrepository.find({'_id': ObjectId(repoid)},{"orderlist":1}))
            if len(elerepo) > 0:
                if "orderlist" in elerepo[0]["orderlist"]:
                    for order in elerepo[0]["orderlist"]:
                        dbsession.dataobjects.delete_one({"_id" : ObjectId(order)})
            dbsession.elementrepository.delete_one({"_id" : ObjectId(repoid)})
            res= {'rows' : 'success'}
        except Exception as e:
            servicesException("deleteElementRepo", e, True)
        return jsonify(res)


    def updateScenarioMindmap(dbsession,scenarioid,parentid):
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

    def updateScenarioMindmapETE(dbsession,scenarioid,parentid):
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
    
    def updateparent(dbsession,type,nodeid,parentid,action):
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

        
    def updateTestcaseIDsInScenario(dbsession,currentscenarioid,testcaseidsforscenario):
        dbsession.testscenarios.update_one({'_id':ObjectId(currentscenarioid)},{'$set':{'testcaseids':testcaseidsforscenario}})
        return

    def updateTestScenariosInModule(dbsession,currentmoduleid,idsforModule):
        dbsession.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':idsforModule}})
        return
    
    def updateTestScenariosInModuleMigration(dbsession,currentmoduleid,idsforModule):
        testCaseId = idsforModule[0]["_id"]
        testScreens = idsforModule[0]["screens"]
        dbsession.mindmaps.update_one({
            "_id": ObjectId(currentmoduleid),
            "testscenarios._id": testCaseId
        },
        {
            '$push': {'testscenarios.$.screens': {"$each": testScreens}}
        })
        return

    def updateScreenAndTestcase(dbsession,screenid,createdby,createdbyrole):
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                projectid=ObjectId(requestdata["projectid"])
                if 'param' in requestdata:
                    
                    screendetails=list(dbsession.elementrepository.aggregate([{'$match': {"projectid": projectid}},{
                                                                        '$lookup': {
                                                                            'from': "dataobjects",
                                                                            'localField': "_id", 
                                                                            'foreignField': "parent", 
                                                                            'as': "related_dataobjects"}},{
                                                                        '$project': {
                                                                            '_id': 1,
                                                                            'name': 1,
                                                                            'parent': 1,
                                                                            'statusCode': 1,
                                                                            'orderlist': 1,
                                                                            'related_dataobjects': 1 }}])) if requestdata['param'] == 'globalRepo'         else    list(dbsession.screens.aggregate([{'$match': {"projectid": projectid}},{
                                                                        '$lookup': {
                                                                            'from': "dataobjects",
                                                                            'localField': "_id", 
                                                                            'foreignField': "parent", 
                                                                            'as': "related_dataobjects"}},{
                                                                        '$project': {
                                                                            '_id': 1,
                                                                            'name': 1,
                                                                            'parent': 1,
                                                                            'statusCode': 1,
                                                                            'orderlist': 1,
                                                                            'related_dataobjects': 1 }}]))     
                else:
                    screendetails=list(dbsession.screens.aggregate([{'$match': {"projectid": projectid}},{
                                                                        '$lookup': {
                                                                            'from': "dataobjects",
                                                                            'localField': "_id", 
                                                                            'foreignField': "parent", 
                                                                            'as': "related_dataobjects"}},{
                                                                        '$project': {
                                                                            '_id': 1,
                                                                            'name': 1,
                                                                            'parent': 1,
                                                                            'statusCode': 1,
                                                                            'orderlist': 1,
                                                                            'related_dataobjects': 1 }}]))          
                screenids = [scr["_id"] for scr in screendetails]
                testcasedetails=list(dbsession.testcases.find({"screenid":{"$in":screenids}},{"_id":1,"name":1,"parent":1,"screenid":1}))                
                if 'param' in requestdata:
                    if requestdata['param'] == 'globalRepo':
                        scrn_det=[]
                        for screenid in screendetails:
                            if 'orderlist' in screenid:
                                for orderlist in screenid['orderlist']:
                                    dataobjectsParent = None
                                    if isinstance(orderlist, dict):        
                                       if isinstance(orderlist['_id'],dict):
                                          dataobjectsParent  = dbsession.dataobjects.find_one({'_id':ObjectId(orderlist["_id"]["_id"])},{'parent':1})
                                       else:
                                          dataobjectsParent  = dbsession.dataobjects.find_one({'_id':ObjectId(orderlist["_id"])},{'parent':1})                                            
                                    else:
                                      if orderlist != None:
                                         if len(orderlist) == 24:
                                            dataobjectsParent  = dbsession.dataobjects.find_one({'_id':ObjectId(orderlist)},{'parent':1}) 
                                            conuntorderlist = list(dbsession.elementrepository.find({"orderlist": orderlist}) )
                                    if len(conuntorderlist) > 1 :
                                        for i, value in enumerate(screenid['orderlist']):
                                                if value == orderlist:
                                                    if isinstance(value, dict):
                                                        screenid['orderlist'][i] = {'_id': value['_id'], 'flag': True}
                                                    else:
                                                        screenid['orderlist'][i] = {'_id': value, 'flag': True}
#-----------------------++++code might required for backup++++--------------------------------------------------
                                    # if dataobjectsParent != None:
                                    #     if len(dataobjectsParent['parent']) > 2 :
                                    #         for i, value in enumerate(screenid['orderlist']):
                                    #             if value == orderlist:
                                    #                 if isinstance(value, dict):
                                    #                     screenid['orderlist'][i] = {'_id': value['_id'], 'flag': True}
                                    #                 else:
                                    #                     screenid['orderlist'][i] = {'_id': value, 'flag': True}
                                    #     elif len(dataobjectsParent['parent']) == 2:
                                    #         reuseElementRepo = 0
                                    #         reuseScreen = 0
                                    #         for id in dataobjectsParent["parent"]:
                                    #             elementId = list(dbsession.elementrepository.find({"_id" : id},{"_id":1}))
                                    #             screenId=list(dbsession.screens.find({"_id" : id},{"_id":1}))
                                    #             if elementId:
                                    #                 reuseElementRepo=reuseElementRepo+1
                                    #             else:
                                    #                 reuseScreen=reuseScreen+1
                                                    
                                    #             # for elem in elementId:
                                    #             #     if dataiobject == elem["_id"]:
                                    #             #         reuse.append(True)
                                    #             #     else:
                                    #             #         reuse.append(False)
                                    #         print (reuseElementRepo)
                                    #         print (reuseScreen)
                                    #         if  reuseScreen == 2 or reuseElementRepo == 2:
                                    #             for i, value in enumerate(screenid['orderlist']):
                                    #                 if value == orderlist:
                                    #                     if isinstance(value, dict):
                                    #                         screenid['orderlist'][i] = {'_id': value['_id'], 'flag': True}
                                    #                     else:
                                    #                         screenid['orderlist'][i] = {'_id': value, 'flag': True}
                                scrn_det.append(screenid)                              
 
                            else:
                                screenid["orderlist"]=[]
                                scrn_det.append(screenid)
                        res={'rows':{'screenList':scrn_det,'testCaseList':testcasedetails}}
                else:
                    res={'rows':{'screenList':screendetails,'testCaseList':testcasedetails}}
            else:
                app.logger.warn("Empty data received. getScreens")
        except Exception as e:
            servicesException("getScreens", e, True)
        return jsonify(res)

    def checkScenarioNameExists(dbsession,projectid,name):
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
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
                        if( checkModuleNameExists(dbsession,moduledata["testsuiteName"],projectid) ):
                            error="Test suite name cannot be reused"
                            break
                        else:
                            currentmoduleid=saveTestSuite(dbsession,projectid,moduledata['testsuiteName'],versionnumber,createdthrough,userid,userroleid,type)
                    else:
                        oldModulename=getModuleName(dbsession,moduledata['testsuiteId'])
                        if oldModulename!=moduledata["testsuiteName"]:
                            if( checkModuleNameExists(dbsession,moduledata["testsuiteName"],projectid) ):
                                error="Test suite name cannot be reused"
                                break
                            else:
                                updateModuleName(dbsession,moduledata["testsuiteName"],projectid,moduledata['testsuiteId'],userid,userroleid)
                        currentmoduleid=moduledata['testsuiteId']
                    for scenariodata in moduledata['testscenarioDetails']:
                        if scenariodata["state"]=="created":
                            if( checkScenarioIDexists(dbsession,scenariodata["testscenarioName"],scenariodata["testscenarioid"]) ):
                                scenarioids.append({"_id":ObjectId(scenariodata["testscenarioid"]),"screens":[]})
                                updateparent(dbsession,"scenarios",scenariodata["testscenarioid"],currentmoduleid,"add")
                            else:
                                error="fail"
                                break
                        else:
                            scenarioids.append({"_id":ObjectId(scenariodata["testscenarioid"]),"screens":[]})
                if currentmoduleid is not None:
                    updateTestScenariosInModule(dbsession,currentmoduleid,scenarioids)
                    # dbsession.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':scenarioids}})
                for node in requestdata['deletednodes']:
                    if node[1] == "scenarios" :
                        updateScenarioMindmapETE(dbsession,node[0],node[2])
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

    def checkScenarioIDexists(dbsession,name,id):
        res=list(dbsession.testscenarios.find({"_id":ObjectId(id),"name":name,"deleted":False},{"_id":1}))
        if len(res)==1:
            return True
        else:
            return False

    def updateModuleName(dbsession,modulename,projectid,moduleid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.mindmaps.update_one({"_id":ObjectId(moduleid)},{"$set":{"name":modulename,"modifiedby":userid,"modifedon":modifiedon,"modifiedbyrole":userroleid}})
        return

    def updateScenarioName(dbsession,scenarioname,projectid,scenarioid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.testscenarios.update_one({"_id":ObjectId(scenarioid)},{"$set":{"name":scenarioname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateScreenName(dbsession,screenname,projectid,screenid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.screens.update_one({"_id":ObjectId(screenid)},{"$set":{"name":screenname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateTestcaseName(dbsession,testcasename,projectid,testcaseid,userid,userroleid):
        modifiedon=datetime.now()
        dbsession.testcases.update_one({"_id":ObjectId(testcaseid)},{"$set":{"name":testcasename,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def getModuleName(dbsession,moduleid):
        modulename=list(dbsession.mindmaps.find({"_id":ObjectId(moduleid),"deleted":False},{"name":1}))
        if len(modulename)!=0:
            res=modulename[0]["name"]
        else:
            res=None
        return res
    
    def getScenarioName(dbsession,scenarioid):
        scenarioname=list(dbsession.testscenarios.find({"_id":ObjectId(scenarioid),"deleted":False},{"name":1}))
        if len(scenarioname)!=0:
            res=scenarioname[0]["name"]
        else:
            res=None
        return res

    def getScreenName(dbsession,screenid):
        screename=list(dbsession.screens.find({"_id":ObjectId(screenid),"deleted":False},{"name":1}))
        if len(screename)!=0:
            res=screename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseName(dbsession,testcaseid):
        testcasename=list(dbsession.testcases.find({"_id":ObjectId(testcaseid),"deleted":False},{"name":1}))
        if len(testcasename)!=0:
            res=testcasename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseID(dbsession,screenid,testcasename):
        testcaseid = list(dbsession.testcases.find({"screenid": ObjectId(screenid),"name": testcasename,"deleted": False}, {"_id": 1}))
        if len(testcaseid) != 0:
            res = str(testcaseid[0]["_id"])
        else:
            res = None
        return res

    def getScreenID(dbsession,screenname,projectid):
        screenname=list(dbsession.screens.find({"projectid":ObjectId(projectid),"name":screenname,"deleted":False},{"_id":1}))
        if len(screenname)==1:
            return str(screenname[0]["_id"])
        else:   
            return None
        
    def get_creds_path():
        currexc = sys.executable
        db_keys = "".join(['N','i','n','E','t','e','E','n','6','8','d','A','t','a','B',
                            'A','s','3','e','N','c','R','y','p','T','1','0','n','k','3','y','S'])    
        try: currfiledir = os.path.dirname(os.path.abspath(__file__))
        except: currfiledir = os.path.dirname(currexc)
        currdir = os.getcwd()
        if os.path.basename(currexc).startswith("AvoAssureDAS"):
            currdir = os.path.dirname(currexc)
        elif os.path.basename(currexc).startswith("python"):
            currdir = currfiledir
            needdir = "das_internals"
            parent_currdir = os.path.abspath(os.path.join(currdir,".."))
            if os.path.isdir(os.path.abspath(os.path.join(parent_currdir,"..",needdir))):
                currdir = os.path.dirname(parent_currdir)
            elif os.path.isdir(parent_currdir + os.sep + needdir):
                currdir = parent_currdir
        internalspath = currdir + os.sep + "das_internals"
        credspath = internalspath + os.sep + ".tokens"
        config_path = currdir + os.sep + "server_config.json"
        config = open(config_path, 'r')
        conf = json.load(config)
        config.close()
        mongo_client_path=currdir+os.sep+"mongoClient"
        if platform.system() == "Windows":                
            mongo_client_path =mongo_client_path + os.sep+"windows"
        else:
            mongo_client_path =mongo_client_path + os.sep+"linux"
        
        if ('DB_IP' in os.environ and 'DB_PORT' in os.environ):
            DB_IP = str(os.environ['DB_IP']) 
            DB_PORT=str(os.environ['DB_PORT'])
            mongo_user= unwrap(conf['avoassuredb']['username'],db_keys)
            mongo_pass= unwrap(conf['avoassuredb']['password'],db_keys)
            authDB= "admin"
        else:
            DB_IP=conf['avoassuredb']["host"]
            DB_PORT=conf['avoassuredb']["port"]
            with open(credspath) as creds_file:
                creds = json.loads(unwrap(creds_file.read(),db_keys))
            mongo_user=creds['avoassuredb']['username']
            mongo_pass =creds['avoassuredb']['password']
            authDB= "avoassure"
        exportImportpath=conf['exportImportpath']
        return mongo_client_path,DB_IP, DB_PORT,exportImportpath,mongo_user,mongo_pass,authDB

    def unpad(data):
        return data[0:-ord(data[-1])]

    def unwrap(hex_data, key, iv=b'0'*16):
        data = codecs.decode(hex_data, 'hex')
        aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
        return unpad(aes.decrypt(data).decode('utf-8'))
    
    
    @app.route('/mindmap/exportMindmap', methods=['POST'])
    def exportMindmap():
        res = {'rows': 'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside exportMindmap.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]                
                userid=requestdata["userid"]                
                mongoFile,DB_IP,DB_PORT,expPath,mongo_user,mongo_pass,authDB=get_creds_path()                              
                mongoFile =mongoFile+ os.sep+"mongoexport"                
                expPath=expPath+os.sep+"ExportMindmap"+os.sep+ userid
                if (requestdata['query'] == 'exportMindmap'):
                    exportcheck=dbsession.Export_mindmap.find().count()
                    if exportcheck==0:
                        mindmapid = [ObjectId(i) for i in requestdata['mindmapId']]
                        if len(mindmapid)>0:
                            dbsession.Export_screens.drop()
                            dbsession.Export_testcases.drop()
                            dbsession.Export_dataobjects.drop()
                            dbsession.Export_testscenarios.drop()
                            dbsession.mindmaps.aggregate([{'$match': {"_id": {'$in':mindmapid}}},{"$out":"Export_mindmap"}])
                            dbsession.Export_mindmap.update_many({},{"$set":{"appType":requestdata["exportProjAppType"]}})
                            dbsession.testscenarios.aggregate([{'$match': {"parent": {'$in':mindmapid}}},
                            {"$out":"Export_testscenarios"}])
                            scenarioIds=list(dbsession.Export_testscenarios.aggregate( [
                                {"$group":{"_id":"null","scenarioids":{"$push":"$_id"}}}, 
                                {"$project":{"_id":0,"scenarioids":1}}
                                ] ))
                            if len(scenarioIds)>0:    
                                scenarios=scenarioIds[0]["scenarioids"]
                                dbsession.screens.aggregate([{'$match': {"parent": {'$in':scenarios}}},{"$out":"Export_screens"}])
                                screenIds=list(dbsession.Export_screens.aggregate( [
                                    {"$group":{"_id":"null","screenids":{"$push":"$_id"}}}, 
                                    {"$project":{"_id":0,"screenids":1}}
                                    ] ))
                                if len(screenIds)>0:  
                                    screens=screenIds[0]["screenids"]  
                                    dbsession.testcases.aggregate([{'$match': {"screenid": {'$in':screens}}},
                                        {"$out":"Export_testcases"}])
                                    dbsession.dataobjects.aggregate([{'$match': {"parent": {'$in':screens}}}
                                        ,{"$out":"Export_dataobjects"}])

                            p=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_mindmap -o {}{}Modules.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,expPath,os.sep))
                            q=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_testscenarios -o {}{}Testscenarios.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,expPath,os.sep))
                            r=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_screens -o {}{}screens.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,expPath,os.sep))
                            s=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_testcases -o {}{}Testcases.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,expPath,os.sep))
                            t=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_dataobjects -o {}{}Dataobjects.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,expPath,os.sep))
                            
                            if p ==q ==r==s==t==0:
                                queryresult="success"
                            else:
                                queryresult="fail"
                            dbsession.Export_mindmap.drop()
                            dbsession.Export_screens.drop()
                            dbsession.Export_testcases.drop()
                            dbsession.Export_dataobjects.drop()
                            dbsession.Export_testscenarios.drop()
                        
                            if queryresult:
                                res ={"rows":queryresult}
                        else:
                            app.logger.warn('Empty data received while exporting mindmap')
                    else:
                        res ={"rows":"InProgress"}
            else:
                app.logger.warn('Empty data received while exporting mindmap')
        except Exception as exportmindmapexc:
            dbsession.Export_mindmap.drop()
            dbsession.Export_screens.drop()
            dbsession.Export_testcases.drop()
            dbsession.Export_dataobjects.drop()
            dbsession.Export_testscenarios.drop()
            servicesException("exportMindmap", exportmindmapexc, True)
        return jsonify(json.loads(json_util.dumps(res)))
    def copyToProject(dbsession,mindmapid,userid,role,createdon,projectid):

        dbsession.Import_scenarios.drop()
        dbsession.Import_screens.drop()
        dbsession.Import_testcases.drop()
        dbsession.mindmap_testscenarios.drop()
        dbsession.scenario_testcase.drop()
        dbsession.screen_parent.drop()
        dbsession.testcase_parent.drop()
        dbsession.Import_module_ids.drop()
        dbsession.Import_scenario_ids.drop()
        dbsession.Import_screen_ids.drop()
        dbsession.Import_testcase_ids.drop()
        dbsession.dtobs.drop() 
        dbsession.dobjectsids.drop()
        dbsession.dobjects_parent.drop()
        

        dbsession.mindmaps.aggregate([
            {'$match': {"_id": {'$in':mindmapid},"type":"basic"}},
            {"$project":{"_id":0,
                        "old_id":"$_id",
                        "name":1,
                        "projectid":projectid,
                        "versionnumber":1 ,
                        "createdby":userid,
                        "createdbyrole":role,
                        "createdthrough":1,
                        "type":1,
                        "createdon":createdon,
                        "deleted":1,
                        "modifiedby":userid,
                        "modifiedbyrole":role,
                        "modifiedon":createdon,
                        "currentlyinuse":"",
                        "tsIds":"$testscenarios"
                        }},{"$out":"Import_mindmaps"}])
        dbsession.testscenarios.aggregate([
                {'$match': {"parent": {'$in':mindmapid}}},
            {"$project":{"_id":0,
                        "old_id":"$_id",
                        "name":1,
                        "projectid":projectid,
                        "old_parent":"$parent" ,
                        "versionnumber":1 ,
                        "createdby":userid,
                        "createdbyrole":role,
                        "createdon":createdon,
                        "deleted":1 ,
                        "modifiedby":userid,
                        "modifiedbyrole":role,
                        "modifiedon":createdon,
                        "testcaseids":1}},{"$out":"Import_scenarios"}])
        scenarioIds=list(dbsession.Import_scenarios.aggregate( [
                                {"$group":{"_id":"null","scenarioids":{"$push":"$old_id"}}}, 
                                {"$project":{"_id":0,"scenarioids":1}}
                                ] ))
        if len(scenarioIds)>0:    
            scenarios=scenarioIds[0]["scenarioids"]
            dbsession.screens.aggregate([{'$match': {"parent": {'$in':scenarios}}},
            {"$project":{
                        "_id":0,
                        "old_id":"$_id",
                        "name":1,
                        "projectid":projectid,
                        "old_parent":"$parent" ,
                        "versionnumber":1 ,
                        "createdby":userid,
                        "createdbyrole":role,
                        "createdon":createdon,
                        "deleted":1,
                        "modifiedby":userid,
                        "modifiedbyrole":role,
                        "modifiedon":createdon,
                        "screenshot":1,
                        "scrapedurl":1,
                        "orderlist":1}},{"$out":"Import_screens"}])
            screenIds=list(dbsession.Import_screens.aggregate( [
                {"$group":{"_id":"null","screenids":{"$push":"$old_id"}}}, 
                {"$project":{"_id":0,"screenids":1}}
                ] ))
            if len(screenIds)>0:  
                screens=screenIds[0]["screenids"]  
                dbsession.testcases.aggregate([{'$match': {"screenid": {'$in':screens}}},
                {"$project":{
                        "_id":0,
                            "old_id":"$_id",
                        "name":1,
                        "old_screenid":"$screenid" ,
                        "versionnumber":1 ,
                        "createdby":userid,
                        "createdbyrole":role,
                        "createdon":createdon,
                        "deleted":1,
                        "modifiedby":userid,
                        "modifiedbyrole":role,
                        "parent":1,
                        "modifiedon":createdon,
                        "steps":1,
                        "projectid":projectid
                        }},
                    {"$out":"Import_testcases"}])
                dbsession.dataobjects.aggregate([{'$match': {"parent": {'$in':screens}}}
                    ,{"$out":"dtobs"}])
       
        mindmapdata=dbsession.Import_mindmaps.aggregate([{"$project":{"_id":1,"tsIds":1}},{"$out":"Import_module_ids"}])
        mindmapIds=list(dbsession.Import_module_ids.find({}))
        scenariodata=dbsession.Import_scenarios.aggregate([{"$project":{"_id":1,"old_id":1,"testcaseids":1}},{"$out":"Import_scenario_ids"}])
        ScenarioIds=list(dbsession.Import_scenario_ids.find({}))
        screendata=dbsession.Import_screens.aggregate([{"$project":{"_id":1,"old_id":1,"old_parent":1}},{"$out":"Import_screen_ids"}])
        screenIds=list(dbsession.Import_screen_ids.find({}))
        testcasedata=dbsession.Import_testcases.aggregate([{"$project":{"_id":1,"old_id":1,"name":1,"old_screenid":1}},{"$out":"Import_testcase_ids"}])
        testcaseIds=list(dbsession.Import_testcase_ids.find({}))
        dataobjectsdata=dbsession.dtobs.aggregate([{"$project":{"_id":1,"parent":1}},{"$out":"dobjectsids"}])
        dataobjectids=list(dbsession.dobjectsids.find({}))

        dobjectsparent=[]
        for i in dataobjectids:
            dobarray={"_id":"","parent":[]}
            dobarray["_id"]=i["_id"]
            parentlist=i["parent"]
            for j in i["parent"]:
                for k in screenIds:
                    if j==k["old_id"]:
                        parentlist.append(k["_id"])
                        break
            dobarray["parent"].append(parentlist)
            dobarray["parent"]=dobarray["parent"][0]
            dobjectsparent.append(dobarray)
        
            
        mycoll=dbsession["dobjects_parent"]
        if len(dobjectsparent)>0:
            dbsession.dobjects_parent.insert_many(dobjectsparent)

        mdmaptscen=[]
        for i in mindmapIds:
            array2={"_id":"","testscenarios":[]}
            array2["_id"]=i["_id"]
            currentmoduleid=i["_id"]
            idsforModule=[]
            if "tsIds" in i:
                for tsId in i["tsIds"]:                    
                    if "_id" in tsId:
                        for j in ScenarioIds:
                            if tsId["_id"]==j["old_id"]:
                                currentscenarioid=j["_id"]
                                break
                        iddata1={"_id":currentscenarioid,"screens":[],"tag":[]}
                        if "screens" in tsId:
                            for screens in tsId["screens"]:                                
                                if "_id" in screens:
                                    for k in screenIds:
                                        if screens["_id"]==k["old_id"]:
                                            currentscreenid=k["_id"]
                                            break
                                    iddata2={"_id":currentscreenid,"testcases":[]}
                                    if "testcases" in screens:
                                        for testcase in screens["testcases"]:
                                            if testcase:                                            
                                                for l in testcaseIds:
                                                    if testcase:
                                                        if testcase == l["old_id"]: 
                                                            currenttestcaseid=l["_id"]
                                                            break                                                           
                                                iddata2["testcases"].append(currenttestcaseid)
                                    iddata1["screens"].append(iddata2)
                        if "tag" in tsId:
                            iddata1["tag"]=tsId["tag"]
                        idsforModule.append(iddata1)
            array2["testscenarios"].append(idsforModule)
            array2["testscenarios"]=array2["testscenarios"][0]
            mdmaptscen.append(array2)

        mycoll=dbsession["mindmap_testscenarios"]
        dbsession.mindmap_testscenarios.insert_many(mdmaptscen)

        scentestcase=[]
        for i in ScenarioIds:
            array1={"_id":"","testcaseids":[]}
            array1["_id"]=i["_id"]
            if "testcaseids" in i:
                for j in i["testcaseids"]:
                    for tcid in testcaseIds:
                        if j==tcid["old_id"]:
                                array1["testcaseids"].append(tcid["_id"])
                                break
            scentestcase.append(array1)
        
        mycoll=dbsession["scenario_testcase"]
        if len(scentestcase)>0:
            dbsession.scenario_testcase.insert_many(scentestcase)

        screenParent=[]
        for i in screenIds:
            nestarray={"_id":"","parent":[]}
            nestarray["_id"]=i["_id"]
            currentscreenidparent=i["_id"]                      
            for j in i["old_parent"]:
                for ts in ScenarioIds:
                    if j==ts["old_id"]:
                        nestarray["parent"].append(ts["_id"])
                        break
            screenParent.append(nestarray)
        
        mycoll=dbsession["screen_parent"]
        if len(screenParent)>0:
            dbsession.screen_parent.insert_many(screenParent)


        dbsession.dtobs.aggregate([
            {'$lookup': {
                        'from': "dobjects_parent",
                        'localField': "_id",
                        'foreignField': "_id",
                        'as': "parentdobs"
                        }
                                },{"$set":{"parent":"$parentdobs.parent"}},{"$unwind":"$parent"},
            { "$project" : {"parentdobs":0}},{"$out":"dtobs"}
                        ])

        dbsession.Import_mindmaps.aggregate([
            {"$match":{"tsIds":{"$exists":"true"},"projectid":projectid}},
            {'$lookup': {
                                    'from': "mindmap_testscenarios",
                                    'localField': "_id",
                                    'foreignField': "_id",
                                    'as': "mindmapscenariodata"
                                }
                                },{"$set":{"testscenarios":"$mindmapscenariodata.testscenarios"}},{"$unwind":"$testscenarios"},
            { "$project" : {"mindmapscenariodata":0}},{"$out":"Import_mindmaps"}
                        ])
                            
        dbsession.Import_scenarios.aggregate([
                                {'$match': {"projectid":projectid}},
                                
                                {'$lookup': {
                                    'from': "scenario_testcase",
                                    'localField': "_id",
                                    'foreignField': "_id",
                                    'as': "scentestcasedata"
                                }
                                }, {'$lookup': {
                                    'from': "Import_mindmaps",
                                    'localField': "old_parent",
                                    'foreignField': "old_id",
                                    'as': "moduledata"
                                }
                                },  {"$set":{"parent" : "$moduledata._id","testcaseids" :"$scentestcasedata.testcaseids"}},
                                {"$unwind":"$testcaseids"},                            
                                { "$project" : {  "scentestcasedata":0,  "moduledata":0                                                        
                                                
        }},
                                
                                {'$out':"Import_scenarios"}
                                ])

        dbsession.Import_screens.aggregate([
            {'$lookup': {
                                    'from': "screen_parent",
                                    'localField': "_id",
                                    'foreignField': "_id",
                                    'as': "scrparent"
                                }},{'$lookup': {
                                    'from': "dataobjects",
                                    'localField': "old_id",
                                    'foreignField': "parent",
                                    'as': "dataobjects"
                                }
                                },
                                {"$set":{"parent" : "$scrparent.parent","orderlist":{"$map": {
                                                    "input": "$dataobjects._id",
                                                    "as": "r",
                                                    "in": { "$toString": "$$r" }}}}},{"$unwind":"$parent"},
                                { "$project" : { "scrparent":0,"dataobjects":0
                                                }},{"$out":"Import_screens"}

        ])

        dbsession.Import_testcases.aggregate([
                                {"$match":{"old_screenid":{"$exists":"true"},"projectid":projectid}},
                                {'$lookup': {
                                    'from': "Import_screens",
                                    'localField': "old_screenid",
                                    'foreignField': "old_id",
                                    'as': "screendata"
                                }},
                                {"$unwind":"$screendata"},{'$set': {'parent': 0,"screenid":"$screendata._id"}},
                                { "$project" : {"screendata":0}},
                                    {"$out":"Import_testcases"}
                                    ])
        
        ImportedData=dbsession.Import_mindmaps.aggregate([{"$project":{"_id":1,"testscenarios":1}},{"$out":"Import_module_ids"}])
        moduleids=list(dbsession.Import_module_ids.find({}))
        queryresult=[]
        for i in moduleids:
            queryresult.append(i["_id"])
        testcaseparent=[]                    
        testcaseids=[]                  
        for i in moduleids:
            if "testscenarios" in i:
                for j in i["testscenarios"]:
                    if "screens" in j:
                        for k in j["screens"]:
                            if "testcases" in k:                                
                                for testcase in k["testcases"]:
                                        array3={"_id":"","parent":[]}                                    
                                        if testcase in testcaseids:                                            
                                            for q in testcaseparent:
                                                if q["_id"] == testcase:                                                    
                                                    parentinc=q["parent"]
                                                    parentinc=parentinc+1
                                                    q["parent"] = parentinc                                                                                            
                                                else:
                                                    continue                         
                                        else:                                            
                                            testcaseids.append(testcase)
                                            array3["_id"]=testcase								
                                            array3["parent"]=1
                                            testcaseparent.append(array3)

        mycoll=dbsession["testcase_parent"]
        dbsession.testcase_parent.delete_many({})
        if len(testcaseparent)>0:
            dbsession.testcase_parent.insert_many(testcaseparent)
            
        dbsession.Import_testcases.aggregate([
                                {"$match":{"old_screenid":{"$exists":"true"},"projectid":projectid}},
    
                                {'$lookup': {
                                    'from': "testcase_parent",
                                    'localField': "_id",
                                    'foreignField': "_id",
                                    'as': "testcaseparentdata"
                                }},{"$set":{"parent":"$testcaseparentdata.parent"}},{"$unwind":"$parent"},
                                { "$project" : {"testcaseparentdata":0,"projectid":0}},
                                    {"$out":"Import_testcases"}
                                    ])
        
                                
        
        dbsession.Import_mindmaps.aggregate([{"$unset":["tsIds","old_id"]},{"$out":"Import_mindmaps"}])
        dbsession.Import_scenarios.aggregate([{"$unset":["old_id","old_parent","screens"]},{"$out":"Import_scenarios"}])
        dbsession.Import_screens.aggregate([{"$unset":["old_id","old_parent","testcases"]},{"$out":"Import_screens"}])
        dbsession.Import_testcases.aggregate([{"$unset":["old_id","old_screenid"]},{"$out":"Import_testcases"}])

        dbsession.Import_mindmaps.aggregate([                                            
        {'$match': {"projectid":projectid}},
        {"$merge":{"into":"mindmaps","on":"_id","whenNotMatched":"insert"}}])                                            
        dbsession.Import_screens.aggregate([
        {'$match': {"projectid":projectid}},
        {"$merge":{"into":"screens","on":"_id","whenNotMatched":"insert"}}])
        dbsession.Import_scenarios.aggregate([
        {'$match': {"projectid":projectid}},
        {"$merge":{"into":"testscenarios","on":"_id","whenNotMatched":"insert"}}])
        dbsession.Import_testcases.aggregate([
        {"$merge":{"into":"testcases","on":"_id","whenNotMatched":"insert"}}])
        dbsession.dtobs.aggregate([
        {"$merge":{"into":"dataobjects","on":"_id","whenMatched":"replace"}}]) 
        
        dbsession.Import_mindmaps.drop()
        dbsession.Import_scenarios.drop()
        dbsession.Import_screens.drop()
        dbsession.Import_testcases.drop()
        dbsession.mindmap_testscenarios.drop()
        dbsession.scenario_testcase.drop()
        dbsession.screen_parent.drop()
        dbsession.testcase_parent.drop()
        dbsession.Import_module_ids.drop()
        dbsession.Import_scenario_ids.drop()
        dbsession.Import_screen_ids.drop()
        dbsession.Import_testcase_ids.drop()
        dbsession.dtobs.drop() 
        dbsession.dobjectsids.drop()
        dbsession.dobjects_parent.drop()
        
        
        if queryresult:
            return queryresult
        else:
            return None

    @app.route('/mindmap/exportToProject', methods=['POST'])
    def exportToProject():
        res = {'rows': 'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside exportToProject.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                if (requestdata['query'] == 'exportToProject'):
                    mindmapid = [ObjectId(i) for i in requestdata['mindmapId']]
                    userid=ObjectId(requestdata["userid"])
                    role=ObjectId(requestdata["role"])
                    createdon = datetime.now()
                    projectid=ObjectId(requestdata["projectId"])
                    exportToProjectCheck=dbsession.Import_mindmaps.find({}).count()
                    if exportToProjectCheck == 0: 
                        queryresult=copyToProject(dbsession,mindmapid,userid,role,createdon,projectid)
                        if queryresult:
                            res = {'rows': queryresult}
                    else:
                        res={'rows': "InProgress"}
                
            else:
                app.logger.warn('Empty data received while exporting mindmap')
        except Exception as exportToProjectexc:
            dbsession.Import_mindmaps.drop()
            dbsession.Import_scenarios.drop()
            dbsession.Import_screens.drop()
            dbsession.Import_testcases.drop()
            dbsession.mindmap_testscenarios.drop()
            dbsession.scenario_testcase.drop()
            dbsession.screen_parent.drop()
            dbsession.testcase_parent.drop()
            dbsession.Import_module_ids.drop()
            dbsession.Import_scenario_ids.drop()
            dbsession.Import_screen_ids.drop()
            dbsession.Import_testcase_ids.drop()
            dbsession.dtobs.drop() 
            dbsession.dobjectsids.drop()
            dbsession.dobjects_parent.drop()
             
            servicesException("exportToProject", exportToProjectexc, True)
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

    @app.route('/mindmap/jsonToMindmap', methods=['POST'])
    def jsonToMindmap():
        res = {'rows': 'fail'}
        try:
            requestdata = loads(request.data)            
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                importtype=requestdata["importtype"]                       
                importproj=ObjectId(requestdata["importproj"])                           
                userid=ObjectId(requestdata["userid"])
                role=ObjectId(requestdata["role"])                
                createdon = datetime.now()
                jsonToMindmap=dbsession.mindmapnames.find({}).count()
                if jsonToMindmap==0:
                    dbsession.jsontomindmap.drop()
                    dbsession.screennames.drop()
                    dbsession.testscenariosnames.drop()
                    dbsession.testscenario_testcase.drop()
                    dbsession.testcasenames.drop()
                    dbsession.testcase_parent_json_Import.drop()
                    dbsession.Module_Import_json_ids.drop()
                    dbsession.mindmap_mapping.drop()
                    dbsession.scenario_testcase_json_Import.drop()
                    dbsession.screen_parent_json_Import.drop()
                    dbsession.scenariotestcasemapping.drop()
                    dbsession.scr_parent.drop()
                    
                    mongoFile,DB_IP,DB_PORT,impJsonPath,mongo_user,mongo_pass,authDB=get_creds_path()                    
                    mongoFile = mongoFile +os.sep+"mongoimport"
                    impJsonPath=impJsonPath+os.sep+"ImportMindmap"+os.sep+ importtype                    
                    
                    js=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection jsontomindmap --file {}{}{}.json  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impJsonPath,os.sep,userid))
                                        

                    dbsession.jsontomindmap.aggregate([
                    {"$project":{"name":1,"testscenarionames":"$testscenarios","_id":0}},{"$out":"mindmapnames"}])
                    dbsession.mindmapnames.aggregate([
                
                            { "$group": {
                                "_id": '$name',
                                "doc": { "$first": '$$ROOT' }
                            } },
                            { "$replaceRoot": {
                                "newRoot": '$doc'
                            } },
                            { "$out": 'mindmapnames' }
                            ], allowDiskUse= True)
                
                        
                    dbsession.jsontomindmap.aggregate([{"$unwind":"$testscenarios"},
                    {"$set":{"parentname":"$name","name":"$testscenarios.name"}},
                    {"$project":{"parentname":1,"name":1,"_id":0}},{ "$group": {
                                "_id": '$name','parentname':{ "$first": '$parentname' }}},{"$project":{"_id":0,"name":"$_id","parentname":1,"testcases":[]}},{"$out":"testscenariosnames"}])

                    dbsession.jsontomindmap.aggregate([{"$match":{"testscenarios.screens.0": {"$exists": "true"},"testscenarios.screens.testcases.0": {"$exists": "true"}}},{"$unwind":"$testscenarios"},
                    {"$unwind":"$testscenarios.screens"},{"$unwind":"$testscenarios.screens.testcases"},
                    {"$set":{"parentname":"$name","name":"$testscenarios.name"}},
                    {"$project":{"parentname":1,"name":1,"_id":0,"testcases": { "$concat": [ "$testscenarios.screens.name", "_", "$testscenarios.screens.testcases" ] }}},{ "$group": {
                                "_id": '$name','testcases':{ "$push": '$testcases' }}},{"$project":{"_id":0,"name":"$_id","parentname":1,"testcases":1}},{"$out":"testscenario_testcase"}])

                    dbsession.testscenariosnames.aggregate([
                
                            { "$group": {
                                "_id": '$name',
                                "doc": { "$first": '$$ROOT' }
                            } },
                            { "$replaceRoot": {
                                "newRoot": '$doc'
                            } },
                            { "$out": 'testscenariosnames' }
                            ], allowDiskUse= True)
                    
                    dbsession.testscenario_testcase.aggregate([
                
                            { "$group": {
                                "_id": '$name',
                                "doc": { "$first": '$$ROOT' }
                            } },
                            { "$replaceRoot": {
                                "newRoot": '$doc'
                            } },
                            { "$out": 'testscenario_testcase' }
                            ], allowDiskUse= True)
                    
                    dbsession.testscenario_testcase.aggregate([{'$lookup': {
                                                'from': "testscenariosnames",
                                                'localField': "name",
                                                'foreignField': "name",
                                                'as': "scentestcasedata"
                                            }},{"$unwind":"$scentestcasedata"},{"$set":{"_id":"$scentestcasedata._id"}},{"$out":"testscenario_testcase"}
                        ])
                    dbsession.testscenario_testcase.aggregate([
                        {"$merge":{"into":"testscenariosnames","on":"_id","whenMatched": [{
                            "$set": {"testcases": '$$new.testcases'}}]}}])     

                    dbsession.jsontomindmap.aggregate([{"$unwind":"$testscenarios"},{"$unwind":"$testscenarios.screens"},
                    {"$set":{"parentname":"$testscenarios.name","name":"$testscenarios.screens.name"}},
                    {"$project":{"parentname":1,"name":1,"_id":0}},{"$out":"screennames"}])
                    
                    dbsession.jsontomindmap.aggregate([{"$unwind":"$testscenarios"},{"$unwind":"$testscenarios.screens"},{"$unwind":"$testscenarios.screens.testcases"},
                    {"$set":{"scenarioname":"$testscenarios.name","parentname":"$testscenarios.screens.name","name":"$testscenarios.screens.testcases"}},
                    {"$project":{"parentname":1,"name":1,"_id":0, "duplicatecheck": { "$concat": [ "$testscenarios.screens.name", "_", "$testscenarios.screens.testcases" ] }}},{"$out":"testcasenames"}])
                    
                    
                    dbsession.testcasenames.aggregate([
                
                            { "$group": {
                                "_id": '$duplicatecheck',
                                "doc": { "$first": '$$ROOT' }
                            } },
                            { "$replaceRoot": {
                                "newRoot": '$doc'
                            } },
                            { "$out": 'testcasenames' }
                            ], allowDiskUse= True)
                    
                    
                    
                    # dbsession.testscenariosnames.aggregate([{"$unwind":"$testcasenames"},{"$unwind":"$testcasenames"},{"$group":{"_id":"$_id","testcases":{"$push" :"$testcasenames"}}},{"$out":"scenariotestcasemapping"}])
                    
                    dbsession.screennames.aggregate([{"$group":{"_id":"$name","parentnames":{"$push":"$parentname"}}},{"$out":"scr_parent"}])

                    dbsession.screennames.aggregate([
                
                            { "$group": {
                                "_id": '$name',
                                "doc": { "$first": '$$ROOT' }
                            } },
                            { "$replaceRoot": {
                                "newRoot": '$doc'
                            } },
                            { "$out": 'screennames' }
                            ], allowDiskUse= True)               
                    
                    mmIds=list(dbsession.mindmapnames.find({}))
                    tsIds=list(dbsession.testscenariosnames.find({}))
                    scrIds=list(dbsession.screennames.find({}))
                    tcIds=list(dbsession.testcasenames.find({}))
                    scen_tc=list(dbsession.scenariotestcasemapping.find({}))
                    scr_parent=list(dbsession.scr_parent.find({}))
                
                    mmmappings=[]
                    if len(mmIds)>0:
                        for mm in mmIds:
                            data={"_id":"","testscenarios":[]}
                            data["_id"]=mm["_id"]
                            if "testscenarionames" in mm:
                                for tsname in mm["testscenarionames"]:
                                    data1={"_id":"","screens":[], "tag":[]}
                                    for ts in tsIds:                                        
                                        if tsname["name"]==ts["name"]:
                                            data1["_id"]=ts["_id"]
                                            break
                                    if "screens" in tsname: 
                                        for scrname in tsname["screens"]:
                                            data2={"_id":"","testcases":[]}
                                            for scr in scrIds:                                                
                                                if scrname["name"]==scr["name"]:
                                                    data2["_id"]=scr["_id"]
                                                    break
                                            if "testcases" in scrname:
                                                for tcname in scrname["testcases"]:
                                                    for tc in tcIds:
                                                        if tcname==tc["name"]:
                                                            if scrname["name"] == tc["parentname"]:
                                                                data2["testcases"].append(tc["_id"])
                                                                break
                                            data1["screens"].append(data2)
                                    if "tag" in tsname: 
                                        data1["tag"]=tsname["tag"]
                                    data["testscenarios"].append(data1)
                            mmmappings.append(data)
                    
                    mycoll=dbsession["mindmap_mapping"]
                    dbsession.mindmap_mapping.delete_many({})
                    if len(mmmappings)>0:
                        dbsession.mindmap_mapping.insert_many(mmmappings) 

                    scentestcase=[]
                    for i in tsIds:
                        array1={"_id":"","testcaseids":[]}
                        array1["_id"]=i["_id"]
                        if "testcases" in i:
                            for j in i["testcases"]:
                                for tcid in tcIds:
                                    if j==tcid["duplicatecheck"]:
                                            array1["testcaseids"].append(tcid["_id"])
                        scentestcase.append(array1)
                    
                    mycoll=dbsession["scenario_testcase_json_Import"]
                    dbsession.scenario_testcase_json_Import.delete_many({})
                    if len(scentestcase)>0:
                        dbsession.scenario_testcase_json_Import.insert_many(scentestcase)
                    
                    screenParent=[]
                    for i in scr_parent:
                        nestarray={"_id":"","parent":[]}
                        nestarray["_id"]=i["_id"]
                        # currentscreenidparent=i["_id"]                      
                        for j in i["parentnames"]:
                            for ts in tsIds:
                                if j==ts["name"]:
                                    nestarray["parent"].append(ts["_id"])
                        screenParent.append(nestarray)
                    
                    mycoll=dbsession["screen_parent_json_Import"]
                    dbsession.screen_parent_json_Import.delete_many({})
                    if len(screenParent)>0:
                        dbsession.screen_parent_json_Import.insert_many(screenParent)
                    mindmapId=list(dbsession.mindmapnames.find({},{"_id":1}))
                    queryresult=[]
                    for i in mindmapId:
                        queryresult.append(i["_id"])
                    
                    dbsession.testscenariosnames.aggregate([                                          
                                                
                                                {'$lookup': {
                                                    'from': "scenario_testcase_json_Import",
                                                    'localField': "_id",
                                                    'foreignField': "_id",
                                                    'as': "scentestcasedata"
                                                }
                                                }, {'$lookup': {
                                                    'from': "mindmapnames",
                                                    'localField': "parentname",
                                                    'foreignField': "name",
                                                    'as': "moduledata"
                                                }
                                                },  {"$set":{"id": {"$toString": "$_id"},'versionnumber': 0,"deleted":False,"parent" : "$moduledata._id","testcaseids":{ "$cond": [{"$eq": [{"$size": '$scentestcasedata'}, 0] }, [[]], '$scentestcasedata.testcaseids'] }}},
                                                {"$unwind":"$testcaseids"} ,                             
                                                
                                                {"$project":{"_id":1,
                                                            "name": { "$concat": [ "$name", "_", "$id" ] },
                                                            "projectid":importproj,
                                                            "parent":1,
                                                            "versionnumber":1 ,
                                                            "createdby":userid,
                                                            "createdbyrole":role,
                                                            "createdon":createdon,
                                                            "deleted":1,
                                                            "modifiedby":userid,
                                                            "modifiedbyrole":role,
                                                            "modifiedon":createdon,
                                                            "testcaseids":1}},                                                                    
                                                            {'$out':"testscenariosnames"}
                                                            ])
                    
                    dbsession.mindmapnames.aggregate([
                            {"$match":{"testscenarionames":{"$exists":"true"}}},
                            {'$lookup': {
                                                    'from': "mindmap_mapping",
                                                    'localField': "_id",
                                                    'foreignField': "_id",
                                                    'as': "mindmapscenariodata"
                                                }
                                                },{"$set":{"id": {"$toString": "$_id"},'versionnumber': 0,"deleted":False,"testscenarios":"$mindmapscenariodata.testscenarios"}},{"$unwind":"$testscenarios"},
                            {"$project":{"_id":1,
                                "name": { "$concat": [ "$name", "_", "$id" ] },
                                "projectid":importproj,
                                "versionnumber":1 ,
                                "createdby":userid,
                                "createdbyrole":role,
                                "createdthrough":"Web",
                                "type":"basic",
                                "createdon":createdon,
                                "deleted":1,
                                "modifiedby":userid,
                                "modifiedbyrole":role,
                                "modifiedon":createdon,
                                "currentlyinuse":"",
                                "testscenarios":1}},
                                {"$out":"mindmapnames"}
                                        ])
                    ImportedData=dbsession.mindmapnames.aggregate([{"$project":{"_id":1,"testscenarios":1}},{"$out":"Module_Import_json_ids"}])
                    mindmapId=list(dbsession.Module_Import_json_ids.find({}))
                    queryresult=[]
                    for i in mindmapId:
                        queryresult.append(i["_id"])
                    testcaseparent=[]                    
                    testcaseids=[]                  
                    for i in mindmapId:
                        if "testscenarios" in i:
                            for j in i["testscenarios"]:
                                if "screens" in j:
                                    for k in j["screens"]:
                                        if "testcases" in k:                                
                                            for testcase in k["testcases"]:
                                                    array3={"_id":"","parent":[]}                                    
                                                    if testcase in testcaseids:                                            
                                                        for q in testcaseparent:
                                                            if q["_id"] == testcase:                                                    
                                                                parentinc=q["parent"]
                                                                parentinc=parentinc+1
                                                                q["parent"] = parentinc                                                                                            
                                                            else:
                                                                continue                         
                                                    else:                                            
                                                        testcaseids.append(testcase)
                                                        array3["_id"]=testcase								
                                                        array3["parent"]=1
                                                        testcaseparent.append(array3)

                    mycoll=dbsession["testcase_parent_json_Import"]
                    dbsession.testcase_parent_json_Import.delete_many({})
                    if len(testcaseparent)>0:
                        dbsession.testcase_parent_json_Import.insert_many(testcaseparent)
                     
                    dbsession.testcasenames.aggregate([            
                                            {'$lookup': {
                                                'from': "testcase_parent_json_Import",
                                                'localField': "_id",
                                                'foreignField': "_id",
                                                'as': "testcaseparentdata"
                                            }},
                                            {'$lookup': {
                                                'from': "screennames",
                                                'localField': "parentname",
                                                'foreignField': "name",
                                                'as': "screen"
                                            }},
                                            {"$set":{"id": {"$toString": "$_id"},'versionnumber': 0,"deleted":False,"parent":"$testcaseparentdata.parent","screenid":"$screen._id"}},{"$unwind":"$parent"},{"$unwind":"$screenid"},
                                            {"$project":{
                                                "_id":1,                                                
                                                "name": { "$concat": [ "$name", "_", "$id" ] },
                                                "screenid":1,
                                                "versionnumber":1 ,
                                                "createdby":userid,
                                                "createdbyrole":role,
                                                "createdon":createdon,
                                                "deleted":1,
                                                "parent":1,
                                                "modifiedby":userid,
                                                "modifiedbyrole":role,
                                                "modifiedon":createdon,
                                                "steps":[],
                                            
                                                }},
                                                {"$out":"testcasenames"}
                                                ])
                    dbsession.screennames.aggregate([
                        {'$lookup': {
                                                'from': "screen_parent_json_Import",
                                                'localField': "name",
                                                'foreignField': "_id",
                                                'as': "scrparent"
                                            }},
                                            {"$set":{"id": {"$toString": "$_id"},'versionnumber': 0,"deleted":False,"parent" : "$scrparent.parent",}},
                                            {"$unwind":"$parent"},
                                            {"$project":{
                                                "_id":1,                                            
                                                "name": { "$concat": [ "$name", "_", "$id" ] },
                                                "projectid":importproj,
                                                "parent":1,
                                                "versionnumber":1 ,
                                                "createdby":userid,
                                                "createdbyrole":role,
                                                "createdon":createdon,
                                                "deleted":1,
                                                "modifiedby":userid,
                                                "modifiedbyrole":role,
                                                "modifiedon":createdon,
                                                "screenshot":"",
                                                "scrapedurl":"",
                                                "orderlist":[]}},
                                            {"$out":"screennames"}
                    ])
                    
                    dbsession.mindmapnames.aggregate([                                            
                    {'$match': {"projectid":importproj}},
                    {"$merge":{"into":"mindmaps","on":"_id","whenNotMatched":"insert"}}])                                            
                    dbsession.screennames.aggregate([
                    {'$match': {"projectid":importproj}},
                    {"$merge":{"into":"screens","on":"_id","whenNotMatched":"insert"}}])
                    dbsession.testscenariosnames.aggregate([
                    {'$match': {"projectid":importproj}},
                    {"$merge":{"into":"testscenarios","on":"_id","whenNotMatched":"insert"}}])
                    dbsession.testcasenames.aggregate([
                    {"$merge":{"into":"testcases","on":"_id","whenNotMatched":"insert"}}])

                    dbsession.mindmapnames.drop()
                    dbsession.screennames.drop()
                    dbsession.testscenariosnames.drop()
                    dbsession.testscenario_testcase.drop()
                    dbsession.testcasenames.drop()
                    dbsession.testcase_parent_json_Import.drop()
                    dbsession.Module_Import_json_ids.drop()
                    dbsession.mindmap_mapping.drop()
                    dbsession.scenario_testcase_json_Import.drop()
                    dbsession.screen_parent_json_Import.drop()
                    dbsession.scenariotestcasemapping.drop()
                    dbsession.scr_parent.drop()
                    dbsession.jsontomindmap.drop()
                    if queryresult:
                                res={'rows':queryresult}                
                else:
                    res={'rows': "InProgress"}
                 
            else:
                app.logger.warn('Empty data received while importing mindmap')

        except Exception as jsonToMindmapexc:
            dbsession.mindmapnames.drop()
            dbsession.screennames.drop()
            dbsession.testscenariosnames.drop()
            dbsession.testscenario_testcase.drop()
            dbsession.testcasenames.drop()
            dbsession.testcase_parent_json_Import.drop()
            dbsession.Module_Import_json_ids.drop()
            dbsession.mindmap_mapping.drop()
            dbsession.scenario_testcase_json_Import.drop()
            dbsession.screen_parent_json_Import.drop()
            dbsession.scenariotestcasemapping.drop()
            dbsession.scr_parent.drop()
            dbsession.jsontomindmap.drop()
            
            servicesException("jsonToMindmap", jsonToMindmapexc, True)
        return jsonify(res)
    @app.route('/mindmap/importMindmap', methods=['POST'])
    def importMindmap():
        res = {'rows': 'fail'}
        try:
            requestdata = loads(request.data)
            app.logger.debug("Inside importMindmap.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                importMindmapcheck= dbsession.Module_Import.find({}).count()
                if importMindmapcheck==0:                    
                    dbsession.Screen_Import.drop()
                    dbsession.Scenario_Import.drop()
                    dbsession.Testcase_Import.drop()
                    dbsession.Dataobjects_Import.drop()
                    dbsession.mindmap_testscenarios_Import.drop()
                    dbsession.scenario_testcase_Import.drop()
                    dbsession.screen_parent_Import.drop()
                    dbsession.testcase_parent_Import.drop()
                    dbsession.dobjects_parent_Import.drop()
                    dbsession.Module_Import_ids.drop()
                    dbsession.Scenario_Import_ids.drop()
                    dbsession.Scenario_Import_tc.drop()
                    dbsession.Screen_Import_ids.drop()
                    dbsession.Testcase_Import_ids.drop()                    
                    dbsession.testcase_steps.drop()                                                          
                    userid=ObjectId(requestdata["userid"])
                    role=ObjectId(requestdata["role"])
                    projectid=ObjectId(requestdata["projectid"])                                        
                    createdon = datetime.now()                
                    
                    mongoFile,DB_IP,DB_PORT,impPath,mongo_user,mongo_pass,authDB=get_creds_path()                                   
                    
                    mongoFile = mongoFile +os.sep+"mongoimport"                    
                    impPath=impPath+os.sep+"ImportMindmap"+os.sep+ str(userid)
                
                    do=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Dataobjects_Import --file {}{}Dataobjects.json --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impPath,os.sep))
                    mm=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Module_Import --file {}{}Modules.json --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impPath,os.sep))
                    ts=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Scenario_Import --file {}{}Testscenarios.json --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impPath,os.sep))
                    sr=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Screen_Import --file {}{}screens.json --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impPath,os.sep))
                    tc=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Testcase_Import --file {}{}Testcases.json --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,impPath,os.sep))
                     
                    dbsession.Module_Import.aggregate([
                    {"$project":{"_id":0,"old_id":"$_id",
                            "name":1,
                            "projectid":projectid,
                            "versionnumber":1 ,
                            "createdby":userid,
                            "createdbyrole":role,
                            "createdthrough":1,
                            "type":"basic",
                            "createdon":createdon,
                            "deleted":1,
                            "modifiedby":userid,
                            "modifiedbyrole":role,
                            "modifiedon":createdon,
                            "currentlyinuse":"",
                            "tsIds":"$testscenarios"}},{"$out":"Module_Import"}
                    ])
                    
                    duplicatemod=list(dbsession.Module_Import.aggregate([
                                {"$group" : { "_id": "$name", "count": { "$sum": 1 } } },
                                {"$match": {"_id" :{ "$ne" : "null" } , "count" : {"$gt": 1} } }, 
                                {"$project": {"name" : "$_id", "_id" : 0} }
                            ]))
                    if len(duplicatemod)>0:
                        dbsession.Module_Import.drop()
                        dbsession.Screen_Import.drop()
                        dbsession.Scenario_Import.drop()
                        dbsession.Testcase_Import.drop()
                        dbsession.Dataobjects_Import.drop()
                        res={'rows': "dupMod"}
                    else:
                        dbsession.Scenario_Import.aggregate([{"$project":{"_id":0,
                                            "old_id":"$_id",
                                            "name":1,
                                            "projectid":projectid,
                                            "old_parent":"$parent" ,
                                            "versionnumber":1 ,
                                            "createdby":userid,
                                            "createdbyrole":role,
                                            "createdon":createdon,
                                            "deleted":1,
                                            "modifiedby":userid,
                                            "modifiedbyrole":role,
                                            "modifiedon":createdon,
                                            "testcaseids":1}},{"$out":"Scenario_Import"}])
                        duplicatesce=list(dbsession.Scenario_Import.aggregate([
                                    {"$group" : { "_id": "$name", "count": { "$sum": 1 } } },
                                    {"$match": {"_id" :{ "$ne" : "null" } , "count" : {"$gt": 1} } }, 
                                    {"$project": {"name" : "$_id", "_id" : 0} }
                                ]))
                        if len(duplicatesce)>0:
                            dbsession.Module_Import.drop()
                            dbsession.Screen_Import.drop()
                            dbsession.Scenario_Import.drop()
                            dbsession.Testcase_Import.drop()
                            dbsession.Dataobjects_Import.drop()
                            res={'rows': "dupSce"}
                        else:
                            dbsession.Screen_Import.aggregate([{"$project":{
                                                    "_id":0,
                                                    "old_id":"$_id",
                                                    "name":1,
                                                    "projectid":projectid,
                                                    "old_parent":"$parent",
                                                    "versionnumber":1 ,
                                                    "createdby":userid,
                                                    "createdbyrole":role,
                                                    "createdon":createdon,
                                                    "deleted":1,
                                                    "modifiedby":userid,
                                                    "modifiedbyrole":role,
                                                    "modifiedon":createdon,
                                                    "screenshot":1,
                                                    "scrapedurl":1,
                                                    "orderlist":1}},{"$out":"Screen_Import"}])
                            
                            dbsession.Testcase_Import.aggregate([{"$project":{
                                                    "_id":0,
                                                        "old_id":"$_id",
                                                    "name":1,
                                                    "old_screenid":"$screenid" ,
                                                    "versionnumber":1 ,
                                                    "createdby":userid,
                                                    "createdbyrole":role,
                                                    "createdon":createdon,
                                                    "deleted":1,
                                                    "modifiedby":userid,
                                                    "modifiedbyrole":role,
                                                    "parent":1,
                                                    "modifiedon":createdon,
                                                    "steps":1,
                                                    "projectid":projectid,
                                                    "datatables":1
                                                    }},{"$out":"Testcase_Import"}])
                            
                    
                            dbsession.Dataobjects_Import.aggregate( [
                            
                        
                            {"$set":{"old_id":"$_id","old_parent" :"$parent"}},
                            
                            { "$project": {"_id":0,"parent":0
                                    } },
                            {"$out":"Dataobjects_Import"}])
                        
                        
                            dbsession.Module_Import.aggregate([{"$project":{"_id":1,"tsIds":1}},{"$out":"Module_Import_ids"}])
                            mindmapIds=list(dbsession.Module_Import_ids.find({}))
                            dbsession.Scenario_Import.aggregate([{"$project":{"_id":1,"old_id":1,"testcaseids":1}},{"$out":"Scenario_Import_ids"}])
                            ScenarioIds=list(dbsession.Scenario_Import_ids.find({}))
                            dbsession.Screen_Import.aggregate([{"$project":{"_id":1,"old_id":1,"old_parent":1}},{"$out":"Screen_Import_ids"}])
                            screenIds=list(dbsession.Screen_Import_ids.find({}))
                            dbsession.Testcase_Import.aggregate([{"$project":{"_id":1,"old_id":1,"name":1,"old_screenid":1}},{"$out":"Testcase_Import_ids"}])
                            testcaseIds=list(dbsession.Testcase_Import_ids.find({}))
                            

                            mindmapId=list(dbsession.Module_Import_ids.find({},{"_id":1}))
                            queryresult=[]
                            for i in mindmapId:
                                queryresult.append(i["_id"])

                            dbsession.Dataobjects_Import.aggregate([{"$lookup":{"from":"Screen_Import",
                                "localField":"old_parent",
                                "foreignField":"old_id",
                                "as":"screens"}},{"$group":{"_id":"$_id","parent":{"$push":"$screens._id"}}},{"$unwind":"$parent"},{"$out":"dobjects_parent_Import"}])
                        

                            for i in mindmapIds:
                                testscen=[]
                                if "tsIds" in i:                                    
                                    for tsId in i["tsIds"]:
                                        if tsId:
                                            if "_id" in tsId:
                                                for j in ScenarioIds:
                                                    if tsId["_id"]==j["old_id"]:
                                                        tsId["_id"]=j["_id"]
                                                        break
                                                testscen.append(tsId)
                                i["tsIds"]=testscen
                                                                                 
                            
                            for i in mindmapIds:
                                if "tsIds" in i:
                                    for tsId in i["tsIds"]:
                                        scrndt=[]
                                        if "screens" in tsId:
                                            for screens in tsId["screens"]:
                                                if screens:
                                                    if "_id" in screens:
                                                        for k in screenIds:
                                                            if screens["_id"]==k["old_id"]:
                                                                screens["_id"]=k["_id"]
                                                                break
                                                        scrndt.append(screens)
                                        tsId["screens"]=scrndt
                                                
                            
                            mdmaptscen=[]
                            for i in mindmapIds:                                               
                                if "tsIds" in i:
                                    for tsId in i["tsIds"]:                           
                                        if "screens" in tsId:
                                            for screens in tsId["screens"]:
                                                testcases=[]
                                                if "testcases" in screens:
                                                    for testcase in screens["testcases"]:
                                                        if testcase:
                                                            for l in testcaseIds:
                                                                if testcase == l["old_id"]:                                                             
                                                                    testcases.append(l["_id"])
                                                                    break
                                                            del testcase
                                                    screens["testcases"]=[]
                                                    screens["testcases"].append(testcases)
                                                    screens["testcases"]=screens["testcases"][0]
                                                            


                            mycoll=dbsession["mindmap_testscenarios_Import"]
                            dbsession.mindmap_testscenarios_Import.delete_many({})
                            if len(mindmapIds)>0:
                                dbsession.mindmap_testscenarios_Import.insert_many(mindmapIds)
                            dbsession.Scenario_Import_ids.aggregate([{'$lookup': {
                                                        'from': "Testcase_Import_ids",
                                                        'localField': "testcaseids",
                                                        'foreignField': "old_id",
                                                        'as': "testcases"
                                }},
                                {"$unwind":"$testcaseids"},{"$set": { "testcases":{ "$cond": [{"$eq": [{"$size": '$testcases'}, 0] }, [[]], '$testcases'] }}},{"$unwind":"$testcases"}, 
                                {"$set":{"testcaseids":{ "$cond": { "if": { "$ne": ["$testcaseids" , "$testcases.old_id" ] }, "then":"na", "else": "$testcases._id"} }}},
                                {"$group":{"_id":"$_id","testcaseids":{"$push":"$testcaseids"}}}, {"$out":"scenario_testcase_Import"}
                                ])
                            dbsession.scenario_testcase_Import.update_many({},{"$pull": {"testcaseids":"na"}})
                            
                            
                            screenParent=[]
                            for i in screenIds:
                                nestarray={"_id":"","parent":[]}
                                nestarray["_id"]=i["_id"]
                                currentscreenidparent=i["_id"]                      
                                for j in i["old_parent"]:
                                    for ts in ScenarioIds:
                                        if j==ts["old_id"]:
                                            nestarray["parent"].append(ts["_id"])
                                            break
                                screenParent.append(nestarray)
                            
                            mycoll=dbsession["screen_parent_Import"]
                            dbsession.screen_parent_Import.delete_many({})
                            if len(screenParent)>0:
                                dbsession.screen_parent_Import.insert_many(screenParent)
                            
                            dbsession.Dataobjects_Import.aggregate([
                                {'$lookup': {
                                            'from': "dobjects_parent_Import",
                                            'localField': "_id",
                                            'foreignField': "_id",
                                            'as': "parentdobs"
                                            }
                                                    },{"$set":{"parent":"$parentdobs.parent"}},{"$unwind":"$parent"},
                                { "$project" : {"parentdobs":0}},{"$out":"Dataobjects_Import"}
                                            ])

                            dbsession.Module_Import.aggregate([
                                {"$match":{"tsIds":{"$exists":"true"},"projectid":projectid}},
                                {'$lookup': {
                                                        'from': "mindmap_testscenarios_Import",
                                                        'localField': "_id",
                                                        'foreignField': "_id",
                                                        'as': "mindmapscenariodata"
                                                    }
                                                    },{"$set":{"testscenarios":"$mindmapscenariodata.tsIds"}},{"$unwind":"$testscenarios"},
                                { "$project" : {"mindmapscenariodata":0,"tsIds":0}},{"$out":"Module_Import"}
                                            ])
                                                
                            dbsession.Scenario_Import.aggregate([
                                                    {'$match': {"projectid":projectid,"testcaseids.0": {"$exists": "true"}}},
                                                    
                                                    {'$lookup': {
                                                        'from': "scenario_testcase_Import",
                                                        'localField': "_id",
                                                        'foreignField': "_id",
                                                        'as': "scentestcasedata"
                                                    }
                                                    },{"$set":{"testcaseids" :"$scentestcasedata.testcaseids"}},                                                                                    
                                                    {"$unwind":"$testcaseids"},
                                                    { "$project" : {  "scentestcasedata":0,}},                                                        
                                                    {'$out':"Scenario_Import_tc"}
                                                    ])
                            dbsession.Scenario_Import.aggregate([{'$lookup': {
                                                        'from': "Module_Import",
                                                        'localField': "old_parent",
                                                        'foreignField': "old_id",
                                                        'as': "moduledata"
                                                    }
                                                    },{"$set":{"parent" : "$moduledata._id"}},{ "$project" : { "moduledata":0}},
                                                    {'$out':"Scenario_Import"} ])
                            dbsession.Scenario_Import_tc.aggregate([
                            {"$merge":{"into":"Scenario_Import","on":"_id","whenMatched": [{
                                "$set": {"testcaseids": '$$new.testcaseids'}}]}}]) 

                            dbsession.Screen_Import.aggregate([
                                {'$lookup': {
                                                        'from': "screen_parent_Import",
                                                        'localField': "_id",
                                                        'foreignField': "_id",
                                                        'as': "scrparent"
                                                    }},
                                                    {'$lookup': {
                                                        'from': "Dataobjects_Import",
                                                        'localField': "old_id",
                                                        'foreignField': "old_parent",
                                                        'as': "dataobjects"
                                                    }
                                                    },
                                                    {"$set":{"parent" : "$scrparent.parent",
                                                    "orderlist":{"$map": {
                                                                        "input": "$dataobjects._id",
                                                                        "as": "r",
                                                                        "in": { "$toString": "$$r" }
                                                                        }}
                                                                        }},{"$unwind":"$parent"},
                                                    { "$project" : { "scrparent":0,
                                                    "dataobjects":0
                                                                    }},{"$out":"Screen_Import"}

                            ])
                            ImportedData=dbsession.Module_Import.aggregate([{"$project":{"_id":1,"testscenarios":1}},{"$out":"Module_Import_ids"}])
                            mindmapId=list(dbsession.Module_Import_ids.find({},{"_id":1}))
                            queryresult=[]
                            for i in mindmapId:
                                queryresult.append(i["_id"])
                            moduleids=list(dbsession.Module_Import_ids.find({}))
                            testcaseparent=[]                    
                            testcaseids=[]                   
                            for i in moduleids:
                                if "testscenarios" in i and len(i["testscenarios"])>0:
                                    for j in i["testscenarios"]:
                                        if "screens" in j and len(j["screens"])>0:
                                            for k in j["screens"]:
                                                if "testcases" in k and len(k["testcases"])>0:                                
                                                    for testcase in k["testcases"]:
                                                            array3={"_id":"","parent":[]}                                    
                                                            if testcase in testcaseids:                                            
                                                                for q in testcaseparent:
                                                                    if q["_id"] == testcase:                                                    
                                                                        parentinc=q["parent"]
                                                                        parentinc=parentinc+1
                                                                        q["parent"] = parentinc                                                                                            
                                                                    else:
                                                                        continue                         
                                                            else:                                            
                                                                testcaseids.append(testcase)
                                                                array3["_id"]=testcase								
                                                                array3["parent"]=1
                                                                testcaseparent.append(array3)

                            mycoll=dbsession["testcase_parent_Import"]
                            dbsession.testcase_parent_Import.delete_many({})
                            if len(testcaseparent)>0:
                                dbsession.testcase_parent_Import.insert_many(testcaseparent)
                            dbsession.Testcase_Import.aggregate([
                                                    {"$match":{"old_screenid":{"$exists":"true"},"projectid":projectid}},
                                                    {'$lookup': {
                                                        'from': "Screen_Import",
                                                        'localField': "old_screenid",
                                                        'foreignField': "old_id",
                                                        'as': "screendata"
                                                    }},{'$lookup': {
                                                        'from': "testcase_parent_Import",
                                                        'localField': "_id",
                                                        'foreignField': "_id",
                                                        'as': "tcparent"
                                                    }},{"$unwind":"$tcparent"},
                                                    {"$unwind":"$screendata"},{'$set': {'parent': { "$convert": { "input": "$tcparent.parent", "to": "int" } }
                                                    ,"screenid":"$screendata._id"}},
                                                    { "$project" : {"screendata":0,"tcparent":0}},
                                                        {"$out":"Testcase_Import"}
                                                        ])
                        
                            dbsession.Testcase_Import.aggregate([{"$match":{"steps.0": {"$exists": "true"}}},{"$unwind":"$steps"},
                                                    {'$lookup': {
                                                        'from': "Dataobjects_Import",
                                                        'localField': "steps.custname",
                                                        'foreignField': "old_id",
                                                        'as': "dbobjects"
                                                    }},
                                                    {"$set": { "dbobjects":{ "$cond": [{"$eq": [{"$size": '$dbobjects'}, 0] }, [[]], '$dbobjects'] }}},{"$unwind":"$dbobjects"}, 
                                                    {"$set":{"steps.custname":{ "$cond": { "if": { "$ne": ["$steps.custname" , "$dbobjects.old_id" ] }, "then":"$steps.custname", "else": "$dbobjects._id"} }}},
                                                    {"$group":{"_id":"$_id","steps":{"$push":"$steps"}}},{"$out":"testcase_steps"}
                                                    ], allowDiskUse= True) 

                            dbsession.testcase_steps.aggregate([
                            {"$merge":{"into":"Testcase_Import","on":"_id","whenMatched": [{
                                "$set": {"steps": '$$new.steps'}}]}}])                   
                                        
                            
                            dbsession.Module_Import.aggregate([{"$unset":["tsIds","old_id"]},{"$out":"Module_Import"}])
                            dbsession.Scenario_Import.aggregate([{"$unset":["old_id","old_parent","screens"]},{"$out":"Scenario_Import"}])
                            dbsession.Screen_Import.aggregate([{"$unset":["old_id","old_parent","testcases"]},{"$out":"Screen_Import"}])
                            dbsession.Testcase_Import.aggregate([{"$unset":["old_id","old_screenid","projectid"]},{"$out":"Testcase_Import"}])
                            dbsession.Dataobjects_Import.aggregate([{"$unset":["old_id","old_parent"]},{"$out":"Dataobjects_Import"}])

                            dbsession.Module_Import.aggregate([                                            
                            {'$match': {"projectid":projectid}},
                            {"$merge":{"into":"mindmaps","on":"_id","whenNotMatched":"insert"}}])                                            
                            dbsession.Screen_Import.aggregate([
                            {'$match': {"projectid":projectid}},
                            {"$merge":{"into":"screens","on":"_id","whenNotMatched":"insert"}}])
                            dbsession.Scenario_Import.aggregate([
                            {'$match': {"projectid":projectid}},
                            {"$merge":{"into":"testscenarios","on":"_id","whenNotMatched":"insert"}}])
                            dbsession.Testcase_Import.aggregate([
                            {"$merge":{"into":"testcases","on":"_id","whenNotMatched":"insert"}}])
                            dbsession.Dataobjects_Import.aggregate([
                            {"$merge":{"into":"dataobjects","on":"_id","whenNotMatched":"insert"}}])

                            dbsession.Module_Import.drop()
                            dbsession.Screen_Import.drop()
                            dbsession.Scenario_Import.drop()
                            dbsession.Testcase_Import.drop()
                            dbsession.Dataobjects_Import.drop()
                            dbsession.mindmap_testscenarios_Import.drop()
                            dbsession.scenario_testcase_Import.drop()
                            dbsession.screen_parent_Import.drop()
                            dbsession.testcase_parent_Import.drop()
                            dbsession.dobjects_parent_Import.drop()
                            dbsession.Module_Import_ids.drop()
                            dbsession.Scenario_Import_ids.drop()
                            dbsession.Scenario_Import_tc.drop()
                            dbsession.Screen_Import_ids.drop()
                            dbsession.Testcase_Import_ids.drop()                    
                            dbsession.testcase_steps.drop()
                                
                            
                            if queryresult:
                                    res={'rows':queryresult}                
            
                else:
                    res={'rows': "InProgress"}
            else:
                app.logger.warn('Empty data received while importing mindmap')
           
        except Exception as importmindmapexc:
            dbsession.Module_Import.drop()
            dbsession.Screen_Import.drop()
            dbsession.Scenario_Import.drop()
            dbsession.Testcase_Import.drop()
            dbsession.Dataobjects_Import.drop()
            dbsession.mindmap_testscenarios_Import.drop()
            dbsession.scenario_testcase_Import.drop()
            dbsession.screen_parent_Import.drop()
            dbsession.testcase_parent_Import.drop()
            dbsession.dobjects_parent_Import.drop()
            dbsession.Module_Import_ids.drop()
            dbsession.Scenario_Import_ids.drop()
            dbsession.Scenario_Import_tc.drop()
            dbsession.Screen_Import_ids.drop()
            dbsession.Testcase_Import_ids.drop()                    
            dbsession.testcase_steps.drop()
           
                
            servicesException("importMindmap", importmindmapexc, True)
        return jsonify(res)
    
    @app.route('/mindmap/gitToMindmap',methods=['POST'])
    def gitToMindmap():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside gitToMindmap.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
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
   
    @app.route('/mindmap/dropTempExpImpColl',methods=['POST'])
    def dropTempExpImpColl():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside dropTempExpImpColl.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                if (requestdata['query'] == 'dropTempExpImpColl'):
                    dbsession.Import_mindmaps.drop()
                    dbsession.Export_mindmap.drop()
                    dbsession.Module_Import.drop()
                    dbsession.mindmapnames.drop()
                    dbsession.Export_mindmap_git.drop()
                    dbsession.git_Module_Import.drop()
                    res={'rows':'pass'}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as dropTempExpImpCollexc:
            servicesException("dropTempExpImpColl",dropTempExpImpCollexc, True)
        return jsonify(res)

    
    @app.route('/mindmap/getProjectsMMTS',methods=['POST'])
    def getProjectsMMTS():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getProjectsMMTS.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                if (requestdata['query'] == 'getProjectsMMTS'):
                    projectid=ObjectId(requestdata["projectid"])
                    mm_det=list(dbsession.mindmaps.aggregate([{"$match":{"projectid":projectid, "type":"basic"}},{'$lookup': {
                                                'from': "testscenarios",
                                                'localField': "_id",
                                                'foreignField': "parent",
                                                'as': "scenarioList"
                                            }},{"$project":{"projectid":1,"scenarioList.name":1,"scenarioList._id":1,"name":1}},
                                            {"$group":{"_id":"$projectid","mindmapList":{"$push":{"_id":"$_id","name":"$name","scenarioList":"$scenarioList"}
                                               }}}
                                               ]))                                              

                    if len(mm_det) > 0 :
                        res={'rows':mm_det}
                    else:
                        res={'rows': [""]}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as getProjectsMMTSexc:
            servicesException("getProjectsMMTS",getProjectsMMTSexc, True)
        return jsonify(res)
    

    @app.route('/mindmap/updateE2E',methods=['POST'])
    def updateE2E():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateE2E.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                sceid=requestdata["scenarioID"]
                queryresult = []
                for scenarioid in sceid:
                    mm_det=dbsession.testscenarios.find_one({"_id":(ObjectId(scenarioid)) },{"parent":1})
                    mm_name=dbsession.mindmaps.find_one({"_id":{"$in":mm_det["parent"]},"type":"basic"},{"projectid":1, "name":1})
                    proj_name=dbsession.projects.find_one({"_id":mm_name["projectid"]},{"name":1})
                    queryresult.append({"module_name":mm_name["name"],"proj_name":proj_name["name"], "scenarioID":scenarioid})      
                res={"rows":queryresult}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as updateE2Eexc:
            servicesException("updateE2E",updateE2Eexc, True)
        return jsonify(res)
    

    @app.route('/mindmap/saveTag',methods=['POST'])
    def saveTag():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside saveTag.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]
                tags = requestdata["tag"]
                testScenarioID = ObjectId(requestdata["testscenarioId"])
                dbsession.mindmaps.update_one({"testscenarios":{"$elemMatch":{"_id":testScenarioID}}},{"$set":{"testscenarios.$.tag":tags}})
                res={"rows":"pass"}
            else:
                app.logger.warn('Failed in saving Tag')
        except Exception as saveTag:
            servicesException("saveTag",saveTag, True)
        return jsonify(res)
    @app.route('/mindmap/assignedUserMM',methods=['POST'])
    def assignedUserMM():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside assignedUserMM.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)            
                dbsession=client[clientName]
                for data in requestdata['data']:
                    userid = data["assigne_to"]
                    testCaseID = data["testcaseId"]
                    # screenid = data["screenId"]                
                    dbsession.mindmaps.update_one({"testscenarios": {"$elemMatch": {"_id": ObjectId(testCaseID)}}},{"$set": {"testscenarios.$.assigneduser": userid}})
                    dbsession.testscenarios.update_one({"_id":ObjectId(testCaseID)},{"$set":{"assignedUser":userid}})
                        # if screenid > 0:
                        #     for screen in screenid:
                        #         dbsession.screens.update_one({"_id":screen}, { "$set":{"assignedUser" : userid}})
                res={"rows":"pass"}
            else:
                app.logger.warn('Failed in assignedUserMM')
        except Exception as assignedUserMM:
            servicesException("assignedUserMM",assignedUserMM, True)
        return jsonify(res)