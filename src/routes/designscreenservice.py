################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *

def LoadServices(app, redissession, n68session2):
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
                if (requestdata['query'] == 'getscrapedata'):
                    if ('testcaseid' in requestdata and requestdata['testcaseid']):
                        screen_id = n68session2.testcases.find_one({'_id':ObjectId(requestdata['testcaseid'])},{'screenid':1})['screenid'] ##add versionnumber in condition if needed
                    else :
                        screen_id = ObjectId(requestdata['screenid'])
                    screen_query=list(n68session2.screens.find({"_id":screen_id,"deleted":False}))
                    if (screen_query != []):
                        dataobj_query = list(n68session2.dataobjects.find({"parent" :{"$in":[screen_id]}}))
                        res["rows"] = {"view":dataobj_query,"scrapedurl":(screen_query[0]["scrapedurl"] if ("scrapedurl" in screen_query[0]) else ""),"mirror":(screen_query[0]["screenshot"] if ("screenshot" in screen_query[0]) else ""),"name":screen_query[0]["name"]}
                if (requestdata['query']=="getWSscrapedata"):
                        dataobj_query = list(n68session2.dataobjects.find({"parent" :{"$in":[screen_id]}}))
                        res = {"rows":dataobj_query}
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as getscrapedataexc:
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
                    screenID = ObjectId(data["screenid"])
                    if data_obj==['deleteAll']:
                        #1-drop document for single parent element #2- pop out screen id from parent for multiple parent element
                        n68session2.dataobjects.update_many({"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session2.dataobjects.delete_many({"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    else:
                        for i in range(len(data_obj)):
                            if "_id" in data_obj[0]:
                                data_push.append(ObjectId(data_obj[i]["_id"]))
                        n68session2.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session2.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    res = {"rows":"Success"}
                elif data["type"] == "update_obj":
                    data_obj=json.loads(data["scrapedata"])
                    data_push=[]
                    try:
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i][0])
                            cust_name=data_obj[i][1]
                            n68session2.dataobjects.update({"_id": data_id},{"$set":{"custname":cust_name}})
                        res = {"rows":"Success"}
                    except:
                        res = {"rows":"fail"}
                elif data["type"] == "insert_obj":
                    screenID = ObjectId(data["screenid"])
                    screenshot = data["scrapedata"]["mirror"]
                    modifiedbyrole= data["modifiedByrole"]
                    modifiedby = data["modifiedbyID"]
                    if "propedit" in requestdata:
                        data_obj=requestdata["propedit"]
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i]["_id"])
                            del data_obj[i]["_id"]
                            n68session2.dataobjects.update({"_id": data_id},{"$set":data_obj[i]})
                        res = {"rows":"Success"}
                    if "modobj" in data["scrapedata"]:
                        data_obj=data["scrapedata"]["modobj"]
                        for i in range(len(data_obj)):
                            data_id=ObjectId(data_obj[i][0])
                            cust_name=data_obj[i][1]
                            n68session2.dataobjects.update({"_id": data_id},{"$set":{"custname":cust_name}})
                        res = {"rows":"Success"}
                    data_obj=data["scrapedata"]["view"]
                    data_push=[]
                    for i in range(len(data_obj)):
                        data_obj[i]["parent"] = [ObjectId(data["screenid"])]
                        data_push.append(data_obj[i])
                    if (data_push != []):
                        n68session2.dataobjects.insert(data_push)
                    if "scrapedurl" in data["scrapedata"]:
                        scrapedurl = data["scrapedata"]["scrapedurl"]
                        n68session2.screens.update({"_id":screenID},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby},"$currentDate": {"modifiedon": True}})
                    else:
                        n68session2.screens.update({"_id":screenID},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby},"$currentDate": {"modifiedon": True}})
                    res = {"rows":"Success"}
                elif data["type"] == "map_obj":
                    del_obj = data["scrapedata"][0]
                    update_obj= data["scrapedata"][1]
                    screenID = ObjectId(data["screenid"])
                    data_push=[]
                    if len(del_obj)>0:
                        for i in range(len(del_obj)):
                            data_push.append(ObjectId(del_obj[i]))
                        n68session2.dataobjects.update_many({"_id":{"$in":data_push},"$and":[{"parent.1":{"$exists":True}},{"parent":screenID}]},{"$pull":{"parent":screenID}})
                        n68session2.dataobjects.delete_many({"_id":{"$in":data_push},"$and":[{"parent":{"$size": 1}},{"parent":screenID}]})
                    for i in range(len(update_obj)):
                            data_id=ObjectId(update_obj[i][0])
                            cust_name=update_obj[i][1]
                            n68session2.dataobjects.update({"_id": data_id},{"$set":{"custname":cust_name}})
                    res = {"rows":"Success"}
                elif data["type"] == "compare_obj":
                    data_obj=json.loads(data["scrapedata"])
                    data_push=[]
                    for i in range(len(data_obj["view"])):
                        ObjId=data_obj["view"][i]["_id"]
                        del data_obj["view"][i]["_id"]
                        n68session2.dataobjects.update({"_id" : ObjectId(ObjId)},{"$set":data_obj["view"][i]})
                    res = {"rows":"Success"}
                elif data["type"] == "WS_obj":
                    screenID = ObjectId(data["screenid"])
                    data_push = json.loads(data["scrapedata"])
                    data_push["parent"] = [screenID]
                    scrapedurl = ""
                    modifiedon=""
                    modifiedbyrole=""
                    modifiedby=""
                    screenshot=""
                    Old_obj = list(n68session2.dataobjects.find({"parent":data_push["parent"]}))
                    if (len(Old_obj) == 0):
                        n68session2.dataobjects.insert(data_push)
                    else:
                        data_push["_id"] = Old_obj[0]["_id"]
                        n68session2.dataobjects.save(data_push)
                    res={"rows":"Success"}

            else:
                app.logger.warn('Empty data received. updating screen')
        except Exception as updatescreenexc:
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
                    n68session2.dataobjects.update({"_id": ObjectId(requestdata["_id"])},{"$set":{"objectType":requestdata["type"]}})
                    res={'rows':'success'}
        except Exception as updateirisobjexc:
            servicesException("updateIrisObjectType",updateirisobjexc)
        return jsonify(res)