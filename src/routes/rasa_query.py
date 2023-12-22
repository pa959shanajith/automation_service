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
        result = dbsession.projects.find({}, {"name":1})
        return result
    except Exception as e:
        return e