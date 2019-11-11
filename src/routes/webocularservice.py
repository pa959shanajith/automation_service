################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *

def LoadServices(app, redissession, webocularsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################


################################################################################
# ADD YOUR ROUTES BELOW
################################################################################
    # Service for Webocular in Nineteen68
    @app.route('/reports/getWebocularData_ICE',methods=['POST'])
    def getWebocularData_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.info("Inside getWebocularData_ICE. Query: " + str(requestdata["query"]))
            if (not isemptyrequest(requestdata)):
                    if( requestdata["query"] == 'moduledata' ):
                        reports_data=list(webocularsession.reports.find({},{"_id":1,"modulename":1}))
                        res={'rows':reports_data}
                    elif( requestdata["query"] == 'reportdata' ):
                        reports_data=webocularsession.reports.find({"_id":ObjectId(requestdata["id"])})
                        res={'rows':reports_data}
                    elif( requestdata["query"] == 'insertdata' ):
                        webocularsession.reports.insert_one(requestdata['data'])
                        res={'rows':'success'}
            else:
                app.logger.warn('Empty data received. getWebocularData_ICE.')
        except Exception as getweboculardataexec:
            app.logger.debug(traceback.format_exc())
            servicesException("getWebocularData_ICE has encountered an exception : ",getweboculardataexec)
        return jsonify(res)