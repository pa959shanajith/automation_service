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
import platform
import requests
import base64

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

def LoadServices(app, redissession, client ,getClientName, *args):
    setenv(app)
    ldap_key = args[0]
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
                clientName=getClientName(requestdata)       
                dbsession=client[clientName]
                versionName=requestdata['gitVersion']
                moduleName=requestdata['folderPath']
                userid=requestdata['userid']
                gitbranch=requestdata['gitbranch']
                gitname=requestdata["gitname"]
                
                gitconfig_data = dbsession.gitconfiguration.find_one({"name":gitname},{"gitaccesstoken":1,"giturl":1,"gituser":1})
                if not gitconfig_data:
                    result ={'rows':'empty'}
                    return result
                commitId = dbsession.gitexportdetails.find_one({'branchname':gitbranch,'folderpath':moduleName,'version':versionName, "parent":gitconfig_data['_id']},{"commitid":1})
                if not commitId:
                    result ={'rows':'empty'}
                    return result
                
                url=gitconfig_data['giturl'].split('://')
                url=url[0]+"://"+unwrap(gitconfig_data['gitaccesstoken'], ldap_key)+':'+'x-oauth-basic'+"@"+url[1]

                path1=currdir+os.sep+'importGit'+os.sep+userid+os.sep
                if(os.path.exists(path1)): remove_dir(path1)
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
            requestdata=json.loads(request.data)
            clientName=getClientName(requestdata)        
            dbsession=client[clientName]
            mindmap_data=result['moduledata']
            screen_info=result['screendata']
            testcase_info=result['tcdata']
            testcasenames=result['tcname_map']
            moduleid=mindmap_data['_id']
            modulename= mindmap_data['name']
            suite_details=[]
            projectid=mindmap_data['projectid']
            suiteIds = list(dbsession.testsuites.find({"mindmapid":ObjectId(moduleid)},{"_id":1}))
            projectDetails=dbsession.projects.find_one({'_id':ObjectId(projectid)},{"name":1,"domain":1,"releases.name":1,"releases.cycles._id":1,"releases.cycles.name":1})
             
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

                screenTcDetails={}
                dts_data = {}

                for i in mindmap_data['testscenarios']:
                    temp1={
                        "condition": 0,
                        "dataparam": [""],
                        "scenarioId": str(i['_id']),
                        "scenarioName": i['testscenarioname']
                    }
                    suiteDetailsTemplate["suiteDetails"].append(temp1)
                
                    #creating template for testcase details
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

    def get_creds_path():
        currexc = sys.executable
        db_keys = "".join(['N','i','n','E','t','e','E','n','6','8','d','A','t','a','B',
                            'A','s','3','e','N','c','R','y','p','T','1','0','n','k','3','y','S'])    
        try: currfiledir = os.path.dirname(os.path.abspath(__file__))
        except: currfiledir = os.path.dirname(currexc)
        currdir = os.getcwd()
        if os.path.basename(currexc).startswith("AvoAssureDAS"):
            currdir = os.path.dirname(currexc)
        elif os.path.basename(currexc).startswith("python"):
            currdir = currfiledir
            needdir = "das_internals"
            parent_currdir = os.path.abspath(os.path.join(currdir,".."))
            if os.path.isdir(os.path.abspath(os.path.join(parent_currdir,"..",needdir))):
                currdir = os.path.dirname(parent_currdir)
            elif os.path.isdir(parent_currdir + os.sep + needdir):
                currdir = parent_currdir
        internalspath = currdir + os.sep + "das_internals"
        credspath = internalspath + os.sep + ".tokens"
        config_path = currdir + os.sep + "server_config.json"
        config = open(config_path, 'r')
        conf = json.load(config)
        config.close()
        mongo_client_path=currdir+os.sep+"mongoClient"
        if platform.system() == "Windows":                
            mongo_client_path =mongo_client_path + os.sep+"windows"
        else:
            mongo_client_path =mongo_client_path + os.sep+"linux"
        
        if ('DB_IP' in os.environ and 'DB_PORT' in os.environ):
            DB_IP = str(os.environ['DB_IP']) 
            DB_PORT=str(os.environ['DB_PORT'])
            mongo_user= unwrap(conf['avoassuredb']['username'],db_keys)
            mongo_pass= unwrap(conf['avoassuredb']['password'],db_keys)
            authDB= "admin"
        else:
            DB_IP=conf['avoassuredb']["host"]
            DB_PORT=conf['avoassuredb']["port"]
            with open(credspath) as creds_file:
                creds = json.loads(unwrap(creds_file.read(),db_keys))
            mongo_user=creds['avoassuredb']['username']
            mongo_pass =creds['avoassuredb']['password']
            authDB= "avoassure"
        exportImportpath=conf['exportImportpath']
        return mongo_client_path,DB_IP, DB_PORT,exportImportpath,mongo_user,mongo_pass,authDB

    #Export mindmap to git repository
    @app.route('/git/exportToGit',methods=['POST'])
    def exportToGit():
        app.logger.debug("Inside exportToGit")
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)       
                dbsession=client[clientName]
                del_flag = False
                git_details = dbsession.gitconfiguration.find_one({"gituser":ObjectId(requestdata["userid"]),"projectid":ObjectId(requestdata["projectId"])},{"giturl":1,"gitaccesstoken":1,"gitusername":1,"gituseremail":1})
                if not git_details:
                    res={'rows':'empty'}
                    return res

                # git_details = dbsession.gitconfiguration.find_one({"name":requestdata["gitname"],"gituser":ObjectId(requestdata["userid"]),"projectid":ObjectId(requestdata["projectId"])},{"giturl":1,"gitaccesstoken":1,"gitusername":1,"gituseremail":1})
                # if not git_details:
                #     res={'rows':'Invalid config name'}
                #     return res

                proj_details = dbsession.gitexportdetails.find({"projectid":ObjectId(requestdata["projectId"])}).count()
                repo_name = requestdata["projectName"]
                branch_name ="main"
                if proj_details <= 0:
                    api_url = "https://api.github.com"
                    access_token = unwrap(git_details['gitaccesstoken'], ldap_key)
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }

                    response = requests.get('https://api.github.com/user/repos', headers=headers)                    
                    repos=[]
                    if not response.status_code == 200:
                        if response.status_code == 401:
                            res = {'rows': "Invalid credentials"}
                            return res
                        else:
                            res={"rows":"Unable to fetch Repos"}
                            return res
                    repositories = response.json()                        
                    for repo in repositories:
                        repos.append(repo["name"])
                    if repo_name not in repos:
                        data = {
                            "name": repo_name,
                            "description": repo_name,
                            "private": True
                        }

                        response1 = requests.post(f"{api_url}/user/repos", headers=headers, json=data)

                        if not response1.status_code == 201:
                            if response.status_code == 401:
                                res = {'rows': "Invalid credentials"}
                                return res
                            else:                         
                                res={'rows':"Error creating repository"}
                                return res
                            
                        repository_info = response1.json()  
                        owner =repository_info["owner"]["login"]
                        file_path = "README.md"
                        commit_message = "Add README.md file"
                        date=datetime.now()
                        readme_content = requestdata["projectName"]+ " was created"

                        file_content = base64.b64encode(readme_content.encode("utf-8")).decode("utf-8")
                        data = {
                            "message": commit_message,
                            "content": file_content
                        }

                        url = f"{api_url}/repos/{owner}/{repo_name}/contents/{file_path}"
                        headers = {
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                        response2 = requests.put(url, headers=headers, json=data)

                        if not response2.status_code == 201:
                            if response.status_code == 401:
                                res = {'rows': "Invalid credentials"}
                                return res
                            else:
                                return res
                    else:
                        repository_info = response.json()
                        for name in  repository_info:
                            if name["name"] == repo_name: 
                                owner = name["owner"]["login"]
                                break                   
                        response3 = requests.get(f"{api_url}/repos/{owner}/{repo_name}/branches", headers=headers)

                        # Check if the request was successful (status code 200)
                        if not response3.status_code == 200:
                            if response.status_code == 401:
                                res = {'rows': "Invalid credentials"}
                                return res
                            else:
                                 return res
                        branches = response3.json()  # Parse the response as JSON
                        branch_names = [branch['name'] for branch in branches]
                        if not 'main' in branch_names:
                            file_path = "README.md"
                            commit_message = "Add README.md file"
                            date=datetime.now()
                            readme_content = requestdata["projectName"]+ " was created"

                            file_content = base64.b64encode(readme_content.encode("utf-8")).decode("utf-8")
                            data = {
                                "message": commit_message,
                                "content": file_content
                            }

                            url = f"{api_url}/repos/{owner}/{repo_name}/contents/{file_path}"
                            headers = {
                                "Authorization": f"Bearer {access_token}",
                                "Accept": "application/vnd.github.v3+json"
                            }
                            response4 = requests.put(url, headers=headers, json=data)

                            if not response4.status_code == 201:
                                if response.status_code == 401:
                                    res = {'rows': "Invalid credentials"}
                                    return res
                                else:
                                    return res
                 
                url=git_details["giturl"].split('://')                
                url=url[0]+'://'+unwrap(git_details['gitaccesstoken'], ldap_key)+':x-oauth-basic@'+url[1]+"/"+ repo_name+".git"
                
                #check whether cred is valid
                git_path=currdir+os.sep+'exportGit'+os.sep+requestdata["userid"]
                if(os.path.exists(git_path)): remove_dir(git_path)

                repo = git.Repo.init(git_path)
                repo.config_writer().set_value('user', 'email', git_details['gituseremail']).release()
                repo.config_writer().set_value('user', 'name', git_details['gitusername']).release()
                origin = repo.create_remote('origin',url)
                try:
                    origin.fetch()
                except:
                    res ={"rows":"unable to connect GIT"}
                    return res
                repo.git.checkout(branch_name)
                try:
                    repo.git.pull(ff=True)
                except:
                    res ={"rows":"unable to connect GIT"}
                    return res

                result = dbsession.gitexportdetails.find({"parent":git_details["_id"],"version":requestdata["gitVersion"]})
                index = result.count() - 1
                result=None
                if index >= 0:
                    res={'rows':'commit exists'}
                    return res
                elif result == None or result.count() == 0:
                    path=currdir+os.sep+"mindmapGit"+os.sep+requestdata["userid"]+os.sep+"main"
                    path=os.path.normpath(path)+os.sep

                    if(os.path.exists(path)): shutil.rmtree(path)
                    exportcheck=dbsession.Export_mindmap_git.find().count()
                    if exportcheck==0:
                        mindmapid = [ObjectId(i) for i in requestdata['moduleId']]                    
                        if len(mindmapid)>0:                            
                            mongoFile,DB_IP,DB_PORT,x,mongo_user,mongo_pass,authDB=get_creds_path()                        
                            mongoFile=mongoFile+os.sep+"mongoexport"
                            dbsession.Export_screens_git.drop()
                            dbsession.Export_testcases_git.drop()
                            dbsession.Export_dataobjects_git.drop()
                            dbsession.Export_testscenarios_git.drop()
                            dbsession.mindmaps.aggregate([{'$match': {"_id": {'$in':mindmapid}}},{"$out":"Export_mindmap_git"}])
                            dbsession.Export_mindmap_git.update_many({},{"$set":{"appType":requestdata["exportProjAppType"]}})
                            dbsession.testscenarios.aggregate([{'$match': {"parent": {'$in':mindmapid}}},
                            {"$out":"Export_testscenarios_git"}])
                            scenarioIds=list(dbsession.Export_testscenarios_git.aggregate( [
                                {"$group":{"_id":"null","scenarioids":{"$push":"$_id"}}}, 
                                {"$project":{"_id":0,"scenarioids":1}}
                                ] ))
                            if len(scenarioIds)>0:    
                                scenarios=scenarioIds[0]["scenarioids"]
                                dbsession.screens.aggregate([{'$match': {"parent": {'$in':scenarios}}},{"$out":"Export_screens_git"}])
                                screenIds=list(dbsession.Export_screens_git.aggregate( [
                                    {"$group":{"_id":"null","screenids":{"$push":"$_id"}}}, 
                                    {"$project":{"_id":0,"screenids":1}}
                                    ] ))
                                if len(screenIds)>0:  
                                    screens=screenIds[0]["screenids"]  
                                    dbsession.testcases.aggregate([{'$match': {"screenid": {'$in':screens}}},
                                        {"$out":"Export_testcases_git"}])
                                    dbsession.dataobjects.aggregate([{'$match': {"parent": {'$in':screens}}}
                                        ,{"$out":"Export_dataobjects_git"}])

                            
                            p=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_mindmap_git -o {}{}Modules  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,path,os.sep))
                            q=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_testscenarios_git -o {}{}Testscenarios  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,path,os.sep))
                            r=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_screens_git -o {}{}screens  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,path,os.sep))
                            s=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_testcases_git -o {}{}Testcases --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,path,os.sep))
                            t=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection Export_dataobjects_git -o {}{}Dataobjects  --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,path,os.sep))
                            dbsession.Export_mindmap_git.drop()
                            dbsession.Export_screens_git.drop()
                            dbsession.Export_testcases_git.drop()
                            dbsession.Export_dataobjects_git.drop()
                            dbsession.Export_testscenarios_git.drop()

                            res = exportdataToGit(dbsession,path, requestdata, origin, repo, repo_name)
                        else:
                            app.logger.warn('Empty data received.')
                    else:
                        res ={"rows":"InProgress"}
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
            dbsession.Export_mindmap_git.drop()
            dbsession.Export_screens_git.drop()
            dbsession.Export_testcases_git.drop()
            dbsession.Export_dataobjects_git.drop()
            dbsession.Export_testscenarios_git.drop()
            servicesException("exportToGit", ex, True)
        # remove_dir(git_path)
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

    def exportdataToGit(dbsession,dirpath, result, origin, repo,repo_name):
        app.logger.debug("Inside exportdataToGit")
        res={'rows':'fail'}
        delpath=None
        git_path=None
        try:
            module_data=result
            delpath=currdir+os.sep+"mindmapGit"
            data={}
            if not isemptyrequest(module_data):
                git_details = dbsession.gitconfiguration.find_one({"gituser":ObjectId(module_data["userid"]),"projectid":ObjectId(module_data["projectId"])},{"_id":1})

                git_path=currdir+os.sep+'exportGit'+os.sep+module_data["userid"]
                final_path=os.path.normpath(git_path+os.sep+"main")

                if(os.path.exists(final_path)):
                    if os.path.exists(dirpath):
                        shutil.rmtree(final_path)
            
                shutil.move(dirpath, final_path)
                # Add mimdmap file to remote repo
                repo.git.add(final_path)
                repo.index.commit(module_data["gitVersion"])
                try:
                    repo.git.push()
                except:
                    res ={"rows":"unable to connect GIT"}
                    return res
                # get the commit id and save it in gitexportdetails
                for i in range(len(origin.refs)):
                    if(origin.refs[i].remote_head=="main"):
                        commit_id = origin.refs[i].commit.hexsha
                        break

                data["userid"] = ObjectId(module_data["userid"])
                data["projectid"] = ObjectId(module_data["projectId"])
                data["branchname"] = "main"
                data["folderpath"] = "main"
                data["version"] = module_data["gitVersion"]
                data["parent"] = git_details["_id"]
                data["commitid"] = commit_id
                data["commitmessage"] = module_data["gitComMsgRef"]
                data["projectname"] = repo_name
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
                clientName=getClientName(requestdata)        
                dbsession=client[clientName]
                expProj=ObjectId(requestdata["expProj"])
                projectid=ObjectId(requestdata["projectid"])
                # gitname = requestdata["gitname"]
                # gitBranch = requestdata["gitbranch"]
                gitVersionName = requestdata["gitversion"]
                # gitFolderPath = requestdata["gitfolderpath"]
                role = requestdata["roleid"]
                userid = requestdata["userid"]
                appType=requestdata["appType"]
                projectName=requestdata["projectName"]
                
                git_data = dbsession.gitconfiguration.find_one({"projectid":projectid},{"gituser":1,"giturl":1,"gitaccesstoken":1})
                if not git_data:
                    # git_data = list(dbsession.gitconfiguration.find({"name":gitname},{"_id":1}))
                    # if len(git_data) > 0:
                    #     res = {'rows': "No entries"}                        
                    # else:
                    res={'rows': "empty"}                        
                else:    
                    result = dbsession.gitexportdetails.find_one({"projectid":expProj,"version":gitVersionName},{"commitid":1,"projectname":1})
                    if not result:
                        res = {'rows': "Invalid inputs"}                   
                        
                    else:
                        git_path=currdir+os.sep+'exportGit'+os.sep+str(userid)
                        final_path=os.path.normpath(git_path)+os.sep+"main"                                    
                        if(os.path.isdir(git_path)): remove_dir(git_path)
                        url=git_data["giturl"].split('://')
                        url=url[0]+'://'+unwrap(git_data["gitaccesstoken"], ldap_key)+':x-oauth-basic@'+url[1]+"/"+result["projectname"]+".git"                       
                        repo = git.Repo.clone_from(url, git_path,no_checkout=True)
                        repo.git.checkout(result['commitid'])

                        importMindmapcheck= dbsession.git_Module_Import.find({}).count()
                        if importMindmapcheck==0:                    
                            dbsession.git_Screen_Import.drop()
                            dbsession.git_Scenario_Import.drop()
                            dbsession.git_Testcase_Import.drop()
                            dbsession.git_Dataobjects_Import.drop()
                            dbsession.git_mindmap_testscenarios_Import.drop()
                            dbsession.git_scenario_testcase_Import.drop()
                            dbsession.git_screen_parent_Import.drop()
                            dbsession.git_testcase_parent_Import.drop()
                            dbsession.git_dobjects_parent_Import.drop()
                            dbsession.git_Module_Import_ids.drop()
                            dbsession.git_Scenario_Import_ids.drop()
                            dbsession.git_Scenario_Import_tc.drop()
                            dbsession.git_Screen_Import_ids.drop()
                            dbsession.git_Testcase_Import_ids.drop()                    
                            dbsession.git_testcase_steps.drop()                                                          
                                                                
                            createdon = datetime.now()                   
                            
                            mongoFile,DB_IP,DB_PORT,x,mongo_user,mongo_pass,authDB=get_creds_path()                                    
                            mongoFile=mongoFile+os.sep+"mongoimport"
                            do=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection git_Dataobjects_Import --file {}{}Dataobjects --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,final_path,os.sep))
                            mm=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection git_Module_Import --file {}{}Modules --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,final_path,os.sep))
                            ts=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection git_Scenario_Import --file {}{}Testscenarios --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,final_path,os.sep))
                            sr=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection git_Screen_Import --file {}{}screens --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,final_path,os.sep))
                            tc=os.system("{} --host {} --port {} --db {} --username {} --password {} --authenticationDatabase {} --collection git_Testcase_Import --file {}{}Testcases --jsonArray".format(mongoFile,DB_IP,DB_PORT,clientName,mongo_user,mongo_pass,authDB,final_path,os.sep))                            
                            importappType=dbsession.git_Module_Import.find_one({},{"appType":1})
                            if appType != importappType["appType"]:
                                dbsession.git_Module_Import.drop()
                                dbsession.git_Screen_Import.drop()
                                dbsession.git_Scenario_Import.drop()
                                dbsession.git_Testcase_Import.drop()
                                dbsession.git_Dataobjects_Import.drop()
                                res={'rows': "appType"}
                            else:
                                dbsession.git_Module_Import.aggregate([
                                {"$project":{"_id":0,"old_id":"$_id",
                                        "name":1,
                                        "projectid":projectid,
                                        "versionnumber":1 ,
                                        "createdby":userid,
                                        "createdbyrole":role,
                                        "createdthrough":1,
                                        "type":"basic",
                                        "createdon":createdon,
                                        "deleted":1,
                                        "modifiedby":userid,
                                        "modifiedbyrole":role,
                                        "modifiedon":createdon,
                                        "tsIds":"$testscenarios"}},{"$out":"git_Module_Import"}
                                ])
                                
                                duplicatemod=list(dbsession.git_Module_Import.aggregate([
                                            {"$group" : { "_id": "$name", "count": { "$sum": 1 } } },
                                            {"$match": {"_id" :{ "$ne" : "null" } , "count" : {"$gt": 1} } }, 
                                            {"$project": {"name" : "$_id", "_id" : 0} }
                                        ]))
                                if len(duplicatemod)>0:
                                    dbsession.git_Module_Import.drop()
                                    dbsession.git_Screen_Import.drop()
                                    dbsession.git_Scenario_Import.drop()
                                    dbsession.git_Testcase_Import.drop()
                                    dbsession.git_Dataobjects_Import.drop()
                                    res={'rows': "dupMod"}
                                else:
                                    dbsession.git_Scenario_Import.aggregate([{"$project":{"_id":0,
                                                        "old_id":"$_id",
                                                        "name":1,
                                                        "projectid":projectid,
                                                        "old_parent":"$parent" ,
                                                        "versionnumber":1 ,
                                                        "createdby":userid,
                                                        "createdbyrole":role,
                                                        "createdon":createdon,
                                                        "deleted":1,
                                                        "modifiedby":userid,
                                                        "modifiedbyrole":role,
                                                        "modifiedon":createdon,
                                                        "testcaseids":1}},{"$out":"git_Scenario_Import"}])
                                    duplicatesce=list(dbsession.git_Scenario_Import.aggregate([
                                                {"$group" : { "_id": "$name", "count": { "$sum": 1 } } },
                                                {"$match": {"_id" :{ "$ne" : "null" } , "count" : {"$gt": 1} } }, 
                                                {"$project": {"name" : "$_id", "_id" : 0} }
                                            ]))
                                    if len(duplicatesce)>0:
                                        dbsession.git_Module_Import.drop()
                                        dbsession.git_Screen_Import.drop()
                                        dbsession.git_Scenario_Import.drop()
                                        dbsession.git_Testcase_Import.drop()
                                        dbsession.git_Dataobjects_Import.drop()
                                        res={'rows': "dupSce"}
                                    else:
                                        dbsession.git_Screen_Import.aggregate([{"$project":{
                                                                "_id":0,
                                                                "old_id":"$_id",
                                                                "name":1,
                                                                "projectid":projectid,
                                                                "old_parent":"$parent",
                                                                "versionnumber":1 ,
                                                                "createdby":userid,
                                                                "createdbyrole":role,
                                                                "createdon":createdon,
                                                                "deleted":1,
                                                                "modifiedby":userid,
                                                                "modifiedbyrole":role,
                                                                "modifiedon":createdon,
                                                                "screenshot":1,
                                                                "scrapedurl":1,
                                                                "orderlist":1}},{"$out":"git_Screen_Import"}])
                                        
                                        dbsession.git_Testcase_Import.aggregate([{"$project":{
                                                                "_id":0,
                                                                    "old_id":"$_id",
                                                                "name":1,
                                                                "old_screenid":"$screenid" ,
                                                                "versionnumber":1 ,
                                                                "createdby":userid,
                                                                "createdbyrole":role,
                                                                "createdon":createdon,
                                                                "deleted":1,
                                                                "modifiedby":userid,
                                                                "modifiedbyrole":role,
                                                                "parent":1,
                                                                "modifiedon":createdon,
                                                                "steps":1,
                                                                "projectid":projectid,
                                                                "datatables":1
                                                                }},{"$out":"git_Testcase_Import"}])
                                        
                                
                                        dbsession.git_Dataobjects_Import.aggregate( [
                                        
                                    
                                        {"$set":{"old_id":"$_id","old_parent" :"$parent"}},
                                        
                                        { "$project": {"_id":0,"parent":0
                                                } },
                                        {"$out":"git_Dataobjects_Import"}])
                                    
                                    
                                        dbsession.git_Module_Import.aggregate([{"$project":{"_id":1,"tsIds":1}},{"$out":"git_Module_Import_ids"}])
                                        mindmapIds=list(dbsession.git_Module_Import_ids.find({}))
                                        dbsession.git_Scenario_Import.aggregate([{"$project":{"_id":1,"old_id":1,"testcaseids":1}},{"$out":"git_Scenario_Import_ids"}])
                                        ScenarioIds=list(dbsession.git_Scenario_Import_ids.find({}))
                                        dbsession.git_Screen_Import.aggregate([{"$project":{"_id":1,"old_id":1,"old_parent":1}},{"$out":"git_Screen_Import_ids"}])
                                        screenIds=list(dbsession.git_Screen_Import_ids.find({}))
                                        dbsession.git_Testcase_Import.aggregate([{"$project":{"_id":1,"old_id":1,"name":1,"old_screenid":1}},{"$out":"git_Testcase_Import_ids"}])
                                        testcaseIds=list(dbsession.git_Testcase_Import_ids.find({}))
                                        

                                        mindmapId=list(dbsession.git_Module_Import_ids.find({},{"_id":1}))                               

                                        dbsession.git_Dataobjects_Import.aggregate([{"$lookup":{"from":"git_Screen_Import",
                                            "localField":"old_parent",
                                            "foreignField":"old_id",
                                            "as":"screens"}},{"$group":{"_id":"$_id","parent":{"$push":"$screens._id"}}},{"$unwind":"$parent"},{"$out":"git_dobjects_parent_Import"}])
                                    

                                        for i in mindmapIds:
                                            if "tsIds" in i:
                                                for tsId in i["tsIds"]:
                                                    for j in ScenarioIds:
                                                        if tsId["_id"]==j["old_id"]:
                                                            tsId["_id"]=j["_id"]
                                                            break
                                        
                                        for i in mindmapIds:
                                            if "tsIds" in i:
                                                for tsId in i["tsIds"]:
                                                    if "screens" in tsId:
                                                        for screens in tsId["screens"]:
                                                            for k in screenIds:
                                                                if "_id" in screens:
                                                                    if screens["_id"]==k["old_id"]:
                                                                        screens["_id"]=k["_id"]
                                                                        break
                                        
                                        mdmaptscen=[]
                                        for i in mindmapIds:                                               
                                            if "tsIds" in i:
                                                for tsId in i["tsIds"]:                           
                                                    if "screens" in tsId:
                                                        for screens in tsId["screens"]:
                                                            testcases=[]
                                                            if "testcases" in screens:
                                                                for testcase in screens["testcases"]:
                                                                    if testcase:
                                                                        for l in testcaseIds:
                                                                            if testcase == l["old_id"]:                                                             
                                                                                testcases.append(l["_id"])
                                                                                break
                                                                        del testcase
                                                                screens["testcases"]=[]
                                                                screens["testcases"].append(testcases)
                                                                screens["testcases"]=screens["testcases"][0]
                                                                        


                                        mycoll=dbsession["git_mindmap_testscenarios_Import"]
                                        dbsession.git_mindmap_testscenarios_Import.delete_many({})
                                        if len(mindmapIds)>0:
                                            dbsession.git_mindmap_testscenarios_Import.insert_many(mindmapIds)
                                        dbsession.git_Scenario_Import_ids.aggregate([{'$lookup': {
                                                                    'from': "git_Testcase_Import_ids",
                                                                    'localField': "testcaseids",
                                                                    'foreignField': "old_id",
                                                                    'as': "testcases"
                                            }},
                                            {"$unwind":"$testcaseids"},{"$set": { "testcases":{ "$cond": [{"$eq": [{"$size": '$testcases'}, 0] }, [[]], '$testcases'] }}},{"$unwind":"$testcases"}, 
                                            {"$set":{"testcaseids":{ "$cond": { "if": { "$ne": ["$testcaseids" , "$testcases.old_id" ] }, "then":"na", "else": "$testcases._id"} }}},
                                            {"$group":{"_id":"$_id","testcaseids":{"$push":"$testcaseids"}}}, {"$out":"git_scenario_testcase_Import"}
                                            ])
                                        dbsession.git_scenario_testcase_Import.update_many({},{"$pull": {"testcaseids":"na"}})
                                        
                                        
                                        screenParent=[]
                                        for i in screenIds:
                                            nestarray={"_id":"","parent":[]}
                                            nestarray["_id"]=i["_id"]
                                            currentscreenidparent=i["_id"]                      
                                            for j in i["old_parent"]:
                                                for ts in ScenarioIds:
                                                    if j==ts["old_id"]:
                                                        nestarray["parent"].append(ts["_id"])
                                                        break
                                            screenParent.append(nestarray)
                                        
                                        mycoll=dbsession["git_screen_parent_Import"]
                                        dbsession.git_screen_parent_Import.delete_many({})
                                        if len(screenParent)>0:
                                            dbsession.git_screen_parent_Import.insert_many(screenParent)
                                        
                                        dbsession.git_Dataobjects_Import.aggregate([
                                            {'$lookup': {
                                                        'from': "git_dobjects_parent_Import",
                                                        'localField': "_id",
                                                        'foreignField': "_id",
                                                        'as': "parentdobs"
                                                        }
                                                                },{"$set":{"parent":"$parentdobs.parent"}},{"$unwind":"$parent"},
                                            { "$project" : {"parentdobs":0}},{"$out":"git_Dataobjects_Import"}
                                                        ])

                                        dbsession.git_Module_Import.aggregate([
                                            {"$match":{"tsIds":{"$exists":"true"},"projectid":projectid}},
                                            {'$lookup': {
                                                                    'from': "git_mindmap_testscenarios_Import",
                                                                    'localField': "_id",
                                                                    'foreignField': "_id",
                                                                    'as': "mindmapscenariodata"
                                                                }
                                                                },{"$set":{"testscenarios":"$mindmapscenariodata.tsIds"}},{"$unwind":"$testscenarios"},
                                            { "$project" : {"mindmapscenariodata":0,"tsIds":0}},{"$out":"git_Module_Import"}
                                                        ])
                                                            
                                        dbsession.git_Scenario_Import.aggregate([
                                                                {'$match': {"projectid":projectid,"testcaseids.0": {"$exists": "true"}}},
                                                                
                                                                {'$lookup': {
                                                                    'from': "git_scenario_testcase_Import",
                                                                    'localField': "_id",
                                                                    'foreignField': "_id",
                                                                    'as': "scentestcasedata"
                                                                }
                                                                },{"$set":{"testcaseids" :"$scentestcasedata.testcaseids"}},                                                                                    
                                                                {"$unwind":"$testcaseids"},
                                                                { "$project" : {  "scentestcasedata":0,}},                                                        
                                                                {'$out':"git_Scenario_Import_tc"}
                                                                ])
                                        dbsession.git_Scenario_Import.aggregate([{'$lookup': {
                                                                    'from': "git_Module_Import",
                                                                    'localField': "old_parent",
                                                                    'foreignField': "old_id",
                                                                    'as': "moduledata"
                                                                }
                                                                },{"$set":{"parent" : "$moduledata._id"}},{ "$project" : { "moduledata":0}},
                                                                {'$out':"git_Scenario_Import"} ])
                                        dbsession.git_Scenario_Import_tc.aggregate([
                                        {"$merge":{"into":"git_Scenario_Import","on":"_id","whenMatched": [{
                                            "$set": {"testcaseids": '$$new.testcaseids'}}]}}]) 

                                        dbsession.git_Screen_Import.aggregate([
                                            {'$lookup': {
                                                                    'from': "git_screen_parent_Import",
                                                                    'localField': "_id",
                                                                    'foreignField': "_id",
                                                                    'as': "scrparent"
                                                                }},
                                                                {'$lookup': {
                                                                    'from': "git_Dataobjects_Import",
                                                                    'localField': "old_id",
                                                                    'foreignField': "old_parent",
                                                                    'as': "dataobjects"
                                                                }
                                                                },
                                                                {"$set":{"parent" : "$scrparent.parent",
                                                                "orderlist":{"$map": {
                                                                                    "input": "$dataobjects._id",
                                                                                    "as": "r",
                                                                                    "in": { "$toString": "$$r" }
                                                                                    }}
                                                                                    }},{"$unwind":"$parent"},
                                                                { "$project" : { "scrparent":0,
                                                                "dataobjects":0
                                                                                }},{"$out":"git_Screen_Import"}

                                        ])
                                        ImportedData=dbsession.git_Module_Import.aggregate([{"$project":{"_id":1,"testscenarios":1}},{"$out":"git_Module_Import_ids"}])
                                        mindmapId=list(dbsession.git_Module_Import_ids.find({},{"_id":1}))
                                        queryresult=[]
                                        for i in mindmapId:
                                            queryresult.append(i["_id"])
                                        moduleids=list(dbsession.git_Module_Import_ids.find({}))
                                        testcaseparent=[]                    
                                        testcaseids=[]                   
                                        for i in moduleids:
                                            if i["testscenarios"] and len(i["testscenarios"])>0:
                                                for j in i["testscenarios"]:
                                                    if j["screens"] and len(j["screens"])>0:
                                                        for k in j["screens"]:
                                                            if k["testcases"] and len(k["testcases"])>0:                                
                                                                for testcase in k["testcases"]:
                                                                        array3={"_id":"","parent":[]}                                    
                                                                        if testcase in testcaseids:                                            
                                                                            for q in testcaseparent:
                                                                                if q["_id"] == testcase:                                                    
                                                                                    parentinc=q["parent"]
                                                                                    parentinc=parentinc+1
                                                                                    q["parent"] = parentinc                                                                                            
                                                                                else:
                                                                                    continue                         
                                                                        else:                                            
                                                                            testcaseids.append(testcase)
                                                                            array3["_id"]=testcase								
                                                                            array3["parent"]=1
                                                                            testcaseparent.append(array3)

                                        mycoll=dbsession["git_testcase_parent_Import"]
                                        dbsession.git_testcase_parent_Import.delete_many({})
                                        if len(testcaseparent)>0:
                                            dbsession.git_testcase_parent_Import.insert_many(testcaseparent)
                                        dbsession.git_Testcase_Import.aggregate([
                                                                {"$match":{"old_screenid":{"$exists":"true"},"projectid":projectid}},
                                                                {'$lookup': {
                                                                    'from': "git_Screen_Import",
                                                                    'localField': "old_screenid",
                                                                    'foreignField': "old_id",
                                                                    'as': "screendata"
                                                                }},{'$lookup': {
                                                                    'from': "git_testcase_parent_Import",
                                                                    'localField': "_id",
                                                                    'foreignField': "_id",
                                                                    'as': "tcparent"
                                                                }},{"$unwind":"$tcparent"},
                                                                {"$unwind":"$screendata"},{'$set': {'parent': { "$convert": { "input": "$tcparent.parent", "to": "int" } }
                                                                ,"screenid":"$screendata._id"}},
                                                                { "$project" : {"screendata":0,"tcparent":0}},
                                                                    {"$out":"git_Testcase_Import"}
                                                                    ])
                                    
                                        dbsession.git_Testcase_Import.aggregate([{"$match":{"steps.0": {"$exists": "true"}}},{"$unwind":"$steps"},
                                                                {'$lookup': {
                                                                    'from': "git_Dataobjects_Import",
                                                                    'localField': "steps.custname",
                                                                    'foreignField': "old_id",
                                                                    'as': "dbobjects"
                                                                }},
                                                                {"$set": { "dbobjects":{ "$cond": [{"$eq": [{"$size": '$dbobjects'}, 0] }, [[]], '$dbobjects'] }}},{"$unwind":"$dbobjects"}, 
                                                                {"$set":{"steps.custname":{ "$cond": { "if": { "$ne": ["$steps.custname" , "$dbobjects.old_id" ] }, "then":"$steps.custname", "else": "$dbobjects._id"} }}},
                                                                {"$group":{"_id":"$_id","steps":{"$push":"$steps"}}},{"$out":"git_testcase_steps"}
                                                                ], allowDiskUse= True) 

                                        dbsession.git_testcase_steps.aggregate([
                                        {"$merge":{"into":"git_Testcase_Import","on":"_id","whenMatched": [{
                                            "$set": {"steps": '$$new.steps'}}]}}])                   
                                                    
                                        
                                        dbsession.git_Module_Import.aggregate([{"$unset":["tsIds","old_id"]},{"$out":"git_Module_Import"}])
                                        dbsession.git_Scenario_Import.aggregate([{"$unset":["old_id","old_parent","screens"]},{"$out":"git_Scenario_Import"}])
                                        dbsession.git_Screen_Import.aggregate([{"$unset":["old_id","old_parent","testcases"]},{"$out":"git_Screen_Import"}])
                                        dbsession.git_Testcase_Import.aggregate([{"$unset":["old_id","old_screenid","projectid"]},{"$out":"git_Testcase_Import"}])
                                        dbsession.git_Dataobjects_Import.aggregate([{"$unset":["old_id","old_parent"]},{"$out":"git_Dataobjects_Import"}])

                                        dbsession.git_Module_Import.aggregate([                                            
                                        {'$match': {"projectid":projectid}},
                                        {"$merge":{"into":"mindmaps","on":"_id","whenNotMatched":"insert"}}])                                            
                                        dbsession.git_Screen_Import.aggregate([
                                        {'$match': {"projectid":projectid}},
                                        {"$merge":{"into":"screens","on":"_id","whenNotMatched":"insert"}}])
                                        dbsession.git_Scenario_Import.aggregate([
                                        {'$match': {"projectid":projectid}},
                                        {"$merge":{"into":"testscenarios","on":"_id","whenNotMatched":"insert"}}])
                                        dbsession.git_Testcase_Import.aggregate([
                                        {"$merge":{"into":"testcases","on":"_id","whenNotMatched":"insert"}}])
                                        dbsession.git_Dataobjects_Import.aggregate([
                                        {"$merge":{"into":"dataobjects","on":"_id","whenNotMatched":"insert"}}])

                                        dbsession.git_Module_Import.drop()
                                        dbsession.git_Screen_Import.drop()
                                        dbsession.git_Scenario_Import.drop()
                                        dbsession.git_Testcase_Import.drop()
                                        dbsession.git_Dataobjects_Import.drop()
                                        dbsession.git_mindmap_testscenarios_Import.drop()
                                        dbsession.git_scenario_testcase_Import.drop()
                                        dbsession.git_screen_parent_Import.drop()
                                        dbsession.git_testcase_parent_Import.drop()
                                        dbsession.git_dobjects_parent_Import.drop()
                                        dbsession.git_Module_Import_ids.drop()
                                        dbsession.git_Scenario_Import_ids.drop()
                                        dbsession.git_Scenario_Import_tc.drop()
                                        dbsession.git_Screen_Import_ids.drop()
                                        dbsession.git_Testcase_Import_ids.drop()                    
                                        dbsession.git_testcase_steps.drop()
                                            
                                        
                                        if queryresult:
                                                res={'rows':queryresult}                
                
                        else:
                            res={'rows': "InProgress"}
            else:
                app.logger.warn('Empty data received.')
        except Exception as ex:
            dbsession.git_Module_Import.drop()
            dbsession.git_Screen_Import.drop()
            dbsession.git_Scenario_Import.drop()
            dbsession.git_Testcase_Import.drop()
            dbsession.git_Dataobjects_Import.drop()
            dbsession.git_mindmap_testscenarios_Import.drop()
            dbsession.git_scenario_testcase_Import.drop()
            dbsession.git_screen_parent_Import.drop()
            dbsession.git_testcase_parent_Import.drop()
            dbsession.git_dobjects_parent_Import.drop()
            dbsession.git_Module_Import_ids.drop()
            dbsession.git_Scenario_Import_ids.drop()
            dbsession.git_Scenario_Import_tc.drop()
            dbsession.git_Screen_Import_ids.drop()
            dbsession.git_Testcase_Import_ids.drop()                    
            dbsession.git_testcase_steps.drop()
            servicesException("importGitMindmap", ex, True)
        # remove_dir(git_path)
        return res

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
        adddataobjects(dbsession,scrid, custnameToAdd)

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
    
    @app.route('/git/checkExportName',methods=['POST'])
    def checkExportName():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside checkExportName.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)             
                dbsession=client[clientName]                
                expName=list(dbsession.gitexportdetails.find({"projectid":ObjectId(requestdata["projectId"])},{"commitmessage":1,"version":1,"_id":0}))
                if requestdata["query"] =="exportgit":
                    ver=[]
                    for version in expName:
                        ver.append(version["version"])                
                    res={"rows":ver}
                else:
                    res={"rows": expName}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as checkExportNameexc:
            servicesException("checkExportName",checkExportNameexc, True)
        return jsonify(res)
    
    