################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime
from pymongo import InsertOne
from pymongo import UpdateOne

def LoadServices(app, redissession, dbsession):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

    # fetches the scrape screen data
    @app.route('/design/getScrapeDataScreenLevel_ICE',methods=['POST'])
    def getScrapeDataScreenLevel_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside getScrapeDataScreenLevel_ICE. Query: "+str(requestdata["query"]))
            if not isemptyrequest(requestdata):
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
                        res["rows"] = { "view": dataobj_query, "name":screen_query["name"],
                                        "createdthrough": (screen_query["createdthrough"] if ("createdthrough" in screen_query) else ""),
                                        "scrapedurl": (screen_query["scrapedurl"] if ("scrapedurl" in screen_query) else ""),
                                        "mirror": (screen_query["screenshot"] if ("screenshot" in screen_query) else ""),
                                        "reuse": True if(len(screen_query["parent"])>1) else False
                                      }
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

    # update/delete/insert opertaions on the screen data
    @app.route('/design/updateScreen_ICE',methods=['POST'])
    def updateScreen_ICE():
        app.logger.debug("Inside updateScreen_ICE")
        res={'rows':'fail'}
        try:
            data=json.loads(request.data)
            if not isemptyrequest(data):
                if data['param'] == 'DebugModeScrapeData':
                    screenId = dbsession.testcases.find_one({'_id':ObjectId(data['testCaseId']), 'versionnumber':data['versionnumber']},{'screenid':1})
                    data['screenId'] = str(screenId['screenid'])
                    data['param'] = 'saveScrapeData'
                if data['param'] == 'saveScrapeData':
                    update_flag = False
                    modifiedbyrole= ObjectId(data["roleId"])
                    modifiedby = ObjectId(data["userId"])
                    screenId = ObjectId(data['screenId'])
                    if('deletedObj' in data and len(data['deletedObj'])>0):
                        update_flag = True
                        print(data['deletedObj'])
                        data_push = [ObjectId(i) for i in data['deletedObj']]
                        dbsession.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                        dbsession.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                    if('modifiedObj' in data and len(data['modifiedObj'])>0):
                        update_flag = True
                        print(data['modifiedObj'])
                        data_obj=data["modifiedObj"]
                        for i in data_obj:
                            data_id=ObjectId(i["_id"])
                            if 'parent' in i:
                                for j in range(len(i['parent'])):
                                    i['parent'][j] = ObjectId(i['parent'][j])
                            del i["_id"]
                            dbsession.dataobjects.update({"_id": data_id},{"$set":i})
                    if('addedObj' in data and len(data['addedObj']['view'])>0):
                        update_flag = True
                        data_obj = data['addedObj']['view']
                        data_push=[]
                        for i in range(len(data_obj)):
                            data_obj[i]["parent"] = [screenId]
                            data_push.append(data_obj[i])
                        if (data_push != []):
                            dbsession.dataobjects.insert(data_push)
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

                    if (update_flag):
                        dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                        res={"rows":"Success"}
                elif data["param"] == "mapScrapeData":
                    objList = data["objList"]
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
                    dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    res = {"rows":"Success"}
                elif data["param"] == "WebserviceScrapeData":
                    screenId = ObjectId(data["screenId"])
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
                    screenId = ObjectId(data["screenId"])
                    data_obj = data["objList"]
                    modifiedbyrole=  ObjectId(data["roleId"])
                    modifiedby =  ObjectId(data["userId"])
                    data_push=[]
                    data_up=[]
                    req = []
                    for i in range(len(data_obj["view"])):
                        if '_id' not in data_obj["view"][i]:
                            data_obj["view"][i]['_id'] = ObjectId()
                        else:
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
                            if "scrapedurl" in data_obj:
                                scrapedurl = data_obj["scrapedurl"]
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                            else:
                                dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
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

    @app.route('/design/updateIrisObjectType',methods=['POST'])
    def updateIrisObjectType():
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside updateIrisObjectType")
            if "_id" in requestdata and requestdata["_id"] == "": del requestdata["_id"]
            if not isemptyrequest(requestdata):
                if "_id" not in requestdata:
                    res={'rows':'unsavedObject'}
                else:
                    dbsession.dataobjects.update({"_id": ObjectId(requestdata["_id"])},{"$set":{"objectType":requestdata["type"]}})
                    res={'rows':'success'}
        except Exception as updateirisobjexc:
            servicesException("updateIrisObjectType",updateirisobjexc, True)
        return jsonify(res)