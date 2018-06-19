import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=True)

# Example to get  ALL requesst which are member of a given campaign and are submitted
# It uses a generic search for specified columns: query='status=submitted'
# Queries can be combined: query='status=submitted&member_of_campaign=Summer12'
all_requests = mcm.get('requests', query='member_of_campaign=Summer12&status=submitted')
for request in all_requests:
    print(request['prepid'])

# Example to retrieve single request dictionary
# More methods are here:
# https://cms-pdmv.cern.ch/mcm/restapi/requests/
single_request_prepid = 'TOP-Summer12-00368'
single_request = mcm.get('requests', single_request_prepid, method='get')
print('Single request "%s":\n%s' % (single_request_prepid, dumps(single_request, indent=4)))
