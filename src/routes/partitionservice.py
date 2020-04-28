################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
# ----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import base64
import json
import datetime
from utility import partition_scenarios
import dateutil.parser as DP


def LoadServices(app, redissession, n68session):
    setenv(app)

################################################################################
# END OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################

################################################################################
# BEGIN OF UTILITIES
# INCLUDES : all admin related actions
################################################################################
    @app.route('/partitons/getPartitions', methods=['POST'])
    def get_partitions():
        app.logger.debug("Inside get_partitions")
        requestdata = json.loads(request.data)
        res = {'result': 'fail'}
        timearr = {}
        taskarr = []
        time_usr = {}
        ipPartitions = {}
        modPartitions = {}
        users,flag = load_sort(requestdata['ipAddressList'],requestdata["time"])

        if requestdata['type'] == 'Scenario Smart Scheduling':
            try:
                for i in range(len(requestdata['scenarios'])):
                    scid = requestdata['scenarios'][i]['scenarioId']
                    result = n68session.executiontimes.find(
                        {"testscenarioid": scid})
                    if result is None or result.count() == 0:
                        timearr[scid] = 315
                        continue
                    cursor_len = result.count()
                    for i in range(cursor_len):
                        if result[i]['count'] > 10:
                            timearr[scid] = result[i]['median']
                        else:
                            timearr[scid] = result[i]['mean']
                partitions = partition_scenarios.main(
                    timearr, requestdata['activeIce'])
                for i in range(len(users)):
                    if i < len(partitions["seq_partitions"]):
                        ipPartitions[users[i]] = str(
                            partitions["seq_partitions"][i]).strip("['']")
                res["result"] = "success"
                res["partitions"] = ipPartitions
                res["totalTime"] = partitions["totalTime"]
                res['timearr'] = timearr
                if flag: res["result"] = "busy"
            except Exception as e:
                app.logger.debug(traceback.format_exc())
                servicesException("partion_scenarios", e)
        elif requestdata['type'] == 'Module Smart Scheduling':
            try:
                modules = requestdata['modules']
                mod_scn = {}
                for i in range(len(modules)):
                    time = 0
                    mod_scn[modules[i]['testsuiteId']] = []
                    for j in range(len(modules[i]['suiteDetails'])):
                        scid = modules[i]['suiteDetails'][j]['scenarioId']
                        mod_scn[modules[i]['testsuiteId']].append(scid)
                        result = n68session.executiontimes.find(
                            {"testscenarioid": scid})
                        if result is None or result.count() == 0:
                            time = time + 315
                            continue
                        cursor_len = result.count()
                        for k in range(cursor_len):
                            if result[k]['count'] > 10:
                                time = time + result[k]['median']
                            else:
                                time = time + result[k]['mean']
                    timearr[modules[i]['testsuiteId']] = time
                partitions = partition_scenarios.main(timearr, len(users))
                
                for i in range(len(users)):
                    if i < len(partitions["seq_partitions"]):
                        mods = str(partitions["seq_partitions"][i]).strip(
                            "['']").split(", ")
                        part_str = ""
                        time_usr[users[i]] = 0
                        modPartitions[users[i]] = []
                        for j in range(len(mods)):
                            mod_name = mods[j].strip("'")
                            part_str = str(mod_scn[mod_name]).strip(
                                "['']") + part_str
                            modPartitions[users[i]].append(mod_name)
                        ipPartitions[users[i]] = part_str

                res["result"] = "success"
                res["partitions"] = ipPartitions
                res["totalTime"] = partitions["totalTime"]
                res['timearr'] = timearr
                res['modPartitions'] = modPartitions
                if flag: res['result'] = 'busy'
            except Exception as e:
                app.logger.debug(traceback.format_exc())
                servicesException("partion_modules", e)

        return jsonify(res)

    def load_sort(users, time):
        available_users = []
        unavailable = 0
        for i in range(len(users)):
            try:
                prev_time = 0
                x = DP.parse(time)
                dtm = datetime.datetime(x.year,x.month,x.day,x.hour,x.minute) 
                result = n68session.scheduledexecutions.find({"scheduledon": {"$lt": dtm}, "target": users[i]})
                latest = result[result.count() - 1]
                scenario_details = latest['scenariodetails']
                for j in range(len(scenario_details)):
                    for k in range(len(scenario_details[j])):
                        prev_time = prev_time + get_time(scenario_details[j][k]['scenarioids'])
                end_time = latest['scheduledon']
                #x = DP.parse(end_time)
                #end_dtm = datetime.datetime(x.year,x.month,x.day,x.hour,x.minute)
                end_dtm = end_time + datetime.timedelta(0,int(prev_time))
                if end_dtm < dtm:
                    available_users.insert(0,users[i])
                elif end_dtm == dtm:
                    available_users.append(users[i])
                else:
                    unavailable += 1
            except Exception as e:
                app.logger.debug(traceback.format_exc())
                return users,True
        if unavailable == len(users):
            return users,True
        return available_users,False
        

    def get_time(scid):
        result = n68session.executiontimes.find({"testscenarioid": scid})
        if result is None or result.count() == 0:
            return 315
        if result[0]['count'] > 10:
            return result[0]['median']
        else:
            return result[0]['mean']
