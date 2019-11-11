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

    # API to get the Release IDs related to a particular ProjectID
    # @app.route('/create_ice/getReleaseIDs_Nineteen68',methods=['GET','POST'])
    # def getReleaseIDs_Nineteen68():
    #     app.logger.debug("Inside getReleaseIDs_Nineteen68")
    #     res={'rows':'fail'}
    #     try:
    #        requestdata= {"projectid":"fla"}# json.loads(request.data)
    #        # dbconn=n68session["projects"]
    #        if not isemptyrequest(requestdata):
    #             app.logger.critical("aaya idhar")
    #             projectid=requestdata['projectid']
    #             query_result=n68session.users.find({})
    #             for q in query_result:
    #                 app.logger.critical(q)
    #             query_result=n68session.reports.find({})
    #             res={'rows':list(query_result)}
    #             app.logger.critical(list(n68session.users.find({})))
    #        else:
    #             app.logger.warn("Empty data received. getReleaseIDs_Nineteen68")
    #     except Exception as e:
    #         servicesException("getReleaseIDs_Nineteen68",e)
    #     return jsonify(res)

    # API to get the Cycle IDs related to a particular ReleaseID
    # (Can be deprecated as in Releases only we will get the list of cycles.)
    # @app.route('/create_ice/getCycleIDs_Nineteen68',methods=['POST'])
    # def getCycleIDs_Nineteen68():
    #     app.logger.debug("Inside getCycleIDs_Nineteen68")
    #     res={'rows':'fail'}
    #     try:
    #        requestdata=json.loads(request.data)
    #        dbconn=n68session["projects"]
    #        if not isemptyrequest(requestdata):
    #             releaseid=requestdata['releaseid']
    #             query_result=dbconn.find({"releases._id":ObjectId(releaseid),"deleted":False},{"releases.cycles":1,"releases._id":1})
    #             res={'rows':query_result}
    #        else:
    #             app.logger.warn("Empty data received. getCycleIDs_Nineteen68")
    #     except Exception as e:
    #         servicesException("getCycleIDs_Nineteen68",e)
    #     return jsonify(res)

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
                prjDetails={
                    'projectId':[],
                    'projectName':[],
                    'appType':[],
                    'releases':[]
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
                            prjDetails['releases'].append(prjDetail[0]["releases"])
                res={'rows':prjDetails}
            else:
                app.logger.warn("Empty data received. getProjectIDs_Nineteen68")
        except Exception as e:
            servicesException("getProjectIDs_Nineteen68",e)
        return jsonify(res)

    #API to get names of Module/Scenario/Screen/Testcase name with given ID.
    # @app.route('/create_ice/getNames_Nineteen68',methods=['POST'])
    # def getAllNames_ICE():
    #     app.logger.debug("Inside getAllNames_ICE")
    #     res={'rows':'fail'}
    #     try:
    #        requestdata=json.loads(request.data)print("req",requestdata)
    #        if not isemptyrequest(requestdata):
    #             name=requestdata['name']
    #             nodeid=requestdata['id']
    #             if name=='module':
    #                 dbconn=n68session["mindmaps"]
    #                 queryresult= dbconn.find({"_id":ObjectId(nodeid),"deleted":False},{"name":1,"testscenarios":1})
    #             elif name=='scenario':
    #                 dbconn=n68session["testscenarios"]
    #                 queryresult= dbconn.find({"_id":ObjectId(nodeid),"deleted":False},{"name":1})
    #             elif name=='screen':
    #                 dbconn=n68session["screens"]
    #                 queryresult= dbconn.find({"_id":ObjectId(nodeid),"deleted":False},{"name":1})
    #             elif name=='testcase':
    #                 dbconn=n68session["testcases"]
    #                 queryresult= dbconn.find({"_id":ObjectId(nodeid),"deleted":False},{"name":1} )
    #             else:
    #                 queryresult='fail'
    #             res={'rows':queryresult}
    #        else:
    #             app.logger.warn("Empty data received. getAllNames_ICE")
    #     except Exception as e:
    #         servicesException("getAllNames_ICE",e)
    #     return jsonify(res)

    #API to get Node Details of Module/Scenario/Screen/Testcase with given ID
    @app.route('/create_ice/get_node_details_ICE',methods=['POST'])
    def get_node_details_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside get_node_details_ICE. Name: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                name=requestdata['name']
                nodeid=requestdata['id']
                if name=='module_details':
                    queryresult= list(n68session.mindmaps.find({"_id":ObjectId(nodeid),"deleted":False}))
                elif name=='testscenario_details':
                    queryresult= list(n68session.testscenarios.find({"_id":ObjectId(nodeid),"deleted":False}))
                elif name=='screen_details':
                    queryresult= list(n68session.screens.find({"_id":ObjectId(nodeid),"deleted":False}))
                elif name=='testcase_details':
                    queryresult= list(n68session.testcases.find({"_id":ObjectId(nodeid),"deleted":False}))
                else:
                    queryresult='fail'
                res={'rows':queryresult}
            else:
                app.logger.warn("Empty data received. get_node_details_ICE")
        except Exception as e:
            servicesException("get_node_details_ICE",e)
        return jsonify(res)

    #API to check if a Test Suite exists
    @app.route('/create_ice/testsuiteid_exists_ICE',methods=['POST'])
    def testsuiteid_exists_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside testsuiteid_exists_ICE. Query: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                query_name=requestdata['name']
                dbconn=n68session["mindmaps"]
                if query_name=='suite_check':
                    queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['module_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                elif query_name=='suite_check_id':
                    queryresult= list(dbconn.find({"_id":ObjectId(requestdata['module_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['module_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                res={'rows':queryresult}
            else:
                app.logger.warn("Empty data received. testsuiteid_exists_ICE")
        except Exception as e:
            servicesException("testsuiteid_exists_ICE",e)
        return jsonify(res)

    #API to check if a Test Scenario exists
    @app.route('/create_ice/testscenariosid_exists_ICE',methods=['POST'])
    def testscenariosid_exists_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside testscenariosid_exists_ICE. Query: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                query_name=requestdata['name']
                dbconn=n68session["testscenarios"]
                if query_name=='scenario_check':
                    queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['scenario_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                elif query_name=='scenario_check_id':
                    queryresult= list(dbconn.find({"_id":ObjectId(requestdata['scenario_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['scenario_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                res={'rows':queryresult}
            else:
                app.logger.warn("Empty data received. testscenariosid_exists_ICE")
        except Exception as e:
            servicesException("testscenariosid_exists_ICE",e)
        return jsonify(res)

    #API to check if a Test Screen exists
    @app.route('/create_ice/testscreenid_exists_ICE',methods=['POST'])
    def testscreenid_exists_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside testscreenid_exists_ICE. Query: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                query_name=requestdata['name']
                dbconn=n68session["screens"]
                if query_name=='screen_check':
                    queryresult= list(dbconn.find({"projectid":ObjectId(requestdata['project_id']),"name":requestdata['screen_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                elif query_name=='screen_check_id':
                    queryresult= list(dbconn.find({"_id":ObjectId(requestdata['screen_id']),"projectid":ObjectId(requestdata['project_id']),"name":requestdata['screen_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                res={'rows':queryresult}
            else:
                app.logger.warn("Empty data received. testscreenid_exists_ICE")
        except Exception as e:
            servicesException("testscreenid_exists_ICE",e)
        return jsonify(res)

    #API to check if a Testcase exists
    @app.route('/create_ice/testcaseid_exists_ICE',methods=['POST'])
    def testcaseid_exists_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside testcaseid_exists_ICE. Query: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                query_name=requestdata['name']
                if query_name=='testcase_check':
                    queryresult=list(n68session.testcases.find({"screenid":ObjectId(requestdata['screen_id']),"name":requestdata['testcase_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                elif query_name=='testcase_check_id':
                    queryresult= list(n68session.testcases.find({"_id":ObjectId(requestdata['testcase_id']),"screenid":ObjectId(requestdata['screen_id']),"name":requestdata['testcase_name'],"versionnumber":requestdata['versionnumber'],"deleted":False},{"_id":1}))
                res={'rows':queryresult}
            else:
                app.logger.warn("Empty data received. testcaseid_exists_ICE")
        except Exception as e:
            servicesException("testcaseid_exists_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/delete_node_ICE',methods=['POST'])
    def delete_node_ICE():
        res={'rows':'fail'}
        try:
            wrong_operation=False
            requestdata=json.loads(request.data)
            app.logger.debug("Inside delete_node_ICE. Name: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                query_name=requestdata['name']
                if query_name=='delete_module':
                    resp=n68session.mindmaps.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
                elif query_name=='delete_testscenario':
                    resp=n68session.testscenarios.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
                elif query_name=='delete_screen':
                    resp=n68session.screens.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'projectid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
                elif query_name=='delete_testcase':
                    resp=n68session.testcases.update_one({'_id':ObjectId(requestdata['id']),'name':requestdata["node_name"],'versionnumber':requestdata['version_number'],'screenid':ObjectId(requestdata['parent_node_id']),'deleted':False},{'$set':{'deleted': True}},upsert=False)
                else:
                    wrong_operation=True
                if not wrong_operation:
                    res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. delete_node_ICE")
        except Exception as e:
            servicesException("delete_node_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/insertInSuite_ICE',methods=['POST'])
    def insertInSuite_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside insertInSuite_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                createdon = datetime.now()
                if(requestdata["query"] == 'notflagsuite'):
                    # createdon = str(getcurrentdate())
                    data={
                    "projectid":ObjectId(requestdata['projectid']),
                    "name":requestdata['modulename'],
                    "versionnumber":requestdata['versionnumber'],
                    "createdon":createdon,
                    "createdthrough":requestdata['createdthrough'],
                    "createdby":ObjectId(requestdata['createdby']),
                    "createdbyrole":ObjectId(requestdata['createdbyrole']), #extra to be sent from the UI
                    "deleted":False,
                    "modifiedby": ObjectId(requestdata['createdby']),
                    "modifiedon": createdon,
                    "modifiedbyrole": ObjectId(requestdata['createdbyrole']),#extra to be sent through UI.
                    "type": requestdata['type'],#extra parameter to be sent
                    "testscenarios":[]
                    }
                    queryresult=n68session.mindmaps.insert_one(data).inserted_id
                    res={'rows':'Success','data':queryresult}
                elif(requestdata["query"] == 'selectsuite'):
                    queryresult=list(n68session.mindmaps.find({"name":requestdata["modulename"],"versionnumber":requestdata["versionnumber"],"deleted":False},{"_id":1}))
                    res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. insertInSuite_ICE")
        except Exception as e:
            servicesException("insertInSuite_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/insertInScenarios_ICE',methods=['POST'])
    def insertInScenarios_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside insertInScenarios_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'notflagscenarios'):
                    createdon = datetime.now()
                    data={
                        "name":requestdata['testscenarioname'],
                        "projectid":ObjectId(requestdata['projectid']),
                        "parent":[] ,# ModuleID to be passed here.
                        "versionnumber":requestdata['versionnumber'],
                        "createdby":ObjectId(requestdata['createdby']),
                        "createdbyrole":ObjectId(requestdata['createdbyrole']),
                        "createdon":createdon,
                        "deleted":False,
                        "modifiedby":ObjectId(requestdata['createdby']),
                        "modifiedbyrole":ObjectId(requestdata['createdbyrole']),
                        "modifiedon":createdon,
                        "testcaseids":[]
                    }
                    queryresult=n68session.testscenarios.insert_one(data).inserted_id
                    res={'rows':'success','data':queryresult}
                else:
                    app.logger.warn("Invalid data received. insertInScenarios_ICE")
                    queryresult=None
            else:
                app.logger.warn("Empty data received. insertInScenarios_ICE")
        except Exception as e:
            servicesException("insertInScenarios_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/insertInScreen_ICE',methods=['POST'])
    def insertInScreen_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside insertInScreen_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'notflagscreen'):
                    if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                        createdon = datetime.now()
                        data={
                        "projectid":ObjectId(requestdata['projectid']),
                        "name":requestdata['screenname'],
                        "versionnumber":requestdata['versionnumber'],
                        "parent":[], #New property added
                        "createdby":ObjectId(requestdata['createdby']),
                        "createdbyrole":ObjectId(requestdata['createdbyrole']), # New parameter to be passed in service
                        "createdon":createdon,
                        "deleted":False,
                        "modifiedby":ObjectId(requestdata['createdby']),
                        "modifiedbyrole":ObjectId(requestdata['createdbyrole']),
                        "modifiedon":createdon,
                        "screenshot":"",
                        "scrapedurl":""
                        }
                        queryresult=n68session.screens.insert_one(data).inserted_id
                        res={'rows':'Success','data':queryresult}
                elif(requestdata["query"] == 'selectscreen'):
                    queryresult=n68session.screens.find({"name":requestdata["screenname"],"versionnumber":requestdata["versionnumber"],"deleted":False},{"_id":1})
                    res={'rows':'Success'}
                else:
                    app.logger.warn("Invalid data received. insertInScreen_ICE")
                    queryresult=None
            else:
                app.logger.warn("Empty data received. insertInScreen_ICE")
        except Exception as e:
            servicesException("insertInScreen_ICE",e)
        return jsonify(res)


    @app.route('/create_ice/insertInTestcase_ICE',methods=['POST'])
    def insertInTestcase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside insertInTestcase_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'notflagtestcase'):
                    createdon = datetime.now()
                    if(requestdata.has_key('subquery') and requestdata["subquery"]=="clonenode"):
                        data={
                            "screenid": ObjectId(requestdata['screenid']),
                            "name":requestdata['testcasename'],
                            "versionnumber":requestdata["versionnumber"],
                            "createdby": ObjectId(requestdata['createdby']),
                            "createdbyrole": ObjectId(requestdata['createdbyrole']),
                            "createdon": createdon,
                            "modifiedby": ObjectId(requestdata['createdby']),
                            "modifiedbyrole": ObjectId(requestdata['createdbyrole']),
                            "modifiedon":createdon,
                            "steps":[],
                            "parent":[],
                            "deleted":False
                        }
                        queryresult=n68session.testcases.insert_one(data).inserted_id
                        res={'rows':'Success','data':queryresult}
                elif(requestdata["query"] == 'selecttestcase'):
                    queryresult=n68session.testcases.find({"name":requestdata["tags"],"versionnumber":versionnumber,"deleted":False},{"_id":1})
                    res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. insertInTestcase_ICE")
        except Exception as e:
            servicesException("insertInTestcase_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateTestScenario_ICE',methods=['POST'])
    def updateTestScenario_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateTestScenario_ICE. Modified_flag: "+str(requestdata["modifiedflag"]))
            if not isemptyrequest(requestdata):
                modifiedon=getcurrentdate()
                if(requestdata['modifiedflag']):
                    # queryresult=n68session.testscenarios.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["testscenarioname"]},{"$set":"testcaseids":requestdata['testcaseid'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                    queryresult=n68session.testscenarios.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"testcaseids":requestdata['testcaseid'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}},upsert=False)
                else:
                    # queryresult=n68session.testscenarios.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["testscenarioname"]},{"$set":"testcaseids":requestdata['testcaseid']})
                    queryresult=n68session.testscenarios.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"testcaseids":requestdata['testcaseid']}},upsert=False)

                res={'rows':'Success','data':queryresult}
            else:
                app.logger.warn("Empty data received. updateTestScenario_ICE")
        except Exception as e:
            servicesException("updateTestScenario_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateModule_ICE',methods=['POST'])
    def updateModule_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateModule_ICE. Modified_flag: "+str(requestdata["modifiedflag"]))
            if not isemptyrequest(requestdata):
                dbconn=n68session["mindmaps"]
                modifiedon=getcurrentdate()
                if(requestdata['modifiedflag']):
                    # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["modulename"]},{"$set":"testscenarios":requestdata['testscenarioids'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                    queryresult=n68session.mindmaps.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"testscenarios":requestdata['testscenarioids'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}},upsert=False)
                else:
                    # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"],"name":requestdata["modulename"]},{"$set":"testscenarios":requestdata['testscenarioids']})
                    queryresult=n68session.mindmaps.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"testscenarios":requestdata['testscenarioids']}},upsert=False)
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateModule_ICE")
        except Exception as e:
            servicesException("updateModule_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateModulename_ICE',methods=['POST'])
    def updateModulename_ICE():
        app.logger.debug("Inside updateModulename_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            dbconn=n68session["mindmaps"]
            modifiedon=getcurrentdate()
            if not isemptyrequest(requestdata):
                # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['moduleid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['modulename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                queryresult=dbconn.update_one({"_id":ObjectId(requestdata['moduleid'])},{"$set":{"name":requestdata['modulename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateModulename_ICE")
        except Exception as e:
            servicesException("updateModulename_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateTestscenarioname_ICE',methods=['POST'])
    def updateTestscenarioname_ICE():
        app.logger.debug("Inside updateTestscenarioname_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            dbconn=n68session["testscenarios"]
            if not isemptyrequest(requestdata):
                modifiedon=getcurrentdate()
                # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testscenarioid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['testscenarioname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                queryresult=dbconn.update_one({"_id":ObjectId(requestdata['testscenarioid'])},{"$set":{"name":requestdata['testscenarioname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateTestscenarioname_ICE")
        except Exception as e:
            servicesException("updateTestscenarioname_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateScreenname_ICE',methods=['POST'])
    def updateScreenname_ICE():
        app.logger.debug("Inside updateScreenname_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            dbconn=n68session["screens"]
            if not isemptyrequest(requestdata):
                modifiedon=getcurrentdate()
                # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['screenid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['screenname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                queryresult=dbconn.update_one({"_id":ObjectId(requestdata['screenid'])},{"$set":{"name":requestdata['screenname'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateScreenname_ICE")
        except Exception as e:
            servicesException("updateScreenname_ICE",e)
        return jsonify(res)

    @app.route('/create_ice/updateTestcasename_ICE',methods=['POST'])
    def updateTestcasename_ICE():
        app.logger.debug("Inside updateTestcasename_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            dbconn=n68session["screens"]
            if not isemptyrequest(requestdata):
                modifiedon=getcurrentdate()
                # queryresult=dbconn.update_one({"projectid":ObjectId(requestdata['projectid']),"_id":ObjectId(requestdata['testcaseid']),"versionnumber":requestdata["versionnumber"]},{"$set":"name":requestdata['testcasename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']})
                queryresult=dbconn.update_one({"_id":ObjectId(requestdata['testcaseid'])},{"$set":{"name":requestdata['testcasename'],"modifiedby":requestdata['modifiedby'],"modifedon":modifiedon,"modifiedbyrole":requestdata['modifiedbyrole']}})
                res={'rows':'Success'}
            else:
                app.logger.warn("Empty data received. updateTestcasename_ICE")
        except Exception as e:
            servicesException("updateTestcasename_ICE",e)
        return jsonify(res)

    #New API to checkReuse of a Node migration from Neo4j to MongoDB
    #  Incomplete
    @app.route('/create_ice/node_reuse_ICE',methods=['POST'])
    def node_reuse_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside node_reuse_ICE. Query: "+str(requestdata["name"]))
            if not isemptyrequest(requestdata):
                # Queries for reuse
                print("Do something")
            else:
                app.logger.warn("Empty data received. node_reuse_ICE")
        except Exception as e:
            servicesException("node_reuse_ICE",e)
        return jsonify(res)

    # New API for getting Module Details.
    @app.route('/mindmap/getModules',methods=['POST'])
    def getModules():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getModules. Query: "+str(requestdata["name"]))
            if 'moduleid' in requestdata and requestdata['moduleid']!=None:
                mindmapdata=list(n68session.mindmaps.find({"_id":ObjectId(requestdata["moduleid"])},{"testscenarios":1,"_id":1,"name":1,"projectid":1}))
                scenarioids=[]
                screenids=[]
                testcaseids=[]
                scenarioidsSeen=set()
                screenidsSeen=set()
                testcaseidsSeen=set()
                taskids=[]
                # Preparing data for fetching details of screens,testcases and scenarios
                for i in range(len(mindmapdata[0]["testscenarios"])):
                    scenarios=mindmapdata[0]["testscenarios"]
                    if scenarios[i]["_id"] not in scenarioidsSeen:
                        scenarioidsSeen.add(scenarios[i]["_id"])
                        scenarioids.append(scenarios[i]["_id"])
                    for j in range(len(scenarios[i]["screens"])):
                        screens=scenarios[i]["screens"]
                        if screens[j]["_id"] not in screenidsSeen:
                            screenidsSeen.add(screens[j]["_id"])
                            screenids.append(screens[j]["_id"])
                        for k in range(len(screens[j]["testcases"])):
                            testcase=screens[j]["testcases"][k]
                            # for l in range(len(testcases)):
                            if testcase not in testcaseidsSeen:
                                testcaseidsSeen.add(testcase)
                                testcaseids.append(testcase)

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
                for i in range(len(taskdetails)):
                    if taskdetails[i]["nodeid"] not in taskdata:
                        taskdata[taskdetails[i]["nodeid"]]=[taskdetails[i]]
                    else:
                        taskdata[taskdetails[i]["nodeid"]].append(taskdetails[i])

                scenariodata={}
                for i in range(len(scenariodetails)):
                    scenariodata[scenariodetails[i]["_id"]]={
                        "name":scenariodetails[i]["name"],
                        "reuse":True if len(scenariodetails[i]["parent"])>1 else False
                        }
                screendata={}
                for i in range(len(screendetails)):
                    screendata[screendetails[i]["_id"]]={
                        "name":screendetails[i]["name"],
                        "reuse":True if len(screendetails[i]["parent"])>1 else False
                        }
                testcasedata={}
                for i in range(len(testcasedetails)):
                    testcasedata[testcasedetails[i]["_id"]]={
                    "name":testcasedetails[i]["name"],
                    # "reuse": True if len(testcasedetails[i]["parent"])>1 else False
                    "reuse": True if testcasedetails[i]["parent"]>1 else False
                    }
                finaldata={}
                finaldata["name"]=mindmapdata[0]["name"]
                finaldata["_id"]=mindmapdata[0]["_id"]
                finaldata["projectID"]=mindmapdata[0]["projectid"]
                finaldata["type"]="modules"
                finaldata["childIndex"]=0
                finaldata["state"]="saved"
                finaldata["children"]=[]
                finaldata["completeFlow"]=True
                finaldata["task"]=taskdata[mindmapdata[0]["_id"]] if mindmapdata[0]["_id"] in taskdata else None
                projectid=mindmapdata[0]["projectid"]

                # Preparing final data in format needed
                if len(mindmapdata[0]["testscenarios"])==0:
                    finaldata["completeFlow"]=False
                for i in range(len(mindmapdata[0]["testscenarios"])):

                    finalscenariodata={}
                    scenarios=mindmapdata[0]["testscenarios"]
                    finalscenariodata["projectID"]=projectid
                    finalscenariodata["_id"]=scenarios[i]["_id"]
                    finalscenariodata["name"]=scenariodata[scenarios[i]["_id"]]["name"]
                    finalscenariodata["type"]="scenarios"
                    finalscenariodata["childIndex"]=str(i+1)
                    finalscenariodata["children"]=[]
                    finalscenariodata["state"]="saved"
                    finalscenariodata["reuse"]=scenariodata[scenarios[i]["_id"]]["reuse"]
                    finalscenariodata["task"]=taskdata[scenarios[i]["_id"]] if scenarios[i]["_id"] in taskdata else None

                    if len(scenarios[i]["screens"])==0:
                        finaldata["completeFlow"]=False
                    for j in range(len(scenarios[i]["screens"])):

                        finalscreendata={}
                        screens=scenarios[i]["screens"]
                        finalscreendata["projectID"]=projectid
                        finalscreendata["_id"]=screens[j]["_id"]
                        finalscreendata["name"]=screendata[screens[j]["_id"]]["name"]
                        finalscreendata["type"]="screens"
                        finalscreendata["childIndex"]=str(j+1)
                        finalscreendata["children"]=[]
                        finalscreendata["reuse"]=screendata[screens[j]["_id"]]["reuse"]
                        finalscreendata["state"]="saved"
                        finalscreendata["task"]=taskdata[screens[j]["_id"]] if screens[j]["_id"] in taskdata else None

                        if len(screens[j]["testcases"])==0:
                            finaldata["completeFlow"]=False
                        for k in range(len(screens[j]["testcases"])):
                            testcase=screens[j]["testcases"][k]
                            finaltestcasedata={}
                            finaltestcasedata["projectID"]=projectid
                            finaltestcasedata["_id"]=testcase
                            finaltestcasedata["name"]=testcasedata[testcase]["name"]
                            finaltestcasedata["type"]="testcases"
                            finaltestcasedata["childIndex"]=str(k+1)
                            finaltestcasedata["children"]=[]
                            finaltestcasedata["reuse"]=testcasedata[testcase]["reuse"]
                            finaltestcasedata["state"]="saved"
                            finaltestcasedata["task"]=taskdata[testcase] if testcase in taskdata else None
                            finalscreendata["children"].append(finaltestcasedata)
                        finalscenariodata["children"].append(finalscreendata)
                    finaldata["children"].append(finalscenariodata)

                res={'rows':finaldata}
            else:
                queryresult=list(n68session.mindmaps.find({"projectid":ObjectId(requestdata["projectid"])},{"name":1,"_id":1,"type":1}))
                res={'rows':queryresult}
        except Exception as e:
            servicesException("getModules",e)
        return jsonify(res)

    # #New API to checkReuse of a Node migration from Neo4j to MongoDB
    # #  Incomplete
    # @app.route('/create_ice/node_reuse_ICE',methods=['POST'])
    # def node_reuse_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside node_reuse_ICE. Query: "+str(requestdata["name"]))
    #         if not isemptyrequest(requestdata):
    #             print("Do something")
    #         else:
    #             app.logger.warn("Empty data received. node_reuse_ICE")
    #     except Exception as e:
    #         servicesException("node_reuse_ICE",e)
    #     return jsonify(res)

    @app.route('/plugins/getTasksJSON',methods=['POST'])
    def getTasksJSON():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            print("req",requestdata)
            app.logger.debug("Inside getTasksJSON.")
            if not isemptyrequest(requestdata):
                userid=requestdata["userid"]
                tasks=list(n68session.tasks.find({"$or":[{"assignedto":ObjectId(userid)},{"reviewer":ObjectId(userid)}]}))
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
        res={'rows':'fail'}
        try:
           requestdata=json.loads(request.data)
           requestdata=requestdata["data"]
           print(requestdata)
           projectid=requestdata['projectid']
           createdby=requestdata['userid']
           createdbyrole=requestdata['userroleid']
           versionnumber=requestdata['versionnumber']
           createdthrough=requestdata['createdthrough']
           module_type="basic"

           for moduledata in requestdata['testsuiteDetails']:
               if moduledata["state"]=="created":
                   currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,module_type)
               else:
                   currentmoduleid=moduledata['testsuiteId']
               idsforModule=[]
               for scenariodata in moduledata['testscenarioDetails']:
                   testcaseidsforscenario=[]
                   if scenariodata["state"]=="created":
                       currentscenarioid=saveTestScenario(projectid,scenariodata['testscenarioName'],versionnumber,createdby,createdbyrole)
                   else:
                       currentscenarioid=scenariodata['testscenarioid']
                   iddata1={"_id":ObjectId(currentscenarioid),"screens":[]}
                   for screendata in scenariodata['screenDetails']:
                       if screendata["state"]=="created":
                           currentscreenid=saveScreen(projectid,screendata["screenName"],versionnumber,createdby,createdbyrole,currentscenarioid)
                       else:
                           currentscreenid=screendata["screenid"]
                       iddata2={"_id":ObjectId(currentscreenid),"testcases":[]}
                       for testcasedata in screendata['testcaseDetails']:
                           if testcasedata["state"]=="created":
                               currenttestcaseid=saveTestcase(currentscreenid,testcasedata['testcaseName'],versionnumber,createdby,createdbyrole)
                           else:
                               currenttestcaseid=testcasedata['testcaseid']
                           testcaseidsforscenario.append(ObjectId(currenttestcaseid))
                           iddata2["testcases"].append(ObjectId(currenttestcaseid))
                       iddata1["screens"].append(iddata2)
                   idsforModule.append(iddata1)
                   n68session.testscenarios.update_one({'_id':ObjectId(currentscenarioid)},{'$set':{'testcaseids':testcaseidsforscenario}})
               n68session.mindmaps.update_one({"_id":ObjectId(currentmoduleid)},{'$set':{'testscenarios':idsforModule}})

           res={'rows':currentmoduleid}
        except Exception as e:
            servicesException("saveMindmap",e)
        return jsonify(res)

    # @app.route('/reports/getAllSuites_ICE',methods=['POST'])
    # def getAllSuites_ICE():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         app.logger.debug("Inside getAllSuites_ICE. Query: "+str(requestdata["query"]))
    #         if not isemptyrequest(requestdata):
    #             if(requestdata["query"] == 'projects'):
    #                 #requestdata["userid"]="5da058104f9e97ecf683306e"
    #                 queryresult1=n68session.users.find_one({"_id": ObjectId(requestdata["userid"])},{"projects":1,"_id":0})
    #                 queryresult=list(n68session.projects.find({"_id":{"$in":queryresult1["projects"]}},{"name":1,"releases":1}))
    #             elif(requestdata["query"] == 'getAlltestSuites'):
    #                 queryresult=list(n68session.testsuites.find({"cycle": ObjectId(requestdata["id"])},{"_id":1,"name":1}))
    #             else:
    #                 return jsonify(res)
    #             res= {"rows":queryresult}
    #             return jsonify(res)
    #         else:
    #             app.logger.warn('Empty data received. report suites details.')
    #             return jsonify(res)
    #     except Exception as getAllSuitesexc:
    #         print (getAllSuitesexc)
    #         servicesException("getAllSuites_ICE",getAllSuitesexc)
    #         res={'rows':'fail'}
    #         return jsonify(res)

    # Under Development

    # @app.route('/create_ice/saveMindmapE2E',methods=['POST'])
    # def saveMindmapEndtoEnd():
    #     res={'rows':'fail'}
    #     try:
    #         requestdata=json.loads(request.data)
    #         print("req",requestdata["data"])
    #         requestdata=requestdata["data"]
    #         app.logger.debug("Inside saveMindmapE2E.")
    #         if not isemptyrequest(requestdata):
    #             projectid=requestdata['projectid']
    #
    #             # userid=requestdata['userid']
    #             # userroleid=requestdata['userroleid']
    #             # versionnumber=requestdata['versionnumber']
    #             # createdthrough=requestdata['createdthrough']
    #             # type=requestdata['type']
    #
    #             # Hardcoded:
    #             createdby="5da8670ff87fdec084ae4993"
    #             createdbyrole="5da865d4f87fdec084ae497d"
    #             versionnumber=0
    #             createdthrough="Web"
    #             type="endtoend"
    #
    #             for moduledata in requestdata['testsuiteDetails']:
    #                 if moduledata["state"]=="created":
    #                     currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,type)
    #                 else:
    #                     currentmoduleid=moduledata['testsuiteId']
    #             currentmoduleid=saveTestSuite(projectid,moduledata['testsuiteName'],versionnumber,createdthrough,createdby,createdbyrole,type)
    #
    #
    #         else:
    #             app.logger.warn("Empty data received. saveMindmapE2E")
    #     except Exception as e:
    #         servicesException("saveMindmapE2E",e)
    #     return jsonify(res)

    def checkReuse():
        pass

    def saveTestSuite(projectid,modulename,versionnumber,createdthrough,createdby,createdbyrole,type,testscenarios=[]):
        app.logger.debug("Inside saveTestSuite.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":modulename,
        "versionnumber":versionnumber,
        "createdon":createdon,
        "createdthrough":createdthrough,
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole), #extra to be sent from the UI
        "deleted":False,
        "modifiedby": ObjectId(createdby),
        "modifiedon": createdon,
        "modifiedbyrole": ObjectId(createdbyrole), #extra to be sent through UI.
        "type": type, #extra parameter to be sent
        "testscenarios":[]
        }
        queryresult=n68session.mindmaps.insert_one(data).inserted_id
        return queryresult

    def saveTestScenario(projectid,testscenarioname,versionnumber,createdby,createdbyrole,testcaseids=[]):
        app.logger.debug("Inside saveTestScenario.")
        createdon = datetime.now()
        data={
            "name":testscenarioname,
            "projectid":ObjectId(projectid),
            "parent":[] ,# ModuleID to be passed here.
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
        return queryresult

    def saveScreen(projectid,screenname,versionnumber,createdby,createdbyrole,scenarioid=None):
        app.logger.debug("Inside saveScreen.")
        createdon = datetime.now()
        data={
        "projectid":ObjectId(projectid),
        "name":screenname,
        "versionnumber":versionnumber,
        "parent":[ObjectId(scenarioid)], #New property added #scenarioid to be send here.
        "createdby":ObjectId(createdby),
        "createdbyrole":ObjectId(createdbyrole), # New parameter to be passed in service
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
        return queryresult

    @app.route('/mindmap/manageTaskDetails',methods=['POST'])
    def manageTaskDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            action=requestdata["action"]
            del requestdata["action"]
            if not isemptyrequest(requestdata):
                if action == "delete":
                    n68session.tasks.delete({"_id":ObjectId(requestdata["taskid"]),"cycle":ObjectId(requestdata["cycleid"])})
                    res={"rows":"success"}
                elif action == "modify":
                    tasks_update=requestdata["update"]
                    for i in tasks_update:
                        i["assignedtime"]=datetime.now()
                        i["startdate"]=datetime.strptime(i["startdate"],"%d/%m/%Y")
                        i["enddate"]=datetime.strptime(i["enddate"],"%d/%m/%Y")
                        n68session.tasks.update({"_id":ObjectId(i["taskid"]),"cycle":ObjectId(i["cycleid"])},{"$set":{"assignedtime":i["assignedtime"],"startdate":i["startdate"],"enddate":i["enddate"],"assignedto":ObjectId(i["assignedto"]),"reviewer":ObjectId(i["reviewer"]),"status":i["status"],"reestimation":i["reestimation"],"complexity":i["complexity"],"history":i["history"]}})
                    tasks_insert=requestdata["insert"]
                    for i in tasks_insert:
                        i["startdate"]=datetime.strptime(i["startdate"],"%d/%m/%Y")
                        i["enddate"]=datetime.strptime(i["enddate"],"%d/%m/%Y")
                        i["assignedtime"]=datetime.now()
                        i["createdon"]=datetime.now()
                        i["owner"]=ObjectId(i["owner"])
                        i["assignedto"]=ObjectId(i["assignedto"])
                        i["nodeid"]=ObjectId(i["nodeid"])
                        if i["parent"] != "":    
                            i["parent"]=ObjectId(i["parent"])
                        i["reviewer"]=ObjectId(i["reviewer"])
                        i["projectid"]=ObjectId(i["projectid"])
                    if len(tasks_insert)>0:
                        n68session.tasks.insert_many(tasks_insert)
                    res={"rows":"success"}
            else:
                app.logger.warn('Empty data received. manage users.')
        except Exception as e:
            servicesException("manageTaskDetails",e)
        return jsonify(res)
