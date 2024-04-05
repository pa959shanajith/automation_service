from datetime import datetime

class UserDocument:
    def __init__(self, project, orgname, name, path, uploadedBy,melvis_file_id, input_type, version='1.0'):
        self.project = project
        self.orgname = orgname
        self.name = name
        self.path = path
        self.uploadedBy = uploadedBy
        self.uploadedTime = datetime.now()
        self.type = input_type
        self.version = version,
        self.melvis_file_id = melvis_file_id

    def to_dict(self):
        return {
            "project": self.project,
            "organization":self.orgname,
            "name": self.name,
            "path": self.path,
            "uploadedBy": self.uploadedBy,
            "uploadedTime": self.uploadedTime,
            "version": self.version,
            "type": self.type,
            "melvis_file_id":self.melvis_file_id
        }
#user level testcase collection
class UserTestcases:
    def __init__(self, project, orgname, name, email, testcases):
        self.project = project
        self.orgname = orgname
        self.name = name
        self.email = email
        self.testcases = testcases

    def to_dict(self):
        return {
            "project": self.project,
            "organization":self.orgname,
            "name": self.name,
            "email": self.email,
            "testcases": self.testcases
        }
# All AI Testcase collection
class AI_Testcases:
    def __init__(self, testcase):
        self.testcase = testcase
        self.uploadedTime = datetime.now()

    def to_dict(self):
        return {
            "testcase": self.testcase,
            "uploadedTime": self.uploadedTime
        }

class OpenAI_LLM_Model:
    def __init__(self, openai_api_key, openai_api_type, openai_api_version, openai_api_base,userinfo,name,deployment_name):
        self.openai_api_key = openai_api_key
        self.openai_api_type = openai_api_type
        self.openai_api_version = openai_api_version
        self.openai_api_base = openai_api_base
        self.modeltype = "openAi"
        self.userinfo = userinfo
        self.name = name
        self.deployment_name = deployment_name
        self.createdAt = datetime.now()

    def to_dict(self):
        return {
            "openai_api_key": self.openai_api_key,
            "openai_api_type":self.openai_api_type,
            "openai_api_version": self.openai_api_version,
            "openai_api_base": self.openai_api_base,
            "modeltype": self.modeltype,
            "createdAt": self.createdAt,
            "userinfo": self.userinfo,
            "name": self.name,
            "openai_deployment_name": self.deployment_name
        }

class Other_LLM_Model:
    def __init__(self, api_key, model, modeltype,userinfo,name):
        self.api_key = api_key
        self.model = model
        self.modeltype = modeltype
        self.userinfo = userinfo
        self.name = name
        self.createdAt = datetime.now()

    def to_dict(self):
        data = {
            "modeltype": self.modeltype,
            "createdAt": self.createdAt,
            "userinfo": self.userinfo,
            "name": self.name

        }
        data[f"{self.modeltype}_api_key"] = self.api_key
        data[f"{self.modeltype}_model"] = self.model

        return data

class Template_Model:
    def __init__(self, name, domain, model_details, test_type ,temperature,description,active,default,userinfo):
        self.name = name
        self.domain = domain
        self.model_details = model_details
        self.test_type = test_type
        self.temperature = temperature
        self.description = description
        self.active = active
        self.default = default
        self.userinfo = userinfo
        self.createdAt = datetime.now()

    def to_dict(self):
        return {
            "name": self.name,
            "domain":self.domain,
            "model_details": self.model_details,
            "test_type": self.test_type,
            "temperature": self.temperature,
            "createdAt": self.createdAt,
            "userinfo": self.userinfo,
            "active": self.active,
            "description": self.description,
            "default": self.default
        }                   