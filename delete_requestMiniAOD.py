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

#requests = mcm.get('requests', query='member_of_campaign=%s&status=approved&prepid=*' % (dest_chained_campaign))
#requests = mcm.get('requests', query='prepid=SUS-RunIIFall17NanoAOD-00082')
#requests = mcm.get('requests', query='prepid=HIG-RunIIFall17MiniAODv2-01676')
requests = mcm.get('requests', query='member_of_campaign=%s&status=new&prepid=*' % (dest_chained_campaign))

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

print 'Dataset name                                   PrepID root request                                         Link to PrepID root request'

for request in requests:

    chained_requests = request['member_of_chain']
    
    for i in range(0,len(chained_requests)):

        chained_request =  mcm.get('chained_requests', chained_requests[i])

        if(len(chained_request)<2):
            break

        #print chained_request['prepid']

        root_id = chained_request['chain'][0]
        root_id_req = mcm.get('requests', root_id)    
        
        dr_id = chained_request['chain'][1]
        root_dr_req = mcm.get('requests', dr_id)    
        
        mini_id = chained_request['chain'][2]
        root_mini_req = mcm.get('requests', mini_id)    
        
        if(len(chained_request['chain'])>3):
            nano_id = chained_request['chain'][3]
            root_nano_req = mcm.get('requests', nano_id)    

        #if(root_id_req['keep_output'][0] != True and root_id_req['status']=='done' and root_dr_req['status']=='new')
        #if(root_id_req['keep_output'][0] != True and root_id_req['status']=='done' and root_dr_req['status']=='done'):
        if(root_id_req['status']=='done' and root_dr_req['status']=='done' and 'AOD' in root_mini_req['input_dataset']):

            print(str(root_id_req['dataset_name'])+'    '+str(root_id_req['prepid'])+'    https://cms-pdmv.cern.ch/mcm/requests?prepid='+str(root_id_req['prepid']))


            answer = mcm._McM__get('restapi/requests/approve/%s' % (root_mini_req['prepid']))
            answer = mcm._McM__get('restapi/requests/approve/%s' % (root_nano_req['prepid']))
            #mcm._McM__get('restapi/chained_requests/flow/%s/force' % (chained_request['prepid']))

            continue

            chained_request['action_parameters']['flag'] = False
            answer = mcm.update('chained_requests', chained_request)
            print answer

            if(len(chained_request['chain'])>3):
                mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
                #mcm._McM__get('restapi/requests/reset/%s' % (root_nano_req['prepid']))        
                answer =  mcm.delete('requests', root_nano_req['prepid'])
                print answer

            mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
            #mcm._McM__get('restapi/requests/reset/%s' % (root_mini_req['prepid']))        
            answer = mcm.delete('requests', root_mini_req['prepid'])
            print answer

            mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
            #mcm._McM__get('restapi/requests/reset/%s' % (root_dr_req['prepid']))        
            answer = mcm.delete('requests', root_dr_req['prepid'])
            print answer

    continue

    #delete chained campaign after the loop to all chains
    
    for i in range(0,len(chained_requests)):

        chained_request =  mcm.get('chained_requests', chained_requests[i])

        if(len(chained_request)>1):
            
            chain_delete_result = mcm.delete('chained_requests', chained_request['prepid'])

            #print 'Deleted chain '+str(chained_request['prepid'])

        else:
            chain_delete_result = mcm.delete('chained_requests', chained_request)
            #print 'Deleted chain '+str(chained_request)

