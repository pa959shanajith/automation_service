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