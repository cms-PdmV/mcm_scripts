import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False)

# Example to edit a request parameter(-s) and save it back in McM
# request_prepid_to_update = 'HIG-Summer12-01257' # Doesn't exist

#requests = mcm.get('requests', query='priority=110000&status=submitted&prepid=*Autumn18DR*')
#requests = mcm.get('requests', query='tags=Autumn18POGP1DR&&priority=110000&status=submitted&prepid=MUO*')
requests = mcm.get('requests', query='prepid=*Autumn18DR*&&priority=85000&status=submitted')
#requests = mcm.get('requests', query='tags=Autumn18P1POGDR')

tot_events=0

for request in requests:

    chained_requests = request['member_of_chain']
    
    chained_request =  mcm.get('chained_requests', chained_requests[0])

    tot_events+=request['total_events']
    
    root_id = chained_request['chain'][0]
    root_id_req = mcm.get('requests', root_id) 

    chained_rootid = root_id_req['member_of_chain']

    print_tag = True
    
    for i in range(0,len(chained_rootid)):

        chained_request_root =  mcm.get('chained_requests', chained_rootid[i]) 

        if('Fall18DR' in chained_request_root['prepid'] or root_id_req['extension']==1):
            print_tag=False

            #if(request['total_events']>100000000):
    print str(request['prepid'])+' '+str(request['dataset_name'])+' '+str(request['total_events'])

    #if(print_tag==True):
        #print str(request['prepid'])+' '+str(request['dataset_name'])+' '+str(request['total_events'])


print tot_events
print len(requests)
