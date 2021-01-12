import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False,cookie='/afs/cern.ch/user/p/pgunnell/private/prod-cookie.txt')

# Example to edit a request parameter(-s) and save it back in McM
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist


for i in range(0,28): print str(0)+','
          
for i in range(28,63): print str(0.029411)+','

#pwgPOG = ['MUO','EGM','TAU','BTV','TSG','HCA','EXO']
pwgPOG = ['JME']
#pwgPAG = ['HIG','SUS','SMP','EXO','BPH','TOP']

campaigns = ['GS','DR','DRPremix']

for i in range(1,50):

    #request_prepid_to_update = 'BTV-RunIIFall18DRPremix-000'+str(i)
    for name in pwgPOG:

        if i<10:
            request_prepid_to_update = name+'-RunIIAutumn18DR-0000'+str(i)
        else:
            request_prepid_to_update = name+'-RunIIAutumn18DR-000'+str(i)
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
            request[field_to_update] = ["Autumn18P1POGDR","Autumn18P1JMEDR"]
            
        # Push it back to McM
            update_response = mcm.update('requests', request)
            print('Update response: %s' % (update_response))
            
        # Fetch the request again, after the update, to check whether value actually changed
            request2 = mcm.get('requests', request_prepid_to_update)
            print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                           field_to_update,
                                                           request2[field_to_update]))
