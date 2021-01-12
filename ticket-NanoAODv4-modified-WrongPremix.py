import sys
import time
from collections import defaultdict
import pprint
import copy
import json

today = time.mktime( time.localtime() )
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM#restful

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def MiniAOD_output_not_saved(list_of_root_request,ochain):
    """Verify that all requests have AODSIM output"""
    set_of_root_request_prepid_without_aodsim = set()
    for root_request_prepid in list_of_root_request:
	crs = mcm.get('chained_requests', query='contains=%s&prepid=%s'%(root_request_prepid,ochain))
	for cr in crs:
		list_of_MiniAOD_request_prepid = [MiniAOD for MiniAOD in cr['chain'] if 'MiniAODv2' in MiniAOD]
		if len(list_of_MiniAOD_request_prepid)==1:
			MiniAOD_request = mcm.get('requests', query='prepid=%s'%(MiniAOD_request_prepid[0]))[0]
			# last step of the request must be saved
			if MiniAOD_request['keep_output'][-1]: continue
			else: set_of_root_request_prepid_without_aodsim.add(root_request_prepid)
		else: set_of_root_request_prepid_without_aodsim.add(root_request_prepid)
    #remove not chainable requests from the original list
    list_of_root_request = [r for r in list_of_root_request if r not in set_of_root_request_prepid_without_aodsim]
    return set_of_root_request_prepid_without_aodsim

# Global settings defining access to McM
cookie_file = ''
is_dev_instance = False#True


#[1] Use False first to check
#Remember to use False first, to make sure that all tickets are creatable.
is_dry_run = True

if is_dry_run:
        print 'This is DRYRUN!'
else:
        print 'WARNING!'*10
        print 'REAL QUERIES WILL BE MADE!!!'
        print 'WARNING!'*10

if is_dev_instance:
        cookie_file = 'dev-cookie.txt'  #dev
        print 'Running on dev instance!'
else:
        cookie_file = 'cookie.txt'      #prod
        print 'WARNING!'*10
        print 'Running on prod instance!!!'
        print 'WARNING!'*10

mcm=McM(dev=is_dev_instance, debug=True)

#pwgs=mcm._McM__get('restapi/users/get_pwg')['results']
#pwgs=mcm.get('restapi/users/get_pwg')['results']
# submit only these groups

N_REQUESTS_PER_TICKET = 30
PRIORITY_BLOCK = 1
TICKET_NOTE = "NanoAODv2 NanoAODv4 central migration" 

#[2] Choose one campaign types
ochain = 'chain_RunIIFall17wmLHEGS_flowRunIIFall17DRPremix_flowRunIIFall17MiniAODv2_flowRunIIFall17NanoAOD'
dchain = 'chain_RunIIFall17wmLHEGS_flowRunIIFall17DRPremix_flowRunIIFall17MiniAODv2_flowRunIIFall17NanoAODv4'

ticketfilename = dchain+'.json'

#collector=defaultdict(lambda : defaultdict( lambda : defaultdict( int )))
#for cc in ccs:
print 50*"-"

listprep = ['JME','HIG','SUS','BPH','SMP','EXO','B2G','BTV','FSQ','MUO','EGM','TOP']

#for pwg in listprep:
    #if pwg != "TOP": continue
        ## get all chains from that pwg in that chained campaign
        #crs = mcm.getA('chained_requests', query='member_of_campaign=%s&pwg=%s'%(cc['prepid'],pwg))
#    crs = mcm.get('chained_requests', query='member_of_campaign=%s&pwg=%s'%(ochain,pwg))
#    print "\t",pwg,":\t",len(crs)
#    for cr in crs:
#        #print "\t\t",cr['prepid'], cr['chain']
#        root_id = cr['chain'][0]
#        #print "\t\t",root_id
        #chainchecks = mcm.getA('chained_requests',query='contains=%s'%(root_id))
        #print chainchecks
#        campaign = root_id.split('-')[1]
#        collector[pwg][campaign][root_id]+=1

print "This is the list of %s requests that are deemed chainable: "%(listprep)
#pprint.pprint( dict(collector) )
#print collector
all_tickets=[]
#ccs = mcm.getA('chained_campaigns', query='contains=....')
#ccs = mcm.get('chained_campaigns', query='prepid=%s'%(dchain))
#print ccs
#for pwg in pwgs:
    ## create a ticket for the correct chain
campaign_name = "RunIIFall17MiniAODv2"
# Going through pages in McM because loading all at once puts too much stress on McM
page = 0
# Array for results. There is one empty dict inside, so it would go into the while loop the first time
#requests = [{}]

# Get requests that are member of given campaign
requests_for_that_repeat=[]

for pwg in listprep:
    requests = mcm.get('requests', query='member_of_campaign=%s&pwg=%s&member_of_chain=*DRPremix_*' % (campaign_name,pwg))

# Iterate through results
    for req in requests:
        # Try to get total_events. Just in case, it's not there - return -1 and not crash
        total_events = req.get('total_events', -1)
        if total_events >= 10:
            print('%s (%s)' % (req['prepid'], total_events))
            
            if(req['prepid'].find("MiniAOD")!=-1):
                
                chained_request_id = req['member_of_chain'][0]
                
                chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))
                
                root_request = chained_requests[0]['chain'][0]
                
                dr_request = chained_requests[0]['chain'][1]

                mini_request = chained_requests[0]['chain'][2]

                do_chain = True

                chained_requests_for_root =  mcm.get('chained_requests', query='contains=%s' % (root_request))

                for lenchainreq in range(0,len(chained_requests_for_root)):
                    if(chained_requests_for_root[lenchainreq]['prepid'].find("NanoAODv4")!=-1):
                        do_chain=False
                        print 'CHAIN already existing'
                    
                if(do_chain and root_request.find("Fall17wmLHEGS")!=-1):

                    request_to_check = mcm.get('requests', query='prepid=%s' % (root_request))
                    dr_request_to_check = mcm.get('requests', query='prepid=%s' % (dr_request))
                    mini_request_to_check = mcm.get('requests', query='prepid=%s' % (mini_request))
                    
                    if(dr_request_to_check[0]['keep_output'][1]==True and dr_request_to_check[0]['status']=='done' and mini_request_to_check[0]['status']=='done'):
                        
                        requests_for_that_repeat.append(root_request)
                        print root_request
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
        
