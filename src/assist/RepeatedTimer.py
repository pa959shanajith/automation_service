#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      yashi.gupta
#
# Created:     23/08/2017
# Copyright:   (c) yashi.gupta 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from threading import Timer,Thread,Event


class repeatedTimer():

   def __init__(self,t,hFunction):
      self.t=t
      self.hFunction = hFunction
      self.thread = Timer(self.t,self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t,self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()
