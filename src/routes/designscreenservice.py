################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from datetime import datetime

def LoadServices(app, redissession, n68session):
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
                    screen_id = n68session.testcases.find_one({'_id':ObjectId(requestdata['testcaseid'])},{'screenid':1})['screenid'] ##add versionnumber in condition if needed
                else :
                    screen_id = ObjectId(requestdata['screenid'])
                if (requestdata['query'] == 'getscrapedata'):
                    screen_query=n68session.screens.find_one({"_id":screen_id,"deleted":False})
                    if (screen_query != []):
                        dataobj_query = list(n68session.dataobjects.find({"parent" :screen_id}))
                        if "scrapeinfo" in screen_query and 'header' in screen_query["scrapeinfo"]:
                            dataobj_query = [screen_query["scrapeinfo"]]
                        res["rows"] = {"view":dataobj_query,"scrapedurl":(screen_query["scrapedurl"] if ("scrapedurl" in screen_query) else ""),
                                        "mirror":(screen_query["screenshot"] if ("screenshot" in screen_query) else ""),"name":screen_query["name"],"reuse":True if(len(screen_query["parent"])>1) else False}
                if (requestdata['query']=="getWSscrapedata"):
                    dataobj_query = list(n68session.dataobjects.find({"parent" :screen_id}))
                    scrapeinfo = n68session.screens.find_one({"_id":screen_id,"deleted":False},{'_id':0,'parent':1,'scrapeinfo':1})
                    res["rows"] = scrapeinfo['scrapeinfo'] if 'scrapeinfo' in scrapeinfo else {}
                    res["rows"]["reuse"] = True if(len(scrapeinfo["parent"])>1) else False
                    res["rows"]["view"] = dataobj_query
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as getscrapedataexc:
            app.logger.debug(traceback.format_exc())
            servicesException("getScrapeDataScreenLevel_ICE",getscrapedataexc)
        return jsonify(res)

    # update/delete/insert opertaions on the screen data
    @app.route('/design/updateScreen_ICE',methods=['POST'])
    def updateScreen_ICE():
        app.logger.debug("Inside updateScreen_ICE")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                data = json.loads(request.data)
                if data["type"] == "delete_obj":
                    data_obj=json.loads(data["scrapedata"])
                    data_push=[]
                    #screenshot = data["scrapedata"]["mirror"]
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    screenID = ObjectId(data["screenid"])
                    if data_obj==['deleteAll']:
                        #1-drop document for single parent element #2- pop out screen id from parent for multiple parent element
                        n68session.dataobjects.update_many({"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session.dataobjects.delete_many({"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    else:
                        for i in range(len(data_obj)):
                            if "_id" in data_obj[0]:
                                data_push.append(ObjectId(data_obj[i]["_id"]))
                        n68session.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    n68session.screens.update({"_id":screenID},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    res = {"rows":"Success"}
                elif data["type"] == "update_obj":
                    data_obj=json.loads(data["scrapedata"])
                    screenID = ObjectId(data["screenid"])
                    #screenshot = data["scrapedata"]["mirror"]
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    data_push=[]
                    try:
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i][0])
                            cust_name=data_obj[i][1]
                            n68session.dataobjects.update({"_id": data_id},{"$set":{"custname":cust_name}})
                        n68session.screens.update({"_id":screenID},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                        res = {"rows":"Success"}
                    except:
                        res = {"rows":"fail"}
                elif data["type"] == "insert_obj":
                    screenID = ObjectId(data["screenid"])
                    screenshot = data["scrapedata"]["mirror"]
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    if "propedit" in requestdata:
                        data_obj=requestdata["propedit"]
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i]["_id"])
                            del data_obj[i]["_id"]
                            n68session.dataobjects.update({"_id": data_id},{"$set":data_obj[i]})
                        #res = {"rows":"Success"}
                    if "modobj" in data["scrapedata"]:
                        data_obj=data["scrapedata"]["modobj"]
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i][0])
                            cust_name=data_obj[i][1]
                            n68session.dataobjects.update({"_id": data_id},{"$set":{"custname":cust_name}})
                        #res = {"rows":"Success"}
                    data_obj=data["scrapedata"]["view"]
                    data_push=[]
                    for i in range(len(data_obj)):
                        data_obj[i]["parent"] = [ObjectId(data["screenid"])]
                        data_push.append(data_obj[i])
                    if (data_push != []):
                        n68session.dataobjects.insert(data_push)
                    if "scrapedurl" in data["scrapedata"]:
                        scrapedurl = data["scrapedata"]["scrapedurl"]
                        n68session.screens.update({"_id":screenID},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    else:
                        n68session.screens.update({"_id":screenID},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    res = {"rows":"Success"}
                elif data["type"] == "map_obj":
                    del_obj = data["scrapedata"][0]
                    update_obj= data["scrapedata"][1]
                    screenID = ObjectId(data["screenid"])
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    data_push=[]
                    for i in range(len(update_obj)):
                        new_id=ObjectId(update_obj[i][0])
                        old_id=ObjectId(update_obj[i][1])
                        new_custname=update_obj[i][2]
                        old_obj = n68session.dataobjects.find_one({"_id": old_id})
                        old_obj['_id'] = new_id
                        old_obj['custname'] = new_custname
                        n68session.dataobjects.save(old_obj)
                    if len(del_obj)>0:
                        for i in range(len(del_obj)):
                            data_push.append(ObjectId(del_obj[i]))
                        n68session.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    n68session.screens.update({"_id":screenID},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    res = {"rows":"Success"}
                elif data["type"] == "compare_obj":
                    data_obj=json.loads(data["scrapedata"])
                    screenID = ObjectId(data["screenid"])
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    for i in range(len(data_obj["view"])):
                        ObjId=data_obj["view"][i]["_id"]
                        del data_obj["view"][i]["_id"]
                        n68session.dataobjects.update({"_id" : ObjectId(ObjId)},{"$set":data_obj["view"][i]})
                    n68session.screens.update({"_id":screenID},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                    res = {"rows":"Success"}
                elif data["type"] == "WS_obj":
                    screenID = ObjectId(data["screenid"])
                    scrapeinfo = json.loads(data["scrapedata"])
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedby"]
                    data_obj=scrapeinfo.pop("view")
                    data_push=[]
                    n68session.screens.update({"_id":screenID},{"$set":{"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                    Old_obj = list(n68session.dataobjects.find({"parent":screenID}))
                    if len(Old_obj)==0:
                        for d in data_obj:
                            d["parent"]=[screenID]
                            data_push.append(d)
                        n68session.dataobjects.insert(data_push)
                    else:
                        remove_data=[]
                        for d in data_obj:
                            already_exists=False
                            old_obj=''
                            d["parent"] = [screenID]
                            for o in Old_obj:
                                if d["xpath"]==o["xpath"]:
                                    d["_id"]=o["_id"]
                                    n68session.dataobjects.update({"_id":d["_id"]},{"$set":d})
                                    already_exists=True
                                    old_obj=o
                                    Old_obj.remove(o)
                                    break
                            if not(already_exists):
                                n68session.dataobjects.insert(d)
                                remove_data.append(o["_id"])
                        if remove_data != []:
                            n68session.dataobjects.delete_many({"_id":{"$in":remove_data}})
                    res={"rows":"Success"}
            else:
                app.logger.warn('Empty data received. updating screen')
        except Exception as updatescreenexc:
            app.logger.debug(traceback.format_exc())
            servicesException("updateScreen_ICE",updatescreenexc)
        return jsonify(res)

    @app.route('/design/updateIrisObjectType',methods=['POST'])
    def updateIrisObjectType():
        res={'rows':'fail'}
        try:
            requestdata = json.loads(request.data)
            app.logger.debug("Inside updateIrisObjectType")
            if("_id" not in requestdata or requestdata["_id"] == ""):
                res={'rows':'unsavedObject'}
            if not isemptyrequest(requestdata):
                    n68session.dataobjects.update({"_id": ObjectId(requestdata["_id"])},{"$set":{"objectType":requestdata["type"]}})
                    res={'rows':'success'}
        except Exception as updateirisobjexc:
            app.logger.debug(traceback.format_exc())
            servicesException("updateIrisObjectType",updateirisobjexc)
        return jsonify(res)