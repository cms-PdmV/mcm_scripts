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

requests = mcm.get('requests', query='status=new&prepid=SUS*MiniAODv3*')

# Make predefined modifications

#print('Number of requests '+str(len(requests)))

numberEvents = []

for request in requests:

    print request['prepid']
    print request['total_events']

    numberEvent.append(request['total_events'])

    compl = float(request['completed_events'])
    tot = float(request['total_events'])

    if(request['output_dataset']!= None):
        print str(request['output_dataset'][0])


for request in requests:  

    chained_requests = request['member_of_chain']
    
    chained_request =  mcm.get('chained_requests', chained_requests[0])  

    root_gs = chained_request['chain'][1]
    root_gs_req = mcm.get('requests', root_gs) 

    print str(root_gs_req['output_dataset'])


    #if(compl/tot>0.9):
        #print(str(request['prepid'])+'        '+str(request['dataset_name'])+'       '+str((compl/tot)*100.)+str('% done'))+'        '+str(request['priority'])+'       https://cms-pdmv.cern.ch/mcm/requests?prepid='+str(request['prepid'])+'\n'

        #print('https://cms-pdmv.cern.ch/mcm/requests?prepid='+str(request['prepid'])+'\n')
        #prepid = request['prepid']
        #print(mcm._McM__put('restapi/requests/add_forcecomplete', {'prepid': prepid}))

        #answer = mcm.get('forcecomplete', str(request['prepid']))
        #print answer

    #print (str(request['history'][0]['updater']['submission_date'])+'\n')
    






        

