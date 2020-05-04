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

def getcwd_exe():
    currdir = os.getcwd()
    currexc = sys.executable
    currexcname = os.path.basename(currexc).replace(".exe", '')
    try: currfiledir = os.path.dirname(os.path.abspath(__file__))
    except: currfiledir = os.path.dirname(currexc)
    if currexcname == "ndac_service":
        currdir = os.path.dirname(currexc)
    elif currexcname == "python" or currexcname.lower() == "pythonservice":
        currdir = currfiledir
    return currdir

class NDAC_Service_Manager(win32serviceutil.ServiceFramework):
    _svc_name_ = "nineteen68NDAC"
    _svc_display_name_ = "Nineteen68 NDAC Service"
    _svc_description_ = "Nineteen68 Data Access Components Service"
    _exe_name_ = "ndac_service.exe" if os.path.basename(sys.executable).replace(".exe", '') == "ndac_service" else "pythonservice.exe"
    child_process_name = "ndac.exe"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
              servicemanager.PYS_SERVICE_STARTED, (self._svc_name_,''))
        self.startFlow()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
          servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_,''))
        self.stopFlow()
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def startFlow(self):
        os.chdir(os.path.dirname(sys.executable))
        servicemanager.LogInfoMsg(self._svc_display_name_+" ("+self._svc_name_+") is RUNNING.")
        rc = None

        cwd = getcwd_exe()
        os.chdir(cwd)
        run_cmd = self.child_process_name
        if not os.path.isfile(run_cmd):  # This is a dev ENV. Run ndac.py
            run_cmd = cwd+os.sep+"python "+cwd+os.sep+"ndac.py"
        if os.path.exists("./ndac_internals/logs/conf.txt"):
            env_in = open("./ndac_internals/logs/conf.txt",'r')
            env_conf = env_in.read().replace(' ','').replace('\n','').replace('\r','')
            env_in.close()
            if len(env_conf) > 0:
                run_cmd += " -" + env_conf
        self.child_process = subprocess.Popen(run_cmd, shell=True)

        while rc != win32event.WAIT_OBJECT_0:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
        servicemanager.LogInfoMsg(self._svc_display_name_+" ("+self._svc_name_+") is STOPPED.")

    def stopFlow(self):
        subprocess.call("TASKKILL /F /PID {pid} /T".format(pid = self.child_process.pid))


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
