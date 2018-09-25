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

requests_query = """
    EXO-RunIIWinter15wmLHE-00333 -> EXO-RunIIWinter15wmLHE-00500
"""

list_of_requests = mcm.get_range_of_requests(requests_query)
# Iterate through all requests in the range
for request in list_of_requests:
    print('\n\nProcessing %s' % (request['prepid']))
    # Get chains that this request is member of. Leave only those that have MiniAODv3 in them
    # Sort prepids, so biggest number would be last
    member_of_chains = sorted(request.get('member_of_chain', []))
    member_of_chains = [chain for chain in member_of_chains if 'MiniAODv3' in chain]
    if len(member_of_chains) <= 1:
        print('%s is member of none or one chain. Skipping' % (request['prepid']))
        continue

    #print('Will leave %s' % (member_of_chains[-1]))
    # Leave the last (with biggest number) chain
    #member_of_chains = member_of_chains[:-1]

    print('Will delete:')
    for chain_prepid in member_of_chains:
        print('    %s' % (chain_prepid))

    for chain_prepid in member_of_chains:
        print('Deleting %s' % (chain_prepid))
        chain = mcm.get('chained_requests', chain_prepid)
        chain['action_parameters']['flag'] = False
        mcm.update('chained_requests', chain)
        requests_in_chain = mcm.get('requests', query='member_of_chain=%s' % (chain_prepid))

        requests_inverted = []

        for request_in_chain in requests_in_chain:
            
            requests_inverted.append(request_in_chain)

        requests_inverted = list(reversed(requests_inverted))

        for request_in_chain in requests_inverted:

            print ("Which requests are in the chain? "+str(request_in_chain['prepid']))

            if((request_in_chain['prepid'].find("NanoAODv3")) and (request_in_chain['status'] == "submitted")):
                print (' Found '+str(chain_prepid))
                chain['action_parameters']['flag'] = True
                continue

            if len(request_in_chain.get('member_of_chain', [])) > 1:
                print('    Not deleting %s because it is a member of %d chains' % (request_in_chain['prepid'],
                                                                                   len(request_in_chain.get('member_of_chain', []))))
            else:

                print ('Going to operate in '+str(request_in_chain['prepid']))

                if(request_in_chain['status'] == "new"):
                    #mcm._McM__get('restapi/chained_requests/rewind/%s' % (chain_prepid))
                    #mcm.get('requests', request_in_chain['prepid'], method='none')
                    request_delete_result = mcm.delete('requests', request_in_chain['prepid'])
                    print('    Deleted %s. %s' % (request_in_chain['prepid'], request_delete_result))
                    #chain_delete_result = mcm.delete('chained_requests', chain_prepid)

        chain_delete_result = mcm.delete('chained_requests', chain_prepid)
        print('    Deleted %s. %s' % (chain_prepid, chain_delete_result))
