# NEED this to be sourced before
# export PYTHONPATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PYTHONPATH}
# export PATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PATH}
# source /afs/cern.ch/cms/PPD/PdmV/tools/wmclient/current/etc/wmclient.sh
#

import os
import sys
import subprocess
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

from rest import *

mcm = restful(dev=True)

results = mcm.getA("requests", query="tags=M17p1A")
print("Found %s requests" % (len(results)))

for el in results:
    if len(el["reqmgr_name"]):
        # we change priority only if request has a registered workflow
        # remove echo command to acutally execute it
        ret = os.system("echo 'wmpriority.py %s %s'" % (el["reqmgr_name"][-1]["name"], 90000))
        if ret != 0:
            print("\t change of priority failed for: %s" % (el["prepid"]))
    else:
        print("Workflow is not registered for %s" %(el["prepid"]))
