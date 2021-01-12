import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

#mcm = McM(dev=True,cookie='/afs/cern.ch/user/p/pgunnell/private/prod-cookie.txt')
mcm = McM(dev=False)

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

# Get a request object which we want to clone
#chained_requests = mcm.get('chained_requests', 'B2G-chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3-00208')

dest_chained_campaign = 'RunIIFall17DRPremix'

requests = mcm.get('requests', query='member_of_campaign=%s&status=approved' % (dest_chained_campaign))

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

print 'Dataset name                                   PrepID root request                                         Link to PrepID root request'

for request in requests:

    chained_request = request['member_of_chain']
    chained_request =  mcm.get('chained_requests', chained_request[0])

    root_id = chained_request['chain'][0]
    root_id_req = mcm.get('requests', root_id)    

    if(root_id_req['keep_output'][0] != True):

        #print(str(root_id_req['dataset_name'])+'    '+str(root_id_req['prepid'])+'    https://cms-pdmv.cern.ch/mcm/requests?prepid='+str(root_id_req['prepid']))
        print(str(root_id_req['dataset_name']))



        

