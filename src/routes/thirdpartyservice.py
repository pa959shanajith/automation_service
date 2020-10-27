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
                    # dbsession.thirdpartyintegration.insert_one(requestdata)
                    # dbsession.thirdpartyintegration.delete_many({"type":"ALM","testscenarioid":requestdata["testscenarioid"]})
                    # dbsession.thirdpartyintegration.delete_many({"type":"ALM","qctestcase":requestdata["qctestcase"]})
                    # dbsession.thirdpartyintegration.insert_one(requestdata)
                    sc=list(dbsession.thirdpartyintegration.find({"testscenarioid":requestdata["testscenarioid"]}))
                    if len(sc)>0:
                        qc_tc_insert=sc[0]['qctestcase']
                        for a in requestdata["qctestcase"]:
                            qc_tc_insert.append(a)
                        dbsession.thirdpartyintegration.update_one({"testscenarioid":requestdata["testscenarioid"]}, {'$set': {"qctestcase":qc_tc_insert}})
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
                    result=list(dbsession.thirdpartyintegration.find({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'qtestdetails'):
                    result=list(dbsession.thirdpartyintegration.find({"type":"qTest","testscenarioid":requestdata["testscenarioid"]}))
                    res= {"rows":result}
            else:
                app.logger.warn('Empty data received. getting QcMappedList.')
        except Exception as e:
            servicesException("viewIntegrationMappedList_ICE", e, True)
        return jsonify(res)
################################################################################
# END OF QUALITYCENTRE
################################################################################