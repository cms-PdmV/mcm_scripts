# NEED this to be sourced before
# export PYTHONPATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PYTHONPATH}
# export PATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PATH}
# source /afs/cern.ch/cms/PPD/PdmV/tools/wmclient/current/etc/wmclient.sh

import os
import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=True)

requests = mcm.get('requests', query='tags=M17p1A')
print('Found %s requests' % (len(requests)))

for request in requests:
    if len(request['reqmgr_name']) > 0:
        # We change priority only if request has a registered workflow
        # Remove echo command to acutally execute it
        # Change priority to 90000
        result = os.system("echo 'wmpriority.py %s %s'" % (request['reqmgr_name'][-1]['name'], 90000))
        if result != 0:
            print('Change of priority failed for: %s. Exit code: %s' % (request['prepid'], result))
    else:
        print('Workflow is not registered for %s' % (request['prepid']))
