# NEED this to be sourced before
#voms-proxy-init -voms cms
#export X509_USER_PROXY=$(voms-proxy-info --path)
#export PYTHONPATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PYTHONPATH}
#export PATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PATH}
# source /afs/cern.ch/cms/PPD/PdmV/tools/wmclient/current/etc/wmclient.sh

import os
import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=False)

#requests = mcm.get('requests', query='tags=Summer16MiniAODv3T2sub1&priority=90000')
#requests = mcm.get('requests', query='tags=Summer16MiniAODv3T2sub2&priority=90000')
#requests = mcm.get('requests', query='priority=85000&status=submitted&prepid=*Autumn18DR*')
requests = mcm.get('requests', query='status=submitted&tags=PAGLHCP2019&priority=85000')
#requests = mcm.get('requests', query='prepid=EXO-RunIIFall17GS-009*&dataset_name=Mustar*')
#requests = mcm.get('requests', query='status=submitted&tags=Summer16MiniAODv3T3')
#requests = mcm.get('requests', query='status=submitted&prepid=HIG-PhaseIIMTDTDRAutumn18wmLHEGS-0000*')
#requests = mcm.get('requests', query='status=submitted&dataset_name=VBF_BulkGravToWW_narrow_M-*')
#requests = mcm.get('requests', query='status=submitted&prepid=SMP-*LowPU*GS*')

#requests = mcm.get('requests', query='prepid=BPH-RunIIFall18GS-0006*')
print('Found %s requests' % (len(requests)))

for request in requests:
    if len(request['reqmgr_name']) > 0:
        # We change priority only if request has a registered workflow
        # Remove echo command to acutally execute it -> already removed
        # Change priority to 200000
        result = os.system("wmpriority.py %s %s" % (request['reqmgr_name'][-1]['name'], 86000))
        if result != 0:
            print('Change of priority failed for: %s. Exit code: %s' % (request['prepid'], result))
        else:
            print result
    else:
        print('Workflow is not registered for %s' % (request['prepid']))


