import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=False)#,int=True,cookie='/afs/cern.ch/user/p/pgunnell/private/int-cookie.txt')

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

# Get a request object which we want to clone
#chained_requests = mcm.get('chained_requests', 'B2G-chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3-00208')

priority=80000

for i in range(2397,2446):
    requests = mcm.get('requests', query='status=submitted&prepid=HIG-RunIIFall17MiniAODv2-0'+str(i)+'&priority='+str(priority))

#requests = mcm.get('requests', query='status=submitted&prepid=*-RunIISummer18*')

    for request in requests:
        print request['prepid']
    
        prepid = request['prepid']
        answer = mcm._McM__put('restapi/requests/add_forcecomplete', {'prepid': prepid})
        print answer
