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
                commitId = dbsession.gitexpimpdetails.find_one({'gittask':'push','branchname':gitbranch,'folderpath':moduleName,'version':versionName, "parent":gitconfig_data['_id']},{"commitid":1})
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

    def create_new_repo(repo_name,api_url,headers,projectName,param,workspace,projectkey):
        try:
            if param=="git":
                data = {
                    "name": repo_name,
                    "description":projectName ,
                    "private": True
                }
                new_repo_response = requests.post(f"{api_url}/user/repos", headers=headers, json=data)
                if not new_repo_response.status_code == 201:
                    if new_repo_response.status_code == 401:
                        res =  "Invalid token"
                        return new_repo_response,res
                    else:
                        app.logger.error(new_repo_response.status_code)                         
                        res="Unable to connect "+param
                        return new_repo_response,res
                else:
                    res="success"
                    return new_repo_response,res
            else:
                data = {
                "scm": "git",
                "project": {
                    "key": projectkey
                },
                "is_private": True,
                "description": projectName
                }
                new_repo_response = requests.post(f"{api_url}/repositories/{workspace}/{repo_name}", json=data, headers=headers)

            
                if not new_repo_response.status_code == 200:
                    if new_repo_response.status_code == 403:
                        res =  "Invalid token"
                        return new_repo_response,res
                    elif new_repo_response.status_code == 404:
                        res= "The project might not exist, or you don't have permission to create a repository in the project."
                        return new_repo_response,res
                    else:
                        app.logger.error(new_repo_response.status_code)                         
                        res="Unable to connect "+param
                        return new_repo_response,res
                else:
                    res="success"
                    return new_repo_response,res
        except Exception as e:
           raise ValueError("Error occurred in create_new_repo",e)

    def create_main_branch(projectName,owner,repo_name,api_url,access_token,param,workspace) :       
        try: 
            file_path = "README.md"
            commit_message = "Add README.md file"
            date=datetime.now()
            readme_content = projectName+ " was created" 
            file_content = base64.b64encode(readme_content.encode("utf-8")).decode("utf-8")
            data = {
                "message": commit_message,
                "content": file_content
            }
            headers = {
                "Authorization": f"Bearer {access_token}",
                # "Accept": "application/vnd.github.v3+json"
            }
            if param =="git":
                url = f"{api_url}/repos/{owner}/{repo_name}/contents/{file_path}"
                main_branch_response = requests.put(url, headers=headers, json=data) 
            else:
                commit_url = f"{api_url}/repositories/{workspace}/{repo_name}/src"                
                payload = {
                    "message": "Add README.md file",
                    "branch": "main",
                    "content": readme_content 
                    }
                headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                main_branch_response = requests.post(commit_url, data=payload, headers=headers)                     
            if not main_branch_response.status_code == 201:
                if main_branch_response.status_code == 401:
                    res =  "Invalid token"
                    return res
                else:
                    app.logger.error(main_branch_response.status_code)
                    res="Unable to connect "+param
                    return res
            else:
                res="success"
                return res
        except Exception as e:
           raise ValueError("Error occurred in create_main_branch",e)

    def create_requested_branch(origin,repo,export_branch,param):
        try:
            commit=""
            for i in range(len(origin.refs)):
                if(origin.refs[i].remote_head=="main"):
                    commit = origin.refs[i].commit.hexsha
                    break
            new_branch =repo.create_head(export_branch, commit=commit)
            # Checkout the newly created branch
            repo.git.checkout(new_branch)
            repo.git.fetch('origin')
            upstream_branch = 'origin/main'         
            repo.git.branch(f"--set-upstream-to={upstream_branch}", export_branch)  
            try:
                repo.git.pull(ff=True)
            except Exception as e:
                app.logger.error(e)
                res ={"rows":"Unable to connect "+param}
                return res
            return repo
        except Exception as e:
           raise ValueError("Error occurred in create_requested_branch",e)

    def get_repo_details(headers,param,workspace):
        try:
            if param =="git":
                response = requests.get('https://api.github.com/user/repos', headers=headers, verify=False)                    
                repos=[]
                if response.status_code ==200:
                    repositories = response.json()
                    response=response.json()
                    for repo in repositories:
                        repos.append(repo["name"])
                    res="success"
                    return repos,response,res
            elif param=="bit":                
                url = f'https://api.bitbucket.org/2.0/repositories/{workspace}'
                response = requests.get(url, headers=headers, verify=False)                    
                repos=[]                
                if response.status_code == 200:
                    repositories = response.json()['values']
                    response = response.json()['values']
                    for repo in repositories:
                        repos.append(repo["name"])
                    res="success"
                    return repos,response,res
            if not response.status_code == 200:
                if response.status_code == 401:
                    res = "Invalid token"
                    return repos,response,res
                else:
                    app.logger.error("error occured while fetching the repositories from GITHUB ",response.status_code)                         
                    res="Unable to connect "+param
                    return repos,response,res               
        except Exception as e:
           raise ValueError("Error occurred in get_repo_details",e)

    def get_branch_name(owner,repo_name,api_url,headers,param,workspace):
        try:            
            if owner:
                if param=="git":                           
                    branch_response = requests.get(f"{api_url}/repos/{owner}/{repo_name}/branches", headers=headers)
                    if branch_response.status_code == 200:
                        branches = branch_response.json()
                        branch_names = [branch['name'] for branch in branches]
                        res="success"
                        return res,branch_names
                else:
                    branch_response = requests.get(f"{api_url}/repositories/{workspace}/{repo_name}/refs/branches" , headers=headers)
                    if branch_response.status_code == 200:
                        branches = branch_response.json()["values"]
                        branch_names = [branch['name'] for branch in branches]
                        res="success"
                        return res,branch_names
                if not branch_response.status_code == 200:
                    if branch_response.status_code == 401:
                        res = "Invalid token"
                        branch_names=[]
                        return res,branch_names
                    else:
                        app.logger.error(branch_response)                         
                        res="Unable to connect "+param
                        branch_names=[]
                        return res,branch_names           
            else:
                res=200
                branch_names=[] 
                return res,branch_names
        except Exception as e:
           raise ValueError("Error occurred in get_branch_name",e)

    def get_owner_info(response,repo_name,param):
        try:            
            owner=""            
            if isinstance(response, list):
                for name in  response:
                    if name["name"] == repo_name:
                        if param=="git": 
                            owner = name["owner"]["login"]
                        else:
                            owner = name["owner"]["username"]
                        break
            else:                
                if param=="git":
                    repository_info = response.json()
                    if repository_info["name"]==repo_name: 
                        owner = repository_info["owner"]["login"]
                else:
                    repository_info = response.json()["values"]
                    if repository_info["name"]==repo_name:
                        owner = repository_info["owner"]["username"]  
            return owner
        except Exception as e:
           raise ValueError("Error occurred in get_owner_info",e)
    
    #Export mindmap to git repository
    @app.route('/git/exportToGit',methods=['POST'])
    def exportToGit():
        app.logger.debug("Inside exportToGit")
        res={'rows':'fail'}
        git_path=None
        try:            
            requestdata=json.loads(request.data)
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)       
                dbsession=client[clientName]
                del_flag = False                               
                param=requestdata["param"]                
                if param=="git":
                    check_gitbranch=list(dbsession.gitconfiguration.find({"gitbranch":{"$exists":False}}))
                    if len(check_gitbranch)>0:
                        dbsession.gitconfiguration.update_many({},{"$set":{"gitbranch":"main"}})
                    git_details = dbsession.gitconfiguration.find_one({"gituser":ObjectId(requestdata["userid"]),"projectid":ObjectId(requestdata["projectId"])},{"giturl":1,"gitaccesstoken":1,"gitusername":1,"gituseremail":1,
                    "gitbranch":1
                    })
                    if not git_details:
                        res={'rows':'empty'}
                        return res
                    proj_details = dbsession.gitexpimpdetails.find_one({"gittask":"push","projectid":ObjectId(requestdata["projectId"])},{"repoName":1})
                    if proj_details:
                        repo_name=proj_details["repoName"]
                    else:
                        repo_name= str(requestdata["projectId"])
                    workspace=None
                    projectkey=None
                    export_branch=git_details["gitbranch"]
                    api_url = "https://api.github.com"
                    access_token = unwrap(git_details["gitaccesstoken"], ldap_key)
                    url=git_details["giturl"].split('://')                             
                    url=url[0]+'://'+access_token+':x-oauth-basic@'+url[1]+"/"+ repo_name+".git"
                else:                                
                    bit_details = dbsession.bitconfiguration.find_one({"bituser":ObjectId(requestdata["userid"]),"projectid":ObjectId(requestdata["projectId"])},{"biturl":1,"bitaccesstoken":1,"bitusername":1,"workspace":1,
                    "bitbranch":1,"projectkey":1
                    })
                    if not bit_details:
                        res={'rows':'empty'}
                        return res
                    proj_details = dbsession.bitexpimpdetails.find_one({"bittask":"push","projectid":ObjectId(requestdata["projectId"])},{"repoName":1})
                    if proj_details:
                        repo_name=proj_details["repoName"]
                    else:
                        repo_name= str(requestdata["projectId"])
                        # repo_name=wrap(requestdata["projectId"],ldap_key)
                    workspace=bit_details["workspace"]
                    projectkey=bit_details["projectkey"]
                    export_branch=bit_details["bitbranch"]
                    api_url = "https://api.bitbucket.org/2.0"
                    access_token = unwrap(bit_details["bitaccesstoken"], ldap_key)                    
                    url=bit_details["biturl"].split('://')
                    url=url[0]+'://'+'x-token-auth:'+access_token+'@'+url[1]+"/"+ repo_name+".git" 
                # git_details = dbsession.gitconfiguration.find_one({"name":requestdata["gitname"],"gituser":ObjectId(requestdata["userid"]),"projectid":ObjectId(requestdata["projectId"])},{"giturl":1,"gitaccesstoken":1,"gitusername":1,"gituseremail":1})
                # if not git_details:
                #     res={'rows':'Invalid config name'}
                #     return res
                projectName=requestdata["projectName"]
                headers = {
                    "Authorization": f"Bearer {access_token}"
                    # "Accept": "application/vnd.github.v3+json"
                }
                repos,repo_response,msg=get_repo_details(headers,param,workspace)
                if msg in ["Invalid token","Unable to connect "+param]:
                    res={"rows":msg}
                    return res
                owner=get_owner_info(repo_response,repo_name,param)
                branch_msg,branch_names=get_branch_name(owner,repo_name,api_url,headers,param,workspace)
                if branch_msg in ["Invalid token","Unable to connect "+param]:
                    res={"rows":branch_msg}
                    return res
                
                if not proj_details:
                    if repo_name in repos:                                              
                        if 'main' not in branch_names:                            
                            main_branch_response=create_main_branch(projectName,owner,repo_name,api_url,access_token,param,workspace)                            
                            if main_branch_response in ["Invalid token","Unable to connect "+param]:
                                res={"rows":main_branch_response}
                                return res
                            branch_names.append("main")       
                    else:
                        new_repo_response,new_repo_msg=create_new_repo(repo_name,api_url,headers,projectName,param,workspace,projectkey)
                        if new_repo_msg in ["Invalid token","Unable to connect "+param, "The project might not exist, or you don't have permission to create a repository in the project."]:
                            res={"rows":new_repo_msg}
                            return res
                        
                        if param=="git":owner=get_owner_info(new_repo_response,repo_name,param)
                        main_branch_response=create_main_branch(projectName,owner,repo_name,api_url,access_token,param,workspace)
                        if main_branch_response in ["Invalid token","Unable to connect "+param]:
                                res={"rows":main_branch_response}
                                return res
                        branch_names.append("main")
                        
                else:
                    if repo_name in repos:                        
                        if 'main' not in branch_names:                            
                            main_branch_response=create_main_branch(projectName,owner,repo_name,api_url,access_token,param,workspace)
                            if main_branch_response in ["Invalid token","Unable to connect "+param]:
                                res={"rows":main_branch_response}
                                return res
                            branch_names.append("main")
                            
                            
                    else:
                        new_repo_response,new_repo_msg=create_new_repo(repo_name,api_url,headers,projectName,param,workspace,projectkey)
                        if new_repo_msg in ["Invalid token","Unable to connect "+param,"The project might not exist, or you don't have permission to create a repository in the project."]:
                            res={"rows":new_repo_msg}
                            return res
                        
                        if param=="git":owner=get_owner_info(new_repo_response,repo_name,param)
                        main_branch_response=create_main_branch(projectName,owner,repo_name,api_url,access_token,param,workspace)
                        if main_branch_response in ["Invalid token","Unable to connect "+param]:
                                res={"rows":main_branch_response}
                                return res
                
                #check whether cred is valid
                git_path=currdir+os.sep+'exportGit'+os.sep+requestdata["userid"]
                if(os.path.exists(git_path)): remove_dir(git_path)

                repo = git.Repo.init(git_path)
                if param=="git":
                    repo.config_writer().set_value('user', 'email', git_details['gituseremail']).release()
                    repo.config_writer().set_value('user', 'name', git_details['gitusername']).release()
                repo.config_writer().set_value('http', 'sslVerify', 'false').release()
                origin = repo.create_remote('origin',url)
                try:
                    origin.fetch()
                except Exception as e:
                    app.logger.error(e)
                    res ={"rows":"Unable to connect "+param}
                    return res
                
                if export_branch not in branch_names :
                    repo=create_requested_branch(origin,repo,export_branch,param)
                else:
                    repo.git.checkout(export_branch)
                try:
                    repo.git.pull(ff=True)
                except Exception as e:
                    app.logger.error(e)
                    res ={"rows":"Unable to connect "+param}
                    return res
                if param=="git":
                    result = dbsession.gitexpimpdetails.find({'gittask':'push',"parent":git_details["_id"],"version":requestdata["gitVersion"]})
                else:                    
                    result = dbsession.bitexpimpdetails.find({'bittask':'push',"parent":bit_details["_id"],"version":requestdata["bitVersion"]})
                index = result.count() - 1
                result=None
                if index >= 0:
                    res={'rows':'commit exists'}
                    return res
                elif result == None or result == 0:
                    path=currdir+os.sep+"mindmapGit"+os.sep+requestdata["userid"]+os.sep+export_branch
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

                            res = exportdataToGit(dbsession,path, requestdata, origin, repo, repo_name,export_branch, projectName, param)
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
        if git_path:remove_dir(git_path)
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

    def exportdataToGit(dbsession,dirpath, result, origin, repo,repo_name,export_branch,projectName,param):
        app.logger.debug("Inside exportdataToGit")
        res={'rows':'fail'}
        delpath=None
        git_path=None
        try:
            module_data=result
            delpath=currdir+os.sep+"mindmapGit"
            data={}
            if not isemptyrequest(module_data):
                if param=="git":
                    git_details = dbsession.gitconfiguration.find_one({"gituser":ObjectId(module_data["userid"]),"projectid":ObjectId(module_data["projectId"])},{"_id":1})
                    verion=module_data["gitVersion"]
                else:
                    bit_details = dbsession.bitconfiguration.find_one({"bituser":ObjectId(module_data["userid"]),"projectid":ObjectId(module_data["projectId"])},{"_id":1,"projectkey":1})
                    verion=module_data["bitVersion"]                
                git_path=currdir+os.sep+'exportGit'+os.sep+module_data["userid"]
                final_path=os.path.normpath(git_path+os.sep+export_branch)

                if(os.path.exists(final_path)):
                    if os.path.exists(dirpath):
                        shutil.rmtree(final_path)
            
                shutil.move(dirpath, final_path)
                # Add mimdmap file to remote repo
                repo.git.add(final_path)
                repo.index.commit(verion)
                try:
                    repo.git.push('origin',export_branch)
                except Exception as e:
                    app.logger.error(e)
                    res ={"rows":"Unable to connect "+param}
                    return res
                # get the commit id and save it in gitexportdetails
                for i in range(len(origin.refs)):
                    if(origin.refs[i].remote_head==export_branch):
                        commit_id = origin.refs[i].commit.hexsha
                        break

                data["userid"] = ObjectId(module_data["userid"])
                data["projectid"] = ObjectId(module_data["projectId"])                
                data["branchname"] = export_branch
                data["folderpath"] = export_branch
                data["commitid"] = commit_id
                data["projectname"] = projectName
                data["modifiedon"]=datetime.now()
                data["repoName"]=repo_name
                if param=="git":
                    data["gittask"]="push"
                    data["version"] = module_data["gitVersion"]
                    data["commitmessage"] = module_data["gitComMsgRef"]
                    data["parent"] = git_details["_id"]
                    data["exportgitid"] = None
                    dbsession.gitexpimpdetails.insert(data)
                else:
                    data["bittask"]="push"
                    data["version"] = module_data["bitVersion"]
                    data["commitmessage"] = module_data["bitComMsgRef"]
                    data["parent"] = bit_details["_id"]
                    data["projectkey"] = "PROJ"
                    data["exportbitid"] = None
                    dbsession.bitexpimpdetails.insert(data)
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
                projectid=ObjectId(requestdata["projectId"])           
                role = ObjectId(requestdata["roleid"])
                userid =ObjectId(requestdata["userid"])
                appType=requestdata["appType"]
                projectName=requestdata["projectName"]                             
                if "param" in requestdata and requestdata["param"]=="git":
                    gitVersionName = requestdata["gitVersion"]
                    check_gitbranch=list(dbsession.gitconfiguration.find({"gitbranch":{"$exists":False}}))
                    if len(check_gitbranch)>0:
                        dbsession.gitconfiguration.update_many({},{"$set":{"gitbranch":"main"}})
                    config_data = dbsession.gitconfiguration.find_one({"projectid":projectid},{"giturl":1,"gitaccesstoken":1,"gitbranch":1})
                    if config_data:
                        config_det={}
                        config_det["url"]=config_data["giturl"]
                        config_det["accesstoken"]=unwrap(config_data["gitaccesstoken"], ldap_key)
                        config_det["branch"]=config_data["gitbranch"]
                        result = dbsession.gitexpimpdetails.find_one({"projectid":expProj,"version":gitVersionName})
                        url=config_det["url"].split('://')
                        repo_name=result["repoName"]
                        url=url[0]+'://'+config_det["accesstoken"]+':x-oauth-basic@'+url[1]+"/"+repo_name+".git" 
                elif "param" in requestdata and requestdata["param"]=="bit":                    
                    bitVersionName = requestdata["bitVersion"]                      
                    config_data = dbsession.bitconfiguration.find_one({"projectid":projectid},{"biturl":1,"bitaccesstoken":1,"bitbranch":1})
                    if config_data:
                        config_det={}
                        config_det["url"]=config_data["biturl"]
                        config_det["accesstoken"]=unwrap(config_data["bitaccesstoken"], ldap_key)
                        config_det["branch"]=config_data["bitbranch"]
                        result = dbsession.bitexpimpdetails.find_one({"projectid":expProj,"version":bitVersionName})                    
                        url=config_det["url"].split('://')  
                        repo_name=result["repoName"]                  
                        url=url[0]+'://'+'x-token-auth:'+config_det["accesstoken"]+"@"+url[1]+"/"+repo_name+".git" 
                if not config_data:
                    # git_data = list(dbsession.gitconfiguration.find({"name":gitname},{"_id":1}))
                    # if len(git_data) > 0:
                    #     res = {'rows': "No entries"}                        
                    # else:
                    res={'rows': "empty"}
                else:                                 
                    if not result:
                        res = {'rows': "Invalid inputs"}                    
                    else:
                        git_path=currdir+os.sep+'exportGit'+os.sep+str(userid)
                        final_path=os.path.normpath(git_path)+os.sep+result["branchname"]                             
                        if(os.path.isdir(git_path)): remove_dir(git_path)                        
                        os.environ['GIT_SSL_NO_VERIFY'] = 'true'
                        repo = git.Repo.clone_from(url, git_path,no_checkout=True)                        
                        try:
                            repo.git.checkout(result['commitid'])
                        except Exception as e:
                            app.logger.error(e)                           
                            res="Unable to find the given commit in "+requestdata["param"] +" repository."
                            return res
                        
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
                                        "currentlyinuse":"",
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
                                            testscen=[]
                                            if "tsIds" in i:                                    
                                                for tsId in i["tsIds"]:
                                                    if tsId:
                                                        if "_id" in tsId:
                                                            for j in ScenarioIds:
                                                                if tsId["_id"]==j["old_id"]:
                                                                    tsId["_id"]=j["_id"]
                                                                    break
                                                            testscen.append(tsId)
                                            i["tsIds"]=testscen
                                                                                            
                                        
                                        for i in mindmapIds:
                                            if "tsIds" in i:
                                                for tsId in i["tsIds"]:
                                                    scrndt=[]
                                                    if "screens" in tsId:
                                                        for screens in tsId["screens"]:
                                                            if screens:
                                                                if "_id" in screens:
                                                                    for k in screenIds:
                                                                        if screens["_id"]==k["old_id"]:
                                                                            screens["_id"]=k["_id"]
                                                                            break
                                                                    scrndt.append(screens)
                                                    tsId["screens"]=scrndt
                                        
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
                                            if "testscenarios" in i and len(i["testscenarios"])>0:
                                                for j in i["testscenarios"]:
                                                    if "screens" in j and len(j["screens"])>0:
                                                        for k in j["screens"]:
                                                            if "testcases" in k and len(k["testcases"])>0:                                
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

                                        impdata={}
                                        if queryresult:
                                            impdata["userid"] = userid
                                            impdata["branchname"] = result["branchname"]
                                            impdata["folderpath"] = result["folderpath"]
                                            impdata["version"] = result["version"]
                                            impdata["parent"] = result["parent"]
                                            impdata["commitid"] = result["commitid"]
                                            impdata["commitmessage"] = result["commitmessage"]
                                            impdata["modifiedon"] = datetime.now()
                                            impdata["repoName"]=repo_name
                                            impdata["projectname"]=result["projectname"]
                                            impdata["projectid"]=projectid
                                            if requestdata["param"]=="git":                                                
                                                impdata["exportgitid"] = result["exportgitid"] if result["gittask"]=="pull" else  result["_id"]                                                
                                                impdata["gittask"]="pull"                                                
                                                dbsession.gitexpimpdetails.insert(impdata)
                                            else:                                              
                                                impdata["exportbitid"] = result["exportbitid"] if result["bittask"]=="pull" else  result["_id"]                                                
                                                impdata["bittask"]="pull" 
                                                impdata["projectkey"]= result["projectkey"]                                            
                                                dbsession.bitexpimpdetails.insert(impdata)
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
        if git_path:remove_dir(git_path)
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
        
    @app.route('/git/checkExportVer',methods=['POST'])
    def checkExportVer():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside checkExportVer.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)                 
                dbsession=client[clientName]               
                if requestdata["param"]=="git":
                    check_gitbranch=list(dbsession.gitconfiguration.find({"gitbranch":{"$exists":False}}))
                    if len(check_gitbranch)>0:
                        dbsession.gitconfiguration.update_many({},{"$set":{"gitbranch":"main"}})
                    git_exp_imp_collec_check= dbsession.gitexpimpdetails.find({}).count()
                    if  git_exp_imp_collec_check ==0:
                        git_export_det_check=dbsession.gitexportdetails.find({}).count()
                        if git_export_det_check >0:
                            dbsession.gitexportdetails.aggregate([{
                                        "$addFields": {
                                            "repoName":"$projectname",
                                            "modifiedon": {"$toDate":{"$add": [
                                                { "$toDate": "$_id" },
                                                { "$multiply": [5.5 * 60 * 60 * 1000, 1] } 
                                            ]}},"gittask":"push","exportgitid":None
                                        }
                                    },{"$out":"gitexpimpdetails"}])               
                    expName=list(dbsession.gitexpimpdetails.find({"projectid":ObjectId(requestdata["projectId"]),"gittask":"push"},{"commitmessage":1,"version":1,"_id":0}))
                else:
                    expName=list(dbsession.bitexpimpdetails.find({"projectid":ObjectId(requestdata["projectId"]),"gittask":"push"},{"commitmessage":1,"version":1,"_id":0}))
                if requestdata["query"] =="exportgit":
                    ver=[]
                    for version in expName:
                        ver.append(version["version"])                
                    res={"rows":ver}
                else:
                    res={"rows": expName}
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as checkExportVerexc:
            servicesException("checkExportVer",checkExportVerexc, True)
        return jsonify(res)
    

    @app.route('/git/fetch_git_exp_details',methods=['POST'])
    def fetch_git_exp_details():
        res={'rows':'fail'}
        try:
            requestdata=json.loads(request.data)
            app.logger.debug("Inside fetch_git_exp_details.")
            if not isemptyrequest(requestdata):
                clientName=getClientName(requestdata)         
                dbsession=client[clientName]               
                if requestdata["param"]=="git":
                    check_gitbranch=list(dbsession.gitconfiguration.find({"gitbranch":{"$exists":False}}))
                    if len(check_gitbranch)>0:
                        dbsession.gitconfiguration.update_many({},{"$set":{"gitbranch":"main"}})
                    git_exp_imp_collec_check= dbsession.gitexpimpdetails.find({}).count()
                    if  git_exp_imp_collec_check ==0:
                        git_export_det_check=dbsession.gitexportdetails.find({}).count()
                        if git_export_det_check >0:
                            dbsession.gitexportdetails.aggregate([{
                                        "$addFields": {
                                            "repoName":"$projectname",
                                            "modifiedon": {"$toDate":{"$add": [
                                                { "$toDate": "$_id" },
                                                { "$multiply": [5.5 * 60 * 60 * 1000, 1] } 
                                            ]}},"gittask":"push","exportgitid":None
                                        }
                                    },{"$out":"gitexpimpdetails"}])             
                    exp_data=list(dbsession.gitexpimpdetails.find({"projectid":ObjectId(requestdata["projectId"])}).sort("modifiedon",-1))
                else:
                    exp_data=list(dbsession.bitexpimpdetails.find({"projectid":ObjectId(requestdata["projectId"])}).sort("modifiedon",-1))              
                res={"rows":exp_data}
                return res                                
            else:
                app.logger.warn('Empty data received while importing mindmap')
        except Exception as fetch_git_exp_detailsexc:
            servicesException("fetch_git_exp_details",fetch_git_exp_detailsexc, True)
        return jsonify(res)
    
    
