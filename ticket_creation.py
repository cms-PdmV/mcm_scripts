import sys
import time
import json
from collections import defaultdict
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM


def chunks(source, chunk_size):
    """
    Yield successive n-sized chunks from source
    """
    for i in range(0, len(source), chunk_size):
        yield source[i:i + chunk_size]


def dr_output_not_saved(list_of_root_request, ochain):
    """
    Verify that all requests have AODSIM output
    """
    set_of_root_request_prepid_without_aodsim = set()
    for root_request_prepid in list_of_root_request:
        crs = mcm.get('chained_requests', query='contains=%s&member_of_campaign=%s' % (root_request_prepid, ochain))

    for cr in crs:
        list_of_dr_request_prepid = [dr for dr in cr['chain'] if 'DR' in dr]
        if len(list_of_dr_request_prepid) == 1:
            dr_request = mcm.get('requests', list_of_dr_request_prepid[0])
            # last step of the request must be saved
            if dr_request['keep_output'][-1]:
                continue
            else:
                set_of_root_request_prepid_without_aodsim.add(root_request_prepid)

        else:
            set_of_root_request_prepid_without_aodsim.add(root_request_prepid)

    # remove not chainable requests from the original list
    list_of_root_request = [r for r in list_of_root_request if r not in set_of_root_request_prepid_without_aodsim]

    return set_of_root_request_prepid_without_aodsim


N_REQUESTS_PER_TICKET = 20
PRIORITY_BLOCK = 2
TICKET_NOTE ='Summer16 miniAODv3/nanoAODv3 reminiAOD'
#org_chained_campaign = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16PremixMiniAODv2_flowRunIISummer16NanoAOD'
#dest_chained_campaign = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'
#org_chained_campaign = 'chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16PremixMiniAODv2_flowRunIISummer16NanoAOD'
#dest_chained_campaign = 'chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3' #chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'

#org_chained_campaign = 'chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16PremixMiniAODv2_flowRunIISummer16NanoAOD'
#dest_chained_campaign = 'chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3' #chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'

org_chained_campaign = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16PremixMiniAODv2_flowRunIISummer16NanoAOD'
dest_chained_campaign = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'

# If dry run is enabled, nothing will be uploaded to McM
dry_run = False #True

# McM instance
#mcm = McM(dev=True, cookie='/afs/cern.ch/work/s/snorberg/miniAODv3/cookie.txt')#/afs/cern.ch/user/j/jrumsevi/private/dev_cookie.txt')
mcm = McM(dev=False)#/afs/cern.ch/user/j/jrumsevi/private/dev_cookie.txt')
# Set list of PWGs here. If no list is set, all PWGs from McM will be used
#pwgs = ['MUO','BTV','JME','TAU','EGM','TSG','SMP','HCA','B2G']
pwgs = ['SUS']
#pwgs = ['SUS','TOP','HIG']
#pwgs = ['BPH']

if not pwgs:
    # Get list of PWGs
    pwgs = mcm._McM__get('restapi/users/get_pwg')['results']

print('Got PWGs: %s' % (pwgs))
# Create a dict of dicts of dicts of integers
collector = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

for pwg in pwgs:
    chained_requests = mcm.get('chained_requests', query='member_of_campaign=%s&pwg=%s' % (org_chained_campaign, pwg))

    print('PWG:%s\tChained requests:%s' % (pwg, len(chained_requests)))
    
    for chained_request in chained_requests:

        root_id = chained_request['chain'][0]
        campaign = root_id.split('-')[1]

        existing_chains = mcm.get('chained_requests', query='contains=%s&pwg=%s' % (root_id, pwg))

        chain_present=False

        for existing_chain in existing_chains:
            #print "Existing chains "+str(existing_chain['prepid'])
            if existing_chain['prepid'].find("chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3") != -1:
                chain_present=True
                                
        if chain_present:
            continue

        collector[pwg][campaign][root_id] += 1
        chain_id = chained_request['prepid']

# Collector now contains all root requests of chains that are member of org_chained_campaign campaign
# It's structured like this: PWG -> campaign name of root request -> request prepid -> count
# print('This is the list of %s requests that are deemed chainable:\n%s' % (pwgs, json.dumps(dict(collector), indent=4)))
all_tickets = []

chained_campaign = mcm.get('chained_campaigns', dest_chained_campaign, method='get')

for pwg in pwgs:
    # Create a ticket for the correct chain
    chained_campaign_prepid = chained_campaign['prepid']

    #print "printing prepid "+str(chained_campaign_prepid)

    root_campaign = chained_campaign['campaigns'][0][0]
    # create tickets with different repetition numbers for root requests
    for repeat in range(10):
        # list of root requests in chained_campaign['prepid'] chained campaign with 'repeat' repetition number
        requests_for_that_repeat = map(lambda i: i[0], filter(lambda i: i[1] == repeat, collector[pwg][root_campaign].items()))
        
        if not requests_for_that_repeat:
            continue

        print "Requests to chain: "+str(requests_for_that_repeat)

        requests_for_that_repeat.sort()
        set_of_invalid_requests = dr_output_not_saved(requests_for_that_repeat, org_chained_campaign)

        if len(set_of_invalid_requests) > 0:
            print('NOT CHAINED: %s' % (set_of_invalid_requests))

        for chunk in chunks(requests_for_that_repeat, N_REQUESTS_PER_TICKET):
                mccm_ticket = {'prepid': pwg,  # this is how one passes it in the first place
                               'pwg': pwg,
                               'requests': chunk,
                               'notes': TICKET_NOTE,
                               'chains': [chained_campaign_prepid],
                               'repetitions': repeat,
                               'block': PRIORITY_BLOCK}
                all_tickets.append(mccm_ticket)

# print(json.dumps(all_tickets, indent=4))
for ticket in all_tickets:
    print('Create ticket:\n%s' % (json.dumps(ticket, indent=4)))
    if not dry_run:
        res = mcm.put('mccms', ticket)
        ticket_prepid = res.get('prepid', None)
        print('Ticket prepid: %s' % (ticket_prepid))
        if ticket_prepid:
            #reserve the requests in the ticket
            mcm._McM__get('restapi/mccms/generate/%s/reserve' % (ticket_prepid))
        else:
            print('Error: no ticket was created')

        # For some reason
        time.sleep(2)


for pwg in pwgs:
    chained_requests = mcm.get('chained_requests', query='member_of_campaign=%s&pwg=%s' % (dest_chained_campaign, pwg))

    for chained_request in chained_requests:

        print chained_request['prepid']

        mcm._McM__get('restapi/chained_requests/flow/%s' % (chained_request['prepid']))
        mcm._McM__get('restapi/chained_requests/flow/%s' % (chained_request['prepid']))
