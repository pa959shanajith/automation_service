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

def LoadServices(app, redissession, client ,getClientName, *args):
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
                clientName=getClientName(requestdata)       
                dbsession=client[clientName]
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
                clientName=getClientName(requestdata)       
                dbsession=client[clientName]
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
                    testcases = requestdata["oldtestid"]
                    
                    #fetch old test mapping
                    findqueryold = {"type":"Zephyr","testid":requestdata["oldtestid"],"testname":requestdata["oldtestname"],"treeid":requestdata["oldtreeid"]}
                    if "oldparentid" in requestdata and requestdata["oldparentid"] != "-1": findqueryold["parentid"] = requestdata["oldparentid"]
                    tests=list(dbsession.thirdpartyintegration.find(findqueryold))
                    
                    #fetch new test mapping
                    findquerynew = {"type":"Zephyr","testid":requestdata["testid"],"testname":requestdata["testname"],"treeid":requestdata["treeid"]}
                    if "parentid" in requestdata and requestdata["parentid"] != "-1": findquerynew["parentid"] = requestdata["parentid"]
                    testsnew=list(dbsession.thirdpartyintegration.find(findquerynew))
                    
                    #old test mapping is found
                    if len(tests) == 1:
                        #read old test data
                        scenarioId=tests[0]['testscenarioid']
                        z_tid=tests[0]['testid']
                        z_tn=tests[0]['testname']
                        z_rd=tests[0]['reqdetails']
                        z_pid=tests[0]['parentid']
                        z_treeid=tests[0]['treeid']
                        z_prid=tests[0]['projectid']
                        z_rid=tests[0]['releaseid']
                        
                        #remove old test from mapping
                        ind = z_tid.index(requestdata["oldtestid"])
                        z_tid.pop(ind)
                        z_tn.pop(ind)
                        z_rd.pop(ind)
                        z_pid.pop(ind)
                        z_treeid.pop(ind)
                        z_prid.pop(ind)
                        z_rid.pop(ind)
                        
                        #add new test to the mapping
                        z_tid.append(requestdata["testid"])
                        z_tn.append(requestdata["testname"])
                        z_rd.append(requestdata["reqdetails"])
                        z_pid.append(requestdata["parentid"])
                        z_treeid.append(requestdata["treeid"])
                        z_prid.append(requestdata["projectid"])
                        z_rid.append(requestdata["releaseid"])
                        
                        #update the mapping with i. old test removed and ii. new test added
                        dbsession.thirdpartyintegration.update_one({"type":"Zephyr","testscenarioid":scenarioId}, {'$set': {"testid":z_tid,"testname":z_tn,"reqdetails":z_rd,"treeid":z_treeid,"parentid":z_pid,"projectid":z_prid,"releaseid":z_rid}})
                        
                        #old test mapping is found and new test is also already mapped to some scenario
                        if len(testsnew) == 1:
                            #read new test mapping data
                            scenarioId=testsnew[0]['testscenarioid']
                            z_tid=testsnew[0]['testid']
                            z_tn=testsnew[0]['testname']
                            z_rd=testsnew[0]['reqdetails']
                            z_pid=testsnew[0]['parentid']
                            z_treeid=testsnew[0]['treeid']
                            z_prid=testsnew[0]['projectid']
                            z_rid=testsnew[0]['releaseid']
                            
                            #remove old test from mapping
                            ind = z_tid.index(requestdata["testid"])
                            z_tid.pop(ind)
                            z_tn.pop(ind)
                            z_rd.pop(ind)
                            z_pid.pop(ind)
                            z_treeid.pop(ind)
                            z_prid.pop(ind)
                            z_rid.pop(ind)
                            
                            #update the mapping after removing new test
                            dbsession.thirdpartyintegration.update_one({"type":"Zephyr","testscenarioid":scenarioId}, {'$set': {"testid":z_tid,"testname":z_tn,"reqdetails":z_rd,"treeid":z_treeid,"parentid":z_pid,"projectid":z_prid,"releaseid":z_rid}})
                    res= {"rows":"success"}
                elif(requestdata["query"] == 'saveZephyrDetails_ICE'):
                    requestdata["type"] = "Zephyr"
                    testcases = requestdata["testname"]
                    scenarios = requestdata["testscenarioid"]
                    testcaselist=list(dbsession.thirdpartyintegration.find({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}))
                    findquerynew = {"type":"Zephyr","testid":requestdata["testid"],"testname":requestdata["testname"],"treeid":requestdata["treeid"]}
                    # if "parentid" in requestdata and requestdata["parentid"] != "-1": findquerynew["parentid"] = requestdata["parentid"]
                    testscenarios=list(dbsession.thirdpartyintegration.find(findquerynew))
                    if len(scenarios) == 1 and len(testcaselist) != 0:
                        z_tid=testcaselist[0]['testid']
                        z_tn=testcaselist[0]['testname']
                        z_rd=testcaselist[0]['reqdetails']
                        z_pid=testcaselist[0]['parentid']
                        z_treeid=testcaselist[0]['treeid']
                        z_prid=testcaselist[0]['projectid']
                        z_rid=testcaselist[0]['releaseid']
                        requestdata_tid = requestdata["testid"]
                        requestdata_tn = requestdata["testname"]
                        requestdata_rd = requestdata["reqdetails"]
                        requestdata_treeid = requestdata["treeid"]
                        requestdata_pid = requestdata["parentid"]
                        requestdata_prid = requestdata["projectid"]
                        requestdata_rid = requestdata["releaseid"]
                        for a in range(len(requestdata_tid)):
                            temp_flag=False
                            for b in range(len(z_tn)):
                                if str(requestdata_tn[a]) == z_tn[b] and str(requestdata_tid[a]) == z_tid[b] and z_pid[b]=='-1' and str(requestdata_treeid[a]) == z_treeid[b]:
                                    z_pid[b]=requestdata_pid[a]
                                    temp_flag=True
                                    break
                                elif str(requestdata_tn[a]) == z_tn[b] and str(requestdata_tid[a]) == z_tid[b] and str(requestdata_pid[a])==z_pid[b] and str(requestdata_treeid[a]) == z_treeid[b]:
                                    temp_flag=True
                                    break
                            if not(temp_flag):
                                z_tid.append(requestdata_tid[a])
                                z_tn.append(requestdata_tn[a])
                                z_rd.append(requestdata_rd[a])
                                z_pid.append(requestdata_pid[a])
                                z_treeid.append(requestdata_treeid[a])
                                z_prid.append(requestdata_prid[a])
                                z_rid.append(requestdata_rid[a])
                        dbsession.thirdpartyintegration.update_one({"type":"Zephyr","testscenarioid":requestdata["testscenarioid"]}, {'$set': {"testid":z_tid,"testname":z_tn,"reqdetails":z_rd,"treeid":z_treeid,"parentid":z_pid,"projectid":z_prid,"releaseid":z_rid}})
                    elif len(testcases) == 1 and len(testscenarios) != 0:
                        z_ts=testscenarios[0]['testscenarioid']
                        requestdata_ts = requestdata["testscenarioid"]
                        z_testcase_pid=testscenarios[0]['parentid']
                        if z_testcase_pid[0]=='-1':
                            if str(requestdata['treeid'][0])==testscenarios[0]['treeid'][0] and str(requestdata['testid'][0])==testscenarios[0]['testid'][0] and str(requestdata['testname'][0])==testscenarios[0]['testname'][0]:
                                z_testcase_pid[0]=str(requestdata['parentid'][0])
                                dbsession.thirdpartyintegration.update_one(findquerynew, {'$set': {"parentid":z_testcase_pid}})
                        for a in requestdata_ts:
                            if a not in z_ts:
                                z_ts.append(a)
                        dbsession.thirdpartyintegration.update_one(findquerynew, {'$set': {"testscenarioid":z_ts}})
                    else:
                        dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
                elif(requestdata["query"] == 'saveJiraDetails_ICE'):
                    requestdata["type"] = "Jira"
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    dbsession.thirdpartyintegration.delete_many({"type":"Jira","testscenarioid":requestdata["testscenarioid"]})
                    dbsession.thirdpartyintegration.delete_many({"type":"Jira","itemCode":requestdata["itemCode"]})
                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
                elif(requestdata["query"] == 'saveAzureDetails_ICE'):
                    requestdata["type"] = "Azure"
                    

                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    dbsession.thirdpartyintegration.delete_many({"type":"Azure","testscenarioid":requestdata["testscenarioid"]})

                    if requestdata["itemType"] == 'UserStory':
                        dbsession.thirdpartyintegration.delete_many({"type":"Azure","userStoryId":requestdata["userStoryId"]})
                    elif requestdata["itemType"] == 'TestCase':
                        dbsession.thirdpartyintegration.delete_many({"type":"Azure","TestCaseId":requestdata["TestCaseId"]})    
                    else:
                        dbsession.thirdpartyintegration.delete_many({"type":"Azure","TestSuiteId":requestdata["TestSuiteId"]})

                    dbsession.thirdpartyintegration.insert_one(requestdata)
                    res= {"rows":"success"}
                elif (requestdata['query'] == 'saveMapping_Testrail'):
                    requestdata["type"] = "Testrail"
                    testcaselist=list(dbsession.thirdpartyintegration.find({"type":"Testrail","testscenarioid":requestdata["testscenarioid"]}))
                    if len(testcaselist) > 0 :
                        testIds = testcaselist[0]['testid']
                        suiteIds = testcaselist[0]['suiteid']
                        projectIds = testcaselist[0]['projectid']
                        testname = testcaselist[0]['testname']
    
                        for i in range(len(requestdata['testid'])):
                            appendingBool = True
                            for j in range(len(testIds)):
                                if requestdata['testid'][i] == testIds[j] :
                                    appendingBool = False
                                    break
                            if appendingBool:
                                testIds.append(requestdata['testid'][i])
                                suiteIds.append(requestdata['suiteid'][i])
                                projectIds.append(requestdata['projectid'][i])
                                testname.append(requestdata['testname'][i])
                                
                        dbsession.thirdpartyintegration.update_one({"type":"Testrail","testscenarioid":requestdata["testscenarioid"]},{'$set': {"testid":testIds,"suiteid":suiteIds,"projectid":projectIds,"testname":testname}})
                        res= {"rows":"success"}
                    else : 
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
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
                elif(requestdata["query"] == 'jiradetails'):
                    result = []
                    projectlist=list(dbsession.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                    if len(projectlist) > 0:
                        projects = projectlist[0]['projects']
                        scenariolist=list(dbsession.testscenarios.find({"projectid":{'$in':projects},"deleted":False,"$where":"this.parent.length>0"},{"name":1,"_id":1}))
                        if len(scenariolist) > 0:
                            scenarios = {str(i['_id']):i['name'] for i in scenariolist}
                            temp_result=list(dbsession.thirdpartyintegration.find({"type":"Jira","testscenarioid":{'$in':list(scenarios.keys())}}))
                            if len(temp_result) > 0:
                                for mapping in temp_result:
                                    mapping['testscenarioname']=[]
                                    scenarioId=mapping['testscenarioid']
                                    if scenarioId in scenarios:
                                        mapping['testscenarioname'].append(scenarios[scenarioId])
                                result.extend(temp_result)
                    if 'scenarioName' in requestdata:
                        for i in result:
                            if requestdata['scenarioName']==i['testscenarioname'][0]:
                                result=i
                                break
                            else:
                                result=[]
                    res= {"rows":result}
                elif(requestdata["query"] == 'azuredetails'):
                    result = []
                    if "testscenarioid" in requestdata:
                        result=list(dbsession.thirdpartyintegration.find({"type":"Azure","testscenarioid":requestdata["testscenarioid"]}))
                        res= {"rows":result}
                    else:
                        projectlist=list(dbsession.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                        if len(projectlist) > 0:
                            projects = projectlist[0]['projects']
                            scenariolist=list(dbsession.testscenarios.find({"projectid":{'$in':projects},"deleted":False,"$where":"this.parent.length>0"},{"name":1,"_id":1}))
                            if len(scenariolist) > 0:
                                scenarios = {str(i['_id']):i['name'] for i in scenariolist}
                                temp_result=list(dbsession.thirdpartyintegration.find({"type":"Azure","testscenarioid":{'$in':list(scenarios.keys())}}))
                                if len(temp_result) > 0:
                                    for mapping in temp_result:
                                        mapping['testscenarioname']=[]
                                        scenarioId=mapping['testscenarioid']
                                        if scenarioId in scenarios:
                                            mapping['testscenarioname'].append(scenarios[scenarioId])
                                    result.extend(temp_result)
                        if 'scenarioName' in requestdata:
                            for i in result:
                                if requestdata['scenarioName']==i['testscenarioname'][0]:
                                    result=i
                                    break
                                else:
                                    result=[]
                        elif 'scenario' in requestdata:
                            for i in result:
                                if requestdata['scenario']==i['testscenarioid']:
                                    result=i
                                    break
                                else:
                                    result=[]            
                    res= {"rows":result}
                elif(requestdata['query'] == 'TestrailDetails'):
                    if "testscenarioid" in requestdata:
                        result=list(dbsession.thirdpartyintegration.find({"type":"Testrail","testscenarioid":requestdata["testscenarioid"]}))
                        res= {"rows":result}
                    else :
                        result = []
                        projectlist=list(dbsession.users.find({"_id":ObjectId(requestdata["userid"])},{"projects":1}))
                        if len(projectlist) > 0:
                            projects = projectlist[0]['projects']
                            scenariolist=list(dbsession.testscenarios.find({"projectid":{'$in':projects},"deleted":False,"$where":"this.parent.length>0"},{"name":1,"_id":1}))
                            if len(scenariolist) > 0:
                                scenarios = {str(i['_id']):i['name'] for i in scenariolist}
                                TestrailMapList=list(dbsession.thirdpartyintegration.find({"type":"Testrail","testscenarioid":{'$in':list(scenarios.keys())}}))
                                
                                if len(TestrailMapList) > 0:
                                    for mapping in TestrailMapList:
                                        mapping['testscenarioname']=[]
                                        for scenarioId in list(mapping['testscenarioid']):
                                            if scenarioId in scenarios:
                                                mapping['testscenarioname'].append(scenarios[scenarioId])
                                            else:
                                                mapping['testscenarioid'].remove(scenarioId)
                                    result.extend(TestrailMapList)
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
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
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
    
    @app.route('/qualityCenter/saveAppActivityData',methods=['POST'])
    def saveAppActivityData():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside saveAppActivityData. Query: "+str(requestdata["activity"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if("activity" in requestdata):
                    result=dbsession.appActivityData.insert_one({"name":requestdata["name"], "activity":requestdata["activity"]})
                    if(result != "fail"):
                        res= {"rows":"sucessfull"}
                    else:
                        res = {"rows": "fail"}
                   
            else:
                app.logger.warn('Empty data received.saveAppActivityData.')

        except Exception as e:
            servicesException("saveAppActivityData", e, True)
        return jsonify(res)  


    @app.route('/qualityCenter/fetchAppData',methods=['POST'])
    def fetchAppData():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)      
                dbsession=client[clientName]
                res['rows']=list(dbsession.appActivityData.find({'name':requestdata['name']['key']}))  
            else:
                app.logger.warn('Empty data received.fetchAppData.')

        except Exception as e:
            servicesException("fetchAppData", e, True)
        return jsonify(res)  
        
    @app.route('/qualityCenter/updateMapDetails_ICE',methods=['POST'])
    def updateMapDetails_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside updateMapDetails_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
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
                                    del result1[0]['projectid'][index]
                                    del result1[0]['releaseid'][index]
                                if len(result1[0]['testname']) == 0 :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Zephyr"}))
                                else:
                                    req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testid":result1[0]['testid'], "testname":result1[0]['testname'],"treeid":result1[0]['treeid'],"parentid":result1[0]['parentid'],"reqdetails":result1[0]['reqdetails'],"projectid":result1[0]['projectid'],"releaseid":result1[0]['releaseid']}}))
                        if len(req)!=0:
                            dbsession.thirdpartyintegration.bulk_write(req)
                        res= {"rows":"success"}
                    elif requestdata['screenType']=='Jira':
                        app.logger.debug("Inside updateMapDetails_ICE - Jira unsync")
                        req=[]
                        for mapObj in requestdata["mapList"]:
                            result1 = list(dbsession.thirdpartyintegration.find({"_id":ObjectId(mapObj["mapid"]),"type":"Jira"}))
                            if "testscenarioid" in mapObj:
                                #updating scenarioid
                                scenarioid = mapObj["testscenarioid"]
                                # for i in scenarioid:
                                if  scenarioid[0]==result1[0]['testscenarioid']:
                                    result1[0]['testscenarioid']=''
                                if result1[0]['testscenarioid'] == '' :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Jira"}))
                                # else:
                                #     req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testscenarioid":result1[0]['testscenarioid']}}))
                            elif "testCaseNames" in mapObj:
                                #updating testcase
                                testname = mapObj["testCaseNames"]
                                if testname[0] == result1[0]['itemCode']:
                                    result1[0]['projectid']=''
                                    result1[0]['projectName']=''
                                    result1[0]['projectCode']=''
                                    result1[0]['itemId']=''
                                    result1[0]['itemCode']=''
                                    result1[0]['itemType']=''
                                    result1[0]['itemSummary']=''
                                if result1[0]['itemCode'] == '' :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Jira"}))
                                # else:
                                #     req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testid":result1[0]['testid'], "testname":result1[0]['testname'],"treeid":result1[0]['treeid'],"parentid":result1[0]['parentid'],"reqdetails":result1[0]['reqdetails'],"projectid":result1[0]['projectid'],"releaseid":result1[0]['releaseid']}}))
                        if len(req)!=0:
                            dbsession.thirdpartyintegration.bulk_write(req)
                            res= {"rows":"success"}
                    elif requestdata['screenType']=='Azure':
                        app.logger.debug("Inside updateMapDetails_ICE - Azure unsync")
                        req=[]
                        for mapObj in requestdata["mapList"]:
                            result1 = list(dbsession.thirdpartyintegration.find({"_id":ObjectId(mapObj["mapid"]),"type":"Azure"}))
                            if "testscenarioid" in mapObj:
                                #updating scenarioid
                                scenarioid = mapObj["testscenarioid"]
                                # for i in scenarioid:
                                if  scenarioid[0]==result1[0]['testscenarioid']:
                                    result1[0]['testscenarioid']=''
                                if result1[0]['testscenarioid'] == '' :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Azure"}))
                                # else:
                                #     req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testscenarioid":result1[0]['testscenarioid']}}))
                            elif "testCaseNames" in mapObj:
                                #updating testcase
                                testname = mapObj["testCaseNames"]
                                if ('userStoryId' in result1[0] and testname[0] == result1[0]['userStoryId']) or ('TestSuiteId' in result1[0] and testname[0] == result1[0]['TestSuiteId']) or ('TestCaseId' in result1[0] and testname[0] == result1[0]['TestCaseId']):
                                    result1[0]['projectid']=''
                                    result1[0]['projectName']=''
                                    result1[0]['projectCode']=''
                                    result1[0]['itemType']=''
                                if result1[0]['itemType'] == '' :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Azure"}))
                                # else:
                                #     req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testid":result1[0]['testid'], "testname":result1[0]['testname'],"treeid":result1[0]['treeid'],"parentid":result1[0]['parentid'],"reqdetails":result1[0]['reqdetails'],"projectid":result1[0]['projectid'],"releaseid":result1[0]['releaseid']}}))
                        if len(req)!=0:
                            dbsession.thirdpartyintegration.bulk_write(req)
                            res= {"rows":"success"}
                    elif requestdata['screenType']=='Testrail':
                        app.logger.debug("Inside updateMapDetails_ICE - Testrail unsync")
                        req=[]
                        for mapObj in requestdata["mapList"]:
                            result1 = list(dbsession.thirdpartyintegration.find({"_id":ObjectId(mapObj["mapid"]),"type":"Testrail"}))
                            if "testscenarioid" in mapObj:
                                #updating scenarioid
                                scenarioid = mapObj["testscenarioid"]
                                for i in scenarioid:
                                    result1[0]['testscenarioid'].remove(i)
                                if len(result1[0]['testscenarioid']) == 0 :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Testrail"}))
                                else:
                                    req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testscenarioid":result1[0]['testscenarioid']}}))
                            elif "testCaseNames" in mapObj:
                                #updating testcase
                                testname = mapObj["testCaseNames"]
                                for i in range(len(testname)):
                                    index = result1[0]['testname'].index(testname[i])
                                    del result1[0]['testid'][index]
                                    del result1[0]['testname'][index]
                                    del result1[0]['suiteid'][index]
                                    del result1[0]['projectid'][index]
                                    
                                if len(result1[0]['testname']) == 0 :
                                    req.append(DeleteOne({"_id":ObjectId(mapObj["mapid"]),"type":"Testrail"}))
                                else:
                                    req.append(UpdateOne({"_id":ObjectId(mapObj["mapid"])}, {'$set': {"testid":result1[0]['testid'], "testname":result1[0]['testname'],"suiteid":result1[0]['suiteid'],"projectid":result1[0]['projectid']}}))
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
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
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