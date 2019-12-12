################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import codecs
from pymongo import InsertOne

def LoadServices(app, redissession, n68session2):
    setenv(app)
    defcn = ['@Window', '@Object', '@System', '@Excel', '@Mobile', '@Android_Custom', '@Word', '@Custom', '@CustomiOS',
                                '@Generic', '@Browser', '@Action', '@Email', '@BrowserPopUp', '@Sap', 'WebService List', 'Mainframe List']

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

    #keywords loader for design screen
    @app.route('/design/getKeywordDetails_ICE',methods=['POST'])
    def getKeywordDetails():
        app.logger.debug('Inside getKeywordDetails')
        res={'rows':'fail'}
        try:
            projecttypename = str(request.data,'utf-8')
            if not (projecttypename == '' or projecttypename == 'undefined'
                    or projecttypename == 'null' or projecttypename == None):
                keywordquery = list(n68session2.projecttypekeywords.find({'name':{'$in':[projecttypename,'Generic']}},{'keywordsmap':1,'_id':0}))
                res = {'rows':keywordquery[0]['keywordsmap']+keywordquery[1]['keywordsmap']}
            else:
                app.logger.warn('Empty data received. getKeywordDetails')
        except Exception as keywordsexc:
            servicesException('getKeywordDetails',keywordsexc)
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
                if(requestdata['query'] == 'gettestcasedetails'):
                    ids = list(n68session2.testscenarios.find({'_id':ObjectId(requestdata['testscenarioid'])},{'testcaseids':1,'_id':0}))
                    if (ids != []):
                        tc_ids = ids[0]['testcaseids']
                        query = [
                            {"$match":{"_id":{"$in":tc_ids}}},
                            {"$addFields":{"__order":{"$indexOfArray":[tc_ids,"$_id"]}}},
                            {"$sort":{"__order":1}},
                            {"$project":{"name":1}}
                        ]
                        queryresult = list(n68session2.testcases.aggregate(query))
                        res= {'rows':queryresult}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. getting testcases.')
        except Exception as e:
            servicesException('getTestcasesByScenarioId_ICE',e)
        return jsonify(res)


    def getScrapeData(hex_data):
        try:
            data = codecs.decode(hex_data, 'hex')
            aes = AES.new(b"Nineeteen68@SecureScrapeDataPath", AES.MODE_CBC, b'0'*16)
            data = aes.decrypt(data).decode('utf-8')
            return data[0:-ord(data[-1])]
        except:
            return hex_data

    def adddataobjects(pid, d):
        if len(d) == 0: return False
        req = []
        custname = {}
        for row in d:
            row["parent"] = [pid]
            req.append(InsertOne(row))
        n68session2.dataobjects.bulk_write(req)

    def createdataobjects(scrid, objs):
        custnameToAdd = []
        for e in objs:
            so = objs[e]
            obn = so["objectName"]
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
                    else: dodata[legend[i]] = ob[i]
                dodata["height"] = dodata["top"] - dodata["height"]
                dodata["width"] = dodata["left"] - dodata["width"]
                dodata["url"] = so["url"]
                dodata["cord"] = so["cord"]
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
                try:
                    for i in range(len(legend)):
                        if (i>=4 and i<=7):
                            if ob[i].isnumeric(): dodata[legend[i]] = int(ob[i])
                        else:
                            if ob[i] != "null": dodata[legend[i]] = ob[i]
                except: pass
                if "tag" in dodata: dodata["tag"] = dodata["tag"].split("[")[0]
                if "class" in dodata: dodata["class"] = dodata["class"].split("[")[0]
                dodata["url"] = so["url"]
                dodata["cord"] = so["cord"]
            elif so["appType"] == "MobileApp":
                ob = obn.split(';')
                if len(ob) == 2 and ob[0].strip() != "": dodata["id"] = ob[0]
            elif so["appType"] == "Desktop":
                gettag = {"btn":"button","txtbox":"input","radiobtn":"radiobutton","select":"select","chkbox":"checkbox","lst":"list","tab":"tab","tree":"tree","dtp":"datepicker","table":"table","elmnt":"label"}
                tag = so["custname"].split("_")[-1]
                if tag in gettag: dodata["tag"] = gettag[tag]
                dodata["control_id"] = obn.split(';')[2]
                dodata["url"] = so["url"]
            elif so["appType"] == "pdf":
                dodata["tag"] = "_".join(so["custname"].split("_")[0:2])
            elif so["appType"] == ["Generic", "SAP", "Webservice", "Mainframe", "System"]: pass
            custnameToAdd.append(dodata)
        adddataobjects(scrid, custnameToAdd)


    #test case updating service
    @app.route('/design/updateTestCase_ICE',methods=['POST'])
    def updateTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside updateTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                query_screen = n68session2.testcases.find_one({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},{'screenid':1})
                queryresult1 = list(n68session2.dataobjects.find({'parent':query_screen['screenid']}))
                custnames = {}
                if (queryresult1 != []):
                    custnames = {i['custname']:i for i in queryresult1}
                steps = []
                if not (requestdata['import_status']):
                    for so in requestdata['testcasesteps']:
                        cid = cname = so["custname"]
                        if cname in custnames: cid = custnames[cname]["_id"]
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
                        cid = cname = so["custname"]
                        if cname in custnames:
                            if (so["objectName"] == custnames[so['custname']]['xpath']) and (so['url'] == custnames[so['custname']]['url']):
                                cid = custnames[cname]["_id"]
                            else:
                                so["custname"] = cname+str(datetime.datetime.today().timestamp())
                                cid = ObjectId()
                                custnames[so["custname"]] = {"_id":cid,"xpath":so["objectName"],"url":so['url']}
                                missingCustname[cid] = so
                        elif (cname not in custnames) and (cname not in defcn):
                            cid = ObjectId()
                            custnames[cname] = {"_id":cid,"xpath":so["objectName"],"url":so['url']}
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
                    createdataobjects(query_screen['screenid'], missingCustname)

                #query to update tescase
                if(requestdata['query'] == 'updatetestcasedata'):
                    queryresult = n68session2.testcases.update_many({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},
                                {'$set':{'modifiedby':ObjectId(requestdata['modifiedby']),'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),'steps':steps},"$currentDate":{'modifiedon':True}}).matched_count
                    if queryresult > 0:
                        res= {'rows': 'success'}
            else:
                app.logger.warn('Empty data received. updating testcases')
        except Exception as updatetestcaseexception:
            servicesException('updateTestCase_ICE',updatetestcaseexception)
        return jsonify(res)


    def update_steps(steps,dataObjects):
        del_flag = False
        try:
            for j in steps:
                j['objectName'], j['url'], j['addTestCaseDetailsInfo'], j['addTestCaseDetails'] = '', '', '', ''
                if 'addDetails' in j:
                    j['addTestCaseDetailsInfo'] = j['addDetails']
                    del j['addDetails']
                if j['custname'] == "@Custom":
                    j['objectName'] = "@Custom"
                    continue
                if 'custname' in j.keys():
                    if j['custname'] in dataObjects.keys():
                        j['objectName'] = dataObjects[j['custname']]['xpath']
                        j['url'] = dataObjects[j['custname']]['url'] if 'url' in dataObjects[j['custname']] else ""
                        j['cord'] = dataObjects[j['custname']]['cord'] if 'cord' in dataObjects[j['custname']] else ""
                        j['custname'] = dataObjects[j['custname']]['custname']
                    elif j['custname'] not in defcn:
                        j['custname'] = 'OBJECT_DELETED'
                        if j['outputVal'].split(';')[-1] != '##':
                            del_flag = True

        except Exception as e:
            servicesException('readTestCase_ICE',e)
        return del_flag



    #test case reading service
    @app.route('/design/readTestCase_ICE',methods=['POST'])
    def readTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside readTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                if(requestdata['query'] == 'testcaseids'):
                    tc_id_list=[]
                    if not isinstance(requestdata['testcaseid'],list):
                        requestdata['testcaseid'] = [requestdata['testcaseid']]
                    for i in requestdata['testcaseid']:
                        tc_id_list.append(ObjectId(i))
                    query = [
                        {"$match":{"_id":{"$in":tc_id_list}}},
                        {"$addFields":{"__order":{"$indexOfArray":[tc_id_list,"$_id"]}}},
                        {"$sort":{"__order":1}},
                        {"$project":{'steps':1,'name':1,'screenid':1,'_id':0}}
                    ]
                    queryresult = list(n68session2.testcases.aggregate(query))
                    if (queryresult != []):
                        for k in queryresult:
                            queryresult1 = list(n68session2.dataobjects.find({'parent':k['screenid']},{'parent':0}))
                            dataObjects = {}
                            if (queryresult1 != []):
                                dataObjects = {i['_id']:i for i in queryresult1}
                            del_flag = update_steps(k['steps'],dataObjects)
                    res= {'rows': queryresult, 'del_flag':del_flag}
                else:
                    queryresult = list(n68session2.testcases.find({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},{'screenid':1,'steps':1,'name':1,'_id':0}))
                    queryresult1 = list(n68session2.dataobjects.find({'parent':queryresult[0]['screenid']},{'parent':0}))
                    dataObjects = {}
                    if (queryresult1 != []):
                        dataObjects = {i['_id']:i for i in queryresult1}
                    if (queryresult != []):
                        del_flag = update_steps(queryresult[0]['steps'],dataObjects)
                    if 'screenName' in requestdata and requestdata['screenName']=='fetch':
                        screen = n68session2.screens.find_one({'_id':queryresult[0]['screenid']},{'name':1})
                        res= {'rows': queryresult, 'del_flag':del_flag, 'screenName':screen['name']}
                    else:
                        res= {'rows': queryresult, 'del_flag':del_flag}
                    # if (not requestdata.has_key('readonly')):
                    #     count = debugcounter + 1
                    #     userid = requestdata['userid']
                    #     counterupdator('testcases',userid,count)
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as readtestcaseexc:
            servicesException('readTestCase_ICE',readtestcaseexc)
        return jsonify(res)
