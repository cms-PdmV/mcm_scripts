import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=True)

# Example to edit a request parameter(-s) and save it back in McM
request_prepid_to_update = 'PPD-RunIIWinter19PFCalib16GS-00001'

request_to_update = mcm.get('requests', request_prepid_to_update)
print request_to_update

field_to_update = 'ppd_tags'
    
print('Request\'s "%s" field "%s" BEFORE update: %s' % (request_prepid_to_update,
                                                        field_to_update,
                                                        request_to_update[field_to_update]))

# Modify what we want
request_to_update[field_to_update] = ["PFCalibPOG16"]

# Push it back to McM
update_response = mcm.update('requests', request_to_update)
print('Update response: %s' % (update_response))

# Fetch the request again, after the update, to check whether value actually changed
request2 = mcm.get('requests', request_prepid_to_update)
print('Request\'s "%s" field "%s" AFTER update: %s' % (request_prepid_to_update,
                                                           field_to_update,
                                                           request2[field_to_update]))
