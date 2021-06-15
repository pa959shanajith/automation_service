import sys
from git import repo
import git
import os
import json
from utils import *
import shutil
import flask
from flask import Flask, request, jsonify, Response
from Crypto.Cipher import AES
import codecs
from os import path
from pymongo import InsertOne
from pymongo import UpdateOne
currdir=os.getcwd()

ldap_key = "".join(['l','!','g','#','t','W','3','l','g','G','h','1','3','@','(',
    'c','E','s','$','T','p','R','0','T','c','O','I','-','k','3','y','S'])

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

def LoadServices(app, redissession, dbsession, *args):
    setenv(app)
    defcn = ['@Window', '@Object', '@System', '@Excel', '@Mobile', '@Android_Custom', '@Word', '@Custom', '@CustomiOS',
             '@Generic', '@Browser', '@Action', '@Email', '@BrowserPopUp', '@Sap','@Oebs', 'WebService List', 'Mainframe List', 'OBJECT_DELETED']

    def remove_dir(rem_path):
        try:
            if os.path.exists(rem_path):
                if sys.platform == 'win32':
                    cmd = "rmdir /Q /S " + rem_path
                if sys.platform in ["linux", "darwin"]:
                    cmd = "rm -rf "+ rem_path
                os.system(cmd)
        except Exception as e:
            app.logger.warn(e)

    #Import mindmap from git repository
    @app.route('/git/importFromGit_ICE',methods=['POST'])
    def importFromGit_ICE():
        app.logger.debug("Inside importFromGit_ICE")
        result={'rows':'gitfail'}
        path1=None
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                versionName=requestdata['gitVersion']
                moduleName=requestdata['folderPath']
                userid=requestdata['userid']
                gitbranch=requestdata['gitbranch']
                gitname=requestdata["gitname"]
                
                gitconfig_data = dbsession.gitconfiguration.find_one({"name":gitname},{"gitaccesstoken":1,"giturl":1,"gituser":1})
                if not gitconfig_data:
                    result ={'rows':'No config'}
                    return result
                commitId = dbsession.gitexportdetails.find_one({'branchname':gitbranch,'folderpath':moduleName,'version':versionName, "parent":gitconfig_data['_id']},{"commitid":1})
                if not commitId:
                    result ={'rows':'empty'}
                    return result
                
                url=gitconfig_data['giturl'].split('://')
                url=url[0]+"://"+unwrap(gitconfig_data['gitaccesstoken'], ldap_key)+':'+'x-oauth-basic'+"@"+url[1]

                path1=currdir+os.sep+'importGit'+os.sep+userid+os.sep
                repo = git.Repo.init(path1)
                origin = repo.create_remote('origin',url)
                origin.fetch()

                repo.git.checkout(commitId['commitid'])

                modulePath = os.path.normpath(path1+moduleName)+os.sep
                screenpath= modulePath+'Screens'+os.sep
                testcasepath= modulePath+'Testcases'+os.sep
                screen_data={}
                tc_data={}
                tc_namesmap={}

                mm_file = [f for f in os.listdir(modulePath) if f.endswith('.mm')]

                with open(modulePath+mm_file[0]) as mindmapFile:
                    data=json.loads(mindmapFile.read())
                    mindmapFile.close()
                
                for eachscreen in os.listdir(screenpath):
                    with open(screenpath+eachscreen, 'r') as screenfile:
                        screen=json.loads(screenfile.read())
                        screenid=eachscreen.split('.')[0].split('_')[-1]
                        screen_data[screenid]=screen
                        screenfile.close()

                for eachTc in os.listdir(testcasepath):
                    with open(testcasepath+eachTc, 'r') as testcasefile:
                        tc=json.loads(testcasefile.read())
                        testcase_nameid = eachTc.split('.')[0].split('_')
                        testcaseid = testcase_nameid[-1]
                        tc_data[testcaseid]=tc
                        tc_namesmap[testcaseid]="_".join(testcase_nameid[:-1])
                        testcasefile.close()
                
                res={"moduledata":data,"screendata":screen_data, 'tcdata':tc_data, 'tcname_map':tc_namesmap, 'userid':userid}
                
                result = executionJson(res)
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            servicesException("importFromGit_ICE", ex, True)
        remove_dir(path1)
        return result

    def executionJson(result):
        app.logger.debug("Inside executionJson")
        res={'rows':'fail'}
        try:
            mindmap_data=result['moduledata']
            screen_info=result['screendata']
            testcase_info=result['tcdata']
            testcasenames=result['tcname_map']
            moduleid=mindmap_data['_id']
            modulename= mindmap_data['name']
            suite_details=[]
            scenarioname_list=[]
            projectid=mindmap_data['projectid']
            suiteIds = list(dbsession.testsuites.find({"mindmapid":ObjectId(moduleid)},{"_id":1}))
            projectDetails=dbsession.projects.find_one({'_id':ObjectId(projectid)},{"name":1,"domain":1,"releases.name":1,"releases.cycles._id":1,"releases.cycles.name":1})
            
            for i in mindmap_data['testscenarios']: #to fetch list of all scenarioid and name
                scenarioname_list.append({'_id': ObjectId(i['_id']), 'name': i['testscenarioname']}) 
             
            for eachsuite in suiteIds: #Fetching each testSuite
                suite_details.append(str(eachsuite['_id']))

            batchInfo=[]
            for suite in suite_details:
                suiteDetailsTemplate = {
                    "testsuiteName": modulename,
                    "testsuiteId": suite,
                    "apptype":'',
                    "domainName": projectDetails['domain'],
                    "projectId": projectid,
                    "projectName": projectDetails['name'],
                    "releaseId": projectDetails['releases'][0]['name'],
                    "cycleName": projectDetails['releases'][0]['cycles'][0]['name'],
                    "cycleId": str(projectDetails['releases'][0]['cycles'][0]['_id']),
                    "suiteDetails": []
                }
                for eachscenario in scenarioname_list:
                    temp1={
                        "condition": 0,
                        "dataparam": [""],
                        "scenarioId": str(eachscenario['_id']),
                        "scenarioName": eachscenario['name']
                    }
                    suiteDetailsTemplate["suiteDetails"].append(temp1)
                
                    screenTcDetails={}
                    dts_data = {}
                    #creating template for testcase details
                    for i in mindmap_data['testscenarios']:
                        screen_tc_details =[]
                        for j in i['screens']:
                            screen_name = screen_info[j['_id']]['name']
                            screen_apptype = screen_info[j['_id']]['appType']
                            for k in j['testcases']:
                                tc_steps = testcase_info[k]
                                tc_name = testcasenames[k]
                                dts = []
                                if len(tc_steps) > 0 and 'datatables' in tc_steps[-1]: 
                                    dtnames = tc_steps[-1]['datatables']
                                    if len(dtnames) > 0:
                                        dts_to_fetch = [i for i in dtnames if i not in dts_data]
                                        dtdet = dbsession.datatables.find({"name": {'$in': dts_to_fetch}})
                                        for dt in dtdet: dts_data[dt['name']] = dt['datatable']
                                        for dt in dtnames: dts.append({dt: dts_data[dt]})
                                    del tc_steps[-1]
                                template1={
                                    "template":"",
                                    "testcase":tc_steps,
                                    "testcasename":tc_name,
                                    "screenid":j['_id'],
                                    "screenname":screen_name,
                                    "datatables": dts
                                }
                                screen_tc_details.append(template1)

                        screenTcDetails[temp1["scenarioId"]] = str(screen_tc_details)

                suiteDetailsTemplate['apptype']=screen_apptype
            batchInfo.append(suiteDetailsTemplate)
            
            git_json = {
                "batchInfo": batchInfo,
                "suitedetails": screenTcDetails
            }
            res={"rows":git_json}
        except Exception as ex:
            app.logger.warn(ex)
        return res

    #Export mindmap to git repository
    @app.route('/git/exportToGit',methods=['POST'])
    def exportToGit():
        app.logger.debug("Inside exportToGit")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                del_flag = False

                project_id = dbsession.mindmaps.find_one({"_id":ObjectId(requestdata["moduleId"])},{"projectid":1,"_id":0})
                chk_config = dbsession.gitconfiguration.find_one({"projectid":project_id["projectid"],"gituser":ObjectId(requestdata["userid"])},{"_id":1})
                if not chk_config:
                    res={'rows':'empty'}
                    return res

                git_details = dbsession.gitconfiguration.find_one({"name":requestdata["gitname"],"gituser":ObjectId(requestdata["userid"]),"projectid":project_id["projectid"]},{"giturl":1,"gitaccesstoken":1,"gitusername":1,"gituseremail":1})
                if not git_details:
                    res={'rows':'Invalid config name'}
                    return res

                url=git_details["giturl"].split('://')
                url=url[0]+'://'+unwrap(git_details['gitaccesstoken'], ldap_key)+':x-oauth-basic@'+url[1]

                #check whether cred is valid
                git_path=currdir+os.sep+'exportGit'+os.sep+requestdata["userid"]
                if(os.path.exists(git_path)): remove_dir(git_path)

                repo = git.Repo.init(git_path)
                repo.config_writer().set_value('user', 'email', git_details['gituseremail']).release()
                repo.config_writer().set_value('user', 'name', git_details['gitusername']).release()
                origin = repo.create_remote('origin',url)
                origin.fetch()
                repo.git.checkout(requestdata["gitBranch"])
                repo.git.pull()

                moduleId = ObjectId(requestdata['moduleId'])
                mindMapsList = list(dbsession.mindmaps.find({'_id':moduleId},{"projectid":1,"name":1,"createdby":1,"versionnumber":1,"deleted":1,"type":1,"testscenarios":1}))
                for i in mindMapsList[0]['testscenarios']:
                    tsc_name = dbsession.testscenarios.find_one({'_id':i['_id']},{"_id":0, "name":1})
                    i['testscenarioname']=tsc_name['name']

                result = dbsession.gitexportdetails.find({"parent":git_details["_id"],"version":requestdata["gitVersion"]})
                index = result.count() - 1
                result=None
                if index >= 0:
                    res={'rows':'commit exists'}
                    return res
                elif result == None or result.count() == 0:
                    path=currdir+os.sep+"mindmapGit"+os.sep+requestdata["userid"]+os.sep+requestdata["gitFolderPath"]
                    path=os.path.normpath(path)+os.sep

                    if(os.path.exists(path)): shutil.rmtree(path)
    
                    os.makedirs(path)
                    os.mkdir(path+'Screens'+os.sep)
                    os.mkdir(path+'Testcases'+os.sep)
                    mm_file=open(path+mindMapsList[0]['name']+'.mm','w')
                    mm_file.write(flask.json.JSONEncoder().encode(mindMapsList[0]))
                    mm_file.close()
                    for i in mindMapsList:
                        scenarios = [s['_id'] for s in i['testscenarios']]
                        i['screens'] = []
                        i['testcases'] = []
                        screenList = list(dbsession.screens.find({'parent':{"$in":scenarios}}))
                        testcaseList = []
                        for j in screenList:
                            dataobj_query = list(dbsession.dataobjects.find({"parent" :j['_id']}))
                            if "scrapeinfo" in j and 'header' in j["scrapeinfo"]:
                                screen_json = j['scrapeinfo'] if 'scrapeinfo' in j else {}
                                screen_json["reuse"] = True if(len(j["parent"])>1) else False
                                screen_json["view"] = dataobj_query
                                screen_json["name"] = j["name"]
                            else:
                                screen_json = { "view": dataobj_query, "name":j["name"],
                                                "createdthrough": (j["createdthrough"] if ("createdthrough" in j) else ""),
                                                "scrapedurl": (j["scrapedurl"] if ("scrapedurl" in j) else ""),
                                                "mirror": (j["screenshot"] if ("screenshot" in j) else ""),
                                                "reuse": True if(len(j["parent"])>1) else False
                                            }
                            app_type=dbsession.projects.find_one({'_id':j["projectid"]},{'type':1})['type']
                            screen_json["appType"] = dbsession.projecttypekeywords.find_one({'_id':app_type},{'name':1})['name']
                            screen_json["screenId"] = j['_id']
                            i['screens'].append(screen_json)
                            dataObjects = {}
                            if (dataobj_query != []):
                                for dos in dataobj_query:
                                    if 'custname' in dos: dos['custname'] = dos['custname'].strip()
                                    dataObjects[dos['_id']] = dos
                            
                            screenNameFormat=screen_json["name"]+'_'+str(screen_json["screenId"])+'.json'
                            screen_file=open(path+'Screens'+os.sep+screenNameFormat,'w')
                            screen_file.write(flask.json.JSONEncoder().encode(screen_json))
                            screen_file.close()
                            testcaseList = list(dbsession.testcases.find({'screenid':j['_id']},{'screenid':1,'steps':1,'name':1,'parent':1,'datatables':1}))
                            for k in testcaseList:
                                del_flag = update_steps(k['steps'],dataObjects)
                                dtnames = k.get('datatables', [])
                                testcaseNameFormat=k["name"]+'_'+str(k["_id"])+'.json'
                                tc_file=open(path+'Testcases'+os.sep+testcaseNameFormat,'w')
                                if len(dtnames) > 0: k['steps'].append({'datatables':dtnames})
                                tc_file.write(flask.json.JSONEncoder().encode(k['steps']))
                                tc_file.close()
                            i['testcases'] += testcaseList
                    res = exportdataToGit(path, requestdata, origin, repo)
            else:
                app.logger.warn('Empty data received.')
        except git.GitCommandError as ex:
            if('pathspec' in ex.stderr):
                res={'rows':'Invalid gitbranch'}   
            elif('repository' in ex.stderr):
                res={'rows':'Invalid url'}
            elif('Authentication' in ex.stderr):
                res={'rows':'Invalid token'}
            servicesException("exportToGit", ex, True)
        except Exception as ex:
            servicesException("exportToGit", ex, True)
        remove_dir(git_path)
        return res

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
                        if 'original_device_width' in dataObjects[j['custname']].keys():
                            j['original_device_width'] = dataObjects[j['custname']]['original_device_width']
                            j['original_device_height'] = dataObjects[j['custname']]['original_device_height']
                        j['custname'] = dataObjects[j['custname']]['custname']
                    elif (j['custname'] not in defcn or j['custname']=='OBJECT_DELETED'):
                        j['custname'] = 'OBJECT_DELETED'
                        if j['outputVal'].split(';')[-1] != '##':
                            del_flag = True
        except Exception as e:
            servicesException('exportProject', e, True)
        return del_flag

    def exportdataToGit(dirpath, result, origin, repo):
        app.logger.debug("Inside exportdataToGit")
        res={'rows':'fail'}
        delpath=None
        git_path=None
        try:
            module_data=result
            delpath=currdir+os.sep+"mindmapGit"
            data={}
            if not isemptyrequest(module_data):
                git_details = dbsession.gitconfiguration.find_one({"name":module_data["gitname"],"gituser":ObjectId(module_data["userid"])},{"projectid":1})

                git_path=currdir+os.sep+'exportGit'+os.sep+module_data["userid"]
                final_path=os.path.normpath(git_path+os.sep+module_data["gitFolderPath"])

                if(os.path.exists(final_path)):
                    if os.path.exists(dirpath):
                        shutil.rmtree(final_path)
                shutil.move(dirpath, final_path)
                # Add mimdmap file to remote repo
                repo.git.add(final_path)
                repo.index.commit(module_data["gitVersion"])
                repo.git.push()

                # get the commit id and save it in gitexportdetails
                for i in range(len(origin.refs)):
                    if(origin.refs[i].remote_head==result["gitBranch"]):
                        commit_id = origin.refs[i].commit.hexsha
                        break

                data["userid"] = ObjectId(module_data["userid"])
                data["projectid"] = git_details["projectid"]
                data["branchname"] = module_data["gitBranch"]
                data["folderpath"] = module_data["gitFolderPath"]
                data["version"] = module_data["gitVersion"]
                data["parent"] = git_details["_id"]
                data["commitid"] = commit_id
                dbsession.gitexportdetails.insert(data)
                
                res={'rows':'Success'}
            else:
                app.logger.warn('Connection to Git failed: Empty data passed from exportToGit service')
        except git.GitCommandError as ex:
            if('Invalid username' in ex.stderr):
                res={'rows':'Invalid token'}
            app.logger.warn(ex)
        except Exception as ex:
            app.logger.warn(ex)
        if(delpath): shutil.rmtree(delpath)
        remove_dir(git_path)
        return res

    @app.route('/git/importGitMindmap', methods=['POST'])
    def importGitMindmap():
        app.logger.debug("Inside importGitMindmap")
        res='fail'
        git_path=None
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                projectid = requestdata["projectid"]
                gitname = requestdata["gitname"]
                gitBranch = requestdata["gitbranch"]
                gitVersionName = requestdata["gitversion"]
                gitFolderPath = requestdata["gitfolderpath"]
                roleid = requestdata["roleid"]
                userid = requestdata["userid"]
                
                git_data = dbsession.gitconfiguration.find_one({"name":gitname,"projectid":ObjectId(projectid)},{"gituser":1,"giturl":1,"gitaccesstoken":1})
                if not git_data:
                    git_data = list(dbsession.gitconfiguration.find({"name":gitname},{"_id":1}))
                    if len(git_data) > 0:
                        res = 'No entries'
                    else:
                        res='empty'
                    return res

                result = dbsession.gitexportdetails.find_one({"branchname":gitBranch,"version":gitVersionName,"projectid":ObjectId(projectid),"folderpath":gitFolderPath,"parent":git_data["_id"]},{"commitid":1})
                if not result:
                    res = 'Invalid inputs'
                    return res
                else:
                    git_path=currdir+os.sep+'exportGit'+os.sep+str(userid)
                    final_path=os.path.normpath(git_path+os.sep+gitFolderPath)
                    
                    if(os.path.isdir(git_path)): remove_dir(git_path)

                    url=git_data["giturl"].split('://')
                    url=url[0]+'://'+unwrap(git_data["gitaccesstoken"], ldap_key)+':x-oauth-basic@'+url[1]

                    repo = git.Repo.clone_from(url, git_path, no_checkout=True)
                    repo.git.checkout(result['commitid'])

                    mm_file = [f for f in os.listdir(final_path) if f.endswith('.mm')]
                    with open(final_path+os.sep+mm_file[0]) as mmFile:
                        json_data=json.loads(mmFile.read())
                        mmFile.close()
                    
                    screen_loc=final_path+os.sep+'Screens'+os.sep
                    testcase_loc=final_path+os.sep+'Testcases'+os.sep
                    for eachscreen in os.listdir(screen_loc):
                        with open(screen_loc+eachscreen, 'r') as screenfile:
                            screen=json.loads(screenfile.read())
                            screenid=eachscreen.split('.')[0].split('_')[-1]
                            screenfile.close()

                        screenId = ObjectId(screenid)
                        modifiedbyrole=  ObjectId(roleid)
                        modifiedby =  ObjectId(userid)
                        data_push=[]
                        data_up=[]
                        req = []
                        dtables = []
                        for i in range(len(screen["view"])):
                            if '_id' not in screen["view"][i]:
                                screen["view"][i]['_id'] = ObjectId()
                            else:
                                screen["view"][i]['_id'] = ObjectId(screen["view"][i]['_id'])
                            result=dbsession.dataobjects.find_one({'_id':screen["view"][i]['_id']},{"parent":1})
                            if result == None:
                                screen["view"][i]["parent"] = [screenId]
                                data_push.append(screen["view"][i])
                            else:
                                temp=result['parent']
                                if screenId not in temp:
                                    temp.append(screenId)
                                    screen["view"][i]["parent"] = temp
                                    data_up.append(screen["view"][i])
                                elif temp == [screenId]:
                                    screen["view"][i]["parent"] = temp
                                    data_push.append(screen["view"][i])
                                else:
                                    screen["view"][i]["parent"] = temp
                                    data_up.append(screen["view"][i])
                        if len(data_push)>0 or len(data_up)>0:
                            dbsession.dataobjects.update_many({"$and":[{"parent.1":{"$exists":True}},{"parent":screenId}]},{"$pull":{"parent":screenId}})
                            dbsession.dataobjects.delete_many({"$and":[{"parent":{"$size": 1}},{"parent":screenId}]})
                            for row in data_push:
                                req.append(InsertOne(row))
                            for row in data_up:
                                req.append(UpdateOne({"_id":row['_id']},{"$set":{"parent":row["parent"]}}))
                            dbsession.dataobjects.bulk_write(req)
                            if "mirror" in screen:
                                screenshot = screen['mirror']
                                if "scrapedurl" in screen:
                                    scrapedurl = screen["scrapedurl"]
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"scrapedurl":scrapedurl,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                                else:
                                    dbsession.screens.update({"_id":screenId},{"$set":{"screenshot":screenshot,"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})
                            elif 'scrapeinfo' in screen:
                                scrapeinfo=screen['scrapeinfo']
                                dbsession.screens.update({"_id":screenId},{"$set":{"scrapedurl":scrapeinfo["endPointURL"],"modifiedby":modifiedby,'modifiedbyrole':modifiedbyrole, 'scrapeinfo':scrapeinfo,"modifiedon" : datetime.now()}})
                            else:
                                dbsession.screens.update({"_id":screenId},{"$set":{"modifiedby":modifiedby, 'modifiedbyrole':modifiedbyrole,"modifiedon" : datetime.now()}})

                    for eachTc in os.listdir(testcase_loc):
                        with open(testcase_loc+eachTc, 'r') as testcasefile:
                            tc=json.loads(testcasefile.read())
                            testcaseid = eachTc.split('.')[0].split('_')[-1]
                            testcasefile.close()

                        if len(tc)> 0 : dtables = tc[-1].get('datatables', '')
                        query_screen = dbsession.testcases.find_one({'_id':ObjectId(testcaseid)},{'screenid':1,'datatables':1})
                        if len(dtables) > 0:
                            #update removed datatable tcs by removing current tcid
                            dbsession.datatables.update_many({"name": {'$nin': dtables}, "testcaseIds": testcaseid}, {"$pull": {"testcaseIds": testcaseid}})
                            #update each datatable tcs list by adding tcid
                            dbsession.datatables.update_many({"name": {'$in': dtables}, "testcaseIds": {"$ne": testcaseid}}, {"$push": {"testcaseIds": testcaseid}})
                            del tc[-1]
                        elif 'datatables' in query_screen and len(query_screen['datatables']) > 0:
                            dbsession.datatables.update_many({"name": {'$in': query_screen['datatables']}, "testcaseIds": testcaseid}, {"$pull": {"testcaseIds": testcaseid}})
                        queryresult1 = list(dbsession.dataobjects.find({'parent':query_screen['screenid']}))
                        custnames = {}
                        if (queryresult1 != []):
                            custnames = {i['custname'].strip():i for i in queryresult1}
                        steps = []
                        missingCustname = {}
                        for so in tc:
                            cid = cname = so["custname"].strip()
                            if cname in custnames:
                                if ('objectName' in so) and ('xpath' in custnames[cname]) and (so["objectName"] == custnames[cname]['xpath']):
                                    cid = custnames[cname]["_id"]
                                else:
                                    cid = ObjectId()
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
                        del tc
                        createdataobjects(query_screen['screenid'], missingCustname)

                        #query to update tescase
                        queryresult = dbsession.testcases.update_many({'_id':ObjectId(testcaseid),'versionnumber':0},
                                    {'$set':{'modifiedby':ObjectId(userid),'modifiedbyrole':ObjectId(roleid),'steps':steps,'datatables':dtables,"modifiedon" : datetime.now()}}).matched_count

                res=json_data
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            servicesException("importGitMindmap", ex, True)
        remove_dir(git_path)
        return res

    def adddataobjects(pid, d):
        if len(d) == 0: return False
        req = []
        for row in d:
            if type(row) == str and len(row) == 0: continue
            if "custname" not in row: row["custname"] = "object"+str(row["_id"])
            row["parent"] = [pid]
            req.append(InsertOne(row))
        dbsession.dataobjects.bulk_write(req)

    def createdataobjects(scrid, objs):
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
                    else: dodata[legend[i]] = ob[i]
                dodata["height"] = dodata["top"] - dodata["height"]
                dodata["width"] = dodata["left"] - dodata["width"]
                dodata["url"] = so["url"] if "url" in so else ""
                dodata["cord"] = so["cord"] if "cord" in so else ""
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
            elif so["appType"] == "pdf":
                dodata["tag"] = "_".join(so["custname"].split("_")[0:2])
            elif so["appType"] == ["Generic", "SAP", "Webservice", "Mainframe", "System"]: pass
            custnameToAdd.append(dodata)
        adddataobjects(scrid, custnameToAdd)

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