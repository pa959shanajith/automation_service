from bson import ObjectId

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
            "$lookup": {
                "from": "testsuites",
                "localField": "_id",
                "foreignField": "_id",
                "as": "Module Name"
            }
        },
        {
            "$project": {
                "Module Name": {"$arrayElemAt": ["$Module Name.name",0]},
                "Count": 1,
                "_id":0
            }
        },
        {
            "$sort": {
                "Count": -1
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


def pipeline_profile_level_defects_trend_analysis(projectid, userid, start_datetime, end_datetime):
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
        },
        {
            "$sort": {"Failed Modules": -1}
        }
    ]
    return pipeline


def pipeline_profile_with_more_defects(projectid, userid, start_datetime, end_datetime):
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
        },
        {
            "$sort": {"Failed Modules": -1}
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_profile_with_less_defects(projectid, userid, start_datetime, end_datetime):
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
        },
        {
            "$sort": {"Failed Modules": 1}
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_execution_environment_defects_trend_analysis(tokens, start_datetime, end_datetime):
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
    return pipeline


def pipeline_execution_environment_with_more_defects(tokens, start_datetime, end_datetime):
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
        },
        {
            "$sort": {
                "Fail Count": -1 
            }
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_execution_environment_with_less_defects(tokens, start_datetime, end_datetime):
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
        },
        {
            "$sort": {
                "Fail Count": 1 
            }
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_test_scenario_level_defects_trend_analysis(executionids):
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["Fail", "fail"]},
                "executionid": { "$in": executionids}
        }
        },
        {
            "$project": {
                "testscenarioid": 1,
                "_id": 0
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
            "$project": {
                "testscenarioid": {"$arrayElemAt": ["$matchedTestScenarios._id", 0]},
                "name": {"$arrayElemAt": ["$matchedTestScenarios.name", 0]}
            }
        },
        {
            "$group": {
                "_id": "$name",
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
    return pipeline


def pipeline_test_scenario_with_more_defects(executionids):
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["Fail", "fail"]},
                "executionid": { "$in": executionids}
        }
        },
        {
            "$project": {
                "testscenarioid": 1,
                "_id": 0
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
            "$project": {
                "testscenarioid": {"$arrayElemAt": ["$matchedTestScenarios._id", 0]},
                "name": {"$arrayElemAt": ["$matchedTestScenarios.name", 0]}
            }
        },
        {
            "$group": {
                "_id": "$name",
                "defect_count": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Test Scenario Name": "$_id",
                "Fail Count": "$defect_count"
            }
        },
        {
            "$sort": {
                "Fail Count": -1
            }
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_test_scenario_with_less_defects(executionids):
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["Fail", "fail"]},
                "executionid": { "$in": executionids}
        }
        },
        {
            "$project": {
                "testscenarioid": 1,
                "_id": 0
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
            "$project": {
                "testscenarioid": {"$arrayElemAt": ["$matchedTestScenarios._id", 0]},
                "name": {"$arrayElemAt": ["$matchedTestScenarios.name", 0]}
            }
        },
        {
            "$group": {
                "_id": "$name",
                "defect_count": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Test Scenario Name": "$_id",
                "Fail Count": "$defect_count"
            }
        },
        {
            "$sort": {
                "Fail Count": 1
            }
        },
        {
            "$limit": 5
        }
    ]
    return pipeline


def pipeline_keyword_level_defects_trend_analysis(executionids):
    # Define the aggregation pipeline
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
                        "defect_count": {"$sum": 1}
                    }
                }
            ]
    return pipeline


def pipeline_keyword_with_more_defects(executionids):
    # Define the aggregation pipeline
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
                        "defect_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {
                        "defect_count": -1
                    }
                },
                {
                    "$limit": 2
                }
            ]
    return pipeline
      

def pipeline_keyword_with_less_defects(executionids):
    # Define the aggregation pipeline
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
                        "defect_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {
                        "defect_count": 1
                    }
                },
                {
                    "$limit": 2
                }
            ]
    return pipeline


def pipeline_browser_version_defects_trend_analysis(token_values, starttime, endtime):
    # Define the aggregation pipeline
    pipeline = [
                {
                    "$match": {
                        "configurekey": {"$in": token_values}, 
                        "status": {"$in": ["Fail", "fail"]}, 
                        "starttime": {"$gte": starttime, "$lte":endtime}
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
                        "browserVersion": "$reportdata.overallstatus.browserVersion",
                    },
                    "defect_count": { "$sum": 1 }
                    }
                },
                {
                    "$project": {
                    "_id": 0,
                    "browserVersion": "$_id.browserVersion",
                    "defect_count": 1
                    }
                }
                ]
                
    return pipeline


def pipeline_browser_version_with_more_defects(token_values, starttime, endtime):
    # Define the aggregation pipeline
    pipeline = [
                {
                    "$match": {
                        "configurekey": {"$in": token_values}, 
                        "status": {"$in": ["Fail", "fail"]}, 
                        "starttime": {"$gte": starttime, "$lte":endtime}
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
                        "browserVersion": "$reportdata.overallstatus.browserVersion",
                    },
                    "defect_count": { "$sum": 1 }
                    }
                },
                {
                    "$project": {
                    "_id": 0,
                    "browserVersion": "$_id.browserVersion",
                    "defect_count": 1
                    }
                },
                {
                    "$sort": {
                        "defect_count": -1 
                    }
                },
                {
                    "$limit": 2
                } 
                ]
                
    return pipeline


def pipeline_browser_version_with_less_defects(token_values, starttime, endtime):
    # Define the aggregation pipeline
    pipeline = [
                {
                    "$match": {
                        "configurekey": {"$in": token_values}, 
                        "status": {"$in": ["Fail", "fail"]}, 
                        "starttime": {"$gte": starttime, "$lte":endtime}
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
                        "browserVersion": "$reportdata.overallstatus.browserVersion",
                    },
                    "defect_count": { "$sum": 1 }
                    }
                },
                {
                    "$project": {
                    "_id": 0,
                    "browserVersion": "$_id.browserVersion",
                    "defect_count": 1
                    }
                },
                {
                    "$sort": {
                        "defect_count": 1 
                    }
                },
                {
                    "$limit": 2
                } 
                ]
                
    return pipeline
