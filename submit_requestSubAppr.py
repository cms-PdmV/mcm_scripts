import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=False)

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

# Get a request object which we want to clone
requests = mcm.get('requests', query='status=approved&approval=submit')

print len(requests)

i=0

for request in requests:
    
    chained_requests = request['member_of_chain']

    for chained_request_loop in chained_requests:
        answer = mcm._McM__get('restapi/chained_requests/inject/%s' % (chained_request_loop))
        print answer
