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

#dest_chained_campaign = 'RunIIFall17MiniAODv2'

#requests = mcm.get('requests', query='member_of_campaign=%s&status=approved&prepid=*' % (dest_chained_campaign))
#requests = mcm.get('requests', query='prepid=SUS-RunIIFall17NanoAOD-00082')
#requests = mcm.get('requests', query='prepid=HIG-RunIIFall17MiniAODv2-01676')
#requests = mcm.get('requests', query='member_of_campaign=%s&status=new&prepid=*' % (dest_chained_campaign))

dest_chained_campaign = 'TOP-RunIISummer16MiniAODv3-00171,TOP-RunIISummer16MiniAODv3-00175'
#requests = mcm.get('requests', query='range=%s' % (dest_chained_campaign))
requests = mcm.get('requests', query='prepid=TOP-RunIISummer16MiniAODv3-00172')

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

print 'Dataset name                                   PrepID root request                                         Link to PrepID root request'

for request in requests:

    chained_requests = request['member_of_chain']
    print chained_requests

    for i in range(0,len(chained_requests)):
        if('Premix' in chained_requests[i]):

            chained_request =  mcm.get('chained_requests', chained_requests[i])
            
            root_id = chained_request['chain'][0]
            root_id_req = mcm.get('requests', root_id)    
        
            dr_id = chained_request['chain'][1]
            root_dr_req = mcm.get('requests', dr_id)    
        
            dr_id = chained_request['chain'][2]
            root_dr_req = mcm.get('requests', dr_id)    

            mini_id = chained_request['chain'][3]
            root_mini_req = mcm.get('requests', mini_id)    
        
            if(len(chained_request['chain'])>3):
                nano_id = chained_request['chain'][4]
                root_nano_req = mcm.get('requests', nano_id)    
                #if(root_mini_req['status']=='approved' and root_mini_req['approval']=='submit'):
                #answer = mcm._McM__get('restapi/requests/reset/%s' % (root_mini_req['prepid']))
                #print answer
                #if(root_nano_req['status']!='done'):
                #answer = mcm._McM__get('restapi/requests/reset/%s' % (root_nano_req['prepid']))
                #print answer
            
                mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
            #mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
            #mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))

                chained_request['action_parameters']['flag'] = False
                answer = mcm.update('chained_requests', chained_request)
                print answer
                print chained_request['action_parameters']['flag']

                answer =  mcm.delete('requests', root_nano_req['prepid'])
                print answer

                answer =  mcm.delete('requests', root_mini_req['prepid'])
                print answer





