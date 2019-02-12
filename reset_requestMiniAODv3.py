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

dest_chained_campaign = 'RunIISummer16NanoAODv3'

#requests = mcm.get('requests', query='member_of_campaign=%s&status=submitted&prepid=HIG*' % (dest_chained_campaign))
requests = mcm.get('requests', query='member_of_campaign=%s&status=submitted' % (dest_chained_campaign))

print len(requests)

for request in requests:

    chained_requests = request['member_of_chain']
    
    chained_request =  mcm.get('chained_requests', chained_requests[0])  

    root_id = chained_request['chain'][0]
    root_id_req = mcm.get('requests', root_id) 

    root_gs = chained_request['chain'][1]
    root_gs_req = mcm.get('requests', root_gs) 
   
    if(root_id_req['status']=='done' and root_gs_req['status']=='done'):

        print str(request['prepid'])+' '+str(request['dataset_name'])

        answer = mcm._McM__get('restapi/requests/reset/%s' % (request['prepid']))        
        print answer
    
        root_dr = chained_request['chain'][2] 
        root_dr_req = mcm.get('requests', root_dr) 

        root_dr1 = chained_request['chain'][3] 
        root_dr1_req = mcm.get('requests', root_dr1) 

        if('MiniAODv3' in root_dr_req['prepid']):
            answer = mcm._McM__get('restapi/requests/reset/%s' % (root_dr_req['prepid']))        
            print answer

        if('MiniAODv3' in root_dr1_req['prepid']):
            answer = mcm._McM__get('restapi/requests/reset/%s' % (root_dr1_req['prepid']))        
            print answer
