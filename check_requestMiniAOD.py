import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=True)

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

# Get a request object which we want to clone
#chained_requests = mcm.get('chained_requests', 'B2G-chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3-00208')

priority=63000

for i in range(2552,2623):
    request = mcm.get('requests', query='status=submitted&prepid=B2G-RunIISummer16MiniAODv2-0'+str(i)+'&priority='+str(priority))

    if(request):
        print request[0]['prepid']

        prepid = request[0]['prepid']
        answer = mcm._McM__put('restapi/requests/add_forcecomplete', {'prepid': prepid})
        print answer
