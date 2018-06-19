import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=True)

# Example to create a request from input dictionary
# Get a default dictionary with the minimal info required
new_request = {'pwg': 'HIG', 'member_of_campaign': 'Summer12'}

# push it to McM
put_answer = mcm.put('requests', new_request)

if put_answer.get('results'):
    print('New PrepID: %s' % (put_answer['prepid']))
else:
    print('Something went wrong while creating a request. %s' % (dumps(put_answer)))
