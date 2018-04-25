#!/usr/bin/env python
## !needs wmcontrol path to be added. run this before the script
#export PATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PATH}
#voms-proxy-init also has to be set

import sys
import time
import subprocess

sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import *

def run_wmpriority(wf, priority):
    p = subprocess.Popen(["wmpriority.py", wf, priority], stdout=subprocess.PIPE)
    out = p.communicate()[0]
    print(out)


if __name__ == '__main__':
    __list_of_requests = ["B2G-PhaseIISpr18AODMiniAOD-00054"]
    mcm = restful(dev=False, cookie='prod-cookie.txt', debug=False)

    for el in __list_of_requests:
        #get request we want to change:
        req = mcm.getA("requests", el, method="get")

        #run actual priority change
        run_wmpriority(req["reqmgr_name"][-1]["name"], "85001")


