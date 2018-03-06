#-------------------------------------------------------------------------------
# Name:        ndac_service_manager
# Purpose:     Deploys NDAC as a service
#
# Author:      ranjan.agrawal
#
# Created:     02-03-2018
# Copyright:   (c) ranjan.agrawal 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import win32service
import win32serviceutil
import win32event
import servicemanager
import os
import subprocess
##LS_SERVICE = "nineteen68LS"

class NDAC_Service_Manager(win32serviceutil.ServiceFramework):
    _svc_name_ = "nineteen68NDAC"
    _svc_display_name_ = "Nineteen68 NDAC Service"
    _svc_description_ = "Nineteen68 Data Access Components Service"
    _exe_name_ = os.path.normpath(os.getcwd()+"/Lib/site-packages/win32/pythonservice.exe")

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
              servicemanager.PYS_SERVICE_STARTED, (self._svc_name_,''))
        self.main()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
          servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_,''))
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def main(self):
        ##serv_stat=None
        ##try:
        ##    serv_stat = win32serviceutil.QueryServiceStatus(LS_SERVICE)
        ##except:
        ##    pass
        ##if serv_stat is None:
        ##    servicemanager.LogErrorMsg("License Server Service ("+LS_SERVICE+") NOT found.\n"
        ##        +self._svc_display_name_+" ("+self._svc_name_+") is NOT Started.")
        ##elif serv_stat[1] == 1:
        ##    servicemanager.LogErrorMsg("License Server Service ("+LS_SERVICE+") is in STOPPED state.\n"
        ##        +self._svc_display_name_+" ("+self._svc_name_+") is NOT Started.")
        ##elif serv_stat[1] == 4:
        os.chdir(os.path.normpath(os.getcwd()+"/../../.."))
        servicemanager.LogInfoMsg(self._svc_display_name_+" ("+self._svc_name_+") is RUNNING.")
        rc = None

        main_process = subprocess.Popen("ndac.exe", shell=True)

        while rc != win32event.WAIT_OBJECT_0:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)

        subprocess.Popen("TASKKILL /F /IM ndac.exe /T")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(NDAC_Service_Manager)