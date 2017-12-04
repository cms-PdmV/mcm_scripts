import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import *

mcm = restful(dev=True)

# example how to move a chained_request to force_done status
# needs production_manager or higher role
mcm_cr = mcm.getA("chained_requests",
        "B2G-chain_RunIISummer15wmLHEGS_flowRunIISpring16DR80PU2016withHLT_flowRunIISpring16MiniAODv2withHLT-00002")

mcm_cr["status"] = "force_done"

answer = mcm.updateA("chained_requests", mcm_cr)
print(answer)
