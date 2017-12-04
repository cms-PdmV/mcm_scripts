import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

from rest import *

mcm = restful(dev=True)

# example to search  ALL requesst which are member of a campaign
# it uses a generic search for specified columns: query='status=submitted'
# queries can be combined: query='status=submitted&member_of_campaign=Summer12'

allRequests = mcm.getA('requests',query='member_of_campaign=Summer12&status=submitted')
for r in allRequests:
    print(r['prepid'])

# example to retrieve single request dictionary
# more methods are here:
# https://cms-pdmv.cern.ch/mcm/restapi/requests/

single_request = 'TOP-Summer12-00368'
__single = mcm.getA('requests', single_request, method='get')
print("Single request prepid: %s" % (__single['prepid']))