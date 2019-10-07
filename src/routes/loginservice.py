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

    @app.route('/login')
    def print_hey_login():
        return "Hey Login!"

    #service for login to Nineteen68
    @app.route('/login/authenticateUser_Nineteen68',methods=['POST'])
    def authenticateUser_Nineteen68():
        app.logger.debug("Inside authenticateUser_Nineteen68")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                print("Some buisness logic")
                res['rows'] = "Success!"
            else:
                app.logger.warn('Empty data received. authentication')
        except Exception as authenticateuserexc:
            #app.logger.debug(traceback.format_exc())
            servicesException('authenticateUser_Nineteen68',authenticateuserexc)
        return jsonify(res)
