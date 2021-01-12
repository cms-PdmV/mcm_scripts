import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=False)

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

list_of_nonflowing = "list_of_nonflowing_chains"

# Get a request object which we want to clone
chained_requests = mcm.get('lists', list_of_nonflowing,method='get')

chained_requests = chained_requests['value']

# Make predefined modifications
print len(chained_requests)

for i in range(0,len(chained_requests)):

    if (chained_requests[i]['chain'].find('MiniAODv3') != -1):

        print chained_requests[i]['chain']

        mcm._McM__get('restapi/chained_requests/flow/%s/force' % (chained_requests[i]['chain']))
