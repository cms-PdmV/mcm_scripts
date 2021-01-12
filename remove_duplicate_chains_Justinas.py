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
mcm = McM(dev=True)#, cookie='/afs/cern.ch/user/j/jrumsevi/private/dev_cookie.txt')

requests_query = """
    B2G-RunIIWinter15wmLHE-00035 -> B2G-RunIIWinter15wmLHE-00035
"""
list_of_requests = mcm.get_range_of_requests(requests_query)
# Iterate through all requests in the range
for request in list_of_requests:
    print('\n\nProcessing %s' % (request['prepid']))
    # Get chains that this request is member of. Leave only those that have MiniAODv3 in them
    # Sort prepids, so biggest number would be last
    member_of_chains = sorted(request.get('member_of_chain', []))
    member_of_chains = [chain for chain in member_of_chains if 'MiniAODv3' in chain]

    print member_of_chains

    if len(member_of_chains) <= 1:
        print('%s is member of none or one chain. Skipping' % (request['prepid']))
        continue

    print('Will leave %s' % (member_of_chains[-1]))
    # Leave the last (with biggest number) chain
    member_of_chains = member_of_chains[:-1]
    print('Will delete:')
    for chain_prepid in member_of_chains:
        print('    %s' % (chain_prepid))

    for chain_prepid in member_of_chains:
        print('Deleting %s' % (chain_prepid))
        chain = mcm.get('chained_requests', chain_prepid)
        chain['action_parameters']['flag'] = False
        mcm.update('chained_requests', chain)
        requests_in_chain = mcm.get('requests', query='member_of_chain=%s' % (chain_prepid) )

        print requests_in_chain

        for request_in_chain in requests_in_chain:
            if len(request_in_chain.get('member_of_chain', [])) > 1:
                print('    Not deleting %s because it is a member of %d chains' % (request_in_chain['prepid'],
                                                                                   len(request_in_chain.get('member_of_chain', []))))
            else:
                mcm.get('requests', request_in_chain['prepid'], method='reset')
                request_delete_result = mcm.delete('requests', request_in_chain['prepid'])
                print('    Deleted %s. %s' % (request_in_chain['prepid'], request_delete_result))

        chain_delete_result = mcm.delete('chained_requests', chain_prepid)
        print('    Deleted %s. %s' % (chain_prepid, chain_delete_result))
