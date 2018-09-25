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

#dest_chained_campaign = 'chain_RunIISummer15wmLHEGS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'                                                           
#dest_chained_campaign = 'chain_RunIIWinter15pLHE_flowLHE2Summer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'                                           
dest_chained_campaign = 'chain_RunIISummer15GS_flowRunIISummer16DR80PremixPUMoriond17_flowRunIISummer16MiniAODv3_flowRunIISummer16NanoAODv3'

chained_requests = mcm.get('chained_requests', query='member_of_campaign=%s&pwg=BTV' % (dest_chained_campaign))

# Make predefined modifications                                                                                                                                                                              

for chained_request in chained_requests:

    root_id = chained_request['chain'][0]
    dr_id = chained_request['chain'][1]
    miniAOD_id = chained_request['chain'][2]
    nanoAOD_id = chained_request['chain'][3]

    root_id_req = mcm.get('requests', root_id)
    dr_id_req = mcm.get('requests', dr_id)
    miniAOD_id_req = mcm.get('requests', miniAOD_id)
    nanoAOD_id_req = mcm.get('requests', nanoAOD_id)

    if(root_id_req['status']== 'done' and dr_id_req['status']== 'done' and miniAOD_id_req['status']== 'new' and nanoAOD_id_req['status']== 'new'):

        print chained_request['prepid']

        mcm._McM__get('restapi/chained_requests/flow/%s/force' % (chained_request['prepid']))


    if(root_id_req['status']== 'new' and dr_id_req['status']== 'new' and miniAOD_id_req['status']== 'new' and nanoAOD_id_req['status']== 'new'):

        chained_request['action_parameters']['flag'] = False
        mcm.update('chained_requests', chained_request)

        request_delete_result = mcm.delete('requests', nanoAOD_id_req['prepid'])
        request_delete_result = mcm.delete('requests', miniAOD_id_req['prepid'])
        request_delete_result = mcm.delete('requests', dr_id_req['prepid'])

        print chained_request['prepid']
