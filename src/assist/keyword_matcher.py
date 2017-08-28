# -*- coding: utf-8 -*-
"""
Created on Mon May 22 15:31:40 2017

@author: yashi.gupta
"""

try:
    import logging
    import logging.config
    from nltk.stem import PorterStemmer
    import simplejson
except:
    print "Error in importing core modules ProfJ"


class ProfJ():

    def Preprocess(self,query_string):
        #creating configuration for logging
        import os
        #print "OS.cwd()------------",os.getcwd()
        base = os.getcwd()
        path = base + "\\Portable_python\\ndac\\src\\assist\\logging_config.conf"
        logging.config.fileConfig(path,disable_existing_loggers=False)

        # Create logger object. This will be used for logging.
        logger = logging.getLogger("ProfJ")

        logger.info("Qustion asked is "+query_string)

        #Step 1: Punctuations Removal
        query1_str = "".join(c for c in query_string if c not in ('@','!','.',':','>','<','"','\'','?','*','/','&','(',')','-'))
        #print "Query after Step 1 of processing:[punctuations removed] ",query1_str

        #Step 2: Converting string into lowercase
        query2 = [w.lower() for w in query1_str.split()]
        query2_str = " ".join(query2)
        #print "Query after Step 2 of processing:[lower Case] ",query2_str


        #Step 3: Correcting appostropes.. Need this dictionary to be quite large
        APPOSTOPHES = {"s" : "is", "'re" : "are","m":"am"}
        words = (' '.join(query2_str.split("'"))).split()
        query5 = [ APPOSTOPHES[word] if word in APPOSTOPHES else word for word in words]
        #print "Query after Step 3 of processing:[appostophes]: ",query5

        import simplejson
        #Step 4: Normalizing words
        path = base + "\\Portable_python\\ndac\\src\\assist\\SYNONYMS.json"
        with open(path,"r") as data_file:
                SYNONYMS = simplejson.load(data_file)
        query6 = [ SYNONYMS[word] if word in SYNONYMS else word for word in query5]
        #print "Query after Step 6 of processing:[synonyms]: ",query6


        #Step 5: Stemming
        ps = PorterStemmer()
        query_final=set([ps.stem(i) for i in query6])
        #print "Query after Step 7 of processing:[stemming] ",query_final
        return query_final


    def matcher(self,query_final):
        intersection = []
        for q in self.pquestions:
            q1 = set (q.split(" "))
           # print "Supposedly Questions", q1
            intersection.append (len(query_final & q1))
           # print len(query_final & q1)
        return intersection

    def getTopX(self,intersection):
        relevance=[]
        cnt = 0
        for i in intersection:
            relevance.append(10**(i+2) + self.weights[cnt])
            cnt+=1

        max_index = [i[0] for i in sorted(enumerate(relevance), key=lambda x:x[1],reverse=True)]
        #max_value = [i[1] for i in sorted(enumerate(relevance), key=lambda x:x[1],reverse=True)]

        #print max_value
        # print max_index
        ans = []
        #print "-------------------------------------------------"
        for i in range(self.topX):
            #print questions_original[max_index[i]]
            if(intersection[max_index[i]]==0):
                break
            ans.append(self.questions[max_index[i]])
            #print (self.questions[max_index[i]]+ "( Intersection: "+str(intersection[max_index[i]])+ " Weightage: "+str(self.weights[max_index[i]])+")")
        #print "-------------------------------------------------"
        return ans

    def calculateRel(self,query_final):
            try:
                #Check whether query contains n68 domain or not
                import sys
                import os
                base = os.getcwd()
                path = base + "\\Portable_python\\ndac\\src\\assist\\keywords_db.txt"
                f = open(path,"r")
                key = f.read()
                keywords = set(key.split())

                if (len(query_final)==0):
                    match=0
                else:
                    match=len(query_final & keywords)/float(len(query_final))
                #print "Percentage Match [In my domain]", match*100,"%"
                return match
            except:
                print "keywords_db.txt not foud."

    def __init__(self,pages,questions,answers,keywords,weights,pquestions, newQuesInfo, savedQueries):
        self.questions = questions
        self.pages = pages
        self.weights = weights
        self.answers = answers
        self.keywords = keywords
        self.pquestions = pquestions
        self.newQuesInfo = newQuesInfo
        self.topX = 5
        self.userQuery=""
        self.savedQueries = savedQueries # Captures all the "Relevant" queries asked by User, It is list of list[[query1,page1],[query2,page2]]

    def setState(self,state):
        self.state = state

    def start(self,userQuery):
        response = []
        #print "I am the right one"
        query_string = userQuery
        self.userQuery = userQuery
        if query_string is not None:
            #when all the plugins will be activeted
            currPage = "mindmaps"
            query_final = self.Preprocess(query_string)
            rel = self.calculateRel(query_final)
            if (rel > 0):
                temp = []
                temp.append(query_string)
                temp.append(currPage)
                self.savedQueries.append(temp)
                #getting intersection
                intersection = self.matcher(query_final)
                #displaying most common and most frequent
                ques = self.getTopX(intersection)
                if ques:
                    for i in range(len(ques)):
                        temp = []
                        temp.append(self.questions.index(ques[i]))
                        temp.append(self.questions[self.questions.index(ques[i])])
                        temp.append(self.answers[self.questions.index(ques[i])])
                        response.append(temp)
                   # print response
                else:
                    response = [[-1,"Sometimes, I may not have the information you need...We recorded your query..will get back to you soon",-1]]
                    flag = True
                    for nques in self.newQuesInfo:
                        if(str(query_final) is nques[1]):
                            nques[2] = nques[2] + 1
                            flag = False
                    if (flag):
                        temp =[]
                        temp.append(str(query_string))
                        temp.append(str(query_final))
                        temp.append(0)
                        self.newQuesInfo.append(temp)

                    #self.newKeys.append(query_string)
            else:
                response = [[-1, "Please be relevant..I work soulfully for Nineteen68", -1]]
        else:
            response = [-1, "Invalid Input...Please try again", -1]
        return response, self.newQuesInfo, self.savedQueries


