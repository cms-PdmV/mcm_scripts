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

dest_chained_campaign = 'RunIISummer16MiniAODv3'

#requests = mcm.get('requests', query='member_of_campaign=%s&status=new&tags=Summer16MiniAODv3T1' % (dest_chained_campaign))
requests = mcm.get('requests', query='member_of_campaign=%s&status=new&tags=Summer16MiniAODv3T4' % (dest_chained_campaign))
#requests = mcm.get('requests', query='prepid=B2G*&member_of_campaign=%s&approval=submit&status=approved&tags=Summer16MiniAODv3T3' % (dest_chained_campaign))

print len(requests)

i=0

for request in requests:
    
    #answer = mcm._McM__get('restapi/requests/approve/%s' % (request['prepid']))        

    #continue

    i+=1

    chained_requests = request['member_of_chain']
    
    chained_request =  mcm.get('chained_requests', chained_requests[0])  

    root_id = chained_request['chain'][0]
    root_id_req = mcm.get('requests', root_id) 

    root_gs = chained_request['chain'][1]
    root_gs_req = mcm.get('requests', root_gs) 

    root_gsdr = chained_request['chain'][2]
    root_gsdr_req = mcm.get('requests', root_gsdr) 
   
    if(root_id_req['status']=='done' and root_gs_req['status']=='done'):

        print str(request['prepid'])+' '+str(request['dataset_name'])

        #answer = mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
        #print answer

        #answer = mcm._McM__get('restapi/chained_requests/rewind/%s' % (chained_request['prepid']))
        #print answer

        answer = mcm._McM__get('restapi/chained_requests/flow/%s' % (chained_request['prepid']))
        print answer

        #answer = mcm._McM__get('restapi/requests/approve/%s' % (request['prepid']))        
        #print answer
    
        root_dr = chained_request['chain'][2] 
        root_dr_req = mcm.get('requests', root_dr) 

        root_dr1 = chained_request['chain'][3] 
        root_dr1_req = mcm.get('requests', root_dr1) 

        answer = mcm._McM__get('restapi/chained_requests/inject/%s' % (chained_request['prepid']))

        if(len(chained_request['chain'])>4):

            print 'wmLHE request'
            root_dr3 = chained_request['chain'][4] 
            root_dr3_req = mcm.get('requests', root_dr3) 

            if('NanoAODv3' in root_dr3_req['prepid']):
                answer = mcm._McM__get('restapi/requests/approve/%s' % (root_dr3_req['prepid']))        
                print answer

        if('NanoAODv3' in root_dr_req['prepid']):
            answer = mcm._McM__get('restapi/requests/approve/%s' % (root_dr_req['prepid']))        
            print answer

        if('NanoAODv3' in root_dr1_req['prepid']):
            answer = mcm._McM__get('restapi/requests/approve/%s' % (root_dr1_req['prepid']))        
            print answer

        #update tag
            #request_prepid_to_update = request['prepid']

#        field_to_update = 'tags'

 #       print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
#                                                                field_to_update,
#                                                                request[field_to_update]))

        # Modify what we want
  #      request[field_to_update] = ["Summer16MiniAODv3T2","Summer16MiniAODv3T2sub2"]

        # Push it back to McM
   #     update_response = mcm.update('requests', request)
     #   print('Update response: %s' % (update_response))
    #       
        # Fetch the request again, after the update, to check whether value actually changed
        #request2 = mcm.get('requests', request_prepid_to_update)
        #print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
        #                                                       field_to_update,
        #                                                       request2[field_to_update]))

     #   print request['input_dataset']

#EXO and SUS done (7+77)
#SMP done (5 requests)
#TOP done (3 requests)
#HIG done (3 requests)
