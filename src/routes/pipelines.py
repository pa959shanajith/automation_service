from bson import ObjectId
from utils import *
from collections import Counter

####################################################################################
##################################### COMMON #######################################
####################################################################################

def fetch_tokens(projectid, userid):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid
            }
        },
        {
            "$project": {
                "_id": 0,
                "token": 1,
                "executionData.configurename": 1
            }
        }
    ]
    return pipeline


def fetch_executionids(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "status": {"$in": ["Fail", "fail"]},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$project": {
                "_id": 1
            }
        }
    ]
    return pipeline

 
####################################################################################
#################################### EXECUTION #####################################
####################################################################################

def fetch_projects(userid):
    pipeline = [
            {"$match": {"_id": ObjectId(userid)}},
            {"$lookup": {
                "from": "projects", 
                "localField": "projects",
                "foreignField": "_id",
                "as": "projectDetails"
            }},
            {"$unwind": "$projectDetails"},
            {"$project": {
                "projectId": "$projectDetails._id",
                "projectName": "$projectDetails.name", 
                "assignedRole": {"$arrayElemAt": [
                "$projectlevelrole.assignedrole",  
                {"$indexOfArray": ["$projects", "$projectDetails._id"]}
                ]}
            }},
            {
                "$addFields": {"roleid": {"$toObjectId": "$assignedRole"}}
            },
            {"$lookup": {
                "from": "permissions", 
                "localField": "roleid",
                "foreignField": "_id",
                "as": "rolename"
                }},
            {"$project": {
                "_id":0,
                "Project Name": "$projectName",
                "Role Name": {"$arrayElemAt": ["$rolename.name",0]}
                }}
        ]
    return pipeline


def fetch_users(projectid):
    pipeline = [
            {"$match": {"projects": ObjectId(projectid)}},
            {"$project": {"Name":"$name", "_id":0}},
            # need to add role name in the output (database bug)
        ]
    return pipeline


def pipeline_list_module_executed(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent"
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "suiteData"
            }
        },
        {
            "$project": {
                "_id":0,
                "Module Names": {"$arrayElemAt":["$suiteData.name",0]}
            }
        }
    ]
    return pipeline 


def pipeline_count_module_executed(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "Count": {"$sum": 1}
            },  
        },
        {
            "$group": {
                "_id": None,
                "Total Modules Executed": {"$sum": 1},
                "Times Executed": {"$sum": "$Count"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "Total Modules Executed": 1,
                "Times Executed": 1
            }
        }
    ]
    return pipeline


def pipeline_modules_execution_status(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "parent",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$project": {
                "testsuiteid": {"$arrayElemAt": ["$parent", 0]},
                "module_name": {"$arrayElemAt": ["$moduledata.name", 0]},
                "start_time": "$starttime",
                "status": "$status",
                "_id": 0
            }
        },
        {
            "$group": {
                "_id": {
                    "testsuiteid": "$testsuiteid",
                    "modulename": "$module_name"
                },
                "latest_start_time": {"$max": "$start_time"},
                "pass_count": {"$sum": {"$cond": [{"$eq": [{"$toLower": "$status"}, "pass"]}, 1, 0]}},
                "fail_count": {"$sum": {"$cond": [{"$eq": [{"$toLower": "$status"}, "fail"]}, 1, 0]}},
                "queued_count": {"$sum": {"$cond": [{"$eq": [{"$toLower": "$status"}, "queued"]}, 1, 0]}},
                "inprogress_count": {"$sum": {"$cond": [{"$eq": [{"$toLower": "$status"}, "inprogress"]}, 1, 0]}},
                "total_count": {"$sum": 1}
            }
        },
        {
            "$sort": {"latest_start_time": -1}
        },
        {
            "$project": {
                "Module Name": "$_id.modulename",
                "Pass Count": "$pass_count",
                "Fail Count": "$fail_count",
                "Queued Count": "$queued_count",
                "Inprogress Count": "$inprogress_count",
                "Total": "$total_count",
                "_id": 0
            }
        },
        {
            "$limit": 10
        }
    ]
    return pipeline


def pipeline_module_execution_duration(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey":{"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime},
                "status":{"$in":["pass", "Pass", "fail", "Fail"]}
            }
        },
        {
            "$project": {
                "parent": "$parent",
                "starttime": "$starttime",
                "endtime": "$endtime",
                "ellapsed_time": {"$subtract": ["$endtime", "$starttime"]}
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "parent",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$group": {
                "_id": {"$arrayElemAt": ["$moduledata.name",0]},
                "max_ellapsed_time": {"$max": {"$divide": ["$ellapsed_time", 1000]}},
                "min_ellapsed_time": {"$min": {"$divide": ["$ellapsed_time", 1000]}},
                "avg_ellapsed_time": {"$avg": {"$divide": ["$ellapsed_time", 1000]}}
            }
        },
        {
            "$project": {
                "Module Name": "$_id",
                "max ellapsed time (sec)": {"$round": ["$max_ellapsed_time", 2]},
                "min ellapsed time (sec)": {"$round": ["$min_ellapsed_time", 2]},
                "avg ellapsed time (sec)": {"$round": ["$avg_ellapsed_time", 2]},
                "_id":0
            }
        }
    ]
    return pipeline


def pipeline_module_execution_frequency(tokens, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "configurekey":{"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$lookup":{
                "from": "testsuites",
                "localField": "parent",
                'foreignField':"_id",
                'as':"moduledata"
            }
        },
        {
            "$group": {
                "_id": {"$arrayElemAt": ["$moduledata.name", 0]},
                "Count": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "Module Name": "$_id",
                "Times Executed": "$Count",
                "_id": 0
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Times Executed": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_module_execution_history(tokens, start_datetime, end_datetime, testsuite_id, testsuite_name):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "parent":testsuite_id,
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$set": {                
                "elapsedtime": {
                    "$dateToString": {
                        "format": "%H:%M:%S.%LZ", 
                        "date": {
                            "$add": [datetime.utcfromtimestamp(0), { "$multiply": [{
                                "$divide": [{"$subtract": ["$endtime", "$starttime"]},86400000]}, 24 * 60 * 60 * 1000] }]                            
                        }
                    }
                }
            }
        },
        {
            "$group":{
                "_id":None,
                "No of times executed":{"$sum":1},"status":{"$push":"$status"},
                "min time":{"$min":"$elapsedtime"},"max time":{"$max":"$elapsedtime"},
                "diff": {
                    "$avg": {
                    "$subtract": ["$endtime","$starttime"]}
                }
            }
        },
        {
            "$set": {
            "Module name":testsuite_name,
            "avg time": {
                "$dateToString": {"date": {"$toDate": "$diff"}, "format": "%H:%M:%S.%LZ"}
                }
            }
        },
        {
            "$project": {
                "_id":0,
                "Module name":1,
                "No of times executed":"$No of times executed",
                "min time":"$min time",
                "max time":"$max time",
                "avg time":"$avg time",
                "status":"$status",
            }
        }
    ]
    return pipeline


def pipeline_module_execution_history_2(min_max_values):
    min_max_values.append(Counter(min_max_values[0]["status"]))    
    del min_max_values[0]["status"]
    res = {}
    for d in min_max_values:
        res.update(d)
    return res


def pipeline_failure_rate_for_module(tokens, start_datetime, end_datetime):
    pipeline = [
                {
            "$match": {
                "configurekey":{"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
                {
                    "$project": {
                        "parent": "$parent",
                        "status":"$status"
                    }
                },
                {
                    "$lookup":{
                    "from": "testsuites",
                        "localField": "parent",
                        'foreignField':"_id",
                        'as':"moduledata"
                    }},
                    
                    {
                "$group": {
                    "_id": "$parent",
                    "module_name": { "$first": "$moduledata.name" },
                    "fail_count": { "$sum": { "$cond": { "if": { "$eq": ["$status", "fail"] }, "then": 1, "else": 0 } } },
                    "total_count": {
                        "$sum": {
                            "$cond": {
                                "if": { "$in": ["$status", ["pass", "fail"]] },
                                "then": 1,
                                "else": 0
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "Failure Rate": {
                        "$cond": {
                            "if": { "$eq": ["$total_count", 0] },
                            "then": None,
                            "else": { "$divide": ["$fail_count", "$total_count"] }
                        }
                    },
                    "Module Name": {"$arrayElemAt":["$module_name",0]}, 
                    "_id": 0
                }
            }
            ]
    return pipeline






####################################################################################
##################################### DEFECT #######################################
####################################################################################

def pipeline_module_level_defects_trend_analysis(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "status": {"$in":["Fail","fail"]},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "status_count": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$project": {
                "Module Name": {"$arrayElemAt": ["$moduledata.name",0]},
                "Fail Count": "$status_count",
                "_id":0
            }
        },
        {
            "$sort": {
                "Fail Count": -1
            }
        }
    ]
    return pipeline


def pipeline_module_with_more_defects(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
                }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "parent",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "module_name": {"$first": "$moduledata.name"},
                "fail_count": {"$sum": {"$cond": {"if": {"$eq": ["$status", "fail"]}, "then": 1, "else": 0}}},
                "total_count": {
                    "$sum": {
                        "$cond": {
                            "if": {"$in": ["$status", ["pass", "fail", "queued", "terminated"]]},
                            "then": 1,
                            "else": 0
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "Module Names": {"$arrayElemAt": ["$module_name", 0]} , 
                "Fail Count": "$fail_count",
                "Total Executions": "$total_count",
                "_id": 0
            }
        },
        {
            "$sort": {"Fail Count": -1}
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_module_with_less_defects(tokens, start_datetime, end_datetime):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
                }
        },
        {
            "$lookup": {
                "from": "testsuites",
                "localField": "parent",
                "foreignField": "_id",
                "as": "moduledata"
            }
        },
        {
            "$group": {
                "_id": "$parent",
                "module_name": {"$first": "$moduledata.name"},
                "fail_count": {"$sum": {"$cond": {"if": {"$eq": ["$status", "fail"]}, "then": 1, "else": 0}}},
                "total_count": {
                    "$sum": {
                        "$cond": {
                            "if": {"$in": ["$status", ["pass", "fail", "queued", "terminated"]]},
                            "then": 1,
                            "else": 0
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "Module Names": {"$arrayElemAt": ["$module_name", 0]} , 
                "Fail Count": "$fail_count",
                "Total Executions": "$total_count",
                "_id": 0
            }
        },
        {
            "$sort": {"Fail Count": 1}
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_profile_level_defects(projectid, userid, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid,
            }
        },
        {
            "$lookup": {
                "from": "executions",
                "localField": "executionData.configurekey",
                "foreignField": "configurekey",
                "as": "executionDetails"
            }
        },
        {
            "$unwind": "$executionDetails"
        },
        {
            "$match": {
                "executionDetails.status": {"$in": ["Fail", "fail"]},
                "executionDetails.starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": "$executionData.configurename",
                "Failed Modules": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "Profile Names": "$_id",
                "Failed Modules": "$Failed Modules"
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Failed Modules": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_execution_environment_defects(tokens, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens},
                "status": {"$in": ["Fail", "fail"]},
                "starttime": {"$gte": start_datetime, "$lte":end_datetime}
            }
        },
        {
            "$lookup": {
                "from": "reports",
                "localField": "_id",
                "foreignField": "executionid",
                "as": "reportdata"
            }
        },
        {
            "$unwind": "$reportdata"
        },
        {
            "$group": {
                "_id": "$reportdata.executedon",
                "Fail Count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "Browser": "$_id",
                "Fail Count": "$Fail Count",
                "_id":0
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_test_scenario_level_defects(executionids, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["Fail", "fail"]},
                "executionid": { "$in": executionids}
        }
        },
        {
            "$lookup": {
                "from": "testscenarios",
                "localField": "testscenarioid",
                "foreignField": "_id",
                "as": "matchedTestScenarios"
            }
        },
        {
            "$group": {
                "_id": {"$arrayElemAt": ["$matchedTestScenarios.name", 0]},
                "defect_count": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Test Scenario Name": "$_id",
                "Fail Count": "$defect_count"
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_browser_version_defects(tokens, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "configurekey": {"$in": tokens}, 
                "status": {"$in": ["Fail", "fail"]},
                "starttime": {"$gte": start_datetime, "$lte": end_datetime}
                }
        },
        {
            "$lookup": {
                "from": "reports",
                "localField": "_id",
                "foreignField": "executionid",
                "as": "reportdata"
            }
        },
        {
            "$unwind": "$reportdata"
        },
        {
            "$group": {
                "_id": {
                    "Browser": "$reportdata.executedon",
                    "Browser Version": "$reportdata.overallstatus.browserVersion"
                },
                "defect_count": {"$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Browser": "$_id.Browser",
                "Browser Version": "$_id.Browser Version",
                "Fail Count": "$defect_count"
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_keyword_level_defects(executionids, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "execution_ids": {"$in": executionids},
                "status": {"$in": ["Fail", "fail"]}
            }
        },
        {
            "$group": {
                "_id": "$Keyword",
                "Fail Count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "Keyword Name": "$_id",
                "Fail Count": "$Fail Count"
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_app_type_defects(projectid, userid, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid,
            }
        },
        {
            "$project": {
                "_id": 0,
                "appType": {"$arrayElemAt": ["$executionData.batchInfo.appType", 0]}  ,
                "configkey": "$executionData.configurekey",
                "profilename": "$executionData.configurename",
                "defect_count": 1
            }
        },
        {
            "$lookup": {
                "from": "executions",
                "localField": "configkey",
                "foreignField": "configurekey",
                "as": "executionDetails"
            }
        },
        {
            "$unwind": "$executionDetails"
        },
        {
            "$match": {
                "executionDetails.status": {"$in": ["fail", "Fail"]},
                "executionDetails.starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": {
                    "token": "$configkey",
                    "profilename": "$profilename",
                    "appType": "$appType"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "Profile Name": "$_id.profilename",
                "appType": "$_id.appType",
                "Fail Count": "$count",
                "_id": 0
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_execution_mode_defects(projectid, userid, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid,
            }
        },
        {
            "$project": {
                "_id": 0,
                "configkey": "$executionData.configurekey",
                "profilename": "$executionData.configurename",
                "executionMode": "$executionData.exectionMode",
            }
        },
        {
            "$lookup": {
                "from": "executions",
                "localField": "configkey",
                "foreignField": "configurekey",
                "as": "executionDetails"
            }
        },
        {
            "$unwind": "$executionDetails"
        },
        {
            "$match": {
                "executionDetails.status": {"$in": ["fail", "Fail"]},
                "executionDetails.starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": {
                    "profilename": "$profilename",
                    "executionMode": "$executionMode"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "Profile Name": "$_id.profilename",
                "Execution Mode": "$_id.executionMode",
                "Fail Count": "$count",
                "_id": 0
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline


def pipeline_project_level_defects(projectid, userid, start_datetime, end_datetime, sort_order=None, limit_count=None):
    pipeline = [
        {
            "$match": {
                "executionData.batchInfo.projectId": projectid,
                "session.userid": userid,
            }
        },
        {
            "$project": {
                "_id": 0,
                "projectName": {"$arrayElemAt": ["$executionData.batchInfo.projectName", 0]}  ,
                "configkey": "$executionData.configurekey"
            }
        },
        {
            "$lookup": {
                "from": "executions",
                "localField": "configkey",
                "foreignField": "configurekey",
                "as": "executionDetails"
            }
        },
        {
            "$unwind": "$executionDetails"
        },
        {
            "$match": {
                "executionDetails.status": {"$in": ["fail", "Fail"]},
                "executionDetails.starttime": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": {
                "projectName": "$projectName"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "Project Name": "$_id.projectName",
                "Fail Count": "$count",
                "_id": 0
            }
        }
    ]

    if sort_order is not None:
        pipeline.append({"$sort": {"Fail Count": sort_order}})

    if limit_count is not None:
        pipeline.append({"$limit": limit_count})

    return pipeline

