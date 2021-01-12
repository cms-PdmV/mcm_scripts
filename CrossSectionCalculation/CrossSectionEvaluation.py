import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps
from subprocess import Popen, PIPE

mcm = McM(dev=False)

dest_output = sys.argv[1]

requests = mcm.get('requests', query='produce=%s' % (dest_output))

for request in requests:

    print request['prepid']

    chained_requests = request['member_of_chain']

    chained_request =  mcm.get('chained_requests', chained_requests[0])

    root_id = chained_request['chain'][0]
    root_id_req = mcm.get('requests', root_id)

    prepid = root_id_req['prepid']

    print prepid

    file_to_download = 'https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_test/'+str(prepid)

script = ("wget "+ str(file_to_download))
script += ("; mv "+ str(prepid) +" script.sh")
script += (";sed -i 's/GEN-SIM/GEN/g' script.sh")
script += (";sed -i 's/python request_fragment_check.py/# python request_fragment_check.py/g' script.sh")
script += (";sed -i 's/GEN,SIM/GEN/g' script.sh")
script += (";")

p = Popen(script, shell=True)
