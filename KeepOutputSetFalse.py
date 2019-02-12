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

requests = mcm.get('requests', query='prepid=B2G-RunIIFall18wmLHEGS-0008*&status=approved')

field_to_update = 'keep_output'

for request in requests:

    print request['prepid']
    if(request['prepid']!='HIN-HINPbPbAutumn18GS-00033'):
    #print('https://cms-pdmv.cern.ch/mcm/requests?prepid='+str(request['prepid'])+'\n')
        keepOutput = request['keep_output']
        print keepOutput
        
        if keepOutput==[True]:
            
            request[field_to_update] = [False]
        # Push it back to McM
            update_response = mcm.update('requests', request)
            print('Update response: %s' % (update_response))
            
    #print (str(request['history'][0]['updater']['submission_date'])+'\n')
    






        

