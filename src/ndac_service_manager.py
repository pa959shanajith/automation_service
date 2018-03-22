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
import os, sys
import subprocess

class NDAC_Service_Manager(win32serviceutil.ServiceFramework):
    _svc_name_ = "nineteen68NDAC"
    _svc_display_name_ = "Nineteen68 NDAC Service"
    _svc_description_ = "Nineteen68 Data Access Components Service"
    _exe_name_ = sys.executable

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
        os.chdir(os.path.dirname(sys.executable))
        servicemanager.LogInfoMsg(self._svc_display_name_+" ("+self._svc_name_+") is RUNNING.")
        rc = None

        run_cmd = "ndac.exe"
        if os.path.exists("./ndac_internals/logs/conf.txt"):
            env_in = open("./ndac_internals/logs/conf.txt",'r')
            env_conf = env_in.read().split(',')
            env_in.close()
            if len(env_conf[0]) > 0:
                run_cmd += " -" + env_conf[0]
            if len(env_conf) > 1 and env_conf[1] == "true":
                run_cmd += " -k offlineuser.key"
        main_process = subprocess.Popen(run_cmd, shell=True)

        while rc != win32event.WAIT_OBJECT_0:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)

        subprocess.call("TASKKILL /F /IM ndac.exe /T")
        servicemanager.LogInfoMsg(self._svc_display_name_+" ("+self._svc_name_+") is STOPPED .")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(NDAC_Service_Manager)
            servicemanager.StartServiceCtrlDispatcher()
        except:
            win32serviceutil.HandleCommandLine(NDAC_Service_Manager)
    else:
        win32serviceutil.HandleCommandLine(NDAC_Service_Manager)
