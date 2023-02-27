################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
#----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import base64
import json
import dateutil.parser as DP
import datetime
import statistics


def LoadServices(app, redissession, client,getClientName):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################

    @app.route('/benchmark/store',methods=['POST'])
    def store_benchmark():
        app.logger.debug("Inside benchmark store")
        requestdata=json.loads(request.data)
        res={'benchmark_store':'fail'}
        inputdata = {}
        inputdata["cpuscore"] = []
        inputdata["memoryscore"] = []
        inputdata["networkscore"] = []
        inputdata["systemscore"] = []
        inputdata["time"] = []
        inputdata["percent_received"] = []
        inputdata["hostip"] = []
        try:
            clientName=getClientName(requestdata)       
            dbsession=client[clientName]
            x = DP.parse(requestdata["time"])
            dtm = datetime.datetime(x.year,x.month,x.day,x.hour,x.minute) 
            result_arr = dbsession.benchmark.find({"hostname":requestdata['hostname'],"time":{"$lt": dtm}})
            index = result_arr.count() - 1
            result = None
            if index >= 0:
                result = result_arr[index]
            if result == None or result['time'][0].day < dtm.day:
                inputdata["cpuscore"].append(requestdata['cpuscore'])
                inputdata["memoryscore"].append(requestdata['memoryscore'])
                inputdata["networkscore"].append(requestdata['networkscore'])
                inputdata["systemscore"].append(requestdata['systemscore'])
                inputdata["percent_received"].append(requestdata["percent_received"])
                inputdata["hostip"].append(requestdata["hostip"])
                inputdata["hostname"] = requestdata["hostname"]
                inputdata["averagecpuscore"] = requestdata['cpuscore']
                inputdata["averagememoryscore"] = requestdata['memoryscore']
                inputdata["averagenetworkscore"] = requestdata['networkscore']
                inputdata["averagesystemscore"] = requestdata["systemscore"]
                inputdata["runcount"] = 1
                inputdata['time'].append(dtm)
                dbsession.benchmark.insert_one(inputdata)
                res={"benchmark_store":"success"}
            else:
                inputdata["cpuscore"].append(requestdata['cpuscore'])
                inputdata["cpuscore"].extend(result["cpuscore"])
                inputdata["memoryscore"].append(requestdata['memoryscore'])
                inputdata["memoryscore"].extend(result["memoryscore"])
                inputdata["networkscore"].append(requestdata['networkscore'])
                inputdata["networkscore"].extend(result["networkscore"])
                inputdata["systemscore"].append(requestdata['systemscore'])
                inputdata["systemscore"].extend(result["systemscore"])
                inputdata["percent_received"].append(requestdata["percent_received"])
                inputdata["percent_received"].extend(result["percent_received"])
                inputdata["hostip"].append(requestdata["hostip"])
                inputdata["hostip"].extend(result["hostip"])
                inputdata["averagecpuscore"] = statistics.mean(inputdata['cpuscore'])
                inputdata["averagememoryscore"] = statistics.mean(inputdata['memoryscore'])
                inputdata["averagenetworkscore"] = statistics.mean(inputdata['networkscore'])
                inputdata["averagesystemscore"] = statistics.mean(inputdata['systemscore'])
                inputdata["runcount"] = result["runcount"] + 1
                inputdata['time'].append(dtm)  
                inputdata['time'].extend(result['time'])      
                dbsession.benchmark.update_one({"_id":result["_id"]},{"$set":{"cpuscore":inputdata["cpuscore"],"networkscore":inputdata["networkscore"],"memoryscore":inputdata["memoryscore"],"percent_received":inputdata["percent_received"],"hostip":inputdata["hostip"],"averagesystemscore":inputdata["averagesystemscore"],"time":inputdata["time"],"runcount":inputdata["runcount"],"systemscore":inputdata["systemscore"],"averagecpuscore":inputdata['averagecpuscore'],"averagenetworkscore":inputdata['averagenetworkscore'],"averagememoryscore":inputdata['averagememoryscore']}})
                res={"benchmark_store":"success"}
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("store_benchmark",e)
        return jsonify(res)
