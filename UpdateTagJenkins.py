import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False)

# Example to edit a request parameter(-s) and save it back in McM
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist

tagstoupdate=['Moriond18','POG','PAG','Moriond16','Moriond17']

for tags in tagstoupdate:
    if(tags=='Moriond18'):
        requests = mcm.get('requests', query='priority=110000&status=submitted&prepid=*Autumn18DR*')
    #requests = mcm.get('requests', query='priority=110000&status=submitted&prepid=*Autumn18*HEM*')
    if(tags=='Moriond18'):
        requests = mcm.get('requests', query='priority=90000&status=submitted&prepid=*Autumn18DR*')
    if(tags=='Moriond17'):
        requests = mcm.get('requests', query='priority=90000&status=submitted&prepid=*Fall17DR*')
    if(tags=='Moriond16'):
        requests = mcm.get('requests', query='priority=90000&status=submitted&prepid=*Summer16DR*')
    if(tags=='PAG'):
        requests = mcm.get('requests', query='priority=85000&status=submitted&prepid=*Autumn18DR*')

    for request in requests:
        
        request_prepid_to_update = request['prepid']
        
        field_to_update = 'tags'
        
        print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
                                                                field_to_update,
                                                                request[field_to_update]))
        
        if(len(request['tags'])==0):
        
            if(tags=='Moriond17'):
                request[field_to_update] = ["Fall17P1Moriond19DR"]
            if(tags=='Moriond16'):
                request[field_to_update] = ["Summer16P1Moriond19DR"]
            #request[field_to_update] = ["Autumn18P1Moriond19DR","Autumn18POGP1DRblock2"]
            if(tags=='Moriond18'):
                request[field_to_update] = ["Autumn18P1Moriond19DR"]
            if(tags=='POG'):
                request[field_to_update] = ["Autumn18POGP1DR"]
            #request[field_to_update] = ["Autumn18PAGP1DR","Autumn18POGP1DRblock3"]
            if(tags=='PAG'):
                request[field_to_update] = ["Autumn18PAGP1DR"]
            #request[field_to_update] = ["Autumn18POGP1DR","Autumn18JMEP1DR"]
        
        # Push it back to McM
            update_response = mcm.update('requests', request)
            print('Update response: %s' % (update_response))
            
        # Fetch the request again, after the update, to check whether value actually changed
            request2 = mcm.get('requests', request_prepid_to_update)
            print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                               field_to_update,
                                                               request2[field_to_update]))
        
