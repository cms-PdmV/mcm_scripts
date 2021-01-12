import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
import json

mcm = McM(dev=False)
ch_requests = [{}]
page = 0
while len(ch_requests) > 0:
    ch_requests = mcm.get('chained_requests', query='prepid=*Autumn18MiniAOD*', page=page)
    for ch_request in ch_requests:
        print(ch_request['prepid'])
        miniaod_prepid = None
        nanoaod_prepid = None
        requests = ch_request.get('chain', [])
        for request_prepid in requests:
            if 'MiniAOD' in request_prepid:
                miniaod_prepid = request_prepid
            elif 'NanoAOD' in request_prepid:
                nanoaod_prepid = request_prepid

        if not miniaod_prepid:
        #     print('    Skipping because no MiniAOD')
            continue
        
        miniaod = mcm.get('requests', miniaod_prepid)
        if nanoaod_prepid:
            nanoaod = mcm.get('requests', nanoaod_prepid)
        else:
            nanoaod = {'status': None}

        if miniaod['status'] == 'done' and (nanoaod['status'] == 'new' or nanoaod['status'] is None):
            print('%s' % (ch_request['prepid']))
            print('    MiniAOD: %s Status: %s' % (miniaod_prepid, miniaod['status']))
            print('    NanoAOD: %s Status: %s\n' % (nanoaod_prepid, nanoaod['status']))

            print(mcm.forceflow(ch_request['prepid']))

    page += 1



# print(mcm.forceflow('B2G-chain_2019GEMUpg14_flow2019GEMUpg14GStoDRCalo300fbNoPU-00001'))
