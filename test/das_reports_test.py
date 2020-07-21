import requests
from pprint import pprint
import uuid,json
requesteddata = {
    "reportid": str(uuid.uuid4()),
    "executionid": str(uuid.uuid4()),
    "testsuiteid": str(uuid.uuid4()),
    "testscenarioid":str(uuid.uuid4()),
    "browser":"Chrome",
    "status":"Pass",
    "report": "This is report JSON",
    "cycleid":str(uuid.uuid4())
}

url = "http://localhost:1990/"
class Test:
    def __init__(self):
        r = requests.get(url)
        print r.text,r.status_code
        if r.text == 'Data Server Ready!!!' and r.status_code== 200:
            print "************* Begining the test****************"
            self.on = True
        else:
            print "!!!!!!!!!!!!!!! Avo Assure DAS Unavailable !!!!!!!!!!!!!!!!!!!"
            self.on = False
    def insertreportquery(self):
        # /suite/ExecuteTestSuite_ICE   insertreportquery
        '''
        query = "insert into reports (reportid,executionid,"
                +"testsuiteid,testscenarioid,executedtime,browser,modifiedon,status,"
                +"report,cycleid) values (" + requestdata['reportid'] + ","
                + requestdata['executionid']+ "," + requestdata['testsuiteid']
                + "," + requestdata['testscenarioid'] + "," + str("date")
                + ",'" + requestdata['browser'] + "'," + str("date")
                + ",'" + requestdata['status']+ "','" + requestdata['report'] + "'," + requestdata['cycleid'] + ")")
                queryresult = icesession.execute(executetestsuitequery5)
        '''
        print requesteddata
        requesteddata["query"] = "insertreportquery"
        r = requests.post(url+'suite/ExecuteTestSuite_ICE', data = json.dumps(requesteddata))
        print r.text,r.status_code
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print "insertreportquery successful!"
        else:
            print "insertreportquery failed!"

    def fetchallreports(self):
        requesteddata["query"] = "allreports"
        requesteddata["scenarioid"] = requesteddata["testscenarioid"]
        r = requests.post(url+'reports/reportStatusScenarios_ICE', data = json.dumps(requesteddata))
        print r.text,r.status_code
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail'):
            print "fetchallreports successful!"
        else:
            print "fetchallreports failed!"                    

    def getcycleidfromreportid(self):
        requesteddata["query"] = "cycleid"
        r = requests.post(url+'reports/getReport', data = json.dumps(requesteddata))
        print r.text,r.status_code
        if(r.status_code == 200 and json.loads(r.text)['rows']!='fail' and json.loads(r.text)['rows'][0]['cycleid']==requesteddata["cycleid"]):
            print "getcycleidfromreportid successful!"
        else:
            print "getcycleidfromreportid failed!"       

p1 = Test()
if(p1.on):
    p1.insertreportquery()
    p1.fetchallreports()
    p1.getcycleidfromreportid()
