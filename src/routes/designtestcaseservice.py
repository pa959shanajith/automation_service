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



    def object_dict(key, queryresult):
        return {i[key]:i for i in queryresult}

    #test case updating service
    @app.route('/design/updateTestCase_ICE',methods=['POST'])
    def updateTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside updateTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                query_screen = n68session2.testcases.find_one({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},{'screenid':1})
                if not (requestdata['import_status']):
                    for i in requestdata['testcasesteps']:
                        if 'dataObject' in i.keys():
                            if i['dataObject'] != '':
                                i['dataObject'] = ObjectId(i['dataObject'])
                                queryresult1 = list(n68session2.dataobjects.find({'_id':i['dataObject']},{'custname':1,'_id':0}))
                                if (queryresult1 != []):
                                    i['custname'] = queryresult1[0]['custname']
                        if 'objectName' in i.keys():
                            del i['objectName']
                        if 'url' in i.keys():
                            del i['url']
                else:
                    #Import testcase
                    queryresult1 = list(n68session2.dataobjects.find({'parent':query_screen['screenid']},{'parent':0}))
                    custnames = {}
                    added=[]
                    if (queryresult1 != []):
                        custnames = object_dict('custname', queryresult1)
                    for i in requestdata['testcasesteps']:
                        data_obj = {}
                        if not i["custname"].startswith("@"):
                            if i["custname"] not in custnames.keys():
                                data_obj["custname"] = i["custname"]
                            else:
                                if i['objectName'] == custnames[i['custname']]['xpath'] and i['url'] == custnames[i['custname']]['url']:
                                    added.append(i["custname"])
                                    i['dataObject'] = custnames[i['custname']]['_id']
                                else:
                                    data_obj["custname"] = i["custname"] + "_new"
                                    i["custname"] = data_obj["custname"]
                            if i["custname"] not in added:
                                added.append(i["custname"])
                                if 'objectName' in i.keys():
                                    data_obj['xpath'] = i['objectName']
                                if 'url' in i.keys():
                                    data_obj['url'] = i['url']
                                data_obj["parent"] = [query_screen["screenid"]]
                                newObj = n68session2.dataobjects.insert_one(data_obj)
                                i['dataObject'] = newObj.inserted_id
                        if 'objectName' in i.keys():
                            del i['objectName']
                        if 'url' in i.keys():
                            del i['url']
                if(requestdata['query'] == 'updatetestcasedata'):
                    queryresult = n68session2.testcases.update_many({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},
                                {'$set':{'modifiedby':ObjectId(requestdata['modifiedby']),'modifiedbyrole':ObjectId(requestdata['modifiedbyrole']),'steps':requestdata['testcasesteps']},"$currentDate":{'modifiedon':True}}).matched_count
                    if queryresult > 0:
                        res= {'rows': 'success'}
            else:
                app.logger.warn('Empty data received. updating testcases')
        except Exception as updatetestcaseexception:
            servicesException('updateTestCase_ICE',updatetestcaseexception)
        return jsonify(res)



    def update_steps(steps,dataObjects):
        for j in steps:
            j['objectName'], j['url'] = '', ''
            if 'dataObject' in j.keys():
                if j['dataObject'] != '':
                    if j['dataObject'] in dataObjects.keys():
                        j['objectName'], j['url'], j['custname'] = dataObjects[j['dataObject']]['xpath'], dataObjects[j['dataObject']]['url'], dataObjects[j['dataObject']]['custname']

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
                                dataObjects = object_dict('_id', queryresult1)
                            update_steps(k['steps'],dataObjects)
                    res= {'rows': queryresult}
                else:
                    queryresult = list(n68session2.testcases.find({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber']},{'screenid':1,'steps':1,'name':1,'_id':0}))
                    queryresult1 = list(n68session2.dataobjects.find({'parent':queryresult[0]['screenid']},{'parent':0}))
                    dataObjects = {}
                    if (queryresult1 != []):
                        dataObjects = object_dict('_id', queryresult1)
                    if (queryresult != []):
                        update_steps(queryresult[0]['steps'],dataObjects)
                    res= {'rows': queryresult}
                    # if (not requestdata.has_key('readonly')):
                    #     count = debugcounter + 1
                    #     userid = requestdata['userid']
                    #     counterupdator('testcases',userid,count)
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as readtestcaseexc:
            servicesException('readTestCase_ICE',readtestcaseexc)
        return jsonify(res)
