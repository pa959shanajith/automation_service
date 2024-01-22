from bson import ObjectId
import pipelines
from utils import *

##########################################################################################
################################### COMMON FUNCTIONS #####################################
##########################################################################################

# Summary if no data found in the database
no_data_summary = "No Data Found for requested query."
exeception_summary = """Regrettably, the requested data is not available at the moment. Kindly pose another question, and I'll be happy to assist you further."""


# Mapping for returned data type
data_type = {
    "table": "table",
    "chart": "chart",
    "text": "text",
    "table/chart": "table/chart"
}


# Mapping for chart type
chart_type = {
    "category1": ["bar", "pie", "doughnut"],
    "category2": ["line"]
}


# Function for database connection
def mongo_connection(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
        return dbsession
    except Exception as e:
        return e
    

# Function to convert dates in mongo comparable format
def date_conversion(request):
    start_time = request["starttime"]
    end_time = request["endtime"]

    formatted_starttime = start_time + " 00:00:00.000Z"
    formatted_endtime = end_time + " 23:59:59.999Z"
    start_datetime = datetime.strptime(formatted_starttime, "%Y-%m-%d %H:%M:%S.%fZ")
    end_datetime = datetime.strptime(formatted_endtime, "%Y-%m-%d %H:%M:%S.%fZ")

    return start_datetime, end_datetime


class DataPreparation:

    # Function to process tabular data
    def process_table_data(dbsession, collectionname, pipeline):
        collection = getattr(dbsession, collectionname)
        result = list(collection.aggregate(pipeline))
        return result


    def process_final_chart_data(**kwargs):
        # Access the desired values from kwargs
        xtitle = kwargs.get("x_title", "")
        ytitle = kwargs.get("y_title", "")
        labels = kwargs.get("labels", [])
        backgroundColor = kwargs.get("backgroundColor", [])
        chartsData = kwargs.get("chartsData", [])
        chartType = kwargs.get("chartType", [])
        displayLegend = kwargs.get("displayLegend", "false")

        if chartType in ["doughnut"]:
            data = {
                "title": xtitle,
                "labels": labels,
                "backgroundColor": backgroundColor,
                "chartsData": chartsData,
                "chartType": chartType,
                "displayLegend": displayLegend
            }

        else:
            data = {
                "xtitle": xtitle,
                "ytitle": ytitle,
                "labels": labels,
                "backgroundColor": backgroundColor,
                "chartsData": chartsData,
                "chartType": chartType,
                "displayLegend": displayLegend
            }
        return data


    def merge_table_and_chart_data(tabledata, chartdata):
        merged_data = {"table_data": tabledata, "chart_data": chartdata}
        return merged_data



##########################################################################################
################################# EXECUTION FUNCTIONS ####################################
##########################################################################################

# Function fetches all the projects the user is assigned to along with their role names
def list_of_projects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        userid = requestdata["sender"]

        # Collection name for the pipeline
        collection_name = "users"
        summary = "Please find the list of projects assigned to you along with the roles."
                     
        # Data processing
        try:
            data_pipeline = pipelines.fetch_projects(userid=userid)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
            else:
                # Arguments for the chart data
                x_title = ""
                color = "#36a2eb"
                charttype = "doughnut"
                labels = "Total Projects"
                chartdata = len(table_result)
                chart_result = None

                chart_result = DataPreparation.process_final_chart_data(
                    x_title=x_title,
                    labels=labels,
                    backgroundColor=color,
                    chartsData=chartdata,
                    chartType=charttype,
                    displayLegend="true"
                )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch the users assigned in a specific project with their roles
def list_of_users(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]

        # Collection name for the pipeline
        collection_name = "users"
        summary = "Here is the list of users assigned to the same project, along with their respective roles."

        # Data processing
        try:
            data_pipeline = pipelines.fetch_users(projectid=projectid)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
            else:
                # Arguments for the chart data
                x_title = ""
                color = "#147524"
                charttype = "doughnut"
                labels = "Users Count"
                chartdata = len(table_result)
                chart_result = None

                chart_result = DataPreparation.process_final_chart_data(
                    x_title=x_title,
                    labels=labels,
                    backgroundColor=color,
                    chartsData=chartdata,
                    chartType=charttype,
                    displayLegend="true"
                )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary
 
        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch the list of modules executed in a project or profile
def list_module_executed(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_list_module_executed(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = ""
                color = "#754e14"
                charttype = "doughnut"
                labels = "Count of modules"
                chartdata = len(table_result)
                chart_result = None

                chart_result = DataPreparation.process_final_chart_data(
                    x_title=x_title,
                    labels=labels,
                    backgroundColor=color,
                    chartsData=len(table_result),
                    chartType=charttype,
                    displayLegend="true"
                )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch the count of modules executed in a project or profile
def count_module_executed(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Collection name for the pipeline
        collection_name = "executions"

        # Data processing
        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = (
                f"Here's the count of modules you've executed in the '{profile_name}' profile "
                f"between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}:"
            ) 
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Here's the count of modules you've executed in the '{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}:"

        try:
            data_pipeline = pipelines.pipeline_count_module_executed(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Module Names"
                y_title = "Times Executed"
                color = "#754e14"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Module Name'])
                    chartdata.append(d['Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch modules with their execution statuses for all the profiles in a project
def modules_execution_status(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Collection name for the pipeline
        collection_name = "executions"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_modules_execution_status(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            
            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Statuses"
                y_title = "Count"
                charttype = "trend"
                labels = ["Total", "Pass", "Fail", "Queued", "Inprogress"]
                datasets = []

                for modules in table_result:
                    datasets.append({
                        'label': modules['module_name'],
                        'data': [modules['total_count'], modules['fail_count'], modules['pass_count'], modules['queued_count'], modules['inprogress_count']],
                        'fill': False,
                        'borderColor': f'rgb({np.random.randint(0, 256)}, {np.random.randint(0, 256)}, {np.random.randint(0, 256)})',
                        'tension': 0.1
                    })

                chartdata = {'datasets': datasets}

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["chart"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=None, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch each module execution frequency in a project or profile
def each_module_execution_frequency(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Collection name for the pipeline
        collection_name = "executions"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_each_module_execution_frequency(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Module Names"
                y_title = "Count"
                color = "#754e80"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Module Name'])
                    chartdata.append(d['Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch the maximum number of times a module is being executed in a project or profile
def highest_number_of_module_executions(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"
        title = "Count of modules"
        color = "#754e14"
        charttype = "bar"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_highest_number_of_module_executions(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            print(table_result)
        except Exception as e:
            table_result = None

        labels = []
        chartdata = []
        for d in table_result:
            labels.append(d['Module Name'])
            chartdata.append(d['Count'])

        chart_result = None
        if table_result:
            chart_result = DataPreparation.process_final_chart_data(
                title=title,
                labels=labels,
                backgroundColor=color,
                chartsData=chartdata,
                chartType=charttype,
                displayLegend="true"
            )

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)

        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch the minimum number of times a module is being executed in a project or profile
def lowest_number_of_module_executions(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"
        title = "Count of modules"
        color = "#754e14"
        charttype = "bar"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_lowest_number_of_module_executions(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            print(table_result)
        except Exception as e:
            table_result = None

        labels = []
        chartdata = []
        for d in table_result:
            labels.append(d['Module Name'])
            chartdata.append(d['Count'])

        chart_result = None
        if table_result:
            chart_result = DataPreparation.process_final_chart_data(
                title=title,
                labels=labels,
                backgroundColor=color,
                chartsData=chartdata,
                chartType=charttype,
                displayLegend="true"
            )

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)

        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function fetches the failure rate of module in a project or profile
def failure_rate_for_module(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)
    
        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]
        profileid = requestdata["metadata"]["profileid"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"
        title = "Count of modules"
        color = "#754e14"
        charttype = "bar"

        if profileid:
            profile_name = list(dbsession.configurekeys.find({"token": profileid}))[0]["executionData"]["configurename"]
            tokens = [profileid]
            summary = f"Given below is the list of modules that have been executed for '{profile_name}' profile during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"
        else:
            project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
            token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
            token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
            tokens = [tokens["token"] for tokens in token_values]
            summary = f"Given below is the list of modules that have been executed in '{project_name}' project during {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')} time range:"

        try:
            data_pipeline = pipelines.pipeline_failure_rate_for_module(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            print(table_result)
        except Exception as e:
            table_result = None

        labels = []
        chartdata = []
        for d in table_result:
            labels.append(d['Module Name'])
            chartdata.append(d['Failure Rate'])

        chart_result = None
        if table_result:
            chart_result = DataPreparation.process_final_chart_data(
                title=title,
                labels=labels,
                backgroundColor=color,
                chartsData=chartdata,
                chartType=charttype,
                displayLegend="true"
            )

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)

        return datatype, summary, result
    
    except Exception as e:
        return e




##########################################################################################
################################### DEFECT FUNCTIONS #####################################
##########################################################################################

# Function to fetch modules with fail counts for all the profiles in a project
def module_level_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "Presented herein is the comprehensive module-level defect trend analysis for the "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows how many times a module is failing in the mentioned time period in a project."
        )

        try:
            data_pipeline = pipelines.pipeline_module_level_defects_trend_analysis(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Module Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Module Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch top five modules with more fail count for all the profiles in a project
def module_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "Presented herein is the summary of modules with more defects for "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows what modules are failing more number of times in the mentioned time period in a project."
        )

        try:
            data_pipeline = pipelines.pipeline_module_with_more_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Module Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Module Names'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch top 5 modules with less fail count for all the profiles in a project
def module_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "Presented herein is the summary of modules with less defects for "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows what modules are failing less number of times in the mentioned time period in a project."
        )

        try:
            data_pipeline = pipelines.pipeline_module_with_less_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Module Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Module Names'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch number of failed modules for all the profile in a project
def profile_level_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of profile-level defect trend analysis under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows the count of failed modules for all profiles in the mentioned time period."
        )

        try:
            data_pipeline = pipelines.pipeline_profile_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Profile Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Profile Names'])
                    chartdata.append(d['Failed Modules'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch top 5 profiles with higher number of failed modules in a project
def profile_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five profiles with maximum number of failed modules under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_profile_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Profile Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Profile Names'])
                    chartdata.append(d['Failed Modules'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch top 5 profiles with less number of failed modules in a project
def profile_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five profiles with minimum number of failed modules under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_profile_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Profile Names"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Profile Names'])
                    chartdata.append(d['Failed Modules'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch execution environment level defect trend analysis for all the profiles in a project
def execution_environment_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the test steps fail count for each execution environment under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_execution_environment_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Browser"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Browser'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch execution environment with more fail count for all the profiles in a project
def execution_environment_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top five execution environment with maximum test steps fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_execution_environment_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Browser"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Browser'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch execution environment with less fail count for all the profiles in a project
def execution_environment_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top five execution environment with minimum test steps fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_execution_environment_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Browser"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Browser'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch TestCase level defect trend analysis for all the profiles in a project
def test_scenario_level_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "reports"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the fail count trend analysis for each TestCase under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [exeid['_id'] for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_test_scenario_level_defects(executionids=exe_objids)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Test Scenarios"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Test Scenario Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch TestCase with more fail count for all the profiles in a project
def test_scenario_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "reports"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top 5 TestCases with maximum fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [exeid['_id'] for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_test_scenario_level_defects(executionids=exe_objids, sort_order=-1, limit_count=5)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Test Scenarios"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Test Scenario Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch TestCase with less fail count for all the profiles in a project
def test_scenario_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "reports"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top 5 TestCases with minimum fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [exeid['_id'] for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_test_scenario_level_defects(executionids=exe_objids, sort_order=1, limit_count=5)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Test Scenarios"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Test Scenario Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch Browser Version level defect trend analysis for all the profiles in a project
def browser_version_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the fail count trend analysis for each Browser Version under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_browser_version_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                chart_result = None

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch Browser Version with more fail count for all the profiles in a project
def browser_version_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top 5 Browser Versions with maximum fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_browser_version_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                chart_result = None

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch Browser Version with less fail count for all the profiles in a project
def browser_version_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "executions"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the top 5 Browser Version with minimum fail count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_browser_version_defects(tokens=tokens, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                chart_result = None

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e


# Function to fetch keyword level fail count trend analysis for all the profiles in a project
def keyword_level_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "reportitems"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "The data showing the fail count trend analysis for each keyword under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [str(exeid['_id']) for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_keyword_level_defects(executionids=exe_objids)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Keyword Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Keyword Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e
    

# Function to fetch keyword with top five maximum number of fail counts for all the profiles in a project
def keyword_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        collection_name = "reportitems"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "Given below is the summary of top five keywords with maximum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [str(exeid['_id']) for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_keyword_level_defects(executionids=exe_objids, sort_order=-1, limit_count=5)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Keyword Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Keyword Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e
    

# Function to fetch keyword with top five minimum number of fail counts for all the profiles in a project
def keyword_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)
        collection_name = "reportitems"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        token_pipeline = pipelines.fetch_tokens(projectid=projectid, userid=userid)
        token_values = list(dbsession.configurekeys.aggregate(token_pipeline))
        tokens = [tokens["token"] for tokens in token_values]
        summary = (
            "Given below is the summary of top five keywords with minimum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            # Fetching unique execution ids for given configurekeys
            executionid_pipeline = pipelines.fetch_executionids(tokens=tokens, start_datetime=starttime, end_datetime=endtime)
            mod_execids = list(dbsession.executions.aggregate(executionid_pipeline))
            
            if mod_execids:
                exe_objids = [str(exeid['_id']) for exeid in mod_execids]
                data_pipeline = pipelines.pipeline_keyword_level_defects(executionids=exe_objids, sort_order=1, limit_count=5)
                table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)
            else:
                table_result = None

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Keyword Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Keyword Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch app type level fail count and profile names trend analysis in a project
def app_type_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of app type defect trend analysis under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows the count of failed app type and profiles in the mentioned time period."
        )

        try:
            data_pipeline = pipelines.pipeline_app_type_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch app type with top five maximum number of fail counts for all the profiles in a project
def app_type_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five app types with maximum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows the count of failed app type and profiles in the mentioned time period."
        )

        try:
            data_pipeline = pipelines.pipeline_app_type_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e
    

# Function to fetch app type with top five minimum number of fail counts for all the profiles in a project
def app_type_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five app types with minimum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows the count of failed app type and profiles in the mentioned time period."
        )

        try:
            data_pipeline = pipelines.pipeline_app_type_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch execution mode  level fail count and profile names trend analysis in a project
def execution_mode_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of execution mode defect trend analysis under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
            "This data shows the count of failed execution mode and profiles in the mentioned time period."
        )

        try:
            data_pipeline = pipelines.pipeline_execution_mode_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch execution mode with top five maximum number of fail counts for all the profiles in a project
def execution_mode_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five execution mode with maximum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_execution_mode_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e
    

# Function to fetch execution mode with top five minimum number of fail counts for all the profiles in a project
def execution_mode_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five execution mode with minimum number of failed count under "
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_execution_mode_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None
                
            else:
                chart_result = None
                
        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result

    except Exception as e:
        return e


# Function to fetch project level fail counts
def project_level_defects_trend_analysis(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of project level defect trend analysis under"
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_project_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Project Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Project Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch project level fail counts with top five maximum number of fail counts
def project_with_more_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five projects with maximum number of failed count under"
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_project_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=-1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Project Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "line"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Project Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e
    

# Function to fetch project level fail counts with top five minimum number of fail counts
def project_with_less_defects(requestdata, client, getClientName):
    try:
        dbsession = mongo_connection(requestdata, client, getClientName)

        # fetch required data from request
        projectid = requestdata["projectid"]
        userid = requestdata["sender"]

        # fetch and convert the date format
        starttime, endtime = date_conversion(request=requestdata)

        # Values for the response
        collection_name = "configurekeys"

        # Data processing
        project_name = list(dbsession.projects.find({"_id": ObjectId(projectid)}))[0]["name"]
        summary = (
            "Given below is the summary of top five projects with minimum number of failed count under"
            f"'{project_name}' project between {starttime.strftime('%d/%m/%Y')} and {endtime.strftime('%d/%m/%Y')}. "
        )

        try:
            data_pipeline = pipelines.pipeline_project_level_defects(projectid=projectid, userid=userid, start_datetime=starttime, end_datetime=endtime, sort_order=1, limit_count=5)
            table_result = DataPreparation.process_table_data(dbsession=dbsession, collectionname=collection_name, pipeline=data_pipeline)

            # Check if table_result is None
            if not table_result:
                summary = no_data_summary
                table_result = None
                chart_result = None

            else:
                x_title = "Project Name"
                y_title = "Fail Count"
                color = "#BEAD0B"
                charttype = "bar"
                labels = []
                chartdata = []
                chart_result = None

                for d in table_result:
                    labels.append(d['Project Name'])
                    chartdata.append(d['Fail Count'])

                # Generating Chart Data
                chart_result = DataPreparation.process_final_chart_data(
                        x_title=x_title,
                        y_title=y_title,
                        labels=labels,
                        backgroundColor=color,
                        chartsData=chartdata,
                        chartType=charttype,
                        displayLegend="true"
                    )

        except Exception as e:
            table_result = None
            chart_result = None
            summary = exeception_summary

        datatype = data_type["table/chart"] if table_result else data_type["text"]
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    
    except Exception as e:
        return e



##########################################################################################
################################### DEFAULT FUNCTIONS ####################################
##########################################################################################
    
def default_fallback(requestdata, client, getClientName):
    try:
        datatype = data_type["text"]
        table_result = None
        chart_result = None
        summary = "I'm sorry, I don't have an answer for that right now. I'll learn and improve over time. Please ask another question."
        
        result = DataPreparation.merge_table_and_chart_data(tabledata=table_result, chartdata=chart_result)
        return datatype, summary, result
    except Exception as e:
        return e