import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

from rest import *

mcm = restful(dev=True)

# example to edit a request parameter(-s) and save it back in McM

#__req_to_update = "HIG-Summer12-01257" # doesn't exists
__req_to_update = "HIG-Summer12-02358"
__field_to_update = "time_event"

# get a the dictionnary of a request
req = mcm.getA("requests", __req_to_update)

if "prepid" not in req:
    # in case the request doesn't exists there is nothing to update
    print("Request doesn't exist")
else:
    print("Request's '%s' BEFORE update: %s" % (__field_to_update, req[__field_to_update]))

    # modify what we want
    # time_event is a list for each sequence step
    req[__field_to_update] = [55]

    # push it back to McM
    answer = mcm.updateA('requests', req)
    print(answer)

    req2 = mcm.getA("requests", __req_to_update)
    print("Request's '%s' AFTER update: %s" %(__field_to_update, req2[__field_to_update]))
