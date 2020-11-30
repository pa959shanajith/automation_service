################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *

def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# BEGIN OF QUALITYCENTRE
# INCLUDES : all qc related actions
################################################################################
#fetches the user roles for assigning during creation/updation user
    @app.route('/qualityCenter/qcProjectDetails_ICE',methods=['POST'])
    def qcProjectDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside qcProjectDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'getprojectDetails'):
                    result=list(dbsession.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'projectname1'):
                    result=list(dbsession.projects.find({"_id":ObjectId(requestdata["projectid"])},{"name":1}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'scenariodata'):
                    result=list(dbsession.testscenarios.find({"projectid":ObjectId(requestdata["projectid"])},{"name":1,"_id":1}))
                    res= {"rows":result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. getting qcProjectDetails.')
        except Exception as e:
            servicesException("qcProjectDetails_ICE", e, True)
        return jsonify(res)

    @app.route('/qualityCenter/saveIntegrationDetails_ICE',methods=['POST'])
    def saveQcDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside saveIntegrationDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'saveQcDetails_ICE'):
                    requestdata["type"] = "ALM"
                    testcases = requestdata["qctestcase"]
                    scenarios = requestdata["testscenarioid"]
                    testcaselist=list(dbsession.thirdpartyintegration.find({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}))
                    testscenarios=list(dbsession.thirdpartyintegration.find({"type":"ALM","qctestcase":requestdata["qctestcase"]}))
                    if len(scenarios) == 1 and len(testcaselist) != 0:
                        qc_tc=testcaselist[0]['qctestcase']
                        requestdata_tc = requestdata["qctestcase"]
                        for a in requestdata_tc:
                            if a not in qc_tc:
                                qc_tc.append(a)
                        dbsession.thirdpartyintegration.update_one({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}, {'$set': {"qctestcase":qc_tc}})
                    elif len(testcases) == 1 and len(testscenarios) != 0:
                        qc_tc=testscenarios[0]['testscenarioid']
                        requestdata_tc = requestdata["testscenarioid"]
                        for a in requestdata_tc:
                            if a not in qc_tc:
                                qc_tc.append(a)
                        dbsession.thirdpartyintegration.update_one({"type":"ALM","qctestcase":requestdata["qctestcase"]}, {'$set': {"testscenarioid":qc_tc}})
                    else:
                        dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
                elif(requestdata["query"] == 'saveQtestDetails_ICE'):
                    requestdata["type"] = "qTest"
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    dbsession.thirdpartyintegration.delete_many({"type":"qTest","testscenarioid":requestdata["testscenarioid"]})
                    dbsession.thirdpartyintegration.delete_many({"type":"qTest","qtestsuite":requestdata["qtestsuite"]})
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
                elif(requestdata["query"] == 'saveZephyrDetails_ICE'):
                    requestdata["type"] = "Zephyr"
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    dbsession.thirdpartyintegration.delete_many({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]})
                    dbsession.thirdpartyintegration.delete_many({"type":"Zephyr","testid":requestdata["testid"]})
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}                  
            else:
                app.logger.warn('Empty data received. getting saveIntegrationDetails_ICE.')
        except Exception as e:
            servicesException("saveIntegrationDetails_ICE", e, True)
        return jsonify(res)

    @app.route('/qualityCenter/viewIntegrationMappedList_ICE',methods=['POST'])
    def viewQcMappedList_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside viewIntegrationMappedList_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'qcdetails'):
                    if "testscenarioid" in requestdata:
                        result=list(dbsession.thirdpartyintegration.find({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}))
                    else:
                        result=list(dbsession.thirdpartyintegration.find({"type":"ALM"}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'qtestdetails'):
                    result=list(dbsession.thirdpartyintegration.find({"type":"qTest","testscenarioid":requestdata["testscenarioid"]}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'zephyrdetails'):
                    result=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}))
                    res= {"rows":result}
            else:
                app.logger.warn('Empty data received. getting QcMappedList.')
        except Exception as e:
            servicesException("viewIntegrationMappedList_ICE", e, True)
        return jsonify(res)
        
    @app.route('/qualityCenter/updateMapDetails_ICE',methods=['POST'])
    def updateMapDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateMapDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'updateMapDetails_ICE'):
                    for mapObj in requestdata["mapList"]:
                        result1 = list(dbsession.thirdpartyintegration.find({"_id":ObjectId(mapObj["mapid"]),"type":"ALM"}))
                        if "testscenarioid" in mapObj:
                            #updating scenarioid
                            scenarioid = mapObj["testscenarioid"]
                            for i in scenarioid:
                                result1[0]['testscenarioid'].remove(i)
                            if len(result1[0]['testscenarioid']) == 0 :
                                dbsession.thirdpartyintegration.delete_one({"_id":ObjectId(mapObj["mapid"]),"type":"ALM"})
                            else:
                                dbsession.thirdpartyintegration.update_one({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testscenarioid":result1[0]['testscenarioid']}})
                        elif "qctestcase" in mapObj:
                            #updating testcase
                            testcase = mapObj["qctestcase"]
                            for i in testcase:
                                result1[0]['qctestcase'].remove(i)
                            if len(result1[0]['qctestcase']) == 0 :
                                dbsession.thirdpartyintegration.delete_one({"_id":ObjectId(mapObj["mapid"]),"type":"ALM"})
                            else:
                                dbsession.thirdpartyintegration.update_one({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"qctestcase":result1[0]['qctestcase']}})
                    res= {"rows":"success"}                  
            else:
                app.logger.warn('Empty data received. updating after unsyc.')
        except Exception as e:
            servicesException("updateMapDetails_ICE", e, True)
        return jsonify(res)
################################################################################
# END OF QUALITYCENTRE
################################################################################