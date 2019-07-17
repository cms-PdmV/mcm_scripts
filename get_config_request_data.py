import sys
import json
import time
import httplib
import os
from urllib2 import Request, urlopen
import re, urllib

#to use arguments
listdata=[]
for arg in sys.argv[1:]:
    inputfile=str(arg)
    listdata.append(inputfile)

if(len(listdata)==0):
    print "Running default example options"
    listdata.append(['/SingleMuon/Run2018D-HcalCalIterativePhiSym-28Feb2019-v1/ALCARECO','/SingleMuon/Run2017H-17Nov2017-v1/MINIAOD'])

print listdata

filename='testDriver.html'
target_output='/afs/cern.ch/user/p/pgunnell/www/DriverMonitoringPage/Test'

def make_simple_request(url):
    req = Request(url)
    return json.loads(urlopen(req).read().decode('utf-8'))

def cmsweb_get(url):
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json'}
    cert = os.getenv('X509_USER_PROXY')
    key = os.getenv('X509_USER_PROXY')
    print('Using certificate and key from %s' % cert)
    if cert is None:
        print('No X509_USER_PROXY found! Run "voms-proxy-init -voms cms; export X509_USER_PROXY=$(voms-proxy-info --path)" and try again')
        return {}

    conn = httplib.HTTPSConnection('cmsweb.cern.ch', cert_file=cert, key_file=key)
    conn.request("GET", url, headers=headers)
    response = conn.getresponse()
    status, data = response.status, response.read()
    conn.close()
    #print('HTTP status: %s' % (status))
    jsonfile = json.loads(data)
    #print json.loads(data)
    idConfig=jsonfile['ConfigCacheID']
    try:
        #return json.loads(data)
        return idConfig
    except:
        print('Error parsing JSON from:\n\n%s' % (data))

def cmsweb_getreq(url):
    cert = os.getenv('X509_USER_PROXY')
    key = os.getenv('X509_USER_PROXY')
    print('Using certificate and key from %s' % cert)
    if cert is None:
        print('No X509_USER_PROXY found! Run "voms-proxy-init -voms cms; export X509_USER_PROXY=$(voms-proxy-info --path)" and try again')
        return {}

    conn = httplib.HTTPSConnection('cmsweb.cern.ch', cert_file=cert, key_file=key)
    conn.request("GET", url)
    response = conn.getresponse()
    status, data = response.status, response.read()
    conn.close()
   
    return data

for dataElement in listdata:
    workflows = make_simple_request('http://vocms074:5984/requests/_design/_designDoc/_view/outputDatasets?key="%s"&limit=10&skip=0&include_docs=True' % (dataElement))
    workflows = workflows.get('rows', [])
    request_transitions = []
    workflow_name = 'empty'
    configId = 0
    for workflow in workflows:
        if '_' in workflow['value']:
            workflow_name = workflow['value']
            print workflow_name

        ConfigCacheID=cmsweb_get('/couchdb/reqmgr_workload_cache/%s' % (workflow_name))

        configReqMgrPage = "/couchdb/reqmgr_config_cache/"+str(ConfigCacheID)+'/configFile'

        item_driver = ''

        for item in cmsweb_getreq(configReqMgrPage).split("\n"):
            if 'with command line options:' in item:
                item_driver = item.replace('with command line options:','cmsDriver')

        print dataElement
        print item_driver
        
        f = open(filename,'a')

        message_string = """<html>
<head></head>
<body><p> %s </p></body>
</html>"""+'\n'+dataElement+'\n'

        message = message_string % (str(item_driver))
        f.write(message)
        f.write('/n')
        f.close()

        os.popen('cp '+filename+' '+target_output)

        break
