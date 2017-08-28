# -*- coding: utf-8 -*-
"""
Created on Tue May 23 16:20:02 2017

@author: Yashi.Gupta
"""

# Data Setup from SQLite File

try:
    # File to read the Data from SQLite File into an array.
    import sqlite3
except:
    print "Error Imprting module sqlite."


class SQLite_DataSetup():
    try:
        def __init__(self):
            self.questions=[] # to store the questions
            self.pages=[] # to store the pages
            self.keywords=[] # to store the keywords
            self.weightages=[] # to store the weightages
            self.answers=[] # to store the answers
            self.pquestions=[] #preprocessed questions
            self.newQuesInfo=[] #list to store relevant info about new questions
    except:
        print "Error in __init__ function."



        # Function to Load Data using JSON file.
    def loadData(self):
       # print "wfsdvaqusgwnqbwh"
        import os
        #print "OS.cwd()------------",os.getcwd()
        base = os.getcwd()
        path = base + "\\Portable_python\\ProfJ.db"
        conn = sqlite3.connect(path)
        c = conn.cursor()
           # print data

        # Preparing the lists
        for row in c.execute('SELECT * FROM mainDB'):

            self.weightages.append(int(row[1]))
            self.questions.append(row[2])
            self.answers.append(row[3])

            self.keywords.append(row[4])
            self.pages.append(row[5])

            self.pquestions.append(row[6])


        for col in c.execute('SELECT * FROM NewQuestions'):
            info =[]
            info.append(col[1])
            info.append(col[2])
            info.append(col[3])

            self.newQuesInfo.append(info)
        conn.close()




    try:
        # Function to get the Pages.
        def getPages(self):
            return self.pages
    except:
        print "Error in getPages()"

    try:
        # Function to return the Questions.
        def getQuestions(self):
            return self.questions
    except:
        print "Error in getQuestions()"

    try:
        # Function to return the Answers.
        def getAnswers(self):
            return self.answers
    except:
        print "Error in getAnswers()"

    try:
        # Function to retun the Weights.
        def getWeightages(self):
            return self.weightages
    except:
        print "Error in getWeightages()"

    try:
        # Function to return Keywords.
        def getKeywords(self):
            return self.keywords
    except:
        print "Error in getKeywords()"

    try:
        # Function to get the Processed Questions.
        def getPQuestions(self):
            return self.pquestions
    except:
        print "Error in getPQuestions()"

    try:
        # Function to get the New Questions.
        def getNewQuesInfo(self):
            return self.newQuesInfo
    except:
        print "Error in getNewQuesInfo()"

    try:
        # Function to update the captured Queries.
        def updateCaptureTable(self,savedQueries):
            t = []
            for list in savedQueries:
                temp = []
                temp.append(list[0])
                temp.append(list[1])
                temp1 = tuple(temp)
                t.append(temp1)
            #print t
            #inserting values in table:
            conn = sqlite3.connect('ProfJ.db')
            c = conn.cursor()
            c.executemany('INSERT INTO CapturedQueries VALUES (?,?)', t)
            conn.commit()
            for row in c.execute('SELECT * FROM CapturedQueries'):
                print row
            conn.close()
            return savedQueries
    except:
        print "Error in updateCaptureTable()"
##
##    try:
##            # Function to update the weightages in Database[Used periodically by thread].
##            def updateWeightages(self,weightages):
##                print "inside update weightages..."
##                conn = sqlite3.connect('ProfJ.db')
##                c = conn.cursor()
##                for i in range(len(weightages)):
##                    c.execute('UPDATE mainDB SET Weightage= ? WHERE qid = ?',(weightage[i],i))
##                conn.commit()
##                conn.close()
##                return True
##    except:
##            print "Error in updateCaptureTable()"

    try:
        # Function to update the new questions in the database.
        def updateCaptureTable(self):
            return True
    except:
        print "Error in updateCaptureTable()"