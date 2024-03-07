from datetime import datetime

class UserDocument:
    def __init__(self, project, orgname, name, path, uploadedBy, input_type, version='1.0'):
        self.project = project
        self.orgname = orgname
        self.name = name
        self.path = path
        self.uploadedBy = uploadedBy
        self.uploadedTime = datetime.now()
        self.type = input_type
        self.version = version

    def to_dict(self):
        return {
            "project": self.project,
            "organization":self.orgname,
            "name": self.name,
            "path": self.path,
            "uploadedBy": self.uploadedBy,
            "uploadedTime": self.uploadedTime,
            "version": self.version,
            "type": self.type
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
    def __init__(self, openai_api_key, openai_api_type, openai_api_version, openai_api_base,userinfo,name,description):
        self.openai_api_key = openai_api_key
        self.openai_api_type = openai_api_type
        self.openai_api_version = openai_api_version
        self.openai_api_base = openai_api_base
        self.modeltype = "openAi"
        self.userinfo = userinfo
        self.name = name
        self.description = description
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
            "description": self.description
        }

class Other_LLM_Model:
    def __init__(self, api_key, model, modeltype,userinfo,name,description):
        self.api_key = api_key
        self.model = model
        self.modeltype = modeltype
        self.userinfo = userinfo
        self.name = name
        self.description = description
        self.createdAt = datetime.now()

    def to_dict(self):
        data = {
            "modeltype": self.modeltype,
            "createdAt": self.createdAt,
            "userinfo": self.userinfo,
            "name": self.name,
            "description": self.description

        }
        data[f"{self.modeltype}_api_key"] = self.api_key
        data[f"{self.modeltype}_model"] = self.model

        return data               