import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
import json

mcm = McM(dev=False)
ch_requests = [{}]
page = 0
while len(ch_requests) > 0:
    requests = mcm.get('requests', query='prepid=*Summer16NanoAODv4*&status=approved', page=page)

    print len(requests)

    for req in requests:
        chained_request_id = req['member_of_chain'][0]
        chained_requests = mcm.get('chained_requests', query='prepid=%s' % (chained_request_id))

        for ch_request in chained_requests:
            #print(mcm.forceflow(ch_request['prepid']))
            mcm._McM__get('restapi/chained_requests/inject/%s' % (ch_request['prepid']))

    page += 1



# print(mcm.forceflow('B2G-chain_2019GEMUpg14_flow2019GEMUpg14GStoDRCalo300fbNoPU-00001'))
