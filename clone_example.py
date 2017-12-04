import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

from rest import *

mcm = restful(dev=True)


# script clones a request to other campaign.
# define list modifications, if member_of_campaign is different
# it will clone to other campaign

modif = {'extension' : 1, 'total_events' : 101, 'member_of_campaign': 'Summer12'}
__req_prepid = "SUS-RunIIWinter15wmLHE-00040"

# get a request object which we want to clone
a_request = mcm.getA('requests', __req_prepid)

# make predefined modifications
for el in modif:
    a_request[el] = modif[el]

answer = mcm.clone(a_request['prepid'], a_request)
print("new_prepid: %s" % (answer["prepid"]))
