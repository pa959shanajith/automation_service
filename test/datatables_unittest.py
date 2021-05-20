import requests
import json

requesteddata = {
    "datatablename": "dtname",
    "datatable": [{"AAA":"a"},{"AAA":"a1"}],
    "dtheaders": ["AAA"]
}
requesteddatanew = {
    "datatablename": "dtname"
}
url = "http://localhost:1990/"

class Test:
    def __init__(self):
        r = requests.get(url)
        if r.text == 'Data Server Ready!!!' and r.status_code== 200:
            print("************* Begining the test****************")
            self.on = True
        else:
            print("!!!!!!!!!!!!!!! DAS Unavailable !!!!!!!!!!!!!!!!!!!")
            self.on = False

    def createDataTable(self):
        requesteddata["action"] = "create"
        r = requests.post(url+'utility/manageDataTable', data = json.dumps(requesteddata))
        if(r.status_code == 200 and json.loads(r.text)['rows']=='success'):
            print("createDataTable successful!")
        elif(r.status_code == 200 and json.loads(r.text)['rows']=='exists'):
            print("Table already exists. Change the table name and try again")
            print("************* Terminating the test****************")
            import sys
            sys.exit()
        else:
            print("createDataTable failed!")

    def createDataTableNameExists(self):
        requesteddata["action"] = "create"
        r = requests.post(url+'utility/manageDataTable', data = json.dumps(requesteddata))
        if(r.status_code == 200 and json.loads(r.text)['rows']=='exists'):
            print("createDataTableNameExists successful!")
        else:
            print("createDataTableNameExists failed!")

    def editDataTable(self):
        requesteddata["action"] = "edit"
        requesteddata['datatable'] = [{"AAA":"a1"},{"AAA":"a2"}]
        r = requests.post(url+'utility/manageDataTable', data = json.dumps(requesteddata))
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print("editDataTable successful!")
        else:
            print("editDataTable failed!")

    def fetchDataTableNames(self):
        requesteddatanew["action"] = "datatablenames"
        r = requests.post(url+'utility/fetchDatatable', data = json.dumps(requesteddatanew))
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print("fetchDataTableNames successful!")
        else:
            print("fetchDataTableNames failed!")

    def fetchDataTables(self):
        requesteddatanew["action"] = "datatable"
        r = requests.post(url+'utility/fetchDatatable', data = json.dumps(requesteddatanew))
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print("fetchDataTables successful!")
        else:
            print("fetchDataTables failed!")

    def deleteDataTableConfirm(self):
        requesteddatanew["action"] = "deleteConfirm"
        r = requests.post(url+'utility/manageDataTable', data = json.dumps(requesteddatanew))
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print("deleteDataTableConfirm successful!")
        else:
            print("deleteDataTableConfirm failed!")

    def deleteDataTable(self):
        requesteddatanew["action"] = "delete"
        r = requests.post(url+'utility/manageDataTable', data = json.dumps(requesteddatanew))
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print("deleteDataTable successful!")
        else:
            print("deleteDataTable failed!")

p1 = Test()
if(p1.on):
    p1.createDataTable()
    p1.createDataTableNameExists()
    p1.editDataTable()
    p1.fetchDataTableNames()
    p1.fetchDataTables()
    p1.deleteDataTableConfirm()
    p1.deleteDataTable()
    print("************* Ending the test****************")
