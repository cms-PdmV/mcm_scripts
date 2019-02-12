import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

mcm = McM(dev=False)

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", dest="filename", default="Priority-List.txt", help="write output in a file", metavar="file")
parser.add_argument("-p", "--priority", dest="priority", default="110000", help="priority of the requests", metavar="priority")
parser.add_argument("-s", "--string", dest="string", default="GS", help="campaign string to be present for the requests", metavar="campaign string")
parser.print_help()

args = parser.parse_args()

field_PID = 'prepid'
field_sequences = 'sequences'
field_events = 'total_events'

#string = args.string

#allRequestsApproved=mcm.get('requests',query='priority=110000')
#query_string='status=submitted&approval=submit&priority='+str(args.priority)
#allRequestsApproved=mcm.get('requests',query=query_string)

#number = 0 

#filenamecomposed=str(args.filename)+"-"+str(args.string)+"-"+str(args.priority)+".txt"

#text_file = open(filenamecomposed, "w")

#text_file.write('PrepID     Dataset name      Completed Events      Total Events     Priority\n') 

#for r in allRequestsApproved:
     
#     number+=1
     #print 'prepID '+r[field_PID]+' total events '+str(r[field_events])
     #print ' '+r[field_PID]+'  '+str(r[field_sequences])
#     if str(string) in r['member_of_campaign']:
#          text_file.write(' '+r[field_PID]+'  '+str(r['dataset_name'])+'  '+str(r['completed_events'])+'  '+str(r['total_events'])+'  '+str(r['priority'])+'\n')

#text_file.write('Total number of requests '+str(number))

#text_file.close()


strings = ["GS","pLHE","wmLHEGS","DR","MiniAOD","NanoAOD"]
priority = [63000,70000,80000,85000,90000,91000,92000,93000,94000,95000,96000,97000,98000,99000,100000,105000,109000,110000,111000]

for i in range(0,len(strings)):

    for j in range(0,len(priority)):

         query_string='status=submitted&approval=submit&priority='+str(priority[j])
         allRequestsApproved=mcm.get('requests',query=query_string)

         number = 0 

         filenamecomposed=str(args.filename)+"-"+str(strings[i])+"-"+str(priority[j])+".txt"

         text_file = open(filenamecomposed, "w")

         text_file.write('PrepID     Dataset name      Completed Events      Total Events     Priority\n') 

         for r in allRequestsApproved:
     
              if str(strings[i]) in r['member_of_campaign']:
                  number+=1
                  text_file.write(' '+r[field_PID]+'  '+str(r['dataset_name'])+'  '+str(r['completed_events'])+'  '+str(r['total_events'])+'  '+str(r['priority'])+'\n')
              

         text_file.write('Total number of requests '+str(number))

         text_file.close()
