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
# ADD YOUR ROUTES BELOW
################################################################################

    @app.route('/admin')
    def print_hey_admin():
        return "Hey Admin!"

    # Service to create/edit/delete users in Nineteen68
    @app.route('/admin/manageUserDetails',methods=['POST'])
    def manageUserDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.info("Inside manageUserDetails. Query: "+str(requestdata["action"]))
            if not isemptyrequest(requestdata):
                print("Some buisness logic")
                res['rows'] = "Success!"
            else:
                app.logger.warn('Empty data received. manage users.')
        except Exception as e:
            #app.logger.debug(traceback.format_exc())
            servicesException("manageUserDetails",e)
        return jsonify(res)
