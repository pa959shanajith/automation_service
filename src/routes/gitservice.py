from git import repo
import git
import os
import logging
import json
from utils import *
import shutil
import flask
from flask import Flask, request, jsonify, Response
import subprocess
import stat
from os import path
currdir=os.getcwd()

def LoadServices(app, redissession, dbsession, *args):
    setenv(app)
    defcn = ['@Window', '@Object', '@System', '@Excel', '@Mobile', '@Android_Custom', '@Word', '@Custom', '@CustomiOS',
             '@Generic', '@Browser', '@Action', '@Email', '@BrowserPopUp', '@Sap','@Oebs', 'WebService List', 'Mainframe List', 'OBJECT_DELETED']

    #Import mindmap from git repository
    @app.route('/git/importFromGit_ICE',methods=['POST'])
    def importFromGit_ICE():
        app.logger.debug("Inside importFromGit_ICE")
        res={'rows':'fail'}
        resultdata = {}
        path1=None
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                # gitAccToken=requestdata['gitAccessToken']
                versionName=requestdata['gitVersionName']
                # GitRepoClonePath=requestdata['gitRepoClonePath']
                moduleName=requestdata['folderPath']
                createdBy=requestdata['createdBy']
                gitbranch=requestdata['gitbranch']

                # if(versionName!=''):
                commitId = dbsession.gitexportdetails.find_one({'branchname':gitbranch,'folderpath':moduleName,'versionname':versionName},{"_id":1,"commitid":1,"parent":1})
                if not commitId:
                    result ={'rows':'empty'}
                    return res
                
                gitconfig_data = dbsession.gitconfiguration.find_one({"_id":commitId["parent"]},{"gitaccesstoken":1,"giturl":1})
                url=gitconfig_data['giturl'].split('://')
                url=url[0]+"://"+gitconfig_data['gitaccesstoken']+':'+'x-oauth-basic'+"@"+url[1]

                path1=currdir+os.sep+'importGit'+os.sep+createdBy+os.sep
                repo = git.Repo.init(path1)
                origin = repo.create_remote('origin',url)
                origin.fetch()

                repo.git.checkout(commitId['commitid'])

                modulePath = path1+moduleName+os.sep
                modulePath = modulePath.replace('/','\\')
                screenpath= modulePath+'Screens'+os.sep
                testcasepath= modulePath+'Testcases'+os.sep
                # mindmapname=moduleName.split('/')[-1]
                screen_data={}
                tc_data={}

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
                        testcaseid = eachTc.split('.')[0].split('_')[-1]
                        tc_data[testcaseid]=tc
                        testcasefile.close()
                
                res={"moduledata":data,"screendata":screen_data, 'tcdata':tc_data, 'createdBy':createdBy}
                
                os.system('rmdir /S /Q "{}"'.format(path1))
                result = executionJson(res, requestdata)
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            if(path1): os.system('rmdir /S /Q "{}"'.format(path1))
            servicesException("importFromGit_ICE", ex, True)
        return result

    def executionJson(result, requestdata):
        app.logger.debug("Inside executionJson")
        res={'rows':'fail'}
        try:
            mindmap_data=result['moduledata']
            screen_info=result['screendata']
            testcase_info=result['tcdata']
            moduleid=mindmap_data['_id']
            modulename= mindmap_data['name']
            createdBy= result['createdBy']
            scenario_names=[]
            scenario_ids=[]
            accessibilitytesting={}
            suite_details=[]
            projectid=mindmap_data['projectid']
            suiteIds = list(dbsession.testsuites.find({"mindmapid":ObjectId(moduleid),"name":modulename},{"_id":1}))
            projectDetails=dbsession.projects.find_one({'_id':ObjectId(projectid)},{"name":1,"domain":1,"releases.name":1,"releases.cycles._id":1,"releases.cycles.name":1})
            
            for i in mindmap_data['testscenarios']: #to fetch list of all scenarioid and name
                # scenarioname_list=dbsession.testscenarios.find_one({"_id":ObjectId(i['_id'])},{"name":1,"accessibilitytesting":1})
                scenarioname_list=dbsession.testscenarios.find_one({"_id":ObjectId(i['_id'])},{"name":1})
                scenarioname_list['accessibilitytesting']=[]
                scenario_names.append(scenarioname_list['name'])
                scenario_ids.append(str(scenarioname_list['_id']))
                accessibilitytesting[str(scenarioname_list['_id'])]=scenarioname_list['accessibilitytesting']
             
            
            for eachsuite in suiteIds: #Fetching each testSuite
                suite_details.append(str(eachsuite['_id']))

            suiteDetailsTemplate = { 
                "browserType": requestdata['browserType'],
                "testsuitename": modulename,
                "testsuiteid": suite_details,
                "domainname": projectDetails['domain'],
                "projectid": projectid,
                "projectname": projectDetails['name'],
                "releaseid": projectDetails['releases'][0]['name'],
                "cyclename": projectDetails['releases'][0]['cycles'][0]['name'],
                "cycleid": str(projectDetails['releases'][0]['cycles'][0]['_id']),
                "condition": [0, 0],
                "dataparampath": ["", ""],
                "scenarioNames": scenario_names,
                "scenarioIds": scenario_ids,
                "accessibilityMap": accessibilitytesting,
                suite_details[0]:[]
            }
            
            #creating template for testcase details
            for i in mindmap_data['testscenarios']:
                screen_tc_details =[]
                for j in i['screens']:
                    screen_name = screen_info[j['_id']]['name']
                    screen_apptype = screen_info[j['_id']]['appType']
                    for k in j['testcases']:
                        tc_steps = testcase_info[k]['steps']
                        tc_name = testcase_info[k]['name']
                        template1={
                            "template":"",
                            "testcase":tc_steps,
                            "testcasename":tc_name,
                            "screenid":j['_id'],
                            "screenname":screen_name
                        }
                        screen_tc_details.append(template1)
                template2 = {
                    i['_id']:screen_tc_details,
                    "integration":""
                }
                suiteDetailsTemplate[suite_details[0]].append(template2)

            starttime = datetime.now()
            batchid = ObjectId() #generating batchid
            execids = []

            #creating execution details in DB
            for tsuid in suite_details:
                insertquery = {"batchid": batchid, "parent": [ObjectId(suiteIds[0]['_id'])],
                    "configuration": {}, "executedby": ObjectId(createdBy),
                    "status": "inprogress", "endtime": None, "starttime": starttime}
                execid = str(dbsession.executions.insert(insertquery))
                execids.append(execid)

            #main json which will be passed to ICE
            git_json = {
                "exec_mode": requestdata['exectionMode'],
                "exec_env" : requestdata['executionEnv'],
                "apptype": screen_apptype,
                "integration": requestdata['integration'],
                "batchId": str(batchid),
                "executionIds": execids,
                "testsuiteIds": suite_details,
                "suitedetails": [suiteDetailsTemplate]
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
                action = requestdata['action']
                del_flag = False
                del_testcases = []

                project_id = dbsession.mindmaps.find_one({"_id":ObjectId(requestdata["moduleId"])},{"projectid":1,"_id":0})
                git_details = list(dbsession.gitconfiguration.find({"projectid":project_id["projectid"],"gituser":ObjectId(requestdata["userid"])},{"giturl":1,"gitaccesstoken":1}))
                if not git_details:
                    res={'rows':'empty'}
                    return res
                
                moduleId = ObjectId(requestdata['moduleId'])
                mindMapsList = list(dbsession.mindmaps.find({'_id':moduleId},{"projectid":1,"name":1,"createdby":1,"versionnumber":1,"deleted":1,"type":1,"testscenarios":1}))

                result = dbsession.gitexportdetails.find({"branchname":requestdata["gitBranch"],"versionname":requestdata["gitVersionName"],"projectid":mindMapsList[0]['projectid'],"folderpath":requestdata['gitFolderPath']})
                index = result.count() - 1
                result=None
                if index >= 0:
                    res={'rows':'commit exists'}
                    return res
                elif result == None or result.count() == 0:
                    path=currdir+os.sep+"mindmapGit"+os.sep+requestdata["userid"]+os.sep+requestdata["gitFolderPath"]+os.sep
                    path=path.replace('/','\\')

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
                            testcaseList = list(dbsession.testcases.find({'screenid':j['_id']},{'screenid':1,'steps':1,'name':1,'parent':1}))
                            for k in testcaseList:
                                del_flag = update_steps(k['steps'],dataObjects)
                                testcaseNameFormat=k["name"]+'_'+str(k["_id"])+'.json'
                                tc_file=open(path+'Testcases'+os.sep+testcaseNameFormat,'w')
                                tc_file.write(flask.json.JSONEncoder().encode(k))
                                tc_file.close()
                            i['testcases'] += testcaseList
                    res = exportdataToGit(path, requestdata, requestdata)
                # res =  {'rows': result}
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            servicesException("exportToGit", ex, True)
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

    def exportdataToGit(dirpath, result):
        app.logger.debug("Inside exportdataToGit")
        res={'rows':'fail'}
        delpath=None
        git_path=None
        try:
            module_data=result
            # path1 = dirpath.split('mindmapGit\\')
            # module_path = path1[0]+path1[1]
            delpath=currdir+os.sep+"mindmapGit"
            data={}
            if not isemptyrequest(module_data):
                project_id = dbsession.mindmaps.find_one({"_id":ObjectId(module_data["moduleId"])},{"projectid":1,"_id":0})
                git_details = list(dbsession.gitconfiguration.find({"projectid":project_id["projectid"],"gituser":ObjectId(result["userid"])},{"gituser":1,"giturl":1,"gitaccesstoken":1}))

                git_path=currdir+os.sep+'exportGit'+os.sep+result["userid"]
                final_path=git_path+os.sep+module_data["gitFolderPath"]
                final_path=final_path.replace('/','\\')

                url=git_details[0]["giturl"].split('://')
                url=url[0]+'://'+git_details[0]['gitaccesstoken']+':x-oauth-basic@'+url[1]

                repo = git.Repo.init(git_path)
                origin = repo.create_remote('origin',url)
                origin.fetch()

                repo.git.checkout(module_data["gitBranch"])
                repo.git.pull()

                # delpath=currdir+os.sep+"mindmapGit"

                if(os.path.exists(final_path)):
                    if os.path.exists(dirpath):
                        shutil.rmtree(final_path)
                shutil.move(dirpath, final_path)
                # Add mimdmap file to remote repo
                repo.git.add(final_path)
                repo.index.commit(module_data["gitVersionName"])

                origin = repo.remote(name="origin")
                origin.push(origin.refs[0].remote_head)

                # get the commit id and save it in gitexportdetails
                commit_id = origin.refs[0].commit.hexsha

                data["parent"] = git_details[0]["_id"]
                data["projectid"] = project_id["projectid"]
                data["branchname"] = module_data["gitBranch"]
                data["folderpath"] = module_data["gitFolderPath"]
                data["versionname"] = module_data["gitVersionName"]
                data["commitid"] = commit_id
                dbsession.gitexportdetails.insert(data)

                # dbsession.gitexportdetails.update_one({"projectid":project_id["projectid"]},{"$set":{"commitid":commit_id}})
                
                shutil.rmtree(delpath)
                os.system('rmdir /S /Q "{}"'.format(git_path))
                res={'rows':'Success'}
            else:
                app.logger.warn('Connection to Git failed: Empty data passed from exportToGit service')
        except Exception as ex:
            if(delpath): shutil.rmtree(delpath)
            if(git_path): os.system('rmdir /S /Q "{}"'.format(git_path))
            app.logger.warn(ex)
        return res

    @app.route('/git/importGitMindmap', methods=['POST'])
    def importGitMindmap():
        app.logger.debug("Inside importGitMindmap")
        res='fail'
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                projectid=requestdata["projectid"]
                gitBranch=requestdata["gitbranch"]
                gitVersionName=requestdata["gitversion"]
                gitFolderPath=requestdata["gitfolderpath"]

                result = dbsession.gitexportdetails.find_one({"branchname":gitBranch,"versionname":gitVersionName,"projectid":ObjectId(projectid),"folderpath":gitFolderPath},{"parent":1,"commitid":1})
                if not result:
                    res = "empty"
                    return res
                else:
                    gitdetails = dbsession.gitconfiguration.find_one({"_id":result["parent"]})
                    git_path=currdir+os.sep+'exportGit'+os.sep+str(gitdetails["gituser"])
                    final_path=git_path+os.sep+gitFolderPath
                    final_path=final_path.replace('/','\\')
                    
                    if(os.path.isdir(git_path)): os.system('rmdir /S /Q "{}"'.format(git_path))

                    url=gitdetails["giturl"].split('://')
                    url=url[0]+'://'+gitdetails["gitaccesstoken"]+':x-oauth-basic@'+url[1]
                    
                    # repo = git.Repo.init(git_path)
                    # origin = repo.create_remote('origin',url)
                    # origin.fetch()

                    repo = git.Repo.clone_from(url, git_path, no_checkout=True)
                    repo.git.checkout(result['commitid'])
                    # repo.git.checkout(result['branchname'])
                    # repo.git.checkout(result['commitid'])
                    # repo.git.pull() #pull the folder from the git branch

                    mm_file = [f for f in os.listdir(final_path) if f.endswith('.mm')]
                    with open(final_path+os.sep+mm_file[0]) as mmFile:
                        json_data=json.loads(mmFile.read())
                        mmFile.close()

                    os.system('rmdir /S /Q "{}"'.format(git_path))
                    res=json_data
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            if(git_path): os.system('rmdir /S /Q "{}"'.format(git_path))
            servicesException("importGitMindmap", ex, True)
        return res