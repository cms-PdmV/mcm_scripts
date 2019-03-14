import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps

mcm = McM(dev=True)

# Script deletes a request of a certain campaign of a certain PWG, Use with care.
dest_chained_campaign = 'YourCampaign'
PwgGroup = 'PWG'

requests = mcm.get('requests', query='member_of_campaign=%s&status=new&prepid=%s*' % (dest_chained_campaign, PwgGroup))

for request in requests:
        request_delete_result = mcm.delete('requests', request['prepid'])
        print request_delete_result

