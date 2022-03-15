################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import codecs
from pymongo import UpdateOne, DeleteOne

def unpad(data):
    return data[0:-ord(data[-1])]

def unwrap(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data, 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def LoadServices(app, redissession, dbsession, *args):
    setenv(app)
    ldap_key = args[0]
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
                    result=list(dbsession.testscenarios.find({"projectid":ObjectId(requestdata["projectid"]),"deleted":False,"$where":"this.parent.length>0"},{"name":1,"_id":1}))
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
                        qc_fld=testcaselist[0]['qcfolderpath']
                        qc_tst=testcaselist[0]['qctestset']
                        qc_fldid=testcaselist[0]['qcfolderid']
                        requestdata_tc = requestdata["qctestcase"]
                        requestdata_folder = requestdata["qcfolderpath"]
                        requestdata_testset = requestdata["qctestset"]
                        requestdata_folderid = requestdata["qcfolderid"]
                        for a in range(len(requestdata_tc)):
                            if requestdata_tc[a] not in qc_tc:
                                qc_tc.append(requestdata_tc[a])
                                qc_fld.append(requestdata_folder[a])
                                qc_tst.append(requestdata_testset[a])
                                qc_fldid.append(requestdata_folderid[a])
                        dbsession.thirdpartyintegration.update_one({"type":"ALM","testscenarioid":requestdata["testscenarioid"]}, {'$set': {"qctestcase":qc_tc,"qcfolderpath":qc_fld,"qctestset":qc_tst,"qcfolderid":qc_fldid}})
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
                elif(requestdata["query"] == 'saveZephyrDetails_ICE' and 'oldtestid' in requestdata):
                    requestdata["type"] = "Zephyr"
                    dbsession.thirdpartyintegration.delete_many({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]})
                    dbsession.thirdpartyintegration.delete_many({"type":"Zephyr","testid":requestdata["oldtestid"]})
                    del requestdata['oldtestid']
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                elif(requestdata["query"] == 'saveZephyrDetails_ICE'):
                    requestdata["type"] = "Zephyr"
                    testcases = requestdata["testname"]
                    scenarios = requestdata["testscenarioid"]
                    testcaselist=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}))
                    testscenarios=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testname":requestdata["testname"]}))
                    if len(scenarios) == 1 and len(testcaselist) != 0:
                        z_tid=testcaselist[0]['testid']
                        z_tn=testcaselist[0]['testname']
                        z_rd=testcaselist[0]['reqdetails']
                        z_pid=testcaselist[0]['parentid']
                        z_treeid=testcaselist[0]['treeid']
                        requestdata_tid = requestdata["testid"]
                        requestdata_tn = requestdata["testname"]
                        requestdata_rd = requestdata["reqdetails"]
                        requestdata_treeid = requestdata["treeid"]
                        requestdata_pid = requestdata["parentid"]
                        for a in range(len(requestdata_tid)):
                            if requestdata_tid[a] not in z_tid:
                                z_tid.append(requestdata_tid[a])
                                z_tn.append(requestdata_tn[a])
                                z_rd.append(requestdata_rd[a])
                                z_pid.append(requestdata_pid[a])
                                z_treeid.append(requestdata_treeid[a])
                        dbsession.thirdpartyintegration.update_one({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}, {'$set': {"testid":z_tid,"testname":z_tn,"reqdetails":z_rd,"treeid":z_treeid,"parentid":z_pid}})
                    elif len(testcases) == 1 and len(testscenarios) != 0:
                        z_ts=testscenarios[0]['testscenarioid']
                        requestdata_ts = requestdata["testscenarioid"]
                        for a in requestdata_ts:
                            if a not in z_ts:
                                z_ts.append(a)
                        dbsession.thirdpartyintegration.update_one({"type":"Zephyr","testname":requestdata["testname"]}, {'$set': {"testscenarioid":z_ts}})
                    else:
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
                    if "testscenarioid" in requestdata:
                        result=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}))
                        res= {"rows":result}
                    else:
                        result = []
                        projectlist=list(dbsession.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                        if len(projectlist) > 0:
                            projects = projectlist[0]['projects']
                            scenariolist=list(dbsession.testscenarios.find({"projectid":{'$in':projects},"deleted":False,"$where":"this.parent.length>0"},{"name":1,"_id":1}))
                            if len(scenariolist) > 0:
                                scenarios = {str(i['_id']):i['name'] for i in scenariolist}
                                zephyrmaplist=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testscenarioid":{'$in':list(scenarios.keys())}}))
                                if len(zephyrmaplist) > 0:
                                    for mapping in zephyrmaplist:
                                        mapping['testscenarioname']=[]
                                        for scenarioId in list(mapping['testscenarioid']):
                                            if scenarioId in scenarios:
                                                mapping['testscenarioname'].append(scenarios[scenarioId])
                                            else:
                                                mapping['testscenarioid'].remove(scenarioId)
                                    result.extend(zephyrmaplist)
                        res= {"rows":result}
            else:
                app.logger.warn('Empty data received. getting QcMappedList.')
        except Exception as e:
            servicesException("viewIntegrationMappedList_ICE", e, True)
        return jsonify(res)

    @app.route('/qualityCenter/getMappedDetails',methods=['POST'])
    def getMappedDetails():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getMappedDetails. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if("releaseId" in requestdata):
                    result=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","releaseid":int(requestdata["releaseId"])}))
                    res= {"rows":result}
                elif("treeid" in requestdata):
                    findquery = {"type":"Zephyr","treeid":str(requestdata["treeid"])}
                    if "parentid" in requestdata and requestdata["parentid"]!='': 
                        findquery["parentid"] = str(requestdata["parentid"])
                    if "testcaseids" in requestdata: 
                        findquery["testid"] = {'$in':requestdata["testcaseids"]}
                    res["rows"] = list(dbsession.thirdpartyintegration.find(findquery))
            else:
                app.logger.warn('Empty data received. getting QcMappedList.')
        except Exception as e:
            servicesException("getMappedDetails", e, True)
        return jsonify(res)

        
    @app.route('/qualityCenter/updateMapDetails_ICE',methods=['POST'])
    def updateMapDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateMapDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                if(requestdata["query"] == 'updateMapDetails_ICE'):
                    if requestdata['screenType']=='ALM':
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
                                folderpath = mapObj["qcfolderpath"]
                                testset = mapObj["qctestset"]
                                for i in range(len(testcase)):
                                    index = result1[0]['qctestcase'].index(testcase[i])
                                    del result1[0]['qcfolderpath'][index]
                                    del result1[0]['qctestset'][index]
                                    del result1[0]['qctestcase'][index]
                                if len(result1[0]['qctestcase']) == 0 :
                                    dbsession.thirdpartyintegration.delete_one({"_id":ObjectId(mapObj["mapid"]),"type":"ALM"})
                                else:
                                    dbsession.thirdpartyintegration.update_one({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"qctestcase":result1[0]['qctestcase'], "qcfolderpath":result1[0]['qcfolderpath'], "qctestset":result1[0]['qctestset']}})
                        res= {"rows":"success"}
                    elif requestdata['screenType']=='Zephyr':
                        app.logger.debug("Inside updateMapDetails_ICE - Zephyr unsync")
                        req=[]
                        for mapObj in requestdata["mapList"]:
                            result1 = list(dbsession.thirdpartyintegration.find({"_id":ObjectId(mapObj["mapid"]),"type":"Zephyr"}))
                            if "testscenarioid" in mapObj:
                                #updating scenarioid
                                scenarioid = mapObj["testscenarioid"]
                                for i in scenarioid:
                                    result1[0]['testscenarioid'].remove(i)
                                if len(result1[0]['testscenarioid']) == 0 :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Zephyr"}))
                                else:
                                    req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testscenarioid":result1[0]['testscenarioid']}}))
                            elif "testCaseNames" in mapObj:
                                #updating testcase
                                testname = mapObj["testCaseNames"]
                                for i in range(len(testname)):
                                    index = result1[0]['testname'].index(testname[i])
                                    del result1[0]['testid'][index]
                                    del result1[0]['testname'][index]
                                    del result1[0]['treeid'][index]
                                    del result1[0]['parentid'][index]
                                    del result1[0]['reqdetails'][index]
                                if len(result1[0]['testname']) == 0 :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Zephyr"}))
                                else:
                                    req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testid":result1[0]['testid'], "testname":result1[0]['testname'],"treeid":result1[0]['treeid'],"parentid":result1[0]['parentid'],"reqdetails":result1[0]['reqdetails']}}))
                        if len(req)!=0:
                            dbsession.thirdpartyintegration.bulk_write(req)
                        res= {"rows":"success"}
            else:
                app.logger.warn('Empty data received. updating after unsyc.')
        except Exception as e:
            servicesException("updateMapDetails_ICE", e, True)
        return jsonify(res)
################################################################################
# END OF QUALITYCENTRE
################################################################################

    @app.route('/plugins/getMappedDiscoverUser',methods=['POST'])
    def getMappedDiscoverUser():
        app.logger.debug("Inside getMappedDiscoverUser")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                userid = ObjectId(requestdata['userid'])
                discoverDocument = dbsession.thirdpartyintegration.find_one({ "type": "AvoDiscover", "avodiscoverconfig.userid": userid})
                if discoverDocument is not None:
                    requser = {}
                    for user in discoverDocument['avodiscoverconfig']:
                        if user['userid'] == ObjectId(requestdata['userid']):
                            requser = user
                            break
                    res = {'result' : 'pass', 'url' : discoverDocument['avodiscoverurl'], 'username': requser['avodiscoveruser'], 'password': unwrap(requser['avodiscoverpswrd'],ldap_key) }
                else:
                    res = {'result' : 'fail'}
            else:
                app.logger.warn('Empty data received while getting mapped discover users.')
        except Exception as e:
            servicesException("getMappedDiscoverUser",e)
        return jsonify(res)