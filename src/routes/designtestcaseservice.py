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
                        queryresult = list(n68session2.testcases.find({'_id':{'$in':ids[0]['testcaseids']}},{'name':1}))
                        res= {'rows':queryresult}
                else:
                    res={'rows':'fail'}
            else:
                app.logger.warn('Empty data received. getting testcases.')
        except Exception as e:
            servicesException('getTestcasesByScenarioId_ICE',e)
        return jsonify(res)




    #test case updating service
    @app.route('/design/updateTestCase_ICE',methods=['POST'])
    def updateTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside updateTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                if not (requestdata['import_status']):
                    for i in requestdata['testcasesteps']:
                        if 'dataObject' in i.keys():
                            if i['dataObject'] != '':
                                i['dataObject'] = ObjectId(i['dataObject'])
                                queryresult1 = list(n68session2.dataobjects.find({'_id':i['dataObject']},{'custname':1,'_id':0}))
                                i['custname'] = queryresult1[0]['custname']
                        if 'objectName' in i.keys():
                            del i['objectName']
                        if 'url' in i.keys():
                            del i['url']
                else:
                    #Import testcase
                    queryresult1 = list(n68session2.dataobjects.find({'parent':ObjectId(requestdata['screenid'])},{'parent':0}))
                    custnames = {}
                    added=[]
                    if (queryresult1 != []):
                        for i in queryresult1:
                            custnames[i['custname']] = i
                    for i in requestdata['testcasesteps']:
                        data_obj = {}
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
                            data_obj["parent"] = [ObjectId(requestdata["screenid"])]
                            newObj = n68session2.dataobjects.insert_one(data_obj)
                            i['dataObject'] = newObj.inserted_id
                        if 'objectName' in i.keys():
                            del i['objectName']
                        if 'url' in i.keys():
                            del i['url']
                if(requestdata['query'] == 'updatetestcasedata'):
                    queryresult = n68session2.testcases.update_many({'_id':ObjectId(requestdata['testcaseid']),'versionnumber':requestdata['versionnumber'],'parent':ObjectId(requestdata['screenid'])},
                                {'$set':{'modifiedby':requestdata['modifiedby'],'steps':requestdata['testcasesteps']},"$currentDate":{'modifiedon':True}}).matched_count
                    if queryresult > 0:
                        res= {'rows': 'success'}
            else:
                app.logger.warn('Empty data received. updating testcases')
        except Exception as updatetestcaseexception:
            servicesException('updateTestCase_ICE',updatetestcaseexception)
        return jsonify(res)




    #test case reading service
    @app.route('/design/readTestCase_ICE',methods=['POST'])
    def readTestCase_ICE():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug('Inside readTestCase_ICE. Query: '+str(requestdata['query']))
            if not isemptyrequest(requestdata):
                if(requestdata['query'] == 'readtestcase'):
                    queryresult = list(n68session2.testcases.find({'_id':ObjectId(requestdata['testcaseid']),'parent':ObjectId(requestdata['screenid']),'versionnumber':requestdata['versionnumber']},{'steps':1,'name':1,'_id':0}))
                    queryresult1 = list(n68session2.dataobjects.find({'parent':ObjectId(requestdata['screenid'])},{'parent':0}))
                    dataObjects = {}
                    if (queryresult1 != []):
                        for i in queryresult1:
                            dataObjects[i['_id']] = i
                    if (queryresult != []):
                        for j in queryresult[0]['steps']:
                            if 'dataObject' in j.keys():
                                if j['dataObject'] != '':
                                    if j['dataObject'] in dataObjects.keys():
                                        j['objectName'] = dataObjects[j['dataObject']]['xpath']
                                        j['url'] = dataObjects[j['dataObject']]['url']
                                        j['custname'] = dataObjects[j['dataObject']]['custname']
                            if 'objectName' not in j.keys():
                                j['objectName'] = ''
                                j['url'] = ''
                    res= {'rows': queryresult}
                elif(requestdata['query'] == 'testcaseid'):
                    tc_id_list=[]
                    if not isinstance(requestdata['testcaseid'],list):
                        requestdata['testcaseid'] = [requestdata['testcaseid']]
                    for i in requestdata['testcaseid']:
                        tc_id_list.append(ObjectId(i))
                    queryresult = list(n68session2.testcases.find({'_id':{'$in':tc_id_list}},{'steps':1,'name':1,'parent':1,'_id':0}))
                    for k in range(len(queryresult)):
                        queryresult1 = list(n68session2.dataobjects.find({'parent':ObjectId(queryresult[k]['parent'][0])},{'parent':0}))
                        dataObjects = {}
                        if (queryresult1 != []):
                            for i in queryresult1:
                                dataObjects[i['_id']] = i
                        if (queryresult != []):
                            for j in queryresult[k]['steps']:
                                if 'dataObject' in j.keys():
                                    if j['dataObject'] != '':
                                        if j['dataObject'] in dataObjects.keys():
                                            j['objectName'] = dataObjects[j['dataObject']]['xpath']
                                            j['url'] = dataObjects[j['dataObject']]['url']
                                            j['custname'] = dataObjects[j['dataObject']]['custname']
                                if 'objectName' not in j.keys():
                                    j['objectName'] = ''
                                    j['url'] = ''
                    res= {'rows': queryresult}
                    #if (not requestdata.has_key('readonly')):
                    #    count = debugcounter + 1
                    #    userid = requestdata['userid']
                    #    counterupdator('testcases',userid,count)
                elif(requestdata['query'] == 'screenid'):
                    queryresult = list(n68session2.testcases.find({'parent':ObjectId(requestdata['screenid'])},{'steps':1,'name':1,'_id':0}))
                    queryresult1 = list(n68session2.dataobjects.find({'parent':ObjectId(requestdata['screenid'])}))
                    dataObjects = {}
                    if (queryresult1 != []):
                        for i in queryresult1:
                            dataObjects[i['_id']] = i
                    if (queryresult != []):
                        for k in range(len(queryresult)):
                            for j in queryresult[k]['steps']:
                                if 'dataObject' in j.keys():
                                    if j['dataObject'] != '':
                                        if j['dataObject'] in dataObjects.keys():
                                            j['objectName'] = dataObjects[j['dataObject']]['xpath']
                                            j['url'] = dataObjects[j['dataObject']]['url']
                                            j['custname'] = dataObjects[j['dataObject']]['custname']
                                if 'objectName' not in j.keys():
                                    j['objectName'] = ''
                                    j['url'] = ''
                    res= {'rows': queryresult}
            else:
                app.logger.warn('Empty data received. reading Testcase')
        except Exception as readtestcaseexc:
            servicesException('readTestCase_ICE',readtestcaseexc)
        return jsonify(res)
