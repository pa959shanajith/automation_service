################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from bson.objectid import ObjectId
import json
from datetime import datetime

def LoadServices(app, redissession, n68session):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################

    # API to get the project type name using the ProjectID
    @app.route('/create_ice/getProjectType_Nineteen68',methods=['POST'])
    def getProjectType_Nineteen68():
        app.logger.debug("Inside getProjectType_Nineteen68")
        res={'rows':'fail'}
        try:
           requestdata=json.loads(request.data)
           if not isemptyrequest(requestdata):
                projectid=requestdata['projectid']
                dbconn=n68session["projects"]
                getProjectType=list(dbconn.find({"_id":ObjectId(projectid)},{"type":1}))
                dbconn=n68session["projecttypekeywords"]
                getProjectTypeName= list(dbconn.find({"_id":ObjectId(getProjectType[0]["type"])},{"name":1}))
                res={'rows':getProjectType,'projecttype':getProjectTypeName}
           else:
                app.logger.warn("Empty data received. getProjectType_Nineteen68")
        except Exception as e:
            servicesException("getProjectType_Nineteen68",e)
        return jsonify(res)

    #API to get ProjectID and Names of project assigned to particular user
    @app.route('/create_ice/getProjectIDs_Nineteen68',methods=['POST'])
    def getProjectIDs_Nineteen68():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getProjectIDs_Nineteen68. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if len(projecttype_names)==0:
                    result=list(n68session.projecttypekeywords.find({},{"_id":1,"name":1}))
                    for p in result:
                        projecttype_names[str(p["_id"])]=p["name"]
                prjDetails={
                    'projectId':[],
                    'projectName':[],
                    'appType':[],
                    'appTypeName':[],
                    'releases':[],
                    'cycles':{},
                    'projecttypes':projecttype_names

                }
                userid=requestdata['userid']
                dbconn=n68session["users"]
                projectIDResult=list(dbconn.find({"_id":ObjectId(userid)},{"projects":1}))
                if(len(projectIDResult)!=0):
                    dbconn=n68session["mindmaps"]
                    prjids=[]
                    for pid in projectIDResult[0]["projects"]:
                        prjids.append(str(pid))
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
                        dbconn=n68session["projects"]
                        prjDetail=list(dbconn.find({"_id":ObjectId(pid)},{"_id":1,"name":1,"type":1,"releases.name":1,"releases.cycles.name":1,"releases.cycles._id":1}))
                        # print(prjDetail)
                        if(len(prjDetail)!=0):
                            prjDetails['projectId'].append(str(prjDetail[0]['_id']))
                            prjDetails['projectName'].append(prjDetail[0]['name'])
                            prjDetails['appType'].append(str(prjDetail[0]['type']))
                            prjDetails['appTypeName'].append(n68session.projecttypekeywords.find_one({"_id":ObjectId(prjDetail[0]['type'])})["name"])
                            prjDetails['releases'].append(prjDetail[0]["releases"])
                            for rel in prjDetail[0]["releases"]:
                                for cyc in rel['cycles']:
                                    prjDetails['cycles'][str(cyc['_id'])]=[str(cyc['_id']),rel['name']]


                res={'rows':prjDetails}
            else:
                app.logger.warn("Empty data received. getProjectIDs_Nineteen68")
        except Exception as e:
            servicesException("getProjectIDs_Nineteen68",e)
        return jsonify(res)


    #API to get Node Details of Module/Scenario/Screen/Testcase with given ID
    # @app.route('/create_ice/get_node_details_ICE',methods=['POST'])
    # def get_node_details_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside get_node_details_ICE. Name: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             name=requestdata['name']
    #             nodeid=requestdata['id']
    #             if name=='module_details':
    #                 queryresult= list(n68session.mindmaps.find({"_id":ObjectId(nodeid),"deleted":False}))
    #             elif name=='testscenario_details':
    #                 queryresult= list(n68session.testscenarios.find({"_id":ObjectId(nodeid),"deleted":False}))
    #             elif name=='screen_details':
    #                 queryresult= list(n68session.screens.find({"_id":ObjectId(nodeid),"deleted":False}))
    #             elif name=='testcase_details':
    #                 queryresult= list(n68session.testcases.find({"_id":ObjectId(nodeid),"deleted":False}))
    #             else:
    #                 queryresult='fail'
    #             res={'rows':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. get_node_details_ICE")
    #     except Exception as e:
    #         servicesException("get_node_details_ICE",e)
    #     return jsonify(res)

    #API to check if a Test Suite exists
    # @app.route('/create_ice/testsuiteid_exists_ICE',methods=['POST'])
    # def testsuiteid_exists_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside testsuiteid_exists_ICE. Query: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             query_name=requestdata['name']
    #             dbconn=n68session["mindmaps"]
    #             if query_name=='suite_check':
    #                 queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['module_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             elif query_name=='suite_check_id':
    #                 queryresult= list(dbconn.find({"_id":ObjectId(requestdata['module_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['module_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             res={'rows':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. testsuiteid_exists_ICE")
    #     except Exception as e:
    #         servicesException("testsuiteid_exists_ICE",e)
    #     return jsonify(res)

    #API to check if a Test Scenario exists
    # @app.route('/create_ice/testscenariosid_exists_ICE',methods=['POST'])
    # def testscenariosid_exists_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside testscenariosid_exists_ICE. Query: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             query_name=requestdata['name']
    #             dbconn=n68session["testscenarios"]
    #             if query_name=='scenario_check':
    #                 queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['scenario_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             elif query_name=='scenario_check_id':
    #                 queryresult= list(dbconn.find({"_id":ObjectId(requestdata['scenario_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['scenario_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             res={'rows':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. testscenariosid_exists_ICE")
    #     except Exception as e:
    #         servicesException("testscenariosid_exists_ICE",e)
    #     return jsonify(res)

    #API to check if a Test Screen exists
    # @app.route('/create_ice/testscreenid_exists_ICE',methods=['POST'])
    # def testscreenid_exists_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside testscreenid_exists_ICE. Query: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             query_name=requestdata['name']
    #             dbconn=n68session["screens"]
    #             if query_name=='screen_check':
    #                 queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['screen_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             elif query_name=='screen_check_id':
    #                 queryresult= list(dbconn.find({"_id":ObjectId(requestdata['screen_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['screen_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             res={'rows':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. testscreenid_exists_ICE")
    #     except Exception as e:
    #         servicesException("testscreenid_exists_ICE",e)
    #     return jsonify(res)

    #API to check if a Testcase exists
    # @app.route('/create_ice/testcaseid_exists_ICE',methods=['POST'])
    # def testcaseid_exists_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside testcaseid_exists_ICE. Query: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             query_name=requestdata['name']
    #             if query_name=='testcase_check':
    #                 queryresult=list(n68session.testcases.find({"screenid":ObjectId(requestdata['screen_id']),"name":requestdata['testcase_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             elif query_name=='testcase_check_id':
    #                 queryresult= list(n68session.testcases.find({"_id":ObjectId(requestdata['testcase_id']),"screenid":ObjectId(requestdata['screen_id']),"name":requestdata['testcase_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
    #             res={'rows':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. testcaseid_exists_ICE")
    #     except Exception as e:
    #         servicesException("testcaseid_exists_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/delete_node_ICE',methods=['POST'])
    # def delete_node_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         wrong_operation=False
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside delete_node_ICE. Name: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             query_name=requestdata['name']
    #             if query_name=='delete_module':
    #                 resp=n68session.mindmaps.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
    #             elif query_name=='delete_testscenario':
    #                 resp=n68session.testscenarios.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
    #             elif query_name=='delete_screen':
    #                 resp=n68session.screens.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
    #             elif query_name=='delete_testcase':
    #                 resp=n68session.testcases.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'screenid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
    #             else:
    #                 wrong_operation=True
    #             if not wrong_operation:
    #                 res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. delete_node_ICE")
    #     except Exception as e:
    #         servicesException("delete_node_ICE",e)
    #     return jsonify(res)


    # @app.route('/create_ice/updateTestScenario_ICE',methods=['POST'])
    # def updateTestScenario_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside updateTestScenario_ICE. Modified_flag: "+str(requestdata["modifiedflag"]))
    #         if not isemptyrequest(requestdata):
    #             modifiedon=datetime.now()
    #             if(requestdata['modifiedflag']):
    #                 # queryresult=n68session.testscenarios.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["testscenarioname"]},{"$set":"testcaseids":requestdata['testcaseid'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #                 queryresult=n68session.testscenarios.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"testcaseids":requestdata['testcaseid'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}},upsert=False)
    #             else:
    #                 # queryresult=n68session.testscenarios.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["testscenarioname"]},{"$set":"testcaseids":requestdata['testcaseid']})
    #                 queryresult=n68session.testscenarios.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"testcaseids":requestdata['testcaseid']}},upsert=False)

    #             res={'rows':'Success','data':queryresult}
    #         else:
    #             app.logger.warn("Empty data received. updateTestScenario_ICE")
    #     except Exception as e:
    #         servicesException("updateTestScenario_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/updateModule_ICE',methods=['POST'])
    # def updateModule_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside updateModule_ICE. Modified_flag: "+str(requestdata["modifiedflag"]))
    #         if not isemptyrequest(requestdata):
    #             dbconn=n68session["mindmaps"]
    #             modifiedon=datetime.now()
    #             if(requestdata['modifiedflag']):
    #                 # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["modulename"]},{"$set":"testscenarios":requestdata['testscenarioids'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #                 queryresult=n68session.mindmaps.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"testscenarios":requestdata['testscenarioids'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}},upsert=False)
    #             else:
    #                 # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["modulename"]},{"$set":"testscenarios":requestdata['testscenarioids']})
    #                 queryresult=n68session.mindmaps.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"testscenarios":requestdata['testscenarioids']}},upsert=False)
    #             res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. updateModule_ICE")
    #     except Exception as e:
    #         servicesException("updateModule_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/updateModulename_ICE',methods=['POST'])
    # def updateModulename_ICE():
    #     app.logger.debug("Inside updateModulename_ICE")
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         dbconn=n68session["mindmaps"]
    #         modifiedon=datetime.now()
    #         if not isemptyrequest(requestdata):
    #             # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['modulename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #             queryresult=dbconn.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"name":requestdata['modulename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
    #             res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. updateModulename_ICE")
    #     except Exception as e:
    #         servicesException("updateModulename_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/updateTestscenarioname_ICE',methods=['POST'])
    # def updateTestscenarioname_ICE():
    #     app.logger.debug("Inside updateTestscenarioname_ICE")
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         dbconn=n68session["testscenarios"]
    #         if not isemptyrequest(requestdata):
    #             modifiedon=datetime.now()
    #             # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['testscenarioname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #             queryresult=dbconn.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"name":requestdata['testscenarioname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
    #             res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. updateTestscenarioname_ICE")
    #     except Exception as e:
    #         servicesException("updateTestscenarioname_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
    # def updateScreenname_ICE():
    #     app.logger.debug("Inside updateScreenname_ICE")
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         dbconn=n68session["screens"]
    #         if not isemptyrequest(requestdata):
    #             modifiedon=datetime.now()
    #             # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['screenid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['screenname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #             queryresult=dbconn.update_one({"_id":ObjectId(requestdata['screenid'])},{"$set":{"name":requestdata['screenname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
    #             res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. updateScreenname_ICE")
    #     except Exception as e:
    #         servicesException("updateScreenname_ICE",e)
    #     return jsonify(res)

    # @app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
    # def updateTestcasename_ICE():
    #     app.logger.debug("Inside updateTestcasename_ICE")
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         dbconn=n68session["screens"]
    #         if not isemptyrequest(requestdata):
    #             modifiedon=datetime.now()
    #             # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testcaseid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['testcasename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
    #             queryresult=dbconn.update_one({"_id":ObjectId(requestdata['testcaseid'])},{"$set":{"name":requestdata['testcasename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
    #             res={'rows':'Success'}
    #         else:
    #             app.logger.warn("Empty data received. updateTestcasename_ICE")
    #     except Exception as e:
    #         servicesException("updateTestcasename_ICE",e)
    #     return jsonify(res)


    # New API for getting Module Details.
    @app.route('/mindmap/getModules',methods=['POST'])
    def getModules():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            tab=requestdata['tab']
            app.logger.debug("Inside getModules. Query: "+str(requestdata["name"]))
            if 'moduleid' in requestdata and requestdata['moduleid']!=None:
                mindmapdata=n68session.mindmaps.find_one({"_id":ObjectId(requestdata["moduleid"])},{"testscenarios":1,"_id":1,"name":1,"projectid":1,"type":1})
                mindmaptype=mindmapdata["type"]
                scenarioids=[]
                screenids=[]
                testcaseids=[]
                # scenarioidsSeen=set()
                # screenidsSeen=set()
                # testcaseidsSeen=set()
                taskids=[]
                cycleid=requestdata['cycleid']
                # Preparing data for fetching details of screens,testcases and scenarios
                for ts in mindmapdata["testscenarios"]:
                    #scenarios=mindmapdata[0]["testscenarios"]
                    if ts["_id"] not in scenarioids:
                        # scenarioidsSeen.add(scenarios[i]["_id"])
                        scenarioids.append(ts["_id"])
                    for sc in ts["screens"]:
                        #screens=scenarios[i]["screens"]
                        if sc["_id"] not in screenids:
                            # screenidsSeen.add(screens[j]["_id"])
                            screenids.append(sc["_id"])
                        for tc in sc["testcases"]:
                            # testcase=screens[j]["testcases"][k]
                            # for l in range(len(testcases)):
                            if tc not in testcaseids:
                                # testcaseidsSeen.add(testcase)
                                testcaseids.append(tc)

                # Preparing data for fetching tasks based on nodeid
                taskids.extend(scenarioids)
                taskids.extend(screenids)
                taskids.extend(testcaseids)
                taskids.append(ObjectId(requestdata['moduleid']))
                taskdetails=list(n68session.tasks.find({"nodeid":{"$in":taskids}}))

                scenariodetails=list(n68session.testscenarios.find({"_id":{"$in":scenarioids}},{"_id":1,"name":1,"parent":1}))
                screendetails=list(n68session.screens.find({"_id":{"$in":screenids}},{"_id":1,"name":1,"parent":1}))
                testcasedetails=list(n68session.testcases.find({"_id":{"$in":testcaseids}},{"_id":1,"name":1,"parent":1}))
                taskdata={}
                moduledata={}
                scenariodata={}
                screendata={}
                testcasedata={}
                data_dict={'testscenarios':scenariodata,
                'screens':screendata,
                'testcases':testcasedata,
                'testsuites':moduledata}
                assignTab=False
                if tab=="tabAssign":
                    assignTab=True
                    for t in taskdetails:
                        if assignTab and ( t['nodetype']=="screens" or t['nodetype']=="testcases" or cycleid==str(t['cycleid'])):
                            data_dict[t['nodetype']][t['nodeid']]={'task':t}
                else:
                    for t in taskdetails:
                        data_dict[t['nodetype']][t['nodeid']]={'taskexists':t}

                # scenariodata={}
                for ts in scenariodetails:
                    if ts["_id"] in scenariodata:
                        scenariodata[ts["_id"]]['name']=ts["name"]
                        scenariodata[ts["_id"]]['reuse']=True if len(ts["parent"])>1 else False
                    else:
                        scenariodata[ts["_id"]]={
                            'name':ts["name"],
                            'reuse': True if len(ts["parent"])>1 else False
                        }

                # screendata={}
                for sc in screendetails:
                    if sc["_id"] in screendata:
                        screendata[sc["_id"]]['name']=sc["name"]
                        screendata[sc["_id"]]['reuse']=True if len(sc["parent"])>1 else False
                    else:
                        screendata[sc["_id"]]={
                            "name":sc["name"],
                            "reuse":True if len(sc["parent"])>1 else False
                            }
                # testcasedata={}
                for tc in testcasedetails:
                    if tc["_id"] in testcasedata:
                        testcasedata[tc["_id"]]['name']=tc["name"]
                        testcasedata[tc["_id"]]['reuse']=True if tc["parent"]>1 else False

                    else:
                        testcasedata[tc["_id"]]={
                        "name":tc["name"],
                        # "reuse": True if len(testcasedetails[i]["parent"])>1 else False
                        "reuse": True if tc["parent"]>1 else False
                        }
                finaldata={}
                finaldata["name"]=mindmapdata["name"]
                finaldata["_id"]=mindmapdata["_id"]
                finaldata["projectID"]=mindmapdata["projectid"]
                finaldata["type"]="modules"
                finaldata["childIndex"]=0
                finaldata["state"]="saved"
                finaldata["children"]=[]
                finaldata["completeFlow"]=True
                finaldata["type"]="modules" if mindmaptype=="basic" else "endtoend"
                finaldata["task"]=moduledata[mindmapdata["_id"]]["task"] if mindmapdata["_id"] in moduledata and 'task' in moduledata[mindmapdata["_id"]] else None
                finaldata["taskexists"]=moduledata[mindmapdata["_id"]]["taskexists"] if mindmapdata["_id"] in moduledata and 'taskexists' in moduledata[mindmapdata["_id"]] else None



                #finaldata["task"]=taskdata[mindmapdata["_id"]] if mindmapdata["_id"] in taskdata else None
                projectid=mindmapdata["projectid"]

                # Preparing final data in format needed
                if len(mindmapdata["testscenarios"])==0 and mindmaptype=="basic":
                    finaldata["completeFlow"]=False
                i=1
                for ts in mindmapdata["testscenarios"]:

                    finalscenariodata={}
                    #scenarios=mindmapdata["testscenarios"]
                    finalscenariodata["projectID"]=projectid
                    finalscenariodata["_id"]=ts["_id"]
                    finalscenariodata["name"]=scenariodata[ts["_id"]]["name"]
                    finalscenariodata["type"]="scenarios"
                    finalscenariodata["childIndex"]=i
                    finalscenariodata["children"]=[]
                    finalscenariodata["state"]="saved"
                    finalscenariodata["reuse"]=scenariodata[ts["_id"]]["reuse"]
                    finalscenariodata["task"]=scenariodata[ts["_id"]]['task'] if 'task' in scenariodata[ts["_id"]] else None
                    finalscenariodata["taskexists"]=scenariodata[ts["_id"]]['taskexists'] if 'taskexists' in scenariodata[ts["_id"]] else None
                    i=i+1
                    if len(ts["screens"])==0  and mindmaptype=="basic":
                        finaldata["completeFlow"]=False
                    j=1
                    for sc in ts["screens"]:

                        finalscreendata={}
                        # screens=ts["screens"]
                        finalscreendata["projectID"]=projectid
                        finalscreendata["_id"]=sc["_id"]
                        finalscreendata["name"]=screendata[sc["_id"]]["name"]
                        finalscreendata["type"]="screens"
                        finalscreendata["childIndex"]=j
                        finalscreendata["children"]=[]
                        finalscreendata["reuse"]=screendata[sc["_id"]]["reuse"]
                        finalscreendata["state"]="saved"
                        finalscreendata["task"]=screendata[sc["_id"]]['task'] if 'task' in screendata[sc["_id"]] else None
                        finalscreendata["taskexists"]=screendata[sc["_id"]]['taskexists'] if 'taskexists' in screendata[sc["_id"]] else None
                        j=j+1
                        if len(sc["testcases"])==0 and mindmaptype=="basic":
                            finaldata["completeFlow"]=False
                        k=1
                        for tc in sc["testcases"]:
                            # testcase=sc["testcases"][k]
                            finaltestcasedata={}
                            finaltestcasedata["projectID"]=projectid
                            finaltestcasedata["_id"]=tc
                            finaltestcasedata["name"]=testcasedata[tc]["name"]
                            finaltestcasedata["type"]="testcases"
                            finaltestcasedata["childIndex"]=k
                            finaltestcasedata["children"]=[]
                            finaltestcasedata["reuse"]=testcasedata[tc]["reuse"]
                            finaltestcasedata["state"]="saved"
                            finaltestcasedata["task"]=testcasedata[tc]['task'] if 'task' in testcasedata[tc] else None
                            finaltestcasedata["taskexists"]=testcasedata[tc]['taskexists'] if 'taskexists' in testcasedata[tc] else None
                            k=k+1
                            finalscreendata["children"].append(finaltestcasedata)
                        finalscenariodata["children"].append(finalscreendata)
                    finaldata["children"].append(finalscenariodata)

                res={'rows':finaldata}
            else:
                if tab=="tabCreate":
                    queryresult=list(n68session.mindmaps.find({"projectid":ObjectId(requestdata["projectid"]),"type":"basic"},{"name":1,"_id":1,"type":1}))
                else:
                    queryresult=list(n68session.mindmaps.find({"projectid":ObjectId(requestdata["projectid"])},{"name":1,"_id":1,"type":1}))
                res={'rows':queryresult}
        except Exception as e:
            import traceback
            traceback.print_exc()
            servicesException("getModules",e)
        return jsonify(res)


    @app.route('/plugins/getTasksJSON',methods=['POST'])
    def getTasksJSON():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            print("req",requestdata)
            app.logger.debug("Inside getTasksJSON.")
            if not isemptyrequest(requestdata):
                userid=requestdata["userid"]
                tasks=list(n68session.tasks.find({"assignedto":ObjectId(userid)}))
                res={'rows':tasks}
            else:
                app.logger.warn("Empty data received. getTasksJSON")
        except Exception as e:
            servicesException("getTasksJSON",e)
        return jsonify(res)

    @app.route('/mindmap/getScenarios',methods=['POST'])
    def getScenarios():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScenarios.")
            if not isemptyrequest(requestdata):
                moduleid=requestdata["moduleid"]
                moduledetails=list(n68session.mindmaps.find({"_id":ObjectId(moduleid)},{"testscenarios":1}))
                scenarioids=[]
                for mod in moduledetails:
                    for sce in mod["testscenarios"]:
                        scenarioids.append(ObjectId(sce["_id"]))
                scenarioslist=list(n68session.testscenarios.find({"_id":{"$in":scenarioids}},{"name":1}))
                res={'rows':scenarioslist}
            else:
                app.logger.warn("Empty data received. getScenarios")
        except Exception as e:
            servicesException("getScenarios",e)
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
                for node in requestdata['deletednodes']:
                    updateparent(node[1],node[0],node[2],"delete")
                res={'rows':currentmoduleid}
            else:
                res={'rows':'fail',"error":error}
        except Exception as e:
            servicesException("saveMindmap",e)
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
        queryresult=n68session.mindmaps.insert_one(data).inserted_id
        print("Save Test Suite",queryresult)
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
            "testcaseids":testcaseids,
            "screens":[]
        }
        queryresult=n68session.testscenarios.insert_one(data).inserted_id
        print("Save Secenario",queryresult)
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
        "scrapedurl":"",
        "testcases":[]
        }
        queryresult=n68session.screens.insert_one(data).inserted_id
        print("Save Screen",queryresult)
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
        queryresult=n68session.testcases.insert_one(data).inserted_id
        print("Save Testcase",queryresult)
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
                        if i['startdate'].find('/') > -1:
                            i["startdate"]=datetime.strptime(i["startdate"],"%d/%m/%Y")
                        if i['enddate'].find('/') > -1:
                            i["enddate"]=datetime.strptime(i["enddate"],"%d/%m/%Y")
                        n68session.tasks.update({"_id":ObjectId(i["_id"]),"cycleid":ObjectId(i["cycleid"])},{"$set":{"assignedtime":i["assignedtime"],"startdate":i["startdate"],"enddate":i["enddate"],"assignedto":ObjectId(i["assignedto"]),"reviewer":ObjectId(i["reviewer"]),"status":i["status"],"reestimation":i["reestimation"],"complexity":i["complexity"],"history":i["history"]}})
                    tasks_insert=requestdata["insert"]
                    for i in tasks_insert:
                        i["startdate"]=datetime.strptime(i["startdate"],"%d/%m/%Y")
                        i["enddate"]=datetime.strptime(i["enddate"],"%d/%m/%Y")
                        i["assignedtime"]=datetime.now()
                        i["createdon"]=datetime.now()
                        i["owner"]=ObjectId(i["owner"])
                        i['cycleid']=ObjectId(i["cycleid"])
                        i["assignedto"]=ObjectId(i["assignedto"])
                        i["nodeid"]=ObjectId(i["nodeid"])
                        if i["parent"] != "":
                            i["parent"]=ObjectId(i["parent"])
                        i["reviewer"]=ObjectId(i["reviewer"])
                        i["projectid"]=ObjectId(i["projectid"])
                    if len(tasks_insert)>0:
                        n68session.tasks.insert_many(tasks_insert)
                    if len(tasks_remove)>0:
                        tasks_remove=[ObjectId(t) for t in tasks_remove]
                        n68session.tasks.delete_many({"nodeid":{"$in":tasks_remove}})
                    res={"rows":"success"}
                elif action=="updatestatus":
                    status=requestdata['status']
                    n68session.tasks.update({"_id":ObjectId(requestdata["id"])},{"$set":{"status":status}})
                    res={"rows":"success"}
                elif action == "delete":
                    n68session.tasks.delete({"_id":ObjectId(requestdata["id"]),"cycle":ObjectId(requestdata["cycleid"])})
                    res={"rows":"success"}
            else:
                app.logger.warn('Empty data received. manage users.')
        except Exception as e:
            servicesException("manageTaskDetails",e)
        return jsonify(res)

    def checkReuse(requestdata):
        scenarionames=set()
        # screennameset=set()
        testcasenameset=set()
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
                # If the the Module has an ID then we will check if the target name has conflict if not then rename will be allowed.
                name=getModuleName(moduledata['testsuiteId'])
                if name!=moduledata["testsuiteName"]:
                    if checkModuleNameExists(moduledata["testsuiteName"],projectid):
                        error="Module cannot be renamed to an existing module name"
                        break
                    else:
                        moduledata["state"]=="renamed"
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
        res=list(n68session.mindmaps.find({"projectid":ObjectId(projectid),"name":name},{"_id":1}))
        if len(res)>0:
            return True
        else:
            return False

    def checkScreenNameExists(name,projectid):
        res = list(n68session.screens.find({"projectid": ObjectId(projectid), "name": name}, {"_id": 1}))
        if len(res) > 0:
            return True
        else:
            return False

    def updateparent(type,nodeid,parentid,action):
        if action=="add":
            if type=="scenarios":
                parentlist=list(n68session.testscenarios.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist.append(ObjectId(parentid))
                n68session.testscenarios.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
            elif type=="screens":
                parentlist=list(n68session.screens.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist.append(ObjectId(parentid))
                n68session.screens.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
            elif type=="testcases":
                parentlist=list(n68session.testcases.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist+=1
                n68session.testcases.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})
        elif action=="delete":
            if type=="scenarios":
                parentlist=list(n68session.testscenarios.find({"_id":ObjectId(nodeid)},{"parent":1}))
                oldparentlist=parentlist[0]['parent']
                newparentlist=[]
                flag=False
                for pid in oldparentlist:
                    if flag or str(pid)!=parentid:
                        newparentlist.append(pid)
                    else:
                        flag=False
                n68session.testscenarios.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':newparentlist}})
            elif type=="screens":
                parentlist=list(n68session.screens.find({"_id":ObjectId(nodeid)},{"parent":1}))
                oldparentlist=parentlist[0]['parent']
                newparentlist=[]
                flag=False
                for pid in oldparentlist:
                    if flag or str(pid)!=parentid:
                        newparentlist.append(pid)
                    else:
                        flag=False
                n68session.screens.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':newparentlist}})
            elif type=="testcases":
                parentlist=list(n68session.testcases.find({"_id":ObjectId(nodeid)},{"parent":1}))
                updateparentlist=parentlist[0]['parent']
                updateparentlist-=1
                n68session.testcases.update_one({'_id':ObjectId(nodeid)},{'$set':{'parent':updateparentlist}})

        
    def updateTestcaseIDsInScenario(currentscenarioid,testcaseidsforscenario):
        n68session.testscenarios.update_one({'_id':ObjectId(currentscenarioid)},{'$set':{'testcaseids':testcaseidsforscenario}})
        return

    def updateTestScenariosInModule(currentmoduleid,idsforModule):
        n68session.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':idsforModule}})
        return


    @app.route('/mindmap/getScreens',methods=['POST'])
    def getScreens():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScreens.")
            if not isemptyrequest(requestdata):
                projectid=requestdata["projectid"]
                moduledetails=list(n68session.mindmaps.find({"projectid":ObjectId(projectid)},{"testscenarios":1}))
                screenidsset=set()
                screenids=[]
                screen_testcase={}
                testcaseidsset=set()
                testcaseids=[]
                for mod in moduledetails:
                    for sce in mod["testscenarios"]:
                        for scr in sce["screens"]:
                            if scr["_id"] not in screenidsset:
                                screenidsset.add(scr["_id"])
                                screenids.append(scr["_id"])
                            for tc in scr["testcases"]:
                                if tc not in testcaseidsset:
                                    testcaseids.append(tc)
                                    testcaseidsset.add(tc)
                                if scr["_id"] not in screen_testcase:
                                    screen_testcase[scr["_id"]]=[]
                                    screen_testcase[scr["_id"]].append(tc)
                                else:
                                    screen_testcase[scr["_id"]].append(tc)
                screendetails=list(n68session.screens.find({"_id":{"$in":screenids}},{"_id":1,"name":1,"parent":1}))
                testcasedetails=list(n68session.testcases.find({"_id":{"$in":testcaseids}},{"_id":1,"name":1,"parent":1}))
                res={'rows':{'screenList':screendetails,'testCaseList':testcasedetails}}
            else:
                app.logger.warn("Empty data received. getScenarios")
        except Exception as e:
            servicesException("getScenarios",e)
        return jsonify(res)

    def checkScenarioNameExists(projectid,name):
        res=list(n68session.testscenarios.find({"projectid":ObjectId(projectid),"name":name},{"_id":1}))
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
                    # n68session.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':scenarioids}})
                for node in requestdata['deletednodes']:
                    updateparent(node[1],node[0],node[2],"delete")
                if error==None:
                    res={'rows':currentmoduleid}
                else:
                    res={'rows':'fail',"error":error}
            else:
                app.logger.warn("Empty data received. saveMindmapE2E")
        except Exception as e:
            servicesException("saveMindmapE2E",e)
        return jsonify(res)

    def checkScenarioIDexists(name,id):
        res=list(n68session.testscenarios.find({"_id":ObjectId(id),"name":name,"deleted":False},{"_id":1}))
        if len(res)==1:
            return True
        else:
            return False

    def updateModuleName(modulename,projectid,moduleid,userid,userroleid):
            modifiedon=datetime.now()
            queryresult=n68session.mindmaps.update_one({"_id":ObjectId(moduleid)},{"$set":{"name":modulename,"modifiedby":userid,"modifedon":modifiedon,"modifiedbyrole":userroleid}})
            return

    def updateScenarioName(scenarioname,projectid,scenarioid,userid,userroleid):
        modifiedon=datetime.now()
        queryresult=n68session.testscenarios.update_one({"_id":ObjectId(scenarioid)},{"$set":{"name":scenarioname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateScreenName(screenname,projectid,screenid,userid,userroleid):
        modifiedon=datetime.now()
        queryresult=n68session.screens.update_one({"_id":ObjectId(screenid)},{"$set":{"name":screenname,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return

    def updateTestcaseName(testcasename,projectid,testcaseid,userid,userroleid):
        modifiedon=datetime.now()
        queryresult=n68session.testcases.update_one({"_id":ObjectId(testcaseid)},{"$set":{"name":testcasename,"modifiedby":ObjectId(userid),"modifedon":modifiedon,"modifiedbyrole":ObjectId(userroleid)}})
        return
    
    def getModuleName(moduleid):
        modulename=list(n68session.mindmaps.find({"_id":ObjectId(moduleid),"deleted":False},{"name":1}))
        if len(modulename)!=0:
            res=modulename[0]["name"]
        else:
            res=None
        return res
    
    def getScenarioName(scenarioid):
        scenarioname=list(n68session.testscenarios.find({"_id":ObjectId(scenarioid),"deleted":False},{"name":1}))
        if len(scenarioname)!=0:
            res=scenarioname[0]["name"]
        else:
            res=None
        return res

    def getScreenName(screenid):
        screename=list(n68session.screens.find({"_id":ObjectId(screenid),"deleted":False},{"name":1}))
        if len(screename)!=0:
            res=screename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseName(testcaseid):
        testcasename=list(n68session.testcases.find({"_id":ObjectId(testcaseid),"deleted":False},{"name":1}))
        if len(testcasename)!=0:
            res=testcasename[0]["name"]
        else:
            res=None
        return res

    def getTestcaseID(screenid,testcasename):
        testcaseid = list(n68session.testcases.find({"screenid": ObjectId(screenid),"name": testcasename,"deleted": False}, {"_id": 1}))
        if len(testcaseid) != 0:
            res = str(testcaseid[0]["_id"])
        else:
            res = None
        return res

    def getScreenID(screenname,projectid):
        screenname=list(n68session.screens.find({"name":screenname,"projectid":ObjectId(projectid),"deleted":False},{"_id":1}))
        if len(screenname)==1:
            return str(screenname[0]["_id"])
        else:   
            return None