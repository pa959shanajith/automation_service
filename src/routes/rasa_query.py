# Dictionary to store the type of presentable data
data_type = {
    1: "table",
    2: "chart",
    3: "text",
    4: "table/chart"
}

##########################################################################################
#################################### MONGO FUNCTIONS #####################################
##########################################################################################

def list_of_projects(requestdata, client, getClientName):
    try:
        clientName = getClientName(requestdata)
        dbsession = client[clientName]
    except Exception as e:
        return e
    
    try:
        datatype = data_type[1]
        result = list(dbsession.projects.find({}, {"name":1}))
        return datatype, result
    except Exception as e:
        return e
    
def default_fallback():
    try:
        datatype = data_type[3]
        result = "I'm sorry, I don't have an answer for that right now. I'll learn and improve over time. Please ask another question."
        return datatype, result
    except Exception as e:
        return e