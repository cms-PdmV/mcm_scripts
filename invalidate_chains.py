"""
Get all requests in given range.
Take all chained requests that these requests are members of.
Leave only those chained requests that have MiniAODv3 in their name.
Skip (remove) chained request with biggest number (the last one).
For all chained requests that are left in the list, set action_parameters.flag to False,
delete requests in them if these requests appear only in that chained request,
delete chained request itself.
"""
import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

# McM instance
mcm = McM(dev=False, cookie='/afs/cern.ch/user/p/pgunnell/private/prod-cookie.txt')

# Iterate through all requests in the range

chain_prepid = 'chain_RunIIFall18pLHE_*Fall18GS*_flowRunIIFall18DR*'

chains = mcm.get('chained_campaigns', query='prepid=%s' % (chain_prepid))

for chain in chains:

    print chain['prepid']
    
    chain['valid'] = False

    answer=mcm.update('chained_campaigns', chain)

    print answer
