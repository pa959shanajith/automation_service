################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime
from pymongo import InsertOne
from pymongo import UpdateOne, UpdateMany
from pymongo import ReplaceOne
from Crypto.Cipher import AES
import codecs

def LoadServices(app, redissession, client ,getClientName):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

    def unpad(data):
        return data[0:-ord(data[-1])]
    
    def unwrap(hex_data, key, iv=b'0'*16):
        dec_data=None
        try:
            data = codecs.decode(hex_data, 'hex')
            aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
            dec_data = unpad(aes.decrypt(data).decode('utf-8'))
        except Exception as e:
            app.logger.error("Invalid input for Decryption")
        return dec_data

    def scrape_unwrap(hex_data):
        key = "".join(['N','i','n','e','e','t','e','e','n','6','8','@','S','e',
            'c','u','r','e','S','c','r','a','p','e','D','a','t','a','P','a','t','h'])
        #to convert string to bytes
        hex_data=hex_data.encode('utf-8')
        return unwrap(hex_data, key)

    # fetches the scrape screen data
    @app.route('/design/getScrapeDataScreenLevel_ICE',methods=['POST'])
    def getScrapeDataScreenLevel_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScrapeDataScreenLevel_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if ('testcaseid' in requestdata and requestdata['testcaseid']):
                    screen_id = dbsession.testcases.find_one({'_id':ObjectId(requestdata['testcaseid'])},{'screenid':1})['screenid'] ##add versionnumber in condition if needed
                else:
                    screen_id = ObjectId(requestdata['screenid'])
                if (requestdata['query'] == 'getscrapedata'):
                    screen_query=dbsession.screens.find_one({"_id":screen_id,"deleted":False})
                    if (screen_query != []):
                        dataobj_query = list(dbsession.dataobjects.find({"parent" :screen_id}))
                        if "scrapeinfo" in screen_query and 'header' in screen_query["scrapeinfo"]:
                            dataobj_query = [screen_query["scrapeinfo"]]
                        for data in dataobj_query:
                            if len(data["parent"]) > 1:
                                data["reused"] = True
                            else:
                                data["reused"] = False
                        res["rows"] = { "view": dataobj_query, "name":screen_query["name"],
                                        "createdthrough": (screen_query["createdthrough"] if ("createdthrough" in screen_query) else ""),
                                        "scrapedurl": (screen_query["scrapedurl"] if ("scrapedurl" in screen_query) else ""),
                                        "mirror": (screen_query["screenshot"] if ("screenshot" in screen_query) else ""),
                                        "reuse": True if("parent" in screen_query and len(screen_query["parent"])>1) else False,
                                        "orderlist": (screen_query["orderlist"] if ("orderlist" in screen_query) else [])
                                      }
                        for scraped_obj in res["rows"]["view"]:
                            xpath_string=scraped_obj["xpath"].split(';')
                            if len(xpath_string) == 3:
                                left_part=scrape_unwrap(xpath_string[0])
                                right_part=scrape_unwrap(xpath_string[2])
                                if left_part is not None and right_part is not None:
                                    scraped_obj["xpath"] = left_part+';'+xpath_string[1]+';'+right_part
                if (requestdata['query']=="getWSscrapedata"):
                    dataobj_query = list(dbsession.dataobjects.find({"parent" :screen_id}))
                    scrapeinfo = dbsession.screens.find_one({"_id":screen_id,"deleted":False},{'_id':0,'parent':1,'scrapeinfo':1})
                    res["rows"] = scrapeinfo['scrapeinfo'] if 'scrapeinfo' in scrapeinfo else {}
                    res["rows"]["reuse"] = True if(len(scrapeinfo["parent"])>1) else False
                    res["rows"]["view"] = dataobj_query
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as getscrapedataexc:
            servicesException("getScrapeDataScreenLevel_ICE",getscrapedataexc, True)
        return jsonify(res)
    
    #updates the screens collection with comparison data after scenario level comparison
    @app.route('/design/updateScenarioComparisionStatus', methods=['POST'])
    def scenarioComparisionData():
        try:
            res={'rows':'fail'}
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]
            app.logger.debug("Inside updateScenarioComparisionStatus. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                scenario_ID = ObjectId(requestdata['scenarioID'])
                scenarioComparisonData = requestdata['scenarioComparisonData']
                for screenComparisonData in scenarioComparisonData:
                    dbsession.screens.update({'_id':ObjectId(screenComparisonData['screenId'])},{"$set":{"changed":screenComparisonData['changed'],"unchanged":screenComparisonData['unchanged'],"notfound":screenComparisonData['notfound'],"statusCode":screenComparisonData['statusCode']}})
                res={"rows":"Success"}
            else:
                app.logger.warn('Empty data received.')
        except Exception as getscrapedataexc:
            servicesException("getScrapeDataScenarioLevel_ICE",getscrapedataexc, True)
        return jsonify(res)       

    #fetches the scraped data on scenario level
    @app.route('/design/getScrapeDataScenarioLevel_ICE', methods=['POST'])
    def getScrapeDataScenarioLevel_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)
            dbsession=client[clientName]
            app.logger.debug("Inside getScrapeDataScenarioLevel_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
                scenario_ID = ObjectId(requestdata['scenarioID'])
                screens = list(dbsession.screens.find({'parent':scenario_ID}))
                testcaseids = dbsession.testscenarios.find_one({'_id':scenario_ID})['testcaseids']
                dataobj_scenario_level = []
                i=0
                for screen in screens:
                    dataobj_query = list(dbsession.dataobjects.find({"parent" :screen['_id']}))
                    dataobj_scenario_level.append({'screen_id'  :screen['_id'],
                                                   'scrapedurl' :screen['scrapedurl'],
                                                   'view'       :dataobj_query,
                                                   'name'       :screen['name'],
                                                   'index'      :i,
                                                   'orderlist'  :screen['orderlist'],
                                                   'mirror'     :screen['screenshot'],
                                                   'testcaseid' :testcaseids[i]})
                    i+=1
                res = {'rows':dataobj_scenario_level}
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as getscrapedataexc:
            servicesException("getScrapeDataScenarioLevel_ICE",getscrapedataexc, True)
        return jsonify(res)

    def update_identifier(object_identifier):
        all_identifier_list = ["xpath","id","rxpath","name","classname","cssselector","href","label"]
        current_identifier_list = []
        for current_identifier_value in object_identifier:
            current_identifier_list.append(current_identifier_value["identifier"])
        if len(all_identifier_list) != len(current_identifier_list):
            for all_identifier_list_index, all_identifier_list_value in enumerate(all_identifier_list):
                if all_identifier_list_value not in current_identifier_list:
                    object_identifier.append({"id":all_identifier_list_index+1,"identifier":all_identifier_list_value})
        return object_identifier


    # Creating a function to update steps if webservice screen is saved
    def updateTestStep(dbsession,to_update_teststep,screen_detail,old_screen_detail):
        #  TO-do authinfo add krna hai
         supported_steps = ["setMethods","setParam","setWholeBody","setHeaderTemplate","setBasicAuth","setBearerToken","setOAuth2.0","setBearerToken"]
         keyword_to_info =  {
                            'setEndPointURL': "endPointURL",
                            'setMethods': "method",
                            'setHeaderTemplate':"header",
                            'setParam':"param",
                            'setWholeBody' : "body",
                            'setBasicAuth':'authKeyword',
                            'setOAuth2.0': 'authKeyword',
                            'setBearerToken':'authKeyword'
                        }
         steps = [
             {
                "stepNo" : 1,
                "custname" : "WebService List",
                "keywordVal" : "setEndPointURL",
                "inputVal" : [ 
                    screen_detail['endPointURL'] if 'endPointURL' in screen_detail else ""
                ],
                "outputVal" : "",
                "appType" : "Webservice",
                "remarks" : "",
                "addDetails" : "",
                "cord" : ""
            }
         ]
         check_for_endpoint_url = False
         if old_screen_detail != {}:
             for step in to_update_teststep['steps']:
                if step['keywordVal'] == 'setEndPointURL' and step['inputVal'][0] == screen_detail['endPointURL']:
                    check_for_endpoint_url = True
                    continue
                if check_for_endpoint_url:
                    if step['keywordVal'] == 'executeRequest':
                        break
                    if step['keywordVal'] not in supported_steps:
                        steps.append(step)
                    else:
                        info = keyword_to_info[step['keywordVal']]
                        if( info == 'authKeyword'):
                            if old_screen_detail[info] != screen_detail[info]:
                                continue
                            if screen_detail[info] == step['keywordVal']:
                                info = 'authInput'
                            elif screen_detail[info] != step['keywordVal']:
                                screen_detail[info]=step['keywordVal']
                                screen_detail['authInput']=step['inputVal'][0]

                        if old_screen_detail[info] == screen_detail[info] and screen_detail[info]!=step['inputVal'][0]:
                            screen_detail[info]=step['inputVal'][0]


         if(screen_detail['method']):
            steps.append({
                            "stepNo" : 2,
                            "custname" : "WebService List",
                            "keywordVal" : "setMethods",
                            "inputVal" : [ 
                                screen_detail['method'] if 'method' in screen_detail else ""
                            ],
                            "outputVal" : "",
                            "appType" : "Webservice",
                            "remarks" : "",
                            "addDetails" : "",
                            "cord" : ""
                        })
         if(screen_detail['header']):
            steps.append({
                            "stepNo" : len(steps)+1,
                            "custname" : "WebService List",
                            "keywordVal" : "setHeaderTemplate",
                            "inputVal" : [ 
                                screen_detail['header'] if 'header' in screen_detail else ""
                            ],
                            "outputVal" : "",
                            "appType" : "Webservice",
                            "remarks" : "",
                            "addDetails" : "",
                            "cord" : ""
                        })
         if(screen_detail['body']):
            steps.append({
                            "stepNo" : len(steps)+1,
                            "custname" : "WebService List",
                            "keywordVal" : "setWholeBody",
                            "inputVal" : [ 
                                screen_detail['body'] if 'body' in screen_detail else ""
                            ],
                            "outputVal" : "",
                            "appType" : "Webservice",
                            "remarks" : "",
                            "addDetails" : "",
                            "cord" : ""
                        })
         if(screen_detail['param']):
            steps.append({
                "stepNo" : len(steps)+1,
                "custname" : "WebService List",
                "keywordVal" : "setParam",
                "inputVal" : [ 
                    screen_detail['param'].replace("##", "&") if 'param' in screen_detail else ""
                ],
                "outputVal" : "",
                "appType" : "Webservice",
                "remarks" : "",
                "addDetails" : "",
                "cord" : ""
            })
         if("authKeyword" in screen_detail and screen_detail['authKeyword']):
            steps.append({
                "stepNo" : len(steps)+1,
                "custname" : "WebService List",
                "keywordVal" : screen_detail['authKeyword'],
                "inputVal" : [ 
                    screen_detail['authInput']
                ],
                "outputVal" : "",
                "appType" : "Webservice",
                "remarks" : "",
                "addDetails" : "",
                "cord" : ""
            }) 
         
         steps.append( {
            "stepNo" : len(steps)+1,
            "custname" : "WebService List",
            "keywordVal" : "executeRequest",
            "inputVal" : [ 
                ""
            ],
            "outputVal" : "",
            "appType" : "Webservice",
            "remarks" : "",
            "addDetails" : "",
            "cord" : ""
        })

                 #  check_for_endpoint_url = False
         
         required_steps = []
         step_count = 1
         check_for_endpoint_url = False
         for step in to_update_teststep['steps']:
             if step['keywordVal'] == 'setEndPointURL' and step['inputVal'][0] == screen_detail['endPointURL']:
                 check_for_endpoint_url = True
             if check_for_endpoint_url:
                 if step['keywordVal'] == 'executeRequest':
                     check_for_endpoint_url = False
                     for updated_step in steps:
                        updated_step['stepNo'] = step_count
                        required_steps.append(updated_step)
                        step_count+=1
             else:
                 step['stepNo'] = step_count
                 required_steps.append(step)
                 step_count+=1
         required_steps = steps if len(required_steps) == 0 else required_steps
         dbsession.testcases.update_one({'_id':to_update_teststep['_id']},{'$set':{'steps':required_steps}})

    # update/delete/insert opertaions on the screen data
    @app.route('/design/updateScreen_ICE',methods=['POST'])
    def updateScreen_ICE():
        app.logger.debug("Inside updateScreen_ICE")
        res={'rows':'fail'}
        try:
            data=json.loads(request.data)
            if not isemptyrequest(data):
                clientName=getClientName(data)         
                dbsession=client[clientName]
                if (data['param']=="updatedIdentifier"):
                    dataObjectIds=[ObjectId(i) for i in data['objectIds']]
                    doiden=data["identifiers"]
                    dbsession.dataobjects.update_many({"_id":{"$in":dataObjectIds}},{"$set":{"identifier":doiden}})
                    res={"rows":"Success"}
                if (data['param']=="updatedProperties"):
                    dataObjectId=data['objectId']
                    xpath=data["xpath"]
                    identifiers=data['identifiers']
                    dbsession.dataobjects.update_one({"_id":ObjectId(dataObjectId)},{"$set":{"xpath":xpath,"identifier":identifiers}})
                    res={"rows":"Success"}
                if data['param'] == 'DebugModeScrapeData':
                    screenId = dbsession.testcases.find_one({'_id':ObjectId(data['testCaseId']), 'versionnumber':data['versionnumber']},{'screenid':1})
                    data['screenId'] = str(screenId['screenid'])
                    data['param'] = 'saveScrapeData'
                if data['param'] == 'saveScrapeData':
                    modifiedbyrole= ObjectId(data["roleId"])
                    modifiedby = ObjectId(data["userId"])
                    screenId = ObjectId(data['screenId'])
                    orderList = data['orderList']
                    if('deletedObj' in data and len(data['deletedObj'])>0):
                        data_push = [ObjectId(i) for i in data['deletedObj']]
                        dbsession.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                        dbsession.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                    if('modifiedObj' in data and len(data['modifiedObj'])>0):
                        data_obj=data["modifiedObj"]
                        for i in data_obj:
                            data_id=ObjectId(i["_id"])
                            if 'parent' in i:
                                for j in range(len(i['parent'])):
                                    i['parent'][j] = ObjectId(i['parent'][j])
                            del i["_id"]
                            dbsession.dataobjects.update({"_id": data_id},{"$set":i})
                    if('addedObj' in data and len(data['addedObj']['view'])>0):
                        data_obj = data['addedObj']['view']
                        data_push=[]
                        tempOrderId_index_dict = {}
                        insertedObjIds = []

                        for i in range(len(data_obj)):
                            data_obj[i]["parent"] = [screenId]
                            tempOrderId_index_dict[data_obj[i]['tempOrderId']] = i
                            del data_obj[i]['tempOrderId']
                            data_push.append(data_obj[i])
                            
                        if (data_push != []):
                            for i in range(len(data_push)):
                                if "_id" in data_push[i]:
                                   insertedObjIds = [{ObjectId(data_push[i]["_id"])}]
                                   dbsession.dataobjects.update({'_id': ObjectId(data_push[i]["_id"])},{"$push":{'parent':screenId}})
                                else:
                                    insertedObjIds = dbsession.dataobjects.insert(data_push)
                                    dbsession.dataobjects.update_many({"_id":{"$in":insertedObjIds}},
                                    {"$set":{"identifier":[{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]}})
                                    break
                                    
                            for index in range(len(orderList)):
                                if (orderList[index] in tempOrderId_index_dict):
                                    addedObjIndex = tempOrderId_index_dict[orderList[index]]
                                    orderList[index] = str(insertedObjIds[addedObjIndex])

                        if "mirror" in data['addedObj']:
                            screenshot = data['addedObj']['mirror']
                            if "scrapedurl" in data['addedObj']:
                                scrapedurl = data['addedObj']["scrapedurl"]
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl}})
                            else:
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot}})
                        elif 'scrapeinfo' in data['addedObj']:
                            scrapeinfo=data['addedObj']['scrapeinfo']
                            dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"], 'scrapeinfo':scrapeinfo}})

                    payload = {"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), "orderlist":orderList}
                    if (len(orderList)<=0):
                        payload['screenshot'] = ""
                        payload['scrapedurl'] = ""

                    dbsession.screens.update({"_id":screenId},{"$set": payload})
                    res={"rows":"Success"}
                if data['param'] == 'renameElenemt':
                    dbsession.dataobjects.update_one({'_id': ObjectId(data['modifiedObj'][0]["id"])},{'$set':{'custname':data['modifiedObj'][0]["custname"]}})
                    res={"rows":"Success"}
                if data["param"] == 'updateMindmapTestcaseScreen':
                    updateteststeps = None
                    mindmapdata=dbsession.mindmaps.find_one({"_id": ObjectId(data["moduleID"]),"projectid": ObjectId(data["projectID"])})
                    for testscenario in mindmapdata['testscenarios']:
                        if testscenario["_id"] == ObjectId(data['parent']):
                            for screen in testscenario['screens']:
                                if screen["_id"] == ObjectId(data['currentScreen']):
                                    if(len(screen['testcases']) >0):
                                        updateteststeps = screen['testcases'][0]
                                        updatescreen = screen["_id"]
                                        res={"row":updateteststeps}
                                        break
                            
                            if(updateteststeps != None):
                                for screen in testscenario['screens']:
                                    if screen["_id"] == ObjectId(data['updateScreen']):
                                        dbsession.mindmaps.update_one(   {
                                                "_id": mindmapdata["_id"],
                                                "testscenarios._id": ObjectId(data['parent']),
                                                "testscenarios.screens._id": ObjectId(data["updateScreen"])
                                            },
                                            {
                                                "$push": {
                                                    "testscenarios.$.screens.$[screen].testcases": updateteststeps
                                                }
                                            },
                                            array_filters=[{"screen._id": ObjectId(data["updateScreen"])}]
                                        )
                                        dbsession.mindmaps.update_one(
                                            {
                                                "_id": mindmapdata["_id"],
                                                "testscenarios._id": ObjectId(data['parent'])
                                            },
                                            {
                                                "$pull": {
                                                    "testscenarios.$[scenario].screens": {"_id": ObjectId(data["currentScreen"])}
                                                }
                                            },
                                            array_filters=[{"scenario._id": ObjectId(data['parent'])}]
                                        )
                                        dbsession.testcases.update({"_id":updateteststeps,"screenid":updatescreen},{"$set":{"screenid":ObjectId(data['updateScreen'])}})
                                        break
                            for screen in testscenario['screens']:
                                screen_ids = []
                                screen_ids.append(screen["_id"])
                                    # Check if all elements in screen_ids are not equal to ObjectId(data['updateScreen'])
                                if all(item != ObjectId(data['updateScreen']) for item in screen_ids):
                                    dbsession.mindmaps.update_one(
                                        {
                                            "_id": mindmapdata["_id"],
                                            "testscenarios._id": ObjectId(data['parent']),
                                            "testscenarios.screens._id": ObjectId(data["currentScreen"])
                                        },
                                        {
                                            "$set": {
                                                "testscenarios.$[scenario].screens.$[screen]._id": ObjectId(data["updateScreen"])
                                            }
                                        },
                                        array_filters=[
                                            {"scenario._id": ObjectId(data['parent'])},
                                            {"screen._id": ObjectId(data["currentScreen"])}
                                        ]
                                    )
                                    if updateteststeps != None:
                                        dbsession.testcases.update({"_id":updateteststeps,"screenid":updatescreen},{"$set":{"screenid":ObjectId(data['updateScreen'])}})
                            dbsession.screens.update({"_id":ObjectId( data["updateScreen"])},{'$push':{'parent': ObjectId(data['parent'])}})
                    res={"rows":data['moduleID']}
                if data["param"] == 'screenPaste':
                    for ordlist in data['orderList']:
                        existingorderlist=dbsession.screens.find_one({"_id": ObjectId(data["screenId"])},{'orderlist': ordlist})
                        object_id_hex = str(existingorderlist['_id'])
                        if ordlist != object_id_hex:
                            dbsession.screens.update({"_id":ObjectId( data["screenId"])},{'$push':{'orderlist': ordlist}})
                            dbsession.dataobjects.update({'_id': ObjectId(ordlist)},{"$push":{'parent':ObjectId(data["screenId"])}})
                            res={"rows": "Success"}
                        else:
                            res={"rows":"Element all ready present"}
                if data['param'] == 'delElement':
                    dbsession.screens.update({'_id': ObjectId(data['screenId'])},{"$set":{'orderlist' : data["orderList"]}})
                    for deletedid in data["deletedObj"]:
                        dbsession.dataobjects.update({'_id': ObjectId(deletedid)},{"$pull":{'parent' : ObjectId(data["screenId"])}})
                    res= {"rows" : "Success"}
                if data['param'] == 'delAllElement':                    
                    for orderlist in data['deletedObj']:
                        list_order = list(dbsession.screens.find({'orderlist': orderlist},{"_id":1, 'orderlist':1}))
                        for inOrderlist in list_order:                            
                            if orderlist in inOrderlist['orderlist']:
                                dbsession.screens.update({"_id": inOrderlist['_id']}, {'$pull':{'orderlist': orderlist}})
                                dbsession.dataobjects.delete_one({'_id': ObjectId(orderlist)})
                    res= {'rows': "Success"}    
                elif data["param"] == "mapScrapeData":
                    objList = data["objList"]
                    orderList = data['orderList']
                    del_obj = []
                    for i in objList:
                        del_obj.append(ObjectId(i[0]))
                    screenId = ObjectId(data["screenId"])
                    modifiedbyrole= data["roleId"]
                    modifiedby = data["userId"]
                    data_push=[]
                    for i in objList:
                        new_id=ObjectId(i[1])
                        old_id=ObjectId(i[0])
                        new_custname=i[2]
                        old_obj = dbsession.dataobjects.find_one({"_id": old_id})
                        old_obj['_id'] = new_id
                        old_obj['custname'] = new_custname
                        dbsession.dataobjects.save(old_obj)
                    if len(del_obj)>0:
                        dbsession.dataobjects.update_many({"_id":{"$in":del_obj},"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                        dbsession.dataobjects.delete_many({"_id":{"$in":del_obj},"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                    dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), "orderlist":orderList}})
                    res = {"rows":"Success"}
                elif data["param"] == "crossReplaceScrapeData":
                    req=[]
                    screenId = ObjectId(data["screenId"])
                    modifiedbyrole= ObjectId(data["roleId"])
                    modifiedby = ObjectId(data["userId"])
                    objList = data["replaceObjList"]
                    old_id=ObjectId(objList['oldObjId'])
                    new_obj=objList['newObjectData']
                    new_obj["parent"]=[screenId]
                    new_obj["identifier"] = [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
                    newObj_id = None
                    query = list(dbsession.dataobjects.find({'_id':old_id}))
                    if len(query[0]['parent'])>=2:
                        newObj_id = dbsession.dataobjects.insert_one(new_obj).inserted_id
                        dbsession.dataobjects.update({"_id":old_id},{"$pull":{"parent":screenId}})
                        dbsession.screens.update({"_id":screenId},{"$pull":{"orderlist":str(old_id)},"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                        dbsession.screens.update({"_id":screenId},{"$push":{"orderlist":str(newObj_id)}})
                    else:
                        req.append(ReplaceOne({"_id":old_id},new_obj))
                        dbsession.dataobjects.bulk_write(req)
                        dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    # update the keywords inside testcases steps
                    for tcid in objList['testcaseIds']:
                        steplist = dbsession.testcases.find_one({'_id':ObjectId(tcid)},{'steps':1,'_id':0})['steps']
                        for newvalue in objList['newKeywordsMap']:
                            for eachstep in steplist:
                                if newObj_id != None and eachstep['keywordVal']==newvalue:
                                    dbsession.testcases.update({'_id':ObjectId(tcid),'steps.'+str(eachstep['stepNo']-1)+'.custname':ObjectId(objList['oldObjId']),'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':newvalue},
                                    {'$set':{'steps.'+str(eachstep['stepNo']-1)+'.custname':newObj_id,'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':objList['newKeywordsMap'][newvalue]}})
                                elif eachstep['custname'] == ObjectId(objList['oldObjId']) and eachstep['keywordVal']==newvalue:
                                    dbsession.testcases.update({'_id':ObjectId(tcid),'steps.'+str(eachstep['stepNo']-1)+'.custname':ObjectId(objList['oldObjId']),'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':newvalue},
                                    {'$set':{'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':objList['newKeywordsMap'][newvalue]}})
                    res={'rows':'Success'}
                elif data["param"] == "WebserviceScrapeData":
                    screenId = ObjectId(data["screenId"])
                    scrapeinfo = json.loads(data["scrapedata"])
                    modifiedbyrole= data["roleId"]
                    modifiedby = data["userId"]
                    data_obj=[]
                    data_push=[]
                    if "view" in scrapeinfo:
                        data_obj=scrapeinfo.pop("view")
                    old_screen_detail = list(dbsession.screens.find({"_id":screenId},{'scrapeinfo':1}))
                    dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"],"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                    Old_obj = list(dbsession.dataobjects.find({"parent":screenId}))
                    for d in data_obj:
                        d["parent"]=[screenId]
                        data_push.append(d)
                    if len(Old_obj)==0 and len(data_push)>0 :
                        dbsession.dataobjects.insert(data_push)
                    elif len(Old_obj)>0 and len(data_push)==0 :
                        remove_data=[o["_id"] for o in Old_obj]
                        dbsession.dataobjects.delete_many({"_id":{"$in":remove_data}})
                    elif len(data_obj)>0:
                        for d in data_obj:
                            d["parent"] = [screenId]
                            existing_object=False
                            for o in Old_obj:
                                #If new_object xpath matches with existing xpath retain the same
                                if d["xpath"]==o["xpath"]:
                                    Old_obj.remove(o)
                                    existing_object=True
                                    break
                            if not(existing_object):
                                dbsession.dataobjects.insert(d)
                        #Delete the old data objects
                        if len(Old_obj) > 0:
                            remove_data=[o["_id"] for o in Old_obj]
                            dbsession.dataobjects.delete_many({"_id":{"$in":remove_data}})
                    
                    # Code to add details in the teststeps
                    to_update_teststep =  list(dbsession.testcases.find({"screenid":screenId}))
                    screen_detail = list(dbsession.screens.find({"_id":screenId}))

                    old_screen_detail  = old_screen_detail[0]['scrapeinfo'] if 'scrapeinfo' in old_screen_detail[0] else {}
                    updateTestStep(dbsession,to_update_teststep[0],screen_detail[0]['scrapeinfo'],old_screen_detail)


                    res={"rows":"Success"}
                elif data["param"] == "importScrapeData":
                    screenId = ObjectId(data["screenId"])
                    data_obj = data["objList"]
                    importedorderlist = []
                    modifiedbyrole=  ObjectId(data["roleId"])
                    modifiedby =  ObjectId(data["userId"])
                    data_push=[]
                    data_up=[]
                    req = []
                    for i in range(len(data_obj["view"])):
                        if '_id' not in data_obj["view"][i]:
                            data_obj["view"][i]['_id'] = ObjectId()
                            importedorderlist.append(str(data_obj["view"][i]['_id']))
                        else:
                            importedorderlist.append(data_obj["view"][i]['_id'])
                            data_obj["view"][i]['_id'] = ObjectId(data_obj["view"][i]['_id'])
                        result=dbsession.dataobjects.find_one({'_id':data_obj["view"][i]['_id']},{"parent":1})
                        if result == None:
                            data_obj["view"][i]["parent"] = [screenId]
                            data_push.append(data_obj["view"][i])
                        else:
                            temp=result['parent']
                            if screenId not in temp:
                                temp.append(screenId)
                                data_obj["view"][i]["parent"] = temp
                                data_up.append(data_obj["view"][i])
                            elif temp == [screenId]:
                                data_obj["view"][i]["parent"] = temp
                                data_push.append(data_obj["view"][i])
                            else:
                                data_obj["view"][i]["parent"] = temp
                                data_up.append(data_obj["view"][i])
                        if "identifier" not in data_obj["view"][i]:
                            data_obj["view"][i]["identifier"] = [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
                        else:
                            data_obj["view"][i]["identifier"] = update_identifier(data_obj["view"][i]["identifier"])
                    if len(data_push)>0 or len(data_up)>0:
                        dbsession.dataobjects.update_many({"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                        dbsession.dataobjects.delete_many({"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                        for row in data_push:
                            req.append(InsertOne(row))
                        for row in data_up:
                            req.append(UpdateOne({"_id":row['_id']},{"$set":{"parent":row["parent"]}}))
                        dbsession.dataobjects.bulk_write(req)
                        if "mirror" in data_obj:
                            screenshot = data_obj['mirror']
                            orderlist = data_obj['orderlist'] if 'orderlist' in data_obj else importedorderlist
                            if "scrapedurl" in data_obj:
                                scrapedurl = data_obj["scrapedurl"]
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                            else:
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                        elif 'scrapeinfo' in data_obj:
                            scrapeinfo=data_obj['scrapeinfo']
                            dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"],"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                        else:
                            dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                        res={"rows":"Success"}
                    else:
                        res={"rows":"fail"}

            else:
                app.logger.warn('Empty data received. updating screen')
        except Exception as updatescreenexc:
            servicesException("updateScreen_ICE",updatescreenexc, True)
        return jsonify(res)



    def getScreenID(dbsession,screenname,projectid):
        screenname=list(dbsession.screens.find({"projectid":ObjectId(projectid),"name":screenname,"deleted":False},{"_id":1}))
        if len(screenname)==1:
            return str(screenname[0]["_id"])
        else:   
            return None

            

    # update/delete/insert opertaions on the screen data using Genius
    @app.route('/design/updateScreen_Genius',methods=['POST'])
    def updateScreen_Genius():
        app.logger.debug("Inside updateScreen_Genius")
        res={'rows':'fail'}
        try:
            dataobjects=json.loads(request.data)
            # app.logger.debug(request.data)
            dataobjectdetails = dataobjects["dataobjects"]
            if not isemptyrequest(dataobjects):
                clientName=getClientName(dataobjects)         
                dbsession=client[clientName]
                for data in dataobjectdetails:
                    if data['param'] == 'DebugModeScrapeData':
                        screenId = dbsession.testcases.find_one({'_id':ObjectId(data['testCaseId']), 'versionnumber':data['versionnumber']},{'screenid':1})
                        data['screenId'] = str(screenId['screenid'])
                        data['param'] = 'saveScrapeData'
                    if data['param'] == 'saveScrapeData':
                        modifiedbyrole= ObjectId(data["roleId"])
                        modifiedby = ObjectId(data["userId"])
                        
                        # screenId = ObjectId(data['screenId'])
                        screenname = data["screenname"]
                        projectid = data["projectid"]
                        screenId = ObjectId(getScreenID(dbsession,screenname,projectid))

                        orderList = data['orderList']
                        temp_orderList = []
                        if('deletedObj' in data and len(data['deletedObj'])>0):
                            data_push = [ObjectId(i) for i in data['deletedObj']]
                            dbsession.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                            dbsession.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                        if('modifiedObj' in data and len(data['modifiedObj'])>0):
                            data_obj=data["modifiedObj"]
                            for i in data_obj:
                                data_id=ObjectId(i["_id"])
                                if 'parent' in i:
                                    for j in range(len(i['parent'])):
                                        i['parent'][j] = ObjectId(i['parent'][j])
                                del i["_id"]
                                dbsession.dataobjects.update({"_id": data_id},{"$set":i})
                        if('addedObj' in data and len(data['addedObj']['view'])>0):
                            data_obj = data['addedObj']['view']
                            # app.logger.debug(data_obj)
                            data_push=[]
                            tempOrderId_index_dict = {}
                            insertedObjIds = []
                            temp_index = 0
                            temp_index_objects = 0
                            for i in range(len(data_obj)):
                                data_obj[i]["parent"] = [screenId]
                                if("custname" in data_obj[i]):
                                    tempOrderId_index_dict[data_obj[i]['tempOrderId']] = temp_index
                                    temp_index+=1
                                del data_obj[i]['tempOrderId']
                                if("custname" in data_obj[i]):
                                    data_push.append(data_obj[i])
                                
                            if (data_push != []):
                                # app.logger.debug(data_push)
                                insertedObjIds = dbsession.dataobjects.insert(data_push)
                                dbsession.dataobjects.update_many({"_id":{"$in":insertedObjIds}},
                                {"$set":{"identifier":[{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]}})

                                for index in range(len(orderList)):
                                    if (orderList[temp_index_objects] in tempOrderId_index_dict):
                                        addedObjIndex = tempOrderId_index_dict[orderList[temp_index_objects]]
                                        orderList[temp_index_objects] = str(insertedObjIds[addedObjIndex])
                                        temp_index_objects+=1
                                    else:
                                        del orderList[temp_index_objects]


                            if "mirror" in data['addedObj']:
                                screenshot = data['addedObj']['mirror']
                                if "scrapedurl" in data['addedObj']:
                                    scrapedurl = data['addedObj']["scrapedurl"]
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl}})
                                else:
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot}})
                            elif 'scrapeinfo' in data['addedObj']:
                                scrapeinfo=data['addedObj']['scrapeinfo']
                                dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"], 'scrapeinfo':scrapeinfo}})

                        payload = {"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), "orderlist":orderList}
                        if (len(orderList)<=0):
                            payload['screenshot'] = ""
                            payload['scrapedurl'] = ""

                        dbsession.screens.update({"_id":screenId},{"$set": payload})
                        res={"rows":"Success"}
                    elif data["param"] == "mapScrapeData":
                        objList = data["objList"]
                        orderList = data['orderList']
                        del_obj = []
                        for i in objList:
                            del_obj.append(ObjectId(i[0]))


                        # screenId = ObjectId(data["screenId"])
                        screenname = data["screenname"]
                        projectid = data["projectid"]
                        screenId = ObjectId(getScreenID(dbsession,screenname,projectid))


                        modifiedbyrole= data["roleId"]
                        modifiedby = data["userId"]
                        data_push=[]
                        for i in objList:
                            new_id=ObjectId(i[1])
                            old_id=ObjectId(i[0])
                            new_custname=i[2]
                            old_obj = dbsession.dataobjects.find_one({"_id": old_id})
                            old_obj['_id'] = new_id
                            old_obj['custname'] = new_custname
                            dbsession.dataobjects.save(old_obj)
                        if len(del_obj)>0:
                            dbsession.dataobjects.update_many({"_id":{"$in":del_obj},"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                            dbsession.dataobjects.delete_many({"_id":{"$in":del_obj},"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                        dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), "orderlist":orderList}})
                        res = {"rows":"Success"}
                    elif data["param"] == "crossReplaceScrapeData":
                        req=[]
                        # screenId = ObjectId(data["screenId"])
                        screenname = data["screenname"]
                        projectid = data["projectid"]
                        screenId = ObjectId(getScreenID(dbsession,screenname,projectid))


                        modifiedbyrole= ObjectId(data["roleId"])
                        modifiedby = ObjectId(data["userId"])
                        objList = data["replaceObjList"]
                        old_id=ObjectId(objList['oldObjId'])
                        new_obj=objList['newObjectData']
                        new_obj["parent"]=[screenId]
                        new_obj["identifier"] = [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
                        newObj_id = None
                        query = list(dbsession.dataobjects.find({'_id':old_id}))
                        if len(query[0]['parent'])>=2:
                            newObj_id = dbsession.dataobjects.insert_one(new_obj).inserted_id
                            dbsession.dataobjects.update({"_id":old_id},{"$pull":{"parent":screenId}})
                            dbsession.screens.update({"_id":screenId},{"$pull":{"orderlist":str(old_id)},"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                            dbsession.screens.update({"_id":screenId},{"$push":{"orderlist":str(newObj_id)}})
                        else:
                            req.append(ReplaceOne({"_id":old_id},new_obj))
                            dbsession.dataobjects.bulk_write(req)
                            dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                        # update the keywords inside testcases steps
                        for tcid in objList['testcaseIds']:
                            steplist = dbsession.testcases.find_one({'_id':ObjectId(tcid)},{'steps':1,'_id':0})['steps']
                            for newvalue in objList['newKeywordsMap']:
                                for eachstep in steplist:
                                    if newObj_id != None and eachstep['keywordVal']==newvalue:
                                        dbsession.testcases.update({'_id':ObjectId(tcid),'steps.'+str(eachstep['stepNo']-1)+'.custname':ObjectId(objList['oldObjId']),'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':newvalue},
                                        {'$set':{'steps.'+str(eachstep['stepNo']-1)+'.custname':newObj_id,'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':objList['newKeywordsMap'][newvalue]}})
                                    elif eachstep['custname'] == ObjectId(objList['oldObjId']) and eachstep['keywordVal']==newvalue:
                                        dbsession.testcases.update({'_id':ObjectId(tcid),'steps.'+str(eachstep['stepNo']-1)+'.custname':ObjectId(objList['oldObjId']),'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':newvalue},
                                        {'$set':{'steps.'+str(eachstep['stepNo']-1)+'.keywordVal':objList['newKeywordsMap'][newvalue]}})
                        res={'rows':'Success'}
                    elif data["param"] == "WebserviceScrapeData":
                        # screenId = ObjectId(data["screenId"])
                        screenname = data["screenname"]
                        projectid = data["projectid"]
                        screenId = ObjectId(getScreenID(dbsession,screenname,projectid))


                        scrapeinfo = json.loads(data["scrapedata"])
                        modifiedbyrole= data["roleId"]
                        modifiedby = data["userId"]
                        data_obj=[]
                        data_push=[]
                        if "view" in scrapeinfo:
                            data_obj=scrapeinfo.pop("view")
                        dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"],"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                        Old_obj = list(dbsession.dataobjects.find({"parent":screenId}))
                        for d in data_obj:
                            d["parent"]=[screenId]
                            data_push.append(d)
                        if len(Old_obj)==0 and len(data_push)>0 :
                            dbsession.dataobjects.insert(data_push)
                        elif len(Old_obj)>0 and len(data_push)==0 :
                            remove_data=[o["_id"] for o in Old_obj]
                            dbsession.dataobjects.delete_many({"_id":{"$in":remove_data}})
                        elif len(data_obj)>0:
                            for d in data_obj:
                                d["parent"] = [screenId]
                                existing_object=False
                                for o in Old_obj:
                                    #If new_object xpath matches with existing xpath retain the same
                                    if d["xpath"]==o["xpath"]:
                                        Old_obj.remove(o)
                                        existing_object=True
                                        break
                                if not(existing_object):
                                    dbsession.dataobjects.insert(d)
                            #Delete the old data objects
                            if len(Old_obj) > 0:
                                remove_data=[o["_id"] for o in Old_obj]
                                dbsession.dataobjects.delete_many({"_id":{"$in":remove_data}})
                        res={"rows":"Success"}
                    elif data["param"] == "importScrapeData":
                        # screenId = ObjectId(data["screenId"])
                        screenname = data["screenname"]
                        projectid = data["projectid"]
                        screenId = ObjectId(getScreenID(dbsession,screenname,projectid))

                        
                        data_obj = data["objList"]
                        importedorderlist = []
                        modifiedbyrole=  ObjectId(data["roleId"])
                        modifiedby =  ObjectId(data["userId"])
                        data_push=[]
                        data_up=[]
                        req = []
                        for i in range(len(data_obj["view"])):
                            if '_id' not in data_obj["view"][i]:
                                data_obj["view"][i]['_id'] = ObjectId()
                                importedorderlist.append(str(data_obj["view"][i]['_id']))
                            else:
                                importedorderlist.append(data_obj["view"][i]['_id'])
                                data_obj["view"][i]['_id'] = ObjectId(data_obj["view"][i]['_id'])
                            result=dbsession.dataobjects.find_one({'_id':data_obj["view"][i]['_id']},{"parent":1})
                            if result == None:
                                data_obj["view"][i]["parent"] = [screenId]
                                data_push.append(data_obj["view"][i])
                            else:
                                temp=result['parent']
                                if screenId not in temp:
                                    temp.append(screenId)
                                    data_obj["view"][i]["parent"] = temp
                                    data_up.append(data_obj["view"][i])
                                elif temp == [screenId]:
                                    data_obj["view"][i]["parent"] = temp
                                    data_push.append(data_obj["view"][i])
                                else:
                                    data_obj["view"][i]["parent"] = temp
                                    data_up.append(data_obj["view"][i])
                            if "identifier" not in data_obj["view"][i]:
                                data_obj["view"][i]["identifier"] = [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
                        if len(data_push)>0 or len(data_up)>0:
                            dbsession.dataobjects.update_many({"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                            dbsession.dataobjects.delete_many({"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                            for row in data_push:
                                req.append(InsertOne(row))
                            for row in data_up:
                                req.append(UpdateOne({"_id":row['_id']},{"$set":{"parent":row["parent"]}}))
                            dbsession.dataobjects.bulk_write(req)
                            if "mirror" in data_obj:
                                screenshot = data_obj['mirror']
                                orderlist = data_obj['orderlist'] if 'orderlist' in data_obj else importedorderlist
                                if "scrapedurl" in data_obj:
                                    scrapedurl = data_obj["scrapedurl"]
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                                else:
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                            elif 'scrapeinfo' in data_obj:
                                scrapeinfo=data_obj['scrapeinfo']
                                dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"],"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                            else:
                                dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                            res={"rows":"Success"}
                        else:
                            res={"rows":"fail"}

            else:
                app.logger.warn('Empty data received. updating screen')
        except Exception as updatescreenexc:
            servicesException("updateScreen_Genius",updatescreenexc, True)
        return jsonify(res)

    @app.route('/design/fetchReplacedKeywords_ICE',methods=['POST'])
    def fetchReplacedKeywords_ICE():
        res={'rows':'fail'}
        try:
            data=json.loads(request.data)
            if not isemptyrequest(data):
                clientName=getClientName(data)         
                dbsession=client[clientName]
                screenid = ObjectId(data['screenId'])
                queryresult = list(dbsession.testcases.find({"screenid":screenid, "deleted":False},{"steps":1}))
                result={
                    'keywordList':{}
                }
                for i in queryresult: #loop through each testcases
                    for k in i['steps']: #loop through each testcase steps
                        if str(k['custname']) in data['objMap']:
                            if str(k['custname']) in result:
                                if k['keywordVal'] not in result[str(k['custname'])]['keywords']:
                                    result[str(k['custname'])]['keywords'].append(k['keywordVal'])
                                if str(i['_id']) not in result[str(k['custname'])]['testcasesids']:
                                    result[str(k['custname'])]['testcasesids'].append(str(i['_id']))
                            else:
                                result[str(k['custname'])] = {'keywords':[k['keywordVal']],'testcasesids':[str(i['_id'])]}
                        
                # fetch keyword list
                keywordquery = dbsession.projecttypekeywords.find_one({'name':data['appType']},{'_id':0,'keywordsmap':1})['keywordsmap']
                
                newlist = []
                for eachobj in data['objMap']:
                    newlist.append(data['objMap'][eachobj])

                for i in keywordquery:
                    # if i['objecttype'] in newlist:
                    result['keywordList'][i['objecttype']] = i['keywords']
                        # newlist.remove(i['objecttype'])
                    if len(newlist) == 0:
                        break

                res={'rows':result}
            else:
                app.logger.warn('Empty data received. Fetch replaced keywords')
        except Exception as fetchkeywordexc:
            servicesException("fetchReplacedKeywords_ICE", fetchkeywordexc, True)
        return jsonify(res)

    @app.route('/design/updateIrisObjectType',methods=['POST'])
    def updateIrisObjectType():
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside updateIrisObjectType")
            if "_id" in requestdata and requestdata["_id"] == "": del requestdata["_id"]
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if "_id" not in requestdata:
                    res={'rows':'unsavedObject'}
                else:
                    xpathList = str(requestdata['xpath']).split(';')
                    if len(xpathList) == 9 :
                        xpathList[6] = requestdata["type"]
                        xpath = ';'.join(xpathList)
                        dbsession.dataobjects.update({"_id": ObjectId(requestdata["_id"])},{"$set":{"objectType":requestdata["type"],"xpath":xpath}})
                    else:
                        dbsession.dataobjects.update({"_id": ObjectId(requestdata["_id"])},{"$set":{"objectType":requestdata["type"]}})
                    res={'rows':'success'}
        except Exception as updateirisobjexc:
            servicesException("updateIrisObjectType",updateirisobjexc, True)
        return jsonify(res)

    @app.route('/design/updateImportObject',methods=['POST'])
    def updateImportObject():
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside updateIrisObjectType")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                screenId = ObjectId(requestdata["screenid"])
                import_objects = requestdata['data']
                obj_types=['a','button','checkbox','elmnt','img','input','list','radiobutton','select','table']
                key = "".join(['N','i','n','e','e','t','e','e','n','6','8','@','S','e',
                'c','u','r','e','S','c','r','a','p','e','D','a','t','a','P','a','t','h'])
                screen_object_names=[]
                screen_objects=list(dbsession.dataobjects.find({"parent":screenId}))
                for j in screen_objects:
                    screen_object_names.append(j['custname'])
                insert_obj={}
                for i in import_objects:
                    xpath_lst=['null']*12
                    if not 'update' in i or i['update'].lower() == 'no':
                        if not ('objtype' in i) or not(i['objtype'] in obj_types): continue
                        name=i['name']
                        if name in screen_object_names:
                            while name in screen_object_names:
                                if name.split('_')[-1].isdigit():
                                    name='_'.join(name.split('_')[:-1])+'_'+str(int(name.split('_')[-1])+1)
                                else: name=i['name']+'_1'
                        else:
                            name=i['name']
                        for k,v in i['modify'].items():
                            xpath_lst[int(k)]=v
                        left_part=wrap(';'.join(xpath_lst[:2]),key)
                        right_part=wrap(';'.join(xpath_lst[3:]),key)
                        xpath=left_part+';'+xpath_lst[2]+';'+right_part
                        insert_obj['custname']=name
                        insert_obj['xpath']=xpath
                        insert_obj['url']= wrap(i['url'],key) if 'url' in i else ""
                        insert_obj['tag']= i['objtype'] if 'objtype' in i else ""
                        insert_obj['parent']=[ObjectId(requestdata["screenid"])]
                        if "_id" in insert_obj:
                            del insert_obj["_id"]
                            dbsession.dataobjects.insert(insert_obj)
                        else:
                            dbsession.dataobjects.insert(insert_obj)
                    elif i['name'] in screen_object_names and i['update'].lower() == 'yes':
                        for j in screen_objects:
                            if i['name'] == j['custname']:
                                left_part=unwrap(j['xpath'].split(';')[0],key)
                                right_part=unwrap(j['xpath'].split(';')[2],key)
                                xpath=left_part+';'+j['xpath'].split(';')[1]+';'+right_part
                                xpath_lst=xpath.split(';')
                                for k,v in i['modify'].items():
                                    xpath_lst[int(k)]=v
                                left_part=wrap(';'.join(xpath_lst[:2]),key)
                                right_part=wrap(';'.join(xpath_lst[3:]),key)
                                xpath=left_part+';'+xpath_lst[2]+';'+right_part
                                dbsession.dataobjects.update({"_id": j['_id']},{"$set":{"xpath":xpath}})
                res={"rows":"Success"}
            else:
                app.logger.warn('Empty data received. update import object')
        except Exception as updateimportobj:
            servicesException("updateImportObject",updateimportobj, True)
        return jsonify(res)

def wrap(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex').decode('utf-8')

def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')

def unpad(data):
    return data[0:-ord(data[-1])]

def unwrap(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data, 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))