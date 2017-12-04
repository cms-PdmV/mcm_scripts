import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

from rest import *

mcm = restful(dev=True)

# example to create a request from input dictionary
# get a default dictionnary with the minimal info required
new_req = {'pwg':'HIG', 'member_of_campaign':'Summer12'}

# push it to McM
answer = mcm.putA('requests', new_req)

if answer['results']:
    print("new prepid:", answer['prepid'])
