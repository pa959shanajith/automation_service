################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import codecs
from pymongo import InsertOne
from datetime import datetime
def LoadServices(app, redissession, client ,getClientName):
    setenv(app)
    defcn = ['@Window', '@Object', '@System', '@Excel', '@Mobile', '@Android_Custom', '@Word', '@Custom', '@CustomiOS',
                                '@Generic', '@Browser', '@Action', '@Email', '@BrowserPopUp', '@Sap','@Oebs', 'WebService List', 'Mainframe List', 'OBJECT_DELETED']

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

    #keywords loader for design screen
    @app.route('/design/getKeywordDetails_ICE',methods=['POST'])
    def getKeywordDetails():
        app.logger.debug('Inside getKeywordDetails')
        res={'rows':'fail'}
        try:
            clientName=getClientName({})       
            dbsession=client[clientName]
            projecttypename = str(request.data,'utf-8')
            if not (projecttypename == '' or projecttypename == 'undefined'
                    or projecttypename == 'null' or projecttypename == None):
                keywordquery = list(dbsession.projecttypekeywords.find({'name':{'$in':[projecttypename,'Generic']}},{'keywordsmap':1,'_id':0}))
                res = {'rows':keywordquery[0]['keywordsmap']+keywordquery[1]['keywordsmap']}
            else:
                app.logger.warn('Empty data received. getKeywordDetails')
        except Exception as keywordsexc:
            servicesException('getKeywordDetails', keywordsexc, True)
        return jsonify(res)


    #get dependant testcases by scenario ids for add dependent testcases
    @app.route('/design/getTestcasesByScenarioId_ICE',methods=['POST'])
    def getTestcasesByScenarioId_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside getTestcasesByScenarioId_ICE. Query: '
                +str(requestdata['query']))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                if(requestdata['query'] == 'gettestcasedetails'):
                    ids = list(dbsession.testscenarios.find({'_id':ObjectId(requestdata['testscenarioid'])},{'testcaseids':1,'_id':0}))
                    if (ids != []):
                        tc_ids = ids[0]['testcaseids']
                        query = [
                            {"$match":{"_id":{"$in":tc_ids}}},
                            {"$addFields":{"__order":{"$indexOfArray":[tc_ids,"$_id"]}}},
                            {"$sort":{"__order":1}},
                            {"$project":{"name":1}}
                        ]
                        queryresult = list(dbsession.testcases.aggregate(query))
                        result=[]
                        for i in tc_ids:
                            for j in queryresult:
                                if i == j["_id"]:
                                    result.append(j["name"])
                        res= {'rows':{'testcaseids':tc_ids,'testcasenames':result}}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. getting testcases.')
        except Exception as e:
            servicesException('getTestcasesByScenarioId_ICE', e, True)
        return jsonify(res)


    def getScrapeData(hex_data):
        try:
            key = "".join(['N','i','n','e','e','t','e','e','n','6','8','@','S','e',
                'c','u','r','e','S','c','r','a','p','e','D','a','t','a','P','a','t','h'])
            data = codecs.decode(hex_data, 'hex')
            aes = AES.new(key.encode("utf-8"), AES.MODE_CBC, b'0'*16)
            data = aes.decrypt(data).decode('utf-8')
            return data[0:-ord(data[-1])]
        except:
            return hex_data

    def adddataobjects(dbsession,pid, d):
        if len(d) == 0: return False
        req = []
        for row in d:
            if type(row) == str and len(row) == 0: continue
            if "custname" not in row: row["custname"] = "object"+str(row["_id"])
            row["parent"] = [pid]
            req.append(InsertOne(row))
        dbsession.dataobjects.bulk_write(req)

    def createdataobjects(dbsession,scrid, objs):
        custnameToAdd = []
        for e in objs:
            so = objs[e]
            obn = so["objectName"] if "objectName" in so else ""
            dodata = {
                "_id": e,
                "custname": so["custname"],
                "xpath": obn
            }
            if obn.strip() == '' :
                custnameToAdd.append(dodata)
                continue
            elif obn.startswith("iris;"):
                ob = obn.split(';')[2:]
                legend = ['left', 'top', 'width', 'height', 'tag']
                for i in range(len(legend)):
                    if i < 4: dodata[legend[i]] = int(ob[i])
                    else: dodata[legend[i]] = ob[-1]
                dodata["height"] = dodata["top"] - dodata["height"]
                dodata["width"] = dodata["left"] - dodata["width"]
                dodata["url"] = so["url"] if "url" in so else ""
                dodata["cord"] = so["cord"] if "cord" in so else ""
                dodata["identifier"] = so["identifier"] if "identifier" in so else [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
            elif so["appType"] in ["Web", "MobileWeb"]:
                ob=[]
                legend = ['id', 'name', 'tag', 'class', 'left', 'top', 'height', 'width', 'text']
                for i in obn.split(';'): ob.append(getScrapeData(i))
                ob = ";".join(ob).split(';')
                ob = ob[1:2] + ob[3:]
                if len(ob) < 4:
                    custnameToAdd.append(dodata)
                    continue
                elif len(ob) == 4: legend = legend[:4]
                elif len(ob) == 8: del legend[3]
                elif len(ob) == 11: dodata["tag"] = ob[-1]
                try:
                    for i in range(len(legend)):
                        if (i>=4 and i<=7):
                            if ob[i].isnumeric(): dodata[legend[i]] = int(ob[i])
                        else:
                            if (ob[i] != "null") and (legend[i] not in dodata): dodata[legend[i]] = ob[i]
                except: pass
                if "tag" in dodata: dodata["tag"] = dodata["tag"].split("[")[0]
                if "class" in dodata: dodata["class"] = dodata["class"].split("[")[0]
                dodata["url"] = so["url"] if 'url' in so else ""
                dodata["cord"] = so["cord"] if "cord" in so else ""
                dodata["identifier"] = so["identifier"] if "identifier" in so else [{"id":1,"identifier":'xpath'},{"id":2,"identifier":'id' },{"id":3, "identifier":'rxpath' },{ "id":4,"identifier":'name' },{"id":5,"identifier":'classname'},{"id":6,"identifier":'cssselector'},{"id":7,"identifier":'href'},{"id":8,"identifier":'label'}]
            elif so["appType"] == "MobileApp":
                ob = obn.split(';')
                if len(ob) >= 2 and ob[0].strip() != "": dodata["id"] = ob[0]
                if len(ob) >2 and ob[2].strip() !="": dodata["tag"] = ob[2]
            elif so["appType"] == "Desktop":
                gettag = {"btn":"button","txtbox":"input","radiobtn":"radiobutton","select":"select","chkbox":"checkbox","lst":"list","tab":"tab","tree":"tree","dtp":"datepicker","table":"table","elmnt":"label"}
                tag = so["custname"].split("_")[-1]
                if tag in gettag: dodata["tag"] = gettag[tag]
                dodata["control_id"] = obn.split(';')[2] if len(obn.split(';'))>1 else ""
                dodata["url"] = so["url"] if 'url' in so else ""
            elif so["appType"] == "OEBS":
                gettag = {"btn":"push button","txtbox":"text","radiobtn":"radio button","select":"combo box","chkbox":"check box","lst":"list","tab":"tab","tree":"tree","table":"table","elmnt":"element","internalframe":"internal frame","frame":"frame","scroll":"scroll bar","link":'hyperlink'}
                tag = so["custname"].split("_")[-1]
                if tag in gettag: dodata["tag"] = gettag[tag]
                dodata["control_id"] = obn.split(';')[2] if len(obn.split(';'))>1 else ""
                dodata["url"] = so["url"] if 'url' in so else ""
            elif so["appType"] == "pdf":
                dodata["tag"] = "_".join(so["custname"].split("_")[0:2])
            elif so["appType"] == ["Generic", "SAP", "Webservice", "Mainframe", "System"]: pass
            custnameToAdd.append(dodata)
        adddataobjects(dbsession,scrid, custnameToAdd)


    #test case updating service
    @app.route('/design/updateTestCase_ICE',methods=['POST'])
    def updateTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside updateTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]
                tcid = requestdata['testcaseid']
                query_screen = dbsession.testcases.find_one({'_id':ObjectId(tcid),'versionnumber':requestdata['versionnumber']},{'screenid':1,'datatables':1})
                dtables = requestdata.get('datatables', '')
                if len(dtables) > 0:
                    #update removed datatable tcs by removing current tcid
                    dbsession.datatables.update_many({"name": {'$nin': dtables}, "testcaseIds": tcid}, 
                        {"$pull": {"testcaseIds": tcid}})
                    #update each datatable tcs list by adding tcid
                    dbsession.datatables.update_many({"name": {'$in': dtables}, "testcaseIds": {"$ne": tcid}}, 
                        {"$push": {"testcaseIds": tcid}})
                elif 'datatables' in query_screen and len(query_screen['datatables']) > 0:
                    dbsession.datatables.update_many({"name": {'$in': query_screen['datatables']}, "testcaseIds": tcid}, {"$pull": {"testcaseIds": tcid}})
                queryresult1 = list(dbsession.dataobjects.find({'parent':query_screen['screenid']}))
                screenQuery = list(dbsession.screens.find({'_id':query_screen['screenid']}))
                custnames = {}
                updated_objects = {}
                orderlist = []
                updateOrder = False
                if (queryresult1 != []):
                    custnames = {i['custname'].strip():i for i in queryresult1}
                if (screenQuery != []):
                    orderlist = screenQuery[0]['orderlist'] if 'orderlist' in screenQuery[0] else []
                steps = []
                if not (requestdata['import_status']):
                    if len(requestdata['copiedTestCases'])>0:
                        copiedObjects = [ObjectId(i) for i in set(requestdata['copiedTestCases'])]
                        copiedObjectList = list(dbsession.dataobjects.find({'_id':{'$in':copiedObjects}}))
                        mapNew =[]
                        addNew = []
                        for co in copiedObjectList:
                            if co['custname'] in custnames:
                                if co['_id'] != custnames[co['custname']]['_id']:
                                    cname = co['custname']
                                    try:
                                        s_cname = cname.split('_')
                                        ind = int(s_cname.pop())
                                        n_cname = '_'.join(s_cname)
                                    except:
                                        ind = 0
                                        n_cname = cname
                                    while True:
                                        ind += 1
                                        if n_cname+'_'+str(ind) not in custnames:
                                            co["custname"] = n_cname+'_'+str(ind)
                                            break
                                    cid = co['_id']
                                    del co['parent']
                                    co['_id'] = ObjectId()
                                    orderlist.append(str(co['_id']))
                                    updateOrder = True
                                    addNew.append(co)
                                    custnames[co['custname']] = co
                                    updated_objects[cid] = co['_id']
                            else:
                                if query_screen['screenid'] not in co['parent']:
                                    co['parent'].append(query_screen['screenid'])
                                    if (str(co['_id']) not in orderlist):
                                        orderlist.append(str(co['_id']))
                                        updateOrder = True
                                    updateOrder = True
                                    mapNew.append(co)
                        for mn in mapNew:
                            custnames[mn['custname']] = mn
                            dbsession.dataobjects.save(mn)
                        adddataobjects(dbsession,query_screen['screenid'],addNew)
                    for so in requestdata['testcasesteps']:
                        cid = cname = so["custname"].strip()
                        if cname in custnames: cid = custnames[cname]["_id"]
                        if ("objectid" in so) and (ObjectId(so["objectid"]) in updated_objects):
                            cid = updated_objects[ObjectId(so["objectid"])]
                        steps.append({
                            "stepNo": so["stepNo"],
                            "custname": cid,
                            "keywordVal": so["keywordVal"],
                            "inputVal": so["inputVal"],
                            "outputVal": so["outputVal"],
                            "appType": so["appType"],
                            "remarks": so["remarks"] if ("remarks" in so) else "",
                            "addDetails": so["addTestCaseDetailsInfo"] if ("addTestCaseDetailsInfo" in so) else "",
                            "cord": so["cord"] if ("cord" in so) else ""
                        })
                    del requestdata['testcasesteps']
                else:
                    #Import testcase
                    missingCustname = {}
                    for so in requestdata['testcasesteps']:
                        cid = cname = so["custname"].strip()
                        if cname in custnames:
                            if ('objectName' in so) and ('xpath' in custnames[cname]) and (so["objectName"] == custnames[cname]['xpath']):
                                cid = custnames[cname]["_id"]
                            else:
                                cid = ObjectId()
                                orderlist.append(str(cid))
                                updateOrder = True
                                try:
                                    s_cname = cname.split('_')
                                    ind = int(s_cname.pop())
                                    n_cname = '_'.join(s_cname)
                                except:
                                    ind = 0
                                    n_cname = cname
                                while True:
                                    if n_cname+'_'+str(ind+1) not in custnames:
                                        so["custname"] = n_cname+'_'+str(ind+1)
                                        break
                                    elif ('objectName' in so) and ('xpath' in custnames[n_cname+'_'+str(ind+1)]) and (so["objectName"] == custnames[n_cname+'_'+str(ind+1)]['xpath']):
                                        cid = custnames[n_cname+'_'+str(ind+1)]["_id"]
                                        break
                                    ind += 1
                                if so["custname"] not in custnames:
                                    custnames[so["custname"]] = {"_id":cid,"xpath":so["objectName"],"url":so['url'] if 'url' in so else ""}
                                    missingCustname[cid] = so
                        elif (cname not in custnames) and (cname not in defcn):
                            cid = ObjectId()
                            orderlist.append(str(cid))
                            updateOrder = True
                            custnames[cname] = {"_id":cid,"xpath":so["objectName"],"url":so['url'] if 'url' in so else ""}
                            missingCustname[cid] = so
                        steps.append({
                            "stepNo": so["stepNo"],
                            "custname": cid,
                            "keywordVal": so["keywordVal"],
                            "inputVal": so["inputVal"],
                            "outputVal": so["outputVal"],
                            "appType": so["appType"],
                            "remarks": so["remarks"] if ("remarks" in so) else "",
                            "addDetails": so["addTestCaseDetailsInfo"] if ("addTestCaseDetailsInfo" in so) else "",
                            "cord": so["cord"] if ("cord" in so) else ""
                        })
                    del requestdata['testcasesteps']
                    createdataobjects(dbsession,query_screen['screenid'], missingCustname)

                #query to update tescase
                if(requestdata['query'] == 'updatetestcasedata'):
                    queryresult = dbsession.testcases.update_many({'_id':ObjectId(tcid),'versionnumber':requestdata['versionnumber']},
                                {'$set':{'modifiedby':ObjectId(requestdata['modifiedby']),'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),'steps':steps,'datatables':dtables,"modifiedon" : datetime.now()}}).matched_count
                    if updateOrder:
                        screenQueryResult = dbsession.screens.update({"_id":query_screen['screenid']},{"$set":{"modifiedby":ObjectId(requestdata['modifiedby']), 'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                        if queryresult > 0 and screenQueryResult:
                            res= {'rows': 'success'}
                    elif queryresult > 0:
                        res= {'rows': 'success'}
            else:
                app.logger.warn('Empty data received. updating testcases')
        except Exception as updatetestcaseexception:
            servicesException('updateTestCase_ICE', updatetestcaseexception, True)
        return jsonify(res)




    def getScreenID(dbsession,screenname,projectid):
        screenname=list(dbsession.screens.find({"projectid":ObjectId(projectid),"name":screenname,"deleted":False},{"_id":1}))
        if len(screenname)==1:
            return str(screenname[0]["_id"])
        else:   
            return None

    def getTestcaseID(dbsession,screenid,testcasename):
        testcaseid = list(dbsession.testcases.find({"screenid": screenid,"name": testcasename,"deleted": False}, {"_id": 1}))
        if len(testcaseid) != 0:
            res = str(testcaseid[0]["_id"])
        else:
            res = None
        return res



    #test case updating service Genius
    @app.route('/design/updateTestCase_Genius',methods=['POST'])
    def updateTestCase_Genius():
        res={'rows':'fail'}
        try:
            data = json.loads(request.data)
            # app.logger.debug(request.data)
            # app.logger.debug('Inside updateTestCase_Genius. Query: '+str(requestdata['query']))
            testcasedetails = data['testcasesteps']
            if not isemptyrequest(data):
                clientName=getClientName(data)         
                dbsession=client[clientName]
                for requestdata in testcasedetails:
                    
                    # tcid = requestdata['testcaseid']
                    projectid = requestdata['projectid']
                    screenname = requestdata['screenname']
                    testcasename = requestdata['testcasename']
                    screenId = ObjectId(getScreenID(dbsession,screenname,projectid))
                    tcid = getTestcaseID(dbsession,screenId,testcasename)
                    

                    query_screen = dbsession.testcases.find_one({'_id':ObjectId(tcid),'versionnumber':requestdata['versionnumber']},{'screenid':1,'datatables':1})
                    dtables = requestdata.get('datatables', '')
                    if len(dtables) > 0:
                        #update removed datatable tcs by removing current tcid
                        dbsession.datatables.update_many({"name": {'$nin': dtables}, "testcaseIds": tcid}, 
                            {"$pull": {"testcaseIds": tcid}})
                        #update each datatable tcs list by adding tcid
                        dbsession.datatables.update_many({"name": {'$in': dtables}, "testcaseIds": {"$ne": tcid}}, 
                            {"$push": {"testcaseIds": tcid}})
                    elif 'datatables' in query_screen and len(query_screen['datatables']) > 0:
                        dbsession.datatables.update_many({"name": {'$in': query_screen['datatables']}, "testcaseIds": tcid}, {"$pull": {"testcaseIds": tcid}})
                    queryresult1 = list(dbsession.dataobjects.find({'parent':query_screen['screenid']}))
                    screenQuery = list(dbsession.screens.find({'_id':query_screen['screenid']}))
                    custnames = {}
                    updated_objects = {}
                    orderlist = []
                    updateOrder = False
                    if (queryresult1 != []):
                        custnames = {i['custname'].strip():i for i in queryresult1 if "custname" in i}
                    if (screenQuery != []):
                        orderlist = screenQuery[0]['orderlist'] if 'orderlist' in screenQuery[0] else []
                    steps = []
                    if not (requestdata['import_status']):
                        if len(requestdata['copiedTestCases'])>0:
                            copiedObjects = [ObjectId(i) for i in set(requestdata['copiedTestCases'])]
                            copiedObjectList = list(dbsession.dataobjects.find({'_id':{'$in':copiedObjects}}))
                            mapNew =[]
                            addNew = []
                            for co in copiedObjectList:
                                if co['custname'] in custnames:
                                    if co['_id'] != custnames[co['custname']]['_id']:
                                        cname = co['custname']
                                        try:
                                            s_cname = cname.split('_')
                                            ind = int(s_cname.pop())
                                            n_cname = '_'.join(s_cname)
                                        except:
                                            ind = 0
                                            n_cname = cname
                                        while True:
                                            ind += 1
                                            if n_cname+'_'+str(ind) not in custnames:
                                                co["custname"] = n_cname+'_'+str(ind)
                                                break
                                        cid = co['_id']
                                        del co['parent']
                                        co['_id'] = ObjectId()
                                        orderlist.append(str(co['_id']))
                                        updateOrder = True
                                        addNew.append(co)
                                        custnames[co['custname']] = co
                                        updated_objects[cid] = co['_id']
                                else:
                                    if query_screen['screenid'] not in co['parent']:
                                        co['parent'].append(query_screen['screenid'])
                                        if (str(co['_id']) not in orderlist):
                                            orderlist.append(str(co['_id']))
                                            updateOrder = True
                                        updateOrder = True
                                        mapNew.append(co)
                            for mn in mapNew:
                                custnames[mn['custname']] = mn
                                dbsession.dataobjects.save(mn)
                            adddataobjects(dbsession,query_screen['screenid'],addNew)
                        for so in requestdata['testcasesteps']:
                            cid = cname = so["custname"].strip()
                            if cname in custnames: cid = custnames[cname]["_id"]
                            if ("objectid" in so) and (ObjectId(so["objectid"]) in updated_objects):
                                cid = updated_objects[ObjectId(so["objectid"])]
                            steps.append({
                                "stepNo": so["stepNo"],
                                "custname": cid,
                                "keywordVal": so["keywordVal"],
                                "inputVal": so["inputVal"],
                                "outputVal": so["outputVal"],
                                "appType": so["appType"],
                                "remarks": so["remarks"] if ("remarks" in so) else "",
                                "addDetails": so["addTestCaseDetailsInfo"] if ("addTestCaseDetailsInfo" in so) else "",
                                "cord": so["cord"] if ("cord" in so) else ""
                            })
                        del requestdata['testcasesteps']
                    else:
                        #Import testcase
                        missingCustname = {}
                        for so in requestdata['testcasesteps']:
                            cid = cname = so["custname"].strip()
                            if cname in custnames:
                                if ('objectName' in so) and ('xpath' in custnames[cname]) and (so["objectName"] == custnames[cname]['xpath']):
                                    cid = custnames[cname]["_id"]
                                else:
                                    cid = ObjectId()
                                    orderlist.append(str(cid))
                                    updateOrder = True
                                    try:
                                        s_cname = cname.split('_')
                                        ind = int(s_cname.pop())
                                        n_cname = '_'.join(s_cname)
                                    except:
                                        ind = 0
                                        n_cname = cname
                                    while True:
                                        if n_cname+'_'+str(ind+1) not in custnames:
                                            so["custname"] = n_cname+'_'+str(ind+1)
                                            break
                                        elif ('objectName' in so) and ('xpath' in custnames[n_cname+'_'+str(ind+1)]) and (so["objectName"] == custnames[n_cname+'_'+str(ind+1)]['xpath']):
                                            cid = custnames[n_cname+'_'+str(ind+1)]["_id"]
                                            break
                                        ind += 1
                                    if so["custname"] not in custnames:
                                        custnames[so["custname"]] = {"_id":cid,"xpath":so["objectName"],"url":so['url'] if 'url' in so else ""}
                                        missingCustname[cid] = so
                            elif (cname not in custnames) and (cname not in defcn):
                                cid = ObjectId()
                                orderlist.append(str(cid))
                                updateOrder = True
                                custnames[cname] = {"_id":cid,"xpath":so["objectName"],"url":so['url'] if 'url' in so else ""}
                                missingCustname[cid] = so
                            steps.append({
                                "stepNo": so["stepNo"],
                                "custname": cid,
                                "keywordVal": so["keywordVal"],
                                "inputVal": so["inputVal"],
                                "outputVal": so["outputVal"],
                                "appType": so["appType"],
                                "remarks": so["remarks"] if ("remarks" in so) else "",
                                "addDetails": so["addTestCaseDetailsInfo"] if ("addTestCaseDetailsInfo" in so) else "",
                                "cord": so["cord"] if ("cord" in so) else ""
                            })
                        del requestdata['testcasesteps']
                        createdataobjects(dbsession,query_screen['screenid'], missingCustname)

                    #query to update tescase
                    if(requestdata['query'] == 'updatetestcasedata'):
                        queryresult = dbsession.testcases.update_many({'_id':ObjectId(tcid),'versionnumber':requestdata['versionnumber']},
                                    {'$set':{'modifiedby':ObjectId(requestdata['modifiedby']),'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),'steps':steps,'datatables':dtables,"modifiedon" : datetime.now()}}).matched_count
                        if updateOrder:
                            screenQueryResult = dbsession.screens.update({"_id":query_screen['screenid']},{"$set":{"modifiedby":ObjectId(requestdata['modifiedby']), 'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),"modifiedon" : datetime.now(), 'orderlist': orderlist}})
                            if queryresult > 0 and screenQueryResult:
                                res= {'rows': 'success'}
                        elif queryresult > 0:
                            res= {'rows': 'success'}
            else:
                app.logger.warn('Empty data received. updating testcases')
        except Exception as updatetestcaseexception:
            servicesException('updateTestCase_Genius', updatetestcaseexception, True)
        return jsonify(res)



    def update_steps(steps,dataObjects):
        del_flag = False
        try:
            for j in steps:
                j['objectName'], j['url'], j['addTestCaseDetailsInfo'], j['addTestCaseDetails'], j['identifier']= '', '', '', '', ''
                if 'addDetails' in j:
                    j['addTestCaseDetailsInfo'] = j['addDetails']
                    del j['addDetails']
                if j['custname'] == "@Custom":
                    j['objectName'] = "@Custom"
                    continue
                if 'custname' in j.keys():
                    if j['custname'] in dataObjects.keys():
                        j['objectName'] = dataObjects[j['custname']]['xpath']
                        if j['appType'] in ['Web','MobileWeb']:
                            j['identifier']=dataObjects[j['custname']]['identifier']
                        j['url'] = dataObjects[j['custname']]['url'] if 'url' in dataObjects[j['custname']] else ""
                        j['cord'] = dataObjects[j['custname']]['cord'] if 'cord' in dataObjects[j['custname']] else ""
                        if 'original_device_width' in dataObjects[j['custname']].keys():
                            j['original_device_width'] = dataObjects[j['custname']]['original_device_width']
                            j['original_device_height'] = dataObjects[j['custname']]['original_device_height']
                        j['objectid'] = j['custname']
                        j['custname'] = dataObjects[j['custname']]['custname']
                    elif (j['custname'] not in defcn or j['custname']=='OBJECT_DELETED'):
                        j['custname'] = 'OBJECT_DELETED'
                        if j['outputVal'].split(';')[-1] != '##':
                            del_flag = True
        except Exception as e:
            servicesException('readTestCase_ICE', e, True)
        return del_flag


    #test case reading service
    @app.route('/design/readTestCase_ICE',methods=['POST'])
    def readTestCase_ICE():
        res={'rows':'fail'}
        del_flag = False
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside readTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                if(requestdata['query'] == 'testcaseids'):
                    if not isinstance(requestdata['testcaseid'], list):
                        requestdata['testcaseid'] = [requestdata['testcaseid']]
                    tc_id_list = [ObjectId(i) for i in requestdata['testcaseid']]
                    query = [
                        {"$match":{"_id":{"$in":tc_id_list}}},
                        {"$addFields":{"__order":{"$indexOfArray":[tc_id_list,"$_id"]}}},
                        {"$sort":{"__order":1}},
                        {"$project":{'steps':1,'name':1,'datatables':1,'screenid':1,'parent':1,'_id':1}}
                    ]
                    result = dbsession.testcases.aggregate(query)
                    tcdict = {}
                    dts_data = {}
                    for tc in result: tcdict[tc['_id']] = tc
                    queryresult = [tcdict[i] for i in tc_id_list]
                    updated_tc_list=[]
                    for k in queryresult:
                        if k['_id'] in updated_tc_list:
                            continue
                        queryresult1 = dbsession.dataobjects.find({'parent':k['screenid']},{'parent':0})
                        dataObjects = {}
                        for dos in queryresult1:
                            if 'custname' in dos: dos['custname'] = dos['custname'].strip()
                            dataObjects[dos['_id']] = dos
                        del_flag = update_steps(k['steps'],dataObjects)
                        updated_tc_list.append(k['_id'])
                        #datatables
                        dtnames = k.get('datatables', [])
                        if len(dtnames) > 0:
                            dts = []
                            dts_to_fetch = [i for i in dtnames if i not in dts_data]
                            dtdet = dbsession.datatables.find({"name": {'$in': dts_to_fetch}})
                            for dt in dtdet: dts_data[dt['name']] = dt['datatable']
                            for dt in dtnames: 
                                if dt in dts_data.keys():
                                    dts.append({dt: dts_data[dt]})
                            k['datatables'] = dts
                    res = {'rows': { 'tc': queryresult, 'del_flag': del_flag}}
                else:
                    dataObjects = {}
                    if "testcaseid" not in requestdata:
                        queryresult = dbsession.testcases.find_one({'screenid':ObjectId(requestdata['screenid']),
                        'versionnumber':requestdata['versionnumber']}, {'screenid':1,'steps':1,'datatables':1,'name':1,'parent':1,'_id':1})
                    else:
                        queryresult = dbsession.testcases.find_one({'_id':ObjectId(requestdata['testcaseid']),
                            'versionnumber':requestdata['versionnumber']}, {'screenid':1,'steps':1,'datatables':1,'name':1,'parent':1,'_id':0})
                    if queryresult is None: res['rows'] = { 'tc': [], 'del_flag': del_flag }
                    else:
                        queryresult1 = dbsession.dataobjects.find({'parent':queryresult['screenid']},{'parent':0})
                        for dos in queryresult1:
                            if 'custname' in dos: dos['custname'] = dos['custname'].strip()
                            dataObjects[dos['_id']] = dos
                        del_flag = update_steps(queryresult['steps'],dataObjects)
                        #datatables
                        dtnames = queryresult.get('datatables', [])
                        if len(dtnames) > 0:
                            dts = []
                            dtdet = dbsession.datatables.find({"name": {'$in': dtnames}})
                            for dt in dtdet:
                                dts.append({dt['name']:dt['datatable']})
                            queryresult['datatables'] = dts
                        res = { 'rows': { 'tc': [queryresult], 'del_flag': del_flag, 'testcaseid':str(queryresult.get('_id', '')) } }
                    if requestdata.get('screenName', '') == 'fetch':
                        screen = dbsession.screens.find_one({'_id':queryresult['screenid']},{'name':1})
                        res['rows']['screenName'] = screen['name']
                    if 'readonly' not in requestdata and 'userid' in requestdata:
                        counterupdator(dbsession,'testcases',ObjectId(requestdata['userid']),1)
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as readtestcaseexc:
            servicesException('readTestCase_ICE', readtestcaseexc, True)
        return jsonify(res)
