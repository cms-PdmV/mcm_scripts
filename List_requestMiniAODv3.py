import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

#mcm = McM(dev=True,cookie='/afs/cern.ch/user/p/pgunnell/private/prod-cookie.txt')
mcm = McM(dev=False)

# Script clones a request to other campaign.
# Fefine list of modifications
# If member_of_campaign is different, it will clone to other campaign

# Get a request object which we want to clone
#chained_requests = mcm.get('chained_requests', 'B2G-chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3-00208')

requests = mcm.get('requests', query='status=new&prepid=*MiniAODv3*')

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

numberEvents = []

for request in requests:

    print(str(request['prepid'])+" "+str(request['total_events']))

    numberEvents.append([request['total_events'],request['prepid']])

numberEvents.sort(reverse=True)
print numberEvents[0][0]

Total = 0
request_n=0

for i in range(0,400):

    requests = mcm.get('requests', query='prepid=%s' % (numberEvents[i][1]))

    for request in requests:

        chained_request_id = request['member_of_chain'][0]
        chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))

        root_request = chained_requests[0]['chain'][0]
        dr_request = chained_requests[0]['chain'][1]
        
        request_to_check = mcm.get('requests', root_request)
        dr_request_to_check = mcm.get('requests', dr_request)
        
        if(dr_request_to_check['status'] == 'done' and request_to_check['status'] == 'done'): 
            request_n+=1
            print numberEvents[i][1]
            Total += numberEvents[i][0]
            for ch_request in chained_requests:

                print(mcm._McM__get('restapi/chained_requests/rewind/%s' % (ch_request['prepid'])))
                print(mcm._McM__get('restapi/chained_requests/rewind/%s' % (ch_request['prepid'])))
                print(mcm.forceflow(ch_request['prepid']))
                
print("Total is "+str(Total))
