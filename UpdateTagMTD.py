import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False)

# Example to edit a request parameter(-s) and save it back in McM
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist

#requests = mcm.get('requests', query='priority=110000&status=submitted&prepid=*Autumn18DR*')
#requests = mcm.get('requests', query='status=submitted&prepid=*MTDTDR*GS*')
requests = mcm.get('requests', query='status=submitted&tags=MTDTDRAutumn18PU200')
#requests = mcm.get('requests', query='tags=Summer16MiniAODv3T2')

#requests = mcm.get('requests', query='tags=Autumn18P1POGDR')

i=0

for request in requests:

    chained_request_id = request['member_of_chain'][0]
    chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))

    if(len(chained_requests[0]['chain'])<3):
        continue

    if('PU0' in chained_requests[0]['prepid']):
        continue

    request_prepid_to_update = chained_requests[0]['chain'][1]

    request_to_update = mcm.get('requests', request_prepid_to_update)

    field_to_update = 'tags'
    
    print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
                                                            field_to_update,
                                                            request_to_update[field_to_update]))

    # Modify what we want
    request_to_update[field_to_update] = ["MTDTDRAutumn18PU200DR"]

    # Push it back to McM
    update_response = mcm.update('requests', request_to_update)
    print('Update response: %s' % (update_response))
            
    # Fetch the request again, after the update, to check whether value actually changed
    request2 = mcm.get('requests', request_prepid_to_update)
    print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                           field_to_update,
                                                           request2[field_to_update]))
