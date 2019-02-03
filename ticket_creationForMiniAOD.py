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
PRIORITY_BLOCK = 3
TICKET_NOTE ='Resubmission of Fall17 not chained requests'

#dest_chained_campaign = 'chain_RunIIFall17wmLHEGS_flowRunIIFall17DRPremixPU2017_flowRunIIFall17MiniAODv2_flowRunIIFall17NanoAOD'
dest_chained_campaign = 'chain_RunIIFall17GS_flowRunIIFall17DRPremixPU2017_flowRunIIFall17MiniAODv2_flowRunIIFall17NanoAOD'

# If dry run is enabled, nothing will be uploaded to McM
dry_run = False

# McM instance
mcm = McM(dev=False)#/afs/cern.ch/user/j/jrumsevi/private/dev_cookie.txt')

requests = []
requests_for_that_repeat = []
i = 0
all_tickets = []

prepids = [
'HIG-RunIIFall17DRPremix-00040',
'HIG-RunIIFall17DRPremix-00041',
'HIG-RunIIFall17DRPremix-00044',
'HIG-RunIIFall17DRPremix-01319',
'HIG-RunIIFall17DRPremix-01318',
'HIG-RunIIFall17DRPremix-01315',
'HIG-RunIIFall17DRPremix-01314',
'HIG-RunIIFall17DRPremix-01316',
'HIG-RunIIFall17DRPremix-01311',
'HIG-RunIIFall17DRPremix-01310',
'HIG-RunIIFall17DRPremix-01313',
'HIG-RunIIFall17DRPremix-01312',
'BTV-RunIIFall17DRPremix-00024',
'HIG-RunIIFall17DRPremix-00069',
'HIG-RunIIFall17DRPremix-00060',
'HIG-RunIIFall17DRPremix-00066',
'HIG-RunIIFall17DRPremix-00067',
'HIG-RunIIFall17DRPremix-01339',
'HIG-RunIIFall17DRPremix-01338',
'HIG-RunIIFall17DRPremix-01333',
'HIG-RunIIFall17DRPremix-01332',
'HIG-RunIIFall17DRPremix-01331',
'HIG-RunIIFall17DRPremix-01330',
'HIG-RunIIFall17DRPremix-01337',
'HIG-RunIIFall17DRPremix-01336',
'HIG-RunIIFall17DRPremix-01335',
'HIG-RunIIFall17DRPremix-01334',
'HIG-RunIIFall17DRPremix-00860',
'HIG-RunIIFall17DRPremix-00311',
'HIG-RunIIFall17DRPremix-00261',
'HIG-RunIIFall17DRPremix-00265',
'HIG-RunIIFall17DRPremix-00080',
'HIG-RunIIFall17DRPremix-00081',
'HIG-RunIIFall17DRPremix-01350',
'HIG-RunIIFall17DRPremix-01353',
'HIG-RunIIFall17DRPremix-01354',
'BPH-RunIIFall17DRPremix-00110',
'BPH-RunIIFall17DRPremix-00111',
'EXO-RunIIFall17DRPremix-00079',
'HIG-RunIIFall17DRPremix-00537',
'HIG-RunIIFall17DRPremix-00538',
'HIG-RunIIFall17DRPremix-00539',
'HIG-RunIIFall17DRPremix-00594',
'HIG-RunIIFall17DRPremix-00595',
'HIG-RunIIFall17DRPremix-00592',
'HIG-RunIIFall17DRPremix-00593',
'HIG-RunIIFall17DRPremix-00185',
'HIG-RunIIFall17DRPremix-01317',
'HIG-RunIIFall17DRPremix-00164',
'HIG-RunIIFall17DRPremix-00574',
'HIG-RunIIFall17DRPremix-00395',
'HIG-RunIIFall17DRPremix-00800',
'HIG-RunIIFall17DRPremix-00801',
'FSQ-RunIIFall17DRPremix-00008',
'FSQ-RunIIFall17DRPremix-00009',
'HIG-RunIIFall17DRPremix-00120',
'HIG-RunIIFall17DRPremix-01298',
'HIG-RunIIFall17DRPremix-01299',
'HIG-RunIIFall17DRPremix-01290',
'HIG-RunIIFall17DRPremix-01291',
'HIG-RunIIFall17DRPremix-01292',
'HIG-RunIIFall17DRPremix-01293',
'HIG-RunIIFall17DRPremix-01294',
'HIG-RunIIFall17DRPremix-01295',
'HIG-RunIIFall17DRPremix-01296',
'HIG-RunIIFall17DRPremix-01297',
'HIG-RunIIFall17DRPremix-01304',
'HIG-RunIIFall17DRPremix-01305',
'BTV-RunIIFall17DRPremix-00114',
'BTV-RunIIFall17DRPremix-00115',
'BTV-RunIIFall17DRPremix-00117',
'BTV-RunIIFall17DRPremix-00111',
'JME-RunIIFall17DRPremix-00008',
'HIG-RunIIFall17DRPremix-00470',
'BPH-RunIIFall17DRPremix-00047',
'BPH-RunIIFall17DRPremix-00071',
'BPH-RunIIFall17DRPremix-00070',
'BPH-RunIIFall17DRPremix-00072',
'BPH-RunIIFall17DRPremix-00075',
'BPH-RunIIFall17DRPremix-00074',
'BPH-RunIIFall17DRPremix-00077',
'BPH-RunIIFall17DRPremix-00076',
'BPH-RunIIFall17DRPremix-00079',
'BPH-RunIIFall17DRPremix-00078',
'HIG-RunIIFall17DRPremix-00315',
'BTV-RunIIFall17DRPremix-00091',
'BTV-RunIIFall17DRPremix-00090',
'BTV-RunIIFall17DRPremix-00093',
'BTV-RunIIFall17DRPremix-00092',
'BTV-RunIIFall17DRPremix-00095',
'BTV-RunIIFall17DRPremix-00094',
'BTV-RunIIFall17DRPremix-00097',
'BTV-RunIIFall17DRPremix-00096',
'BTV-RunIIFall17DRPremix-00099',
'BTV-RunIIFall17DRPremix-00098',
'FSQ-RunIIFall17DRPremix-00013',
'FSQ-RunIIFall17DRPremix-00012',
'FSQ-RunIIFall17DRPremix-00011',
'FSQ-RunIIFall17DRPremix-00010',
'FSQ-RunIIFall17DRPremix-00018',
'B2G-RunIIFall17DRPremix-00005',
'B2G-RunIIFall17DRPremix-00003',
'BPH-RunIIFall17DRPremix-00059',
'BPH-RunIIFall17DRPremix-00058',
'BPH-RunIIFall17DRPremix-00057',
'BPH-RunIIFall17DRPremix-00056',
'BPH-RunIIFall17DRPremix-00055',
'BPH-RunIIFall17DRPremix-00054',
'BPH-RunIIFall17DRPremix-00053',
'TAU-RunIIFall17DRPremix-00026',
'TAU-RunIIFall17DRPremix-00027',
'TAU-RunIIFall17DRPremix-00024',
'TAU-RunIIFall17DRPremix-00025',
'TAU-RunIIFall17DRPremix-00023',
'TAU-RunIIFall17DRPremix-00020',
'TAU-RunIIFall17DRPremix-00021',
'TAU-RunIIFall17DRPremix-00028',
'TAU-RunIIFall17DRPremix-00029',
'HIG-RunIIFall17DRPremix-00294',
'EXO-RunIIFall17DRPremix-00129',
'EXO-RunIIFall17DRPremix-00123',
'EXO-RunIIFall17DRPremix-00121',
'EXO-RunIIFall17DRPremix-00120',
'EXO-RunIIFall17DRPremix-00127',
'EXOunIIFall17DRPremix-00009',
'HIG-RunIIFall17DRPremix-00135',
'JME-RunIIFall17DRPremix-00014',
'JME-RunIIFall17DRPremix-00017',
'JME-RunIIFall17DRPremix-00016',
'JME-RunIIFall17DRPremix-00011',
'JME-RunIIFall17DRPremix-00013',
'JME-RunIIFall17DRPremix-00012',
'JME-RunIIFall17DRPremix-00018',
'BTV-RunIIFall17DRPremix-00103',
'BTV-RunIIFall17DRPremix-00102',
'BTV-RunIIFall17DRPremix-00101',
'BTV-RunIIFall17DRPremix-00100',
'BTV-RunIIFall17DRPremix-00107',
'BTV-RunIIFall17DRPremix-00105',
'BTV-RunIIFall17DRPremix-00109',
'BTV-RunIIFall17DRPremix-00108',
'TRK-RunIIFall17DRPremix-00003',
'SMP-RunIIFall17DRPremix-00030',
'HIG-RunIIFall17DRPremix-00110',
'HIG-RunIIFall17DRPremix-00112',
'HIG-RunIIFall17DRPremix-00113',
'HIG-RunIIFall17DRPremix-00118',
'BPH-RunIIFall17DRPremix-00004',
'BPH-RunIIFall17DRPremix-00006',
'HIG-RunIIFall17DRPremix-00799',
'HIG-RunIIFall17DRPremix-00796',
'HIG-RunIIFall17DRPremix-00797',
'BPH-RunIIFall17DRPremix-00062',
'BPH-RunIIFall17DRPremix-00063',
'BPH-RunIIFall17DRPremix-00060',
'BPH-RunIIFall17DRPremix-00061',
'BPH-RunIIFall17DRPremix-00066',
'BPH-RunIIFall17DRPremix-00067',
'BPH-RunIIFall17DRPremix-00064',
'BPH-RunIIFall17DRPremix-00065',
'BPH-RunIIFall17DRPremix-00068',
'BPH-RunIIFall17DRPremix-00069',
'TAU-RunIIFall17DRPremix-00030',
'BTV-RunIIFall17DRPremix-00082',
'BTV-RunIIFall17DRPremix-00080',
'BTV-RunIIFall17DRPremix-00086',
'BTV-RunIIFall17DRPremix-00084',
'BTV-RunIIFall17DRPremix-00088',
'HIG-RunIIFall17DRPremix-00405',
'BPH-RunIIFall17DRPremix-00046',
'EXO-RunIIFall17DRPremix-00119',
'BPH-RunIIFall17DRPremix-00088',
'TAU-RunIIFall17DRPremix-00017',
'TAU-RunIIFall17DRPremix-00016',
'TAU-RunIIFall17DRPremix-00019',
'TAU-RunIIFall17DRPremix-00018',
'HIG-RunIIFall17DRPremix-00342',
'B2G-RunIIFall17DRPremix-00038',
'EXO-RunIIFall17DRPremix-00134',
'EXO-RunIIFall17DRPremix-00135',
'EXO-RunIIFall17DRPremix-00136',
'EXO-RunIIFall17DRPremix-00137',
'EXO-RunIIFall17DRPremix-00130',
'EXO-RunIIFall17DRPremix-00131',
'EXO-RunIIFall17DRPremix-00132',
'EXO-RunIIFall17DRPremix-00133',
'EXO-RunIIFall17DRPremix-00138',
'EXO-RunIIFall17DRPremix-00139',
'EXO-RunIIFall17DRPremix-00057',
'BTV-RunIIFall17DRPremix-00046',
'BTV-RunIIFall17DRPremix-00047',
'BTV-RunIIFall17DRPremix-00044',
'BTV-RunIIFall17DRPremix-00045',
'BTV-RunIIFall17DRPremix-00042',
'BTV-RunIIFall17DRPremix-00043',
'BTV-RunIIFall17DRPremix-00041',
'BTV-RunIIFall17DRPremix-00048',
'BTV-RunIIFall17DRPremix-00049',
'HIG-RunIIFall17DRPremix-00009',
'HIG-RunIIFall17DRPremix-00005',
'BPH-RunIIFall17DRPremix-00084',
'BPH-RunIIFall17DRPremix-00085',
'BPH-RunIIFall17DRPremix-00086',
'BPH-RunIIFall17DRPremix-00087',
'BPH-RunIIFall17DRPremix-00080',
'BPH-RunIIFall17DRPremix-00081',
'BPH-RunIIFall17DRPremix-00082',
'BPH-RunIIFall17DRPremix-00083',
'SMP-RunIIFall17DRPremix-00033',
'SMP-RunIIFall17DRPremix-00037',
'SMP-RunIIFall17DRPremix-00036',
'SMP-RunIIFall17DRPremix-00035',
'SMP-RunIIFall17DRPremix-00034',
'SMP-RunIIFall17DRPremix-00038',
'BTV-RunIIFall17DRPremix-00068',
'BTV-RunIIFall17DRPremix-00060',
'BTV-RunIIFall17DRPremix-00061',
'HIG-RunIIFall17DRPremix-00026',
'HIG-RunIIFall17DRPremix-00020',
'HIG-RunIIFall17DRPremix-00021',
'HIG-RunIIFall17DRPremix-00029',
'HIG-RunIIFall17DRPremix-01923',
]

for prepid in prepids:
    requests.append(mcm.get('chained_requests', query='contains=%s' % (prepid)))

for request in requests:
    
    for i in range(0,len(request)):

        if(request[i]['prepid'].find("MiniAOD")!=-1):
            
            root_id = request[i]['chain'][0]

            root_requests = mcm.get('chained_requests', query='contains=%s' % (root_id))

            do_chain = True

            for index in range(0,len(root_requests)):
            
                if(root_requests[index]['prepid'].find("MiniAODv2")!=-1):
                    do_chain=False
                
            #if(do_chain and root_requests[index]['prepid'].find('wmLHEGS')!=-1):
            if(do_chain and root_requests[index]['prepid'].find('Fall17GS')!=-1):
                
                request_to_check = mcm.get('requests', query='prepid=%s' % (root_id))
                
                print request_to_check[0]['keep_output'][0]
                if(request_to_check[0]['keep_output'][0]==True):
            
                    requests_for_that_repeat.append(root_id)
                    print root_id
                    requests_for_that_repeat.sort()

for chunk in chunks(requests_for_that_repeat, N_REQUESTS_PER_TICKET):
    mccm_ticket = {'prepid': 'PPD',  # this is how one passes it in the first place
                   'pwg': 'PPD',
                   'requests': chunk,
                   'notes': TICKET_NOTE,
                   'chains': dest_chained_campaign,
                   'block': PRIORITY_BLOCK}
    all_tickets.append(mccm_ticket)

for ticket in all_tickets:
    print('Create ticket:\n%s' % (json.dumps(ticket, indent=4)))
    if not dry_run:
        res = mcm.put('mccms', ticket)
        ticket_prepid = res.get('prepid', None)
        print('Ticket prepid: %s' % (ticket_prepid))
        #if ticket_prepid:
            #reserve the requests in the ticket
        #    mcm._McM__get('restapi/mccms/generate/%s/reserve' % (ticket_prepid))
        #else:
        #    print('Error: no ticket was created')

        # For some reason
        time.sleep(2)


