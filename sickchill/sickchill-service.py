import multiprocessing
import os.path
import sys

import servicemanager
import SickChill
import win32service
import win32serviceutil


class SickChillService(win32serviceutil.ServiceFramework):
    _svc_name_ = "sickchill"
    _svc_display_name_ = "sickchill service"
    _svc_description_ = "Runs sickchill web service in the background."
    _exe_name_ = sys.executable
    _exe_args_ = f"-u -E {os.path.abspath(__file__)}"

    proc = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.proc:
            self.proc.terminate()

    def SvcRun(self):
        self.proc = multiprocessing.Process(target=SickChill.main)
        self.proc.start()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.SvcDoRun()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

    def SvcDoRun(self):
        self.proc.join()


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        if len(sys.argv) == 1:
            import win32traceutil

            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(SickChillService)
            servicemanager.StartServiceCtrlDispatcher()
        elif "--fg" in sys.argv:
            sys.argv.remove("--fg")
            SickChill.main()
        else:
            win32serviceutil.HandleCommandLine(SickChillService)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception:
        import traceback

        traceback.print_exc()
