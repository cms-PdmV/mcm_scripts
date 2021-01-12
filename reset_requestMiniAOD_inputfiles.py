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

dest_chained_campaign = 'RunIIFall17MiniAODv2'

#requests = mcm.get('requests', query='member_of_campaign=%s&status=approved' % (dest_chained_campaign))
#requests = mcm.get('requests', query='prepid=SMP*&member_of_campaign=%s&status=approved' % (dest_chained_campaign))
requests = mcm.get('requests', query='prepid=B2G-RunIIFall17MiniAODv2-00246')

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

field_to_update = 'input_dataset'

for request in requests:

    chained_requests = request['member_of_chain']
    
    print len(chained_requests)

    for i in range(0,len(chained_requests)):

        print chained_requests[i]
        
        chained_request =  mcm.get('chained_requests', chained_requests[i])

        answer = mcm._McM__get('restapi/chained_requests/inject/%s' % (chained_request['prepid']))
        print answer
        
        #resetting nanoAOD
        nano_id = chained_request['chain'][3]
        root_nano_req = mcm.get('requests', nano_id) 
        
        answer = mcm._McM__get('restapi/requests/reset/%s' % (root_nano_req['prepid']))        
        print answer

        answer = mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
        print answer
        
        answer = mcm._McM__get('restapi/requests/reset/%s' % (request['prepid']))        
        print answer

for request in requests:
    
    print request['prepid']
    
    chained_requests = request['member_of_chain']
    
    print len(chained_requests)

    input_dataset = 'empty'

    for i in range(0,len(chained_requests)):

        print chained_requests[i]        
        chained_request =  mcm.get('chained_requests', chained_requests[i])

        mini_id = chained_request['chain'][1]
        root_mini_req = mcm.get('requests', mini_id)
        
        print root_mini_req['output_dataset']
        input_dataset = root_mini_req['output_dataset'][0]

    print input_dataset

    request = mcm.get('requests', request['prepid'])

    print request[field_to_update]
    request[field_to_update] = input_dataset

    answer = mcm.update('requests', request)
    print answer
    
    request2 = mcm.get('requests', request['prepid'])
    
    print request2['input_dataset']


for request in requests:

    answer = mcm._McM__get('restapi/requests/approve/%s' % (request['prepid']))               
    print answer
    
    chained_requests = request['member_of_chain']
    
    chained_request =  mcm.get('chained_requests', chained_requests[i])

    #resetting nanoAOD
    nano_id = chained_request['chain'][3]
    root_nano_req = mcm.get('requests', nano_id) 

    answer = mcm._McM__get('restapi/requests/approve/%s' % (root_nano_req['prepid']))        
    print answer
