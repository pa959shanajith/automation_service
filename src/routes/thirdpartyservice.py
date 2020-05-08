################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *

def LoadServices(app, redissession, n68session):
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
                    result=list(n68session.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'projectname1'):
                    result=list(n68session.projects.find({"_id":ObjectId(requestdata["projectid"])},{"name":1}))
                    res= {"rows":result}
                elif(requestdata["query"] == 'scenariodata'):
                    result=list(n68session.testscenarios.find({"projectid":ObjectId(requestdata["projectid"])},{"name":1,"_id":1}))
                    res= {"rows":result}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. getting qcProjectDetails.')
        except Exception as e:
            servicesException("qcProjectDetails_ICE", e, True)
        return jsonify(res)

    @app.route('/qualityCenter/saveQcDetails_ICE',methods=['POST'])
    def saveQcDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside saveQcDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'saveQcDetails_ICE'):
                    requestdata["type"] = "ALM"
                    n68session.thirdpartyintegration.insert_one(requestdata)
                    n68session.thirdpartyintegration.delete_many({"type":"ALM","testscenarioid":requestdata["testscenarioid"]})
                    n68session.thirdpartyintegration.delete_many({"type":"ALM","qctestcase":requestdata["qctestcase"]})
                    n68session.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
            else:
                app.logger.warn('Empty data received. getting saveQcDetails.')
        except Exception as e:
            servicesException("saveQcDetails_ICE", e, True)
        return jsonify(res)

    @app.route('/qualityCenter/viewQcMappedList_ICE',methods=['POST'])
    def viewQcMappedList_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside viewQcMappedList_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'qcdetails'):
                    result=list(n68session.thirdpartyintegration.find({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}))
                    res= {"rows":result}
            else:
                app.logger.warn('Empty data received. getting QcMappedList.')
        except Exception as e:
            servicesException("viewQcMappedList_ICE", e, True)
        return jsonify(res)
################################################################################
# END OF QUALITYCENTRE
################################################################################