################################################################################
# BEGIN OF DEFAULT METHODS AND IMPORTS       -----------DO NOT EDIT
################################################################################
# ----------DEFAULT METHODS AND IMPORTS------------DO NOT EDIT-------------------
from utils import *
from Crypto.Cipher import AES
import base64
import json
import datetime
import partition_scenarios
import dateutil.parser as DP


def LoadServices(app, redissession, dbsession):
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
        users = bench_mark_sort(requestdata['ipAddressList'])
        if requestdata["time"] != "Now":
            users,flag = load_sort(users,requestdata["time"])
        else:
            flag = False
        try:
            if 'scenario' in requestdata['type'].lower():
                for i in range(len(requestdata['scenarios'])):
                    time = 0
                    scid = requestdata['scenarios'][i]['scenarioId']
                    time = get_time(scid)
                    if scid in timearr:
                        scid = scid + str(i)
                    timearr[scid] = time
                partitions = partition_scenarios.main(timearr, len(users))
                for i in range(len(users)):
                    if i < len(partitions["seq_partitions"]):
                        ipPartitions[users[i]] = str(
                            partitions["seq_partitions"][i]).strip("['']")
            elif 'module' in requestdata["type"].lower():
                modules = requestdata['modules']
                mod_scn = {}
                for i in range(len(modules)):
                    time = 0
                    mod_scn[modules[i]['testsuiteId']] = []
                    for j in range(len(modules[i]['suiteDetails'])):
                        scid = modules[i]['suiteDetails'][j]['scenarioId']
                        mod_scn[modules[i]['testsuiteId']].append(scid)
                        time = time + get_time(scid)
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
                res['modPartitions'] = modPartitions
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            servicesException("partion_modules", e)
        res["result"] = "success"
        res["partitions"] = ipPartitions
        res["totalTime"] = partitions["totalTime"]
        res['timearr'] = timearr
        if flag: res["result"] = "busy"
        return jsonify(res)

    def load_sort(users, time):
        available_users = []
        unavailable = 0
        for i in range(len(users)):
            try:
                prev_time = 0
                x = DP.parse(time)
                dtm = datetime.datetime(x.year,x.month,x.day,x.hour,x.minute) 
                result = dbsession.scheduledexecutions.find({"scheduledon": {"$lt": dtm}, "target": users[i],"status":"scheduled"})
                if result is None or result.count() == 0:
                    available_users.insert(0,users[i])
                    continue
                latest = result[result.count() - 1]
                scenario_details = latest['scenariodetails']
                for j in range(len(scenario_details)):
                    for k in range(len(scenario_details[j])):
                        prev_time = prev_time + get_time(scenario_details[j][k]['scenarioId'])
                end_time = latest['scheduledon']
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
        result = dbsession.executiontimes.find({"testscenarioid": scid})
        if result is None or result.count() == 0:
            return 315
        if result[0]['count'] > 10:
            return result[0]['median']
        else:
            return result[0]['mean']

    def bench_mark_sort(users):
        try:
            score = []
            scoreMap = {}
            for i in range(len(users)):
                result = dbsession.benchmark.find({"hostname": users[i]})
                latest = -1
                if result is not None and result.count() - 1 >=0:
                    latest = result.count() - 1
                else:
                    score.append(i*1000)
                    scoreMap[i*1000] = users[i]
                    continue
                score.append(result[latest]["averagesystemscore"])
                scoreMap[result[latest]["averagesystemscore"]] = users[i]

            score.sort()
            sorted_list = []
            for i in range(len(score)):
                sorted_list.append(scoreMap[score[i]])
            return sorted_list
        except Exception as e:
            app.logger.debug(traceback.format_exc())
            return users

        