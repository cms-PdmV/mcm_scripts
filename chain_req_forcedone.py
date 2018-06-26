import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=True)

# Example how to move a chained_request to force_done status
# Needs production_manager or higher role
chained_request = mcm.get('chained_requests',
                          'B2G-chain_RunIISummer15wmLHEGS_flowRunIISpring16DR80PU2016withHLT_flowRunIISpring16MiniAODv2withHLT-00002')

chained_request['status'] = 'force_done'

update_answer = mcm.update('chained_requests', chained_request)
print(update_answer)
