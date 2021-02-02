################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import base64

def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################

#encrpytion utility AES
    @app.route('/utility/encrypt_ICE/aes',methods=['POST'])
    def encrypt_ICE():
        app.logger.debug("Inside encrypt_ICE")
        res = "fail"
        try:
            BS = 16
            pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
            key = b'\x74\x68\x69\x73\x49\x73\x41\x53\x65\x63\x72\x65\x74\x4b\x65\x79'
            raw=request.data.decode()
            if not (raw is None and raw is ''):
                raw = pad(raw)
                cipher = AES.new( key, AES.MODE_ECB)
                res={'rows':base64.b64encode(cipher.encrypt( raw.encode() )).decode()}
                return jsonify(res)
            else:
                app.logger.error("Invalid input")
                return str(res)
        except Exception as e:
            servicesException("encrypt_ICE", e, True)
            return str(res)

    #directly updates license data
    @app.route('/utility/dataUpdator_ICE',methods=['POST'])
    def dataUpdator_ICE():
        app.logger.debug("Inside dataUpdator_ICE")
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            if not isemptyrequest(requestdata):
                if requestdata['query'] == 'testsuites':
                    count = requestdata['count']
                    userid = ObjectId(requestdata['userid']) if 'userid' in requestdata else ""
                    response = counterupdator(dbsession,'testsuites',userid,count)
                    if response != True:
                        res={'rows':'fail'}
                    else:
                        res={'rows':'success'}
                else:
                    res = {'rows':'fail'}
            else:
                app.logger.warn('Empty data received. Data Updator.')
        except Exception as e:
            servicesException("dataUpdator_ICE", e, True)
        return jsonify(res)

    #directly updates user access
    @app.route('/utility/userAccess',methods=['POST'])
    def userAccess():
        app.logger.debug('Inside userAccess')
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            emptyRequestCheck = isemptyrequest(requestdata)
            if type(emptyRequestCheck) != bool:
                res['rows'] = 'off'
            elif not emptyRequestCheck:
                servicename = requestdata.get('servicename', '')
                roleid = requestdata.get('roleid', '')
                if servicename in EXEMPTED_SERVICES:
                    res['rows'] = True
                elif roleid != 'blank':
                    filter_query = {'_id': ObjectId(roleid), 'servicelist': servicename}
                    result = dbsession.permissions.find_one(filter_query, {"_id":1})
                    res['rows'] = result != None
                else:
                    res['rows'] = True
            else:
                app.logger.warn('Empty data received. user Access Permission.')
        except Exception as useraccessexc:
            servicesException('userAccess', useraccessexc, True)
        return jsonify(res)

################################################################################
# END OF UTILITIES
################################################################################