import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=False)

# Example to edit a request parameter(-s) and save it back in McM                                                                                                                                            
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist                                                                                                                                            

for i in range(0,20):

    request_prepid_to_update = 'EGM-RunIIFall18GS-000'+str(i)
    field_to_update = 'tags'

# get a the dictionnary of a request                                                                                                                                                                         
    request = mcm.get('requests', request_prepid_to_update)

    if 'prepid' not in request:
        # In case the request doesn't exist, there is nothing to update                                                                                                                                      
        print('Request "%s" doesn\'t exist' % (request_prepid_to_update))
    else:
        print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
                                                            field_to_update,
                                                            request[field_to_update]))
        # Modify what we want                                                                                                                                                                                
        # time_event is a list for each sequence step                                                                                                                                                        
        request[field_to_update] = ["Fall18P1POGGS"]

    # Push it back to McM                                                                                                                                                                                    
        update_response = mcm.update('requests', request)
        print('Update response: %s' % (update_response))

    # Fetch the request again, after the update, to check whether value actually changed                                                                                                                     
        request2 = mcm.get('requests', request_prepid_to_update)
        print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                           field_to_update,
                                                           request2[field_to_update]))
