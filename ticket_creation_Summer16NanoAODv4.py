import sys
import time
from collections import defaultdict
import pprint
import copy
import json

sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

# Global settings defining access to McM
cookie_file = ''
use_dev_instance = False  # True
# Remember to use False first, to make sure that all tickets are creatable.
is_dry_run = False

if is_dry_run:
    print 'This is DRYRUN! No tickets will be created'
else:
    print 'WARNING!'*10
    print 'REAL QUERIES WILL BE MADE!!! Tickets will be created'
    print 'WARNING!'*10

if use_dev_instance:
    cookie_file = 'dev-cookie.txt'  #dev
    print 'Running on dev instance!'
else:
    cookie_file = 'cookie.txt'      #prod
    print 'WARNING!'*10
    print 'Running on prod instance!!!'
    print 'WARNING!'*10

mcm = McM(dev=use_dev_instance, debug=True)

#pwgs=mcm._McM__get('restapi/users/get_pwg')['results']
#pwgs=mcm.get('restapi/users/get_pwg')['results']
# submit only these groups

N_REQUESTS_PER_TICKET = 30
PRIORITY_BLOCK = 1
TICKET_NOTE = "NanoAODv2 NanoAODv4 central migration" 
campaigntochain = 'GS' # 'GS' # 'wmLHEGS' #'pLHE' #wmLHE


#[2] Choose one campaign types
#For wmLHEGS
if(campaigntochain=='wmLHEGS'):
    ochain = 'chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'
    dchain = 'chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv4'
elif (campaigntochain=='GS'):
#For GS
    ochain = 'chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'
    dchain = 'chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv4'

elif (campaigntochain=='pLHE'):
#For pLHE
    ochain = 'chain_RunIIWinter15pLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'
    dchain = 'chain_RunIIWinter15pLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv4'

elif (campaigntochain=='wmLHE'):
#For wmLHE
    ochain = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'
    dchain = 'chain_RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv4'

ticketfilename = dchain + '.json'

print 50*"-"

listprep = ['JME','HIG','SUS','BPH','SMP','EXO','B2G','BTV','FSQ','MUO','EGM','TOP']

print "This is the list of %s requests that are deemed chainable: " % (listprep)
all_tickets=[]
campaign_name = "RunIISummer16MiniAODv3"

# Get requests that are member of given campaign
requests_for_that_repeat=[]

for pwg in listprep:
    page = 0
    requests = [{}]
    while len(requests) > 0:
        if(campaigntochain=='wmLHEGS'):
            requests = mcm.get('requests', query='status=done&member_of_campaign=%s&pwg=%s&member_of_chain=*wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_*' % (campaign_name,pwg), page=page)
            page += 1

        elif(campaigntochain=='GS'):
            requests = mcm.get('requests', query='status=done&member_of_campaign=%s&pwg=%s&member_of_chain=*chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_*' % (campaign_name,pwg), page=page)
            page += 1

        elif(campaigntochain=='pLHE'):
            requests = mcm.get('requests', query='status=done&member_of_campaign=%s&pwg=%s&member_of_chain=*RunIIWinter15pLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_*' % (campaign_name,pwg), page=page)
            page += 1

        elif(campaigntochain=='wmLHE'):
            requests = mcm.get('requests', query='status=done&member_of_campaign=%s&pwg=%s&member_of_chain=*RunIIWinter15wmLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_*' % (campaign_name,pwg), page=page)
            page += 1

        # Iterate through results
        for req in requests:
            # Try to get total_events. Just in case, it's not there - return -1 and not crash
            total_events = req.get('total_events', -1)
            if total_events >= 1:
                print('%s (%s)' % (req['prepid'], total_events))
                if ('MiniAOD' in req['prepid']):
                    chained_request_id = req['member_of_chain'][0]
                    chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))
                    if len(chained_requests) < 1:
                        print('Could not find %s' % (chained_request_id))
                        continue

                    if len(chained_requests[0]['chain']) < 3:
                        print('Chain of %s is not long enough' % (chained_request_id))
                        continue

                    root_request = chained_requests[0]['chain'][0]
                    dr_request = chained_requests[0]['chain'][1]
                    mini_request = chained_requests[0]['chain'][2]
                    do_chain = True
                    chained_requests_for_root = mcm.get('chained_requests', query='contains=%s' % (root_request))
                    for chained_request_for_root in chained_requests_for_root:
                        if('NanoAODv4' in chained_request_for_root['prepid']):
                            do_chain=False
                            print 'CHAIN %s already existing' % (chained_request_for_root)
                            break
                    
                        #if do_chain and 'Fall17wmLHEGS' in root_request:
                    if do_chain:
                        request_to_check = mcm.get('requests', root_request)
                        dr_request_to_check = mcm.get('requests', dr_request)
                        mini_request_to_check = mcm.get('requests', mini_request)
                        
                        if dr_request_to_check['keep_output'][1] == True and dr_request_to_check['status'] == 'done' and mini_request_to_check['status'] == 'done': 
                            requests_for_that_repeat.append(root_request)
                            print 'Added %s' % (root_request)

requests_for_that_repeat.sort()

for chunk in chunks(requests_for_that_repeat, N_REQUESTS_PER_TICKET):
    mccm_ticket = {'prepid': 'PPD',  
                   'pwg': 'PPD',
                   'requests': chunk,
                   'notes': TICKET_NOTE,
                   'chains': [str(dchain)],
                   'block': PRIORITY_BLOCK}
    all_tickets.append(mccm_ticket)

for ticket in all_tickets:
    print('Create ticket:\n%s' % (json.dumps(ticket, indent=4)))
    if not is_dry_run:
        res = mcm.put('mccms', ticket)
        ticket_prepid = res.get('prepid', None)
        print('Ticket prepid: %s' % (ticket_prepid))
        print('Generating and reserving requests...')
        res = mcm._McM__get('restapi/mccms/generate/%s/reserve/' % (ticket_prepid))
        #if res is not None:
        #    for ch_req in res.get('message'):
        #        print('Flow %s' % (ch_req['prepid']))
        #        flow_res = mcm.get('chained_requests', ch_req['prepid'], 'flow')
        #        print(flow_res)
        #        time.sleep(0.1)
        #else:
        #    print('Error generating and reserving for %s' % (ticket_prepid))

        time.sleep(0.2)
