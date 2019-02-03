import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False)

# Example to edit a request parameter(-s) and save it back in McM
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist

#requests = mcm.get('requests', query='priority=110000&status=submitted&prepid=*Autumn18DR*')
#requests = mcm.get('requests', query='status=submitted&tags=Summer16MiniAODv3T2sub2')
#requests = mcm.get('requests', query='status=submitted&member_of_campaign=*MiniAODv3&prepid=HIG*')
requests = mcm.get('requests', query='member_of_campaign=*MiniAODv3&prepid=HIG*')
#requests = mcm.get('requests', query='status=submitted&tags=Summer16MiniAODv3T4')
#requests = mcm.get('requests', query='tags=Summer16MiniAODv3T2')

#requests = mcm.get('requests', query='tags=Autumn18P1POGDR')

i=0

for request in requests:

    i+=1
    print i

    request_prepid_to_update = request['prepid']
    request_prepid_to_update_req = mcm.get('requests', request_prepid_to_update)

    print request_prepid_to_update

    chained_request_id = request['member_of_chain'][0]
    chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))

    request1_to_check = chained_requests[0]['chain'][0]
    request2_to_check = chained_requests[0]['chain'][1]

    request1_to_check_if_done = mcm.get('requests', request1_to_check)
    request2_to_check_if_done = mcm.get('requests', request2_to_check)

    if(request1_to_check_if_done['status']!='done' or request2_to_check_if_done['status']!='done'):
        continue

    if('Summer16MiniAODv3T1' in request_prepid_to_update_req['tags']):
        continue

    if('Summer16MiniAODv3T2' in request_prepid_to_update_req['tags']):
        continue

    if('Summer16MiniAODv3T3' in request_prepid_to_update_req['tags']):
        continue
    
    if('Summer16MiniAODv3T4' in request_prepid_to_update_req['tags']):
        continue

    for entry in request_prepid_to_update_req.get('history',[]):
        if ('2019-01-24' in entry['updater']['submission_date'] and 'Paolo' in entry['updater']['author_name']):

            field_to_update = 'tags'
    
            print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
                                                                field_to_update,
                                                                request[field_to_update]))

    # Modify what we want
            request[field_to_update] = ["Summer16MiniAODv3T4"]
    #request[field_to_update] = [""]
        
    # Push it back to McM
            update_response = mcm.update('requests', request)
            print('Update response: %s' % (update_response))
    
    # Fetch the request again, after the update, to check whether value actually changed
            request2 = mcm.get('requests', request_prepid_to_update)
            print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                                   field_to_update,
                                                                   request2[field_to_update]))
