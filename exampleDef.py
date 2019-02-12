import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=False)


field_PID = 'prepid'
field_sequences = 'sequences'
field_events = 'total_events'

#allRequestsApproved=mcm.get('requests',query='priority=110000')
#allRequestsApproved=mcm.get('requests',query='status=defined&approval=define&prepid=*Fall18*GS*')
allRequestsApproved=mcm.get('requests',query='status=approved&approval=approve&prepid=*Fall18*GS*')

number = 0 
events = 0

text_file = open("Output.txt", "w")

text_file.write('PrepID     Dataset name      Completed Events      Total Events     Priority\n') 

for r in allRequestsApproved:
     
     number+=1
     events+=r[field_events]
     #print r
     #print 'prepID '+r[field_PID]+' total events '+str(r[field_events])
     #print ' '+r[field_PID]+'  '+str(r[field_sequences])
     #text_file.write(' '+r[field_PID]+'  '+str(r['dataset_name'])+'  '+str(r['completed_events'])+'  '+str(r['total_events'])+'  '+str(r['priority'])+'\n')

text_file.write('Total number of requests '+str(number))
print('Total number of events '+str(events))

text_file.close()
