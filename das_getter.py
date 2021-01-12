import httplib
import os
import json

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
    print('HTTP status: %s' % (status))
    jsonfile = json.loads(data)
    print json.loads(data)
    filesizetotal=jsonfile[0]['file_size']
    try:
        #return json.loads(data)
        return filesizetotal
    except:
        print('Error parsing JSON from:\n\n%s' % (data))


Files = [
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v3/ALCARECO',
'/ZeroBias/Run2017B-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias/Run2017C-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias/Run2017C-TkAlMinBias-PromptReco-v3/ALCARECO',
'/ZeroBias/Run2017D-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017E-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017F-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017G-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017H-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias8b4e1/Run2017D-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias1/Run2017C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias/Run2016B-TkAlMinBias-07Aug17_ver1-v1/ALCARECO',
'/ZeroBias/Run2016B-TkAlMinBias-07Aug17_ver2-v1/ALCARECO',
'/ZeroBias/Run2016C-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016D-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016E-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016F-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016G-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016H-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias0/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias1/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias2/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias3/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias4/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias5/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias6/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias7/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias8/Run2016B-TkAlMinBias-PromptReco-v2/ALCARECO',
]

Files2 = [
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v3/ALCARECO',
'/Cosmics/Run2017B-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017B-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v3/ALCARECO',
'/Cosmics/Run2017D-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017E-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017F-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017G-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017H-TkAlCosmics0T-PromptReco-v1/ALCARECO',

'/DoubleMuon/Run2017A-TkAlZMuMu-09Oct2017-v1/ALCARECO',
'/DoubleMuon/Run2017A-TkAlZMuMu-PromptReco-v1/ALCARECO',
'/DoubleMuon/Run2017A-TkAlZMuMu-PromptReco-v2/ALCARECO',
'/DoubleMuon/Run2017A-TkAlZMuMu-PromptReco-v3/ALCARECO',
'/DoubleMuon/Run2017B-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017C-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017D-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017E-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017F-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017G-TkAlZMuMu-17Nov2017-v1/ALCARECO',
'/DoubleMuon/Run2017H-TkAlZMuMu-17Nov2017-v1/ALCARECO',

'/NoBPTX/Run2017A-TkAlCosmicsInCollisions-PromptReco-v1/ALCARECO',
'/NoBPTX/Run2017A-TkAlCosmicsInCollisions-PromptReco-v2/ALCARECO',
'/NoBPTX/Run2017A-TkAlCosmicsInCollisions-PromptReco-v3/ALCARECO',
'/NoBPTX/Run2017B-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
'/NoBPTX/Run2017C-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
'/NoBPTX/Run2017D-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
'/NoBPTX/Run2017E-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
'/NoBPTX/Run2017F-TkAlCosmicsInCollisions-09May2018-v1/ALCARECO',
'/NoBPTX/Run2017G-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
'/NoBPTX/Run2017H-TkAlCosmicsInCollisions-17Nov2017-v1/ALCARECO',
 
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/ZeroBias/Run2017A-TkAlMinBias-PromptReco-v3/ALCARECO',
'/ZeroBias/Run2017B-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017C-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017D-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017E-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017F-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017G-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/ZeroBias/Run2017H-TkAlMinBias-17Nov2017-v1/ALCARECO',

'/HLTPhysics/Run2017A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2017A-TkAlMinBias-PromptReco-v3/ALCARECO',
'/HLTPhysics/Run2017B-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2017C-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2017C-TkAlMinBias-PromptReco-v3/ALCARECO',
'/HLTPhysics/Run2017D-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017E-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017F-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2017G-TkAlMinBias-17Nov2017-v1/ALCARECO',
'/HLTPhysics/Run2017H-TkAlMinBias-17Nov2017-v1/ALCARECO',

'/MinimumBias/Run2017A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2017A-TkAlMinBias-PromptReco-v3/ALCARECO',
'/MinimumBias/Run2017B-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017B-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2017C-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2017C-TkAlMinBias-PromptReco-v3/ALCARECO',
'/MinimumBias/Run2017D-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017E-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017F-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017G-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2017H-TkAlMinBias-PromptReco-v1/ALCARECO',

'/Charmonium/Run2017A-TkAlJpsiMuMu-PromptReco-v1/ALCARECO',
'/Charmonium/Run2017A-TkAlJpsiMuMu-PromptReco-v2/ALCARECO',
'/Charmonium/Run2017A-TkAlJpsiMuMu-PromptReco-v3/ALCARECO',
'/Charmonium/Run2017B-TkAlJpsiMuMu-17Nov2017-v1/ALCARECO',
'/Charmonium/Run2017C-TkAlJpsiMuMu-17Nov2017-v1/ALCARECO',
'/Charmonium/Run2017D-TkAlJpsiMuMu-17Nov2017-v1/ALCARECO',
'/Charmonium/Run2017E-TkAlJpsiMuMu-17Nov2017-v1/ALCARECO',
'/Charmonium/Run2017F-TkAlJpsiMuMu-09May2018-v1/ALCARECO',

'/MuOnia/Run2017B-TkAlUpsilonMuMu-17Nov2017-v1/ALCARECO',
'/MuOnia/Run2017C-TkAlUpsilonMuMu-17Nov2017-v1/ALCARECO',
'/MuOnia/Run2017D-TkAlUpsilonMuMu-17Nov2017-v1/ALCARECO',
'/MuOnia/Run2017E-TkAlUpsilonMuMu-17Nov2017-v1/ALCARECO',
'/MuOnia/Run2017F-TkAlUpsilonMuMu-09May2018-v1/ALCARECO',

'/SingleMuon/Run2017A-TkAlMuonIsolated-PromptReco-v2/ALCARECO',
'/SingleMuon/Run2017A-TkAlMuonIsolated-PromptReco-v3/ALCARECO',
'/SingleMuon/Run2017B-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017C-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017D-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017E-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017F-TkAlMuonIsolated-09May2018-v1/ALCARECO',
'/SingleMuon/Run2017F-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017G-TkAlMuonIsolated-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017H-TkAlMuonIsolated-17Nov2017-v2/ALCARECO',
]

Files3 = [
'/SingleMuon/Run2018A-MuAlCalIsolatedMu-06Jun2018-v1/ALCARECO',
'/SingleMuon/Run2018B-MuAlCalIsolatedMu-17Sep2018-v1/ALCARECO',
'/SingleMuon/Run2018C-MuAlCalIsolatedMu-17Sep2018-v1/ALCARECO',
'/SingleMuon/Run2018D-MuAlCalIsolatedMu-PromptReco-v2/ALCARECO',

'/SingleMuon/Run2017A-MuAlCalIsolatedMu-PromptReco-v2/ALCARECO',
'/SingleMuon/Run2017B-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017C-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017C-MuAlCalIsolatedMu-12Sep2017-v1/ALCARECO',
'/SingleMuon/Run2017D-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017E-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017F-MuAlCalIsolatedMu-09May2018-v1/ALCARECO',
'/SingleMuon/Run2017G-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017H-MuAlCalIsolatedMu-17Nov2017-v1/ALCARECO',
'/SingleMuon/Run2017H-MuAlCalIsolatedMu-17Nov2017-v2/ALCARECO',

'/SingleMuon/Run2016B-MuAlCalIsolatedMu-07Aug17_ver1-v1/ALCARECO',
'/SingleMuon/Run2016B-MuAlCalIsolatedMu-07Aug17_ver2-v1/ALCARECO',
'/SingleMuon/Run2016C-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016D-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016E-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016F-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016G-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016H-MuAlCalIsolatedMu-07Aug17-v1/ALCARECO', 
]


Files4 = [
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017A-TkAlCosmics0T-PromptReco-v3/ALCARECO',
'/Cosmics/Run2017B-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017B-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v2/ALCARECO',
'/Cosmics/Run2017C-TkAlCosmics0T-PromptReco-v3/ALCARECO',
'/Cosmics/Run2017D-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017E-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017F-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017G-TkAlCosmics0T-PromptReco-v1/ALCARECO',
'/Cosmics/Run2017H-TkAlCosmics0T-PromptReco-v1/ALCARECO',

'/DoubleMuon/Run2016B-TkAlZMuMu-07Aug17_ver1-v1/ALCARECO',
'/DoubleMuon/Run2016B-TkAlZMuMu-07Aug17_ver2-v1/ALCARECO',
'/DoubleMuon/Run2016C-TkAlZMuMu-07Aug17-v1/ALCARECO',
'/DoubleMuon/Run2016D-TkAlZMuMu-07Aug17-v1/ALCARECO',
'/DoubleMuon/Run2016E-TkAlZMuMu-07Aug17-v1/ALCARECO',
'/DoubleMuon/Run2016F-TkAlZMuMu-07Aug17-v1/ALCARECO',
'/DoubleMuon/Run2016G-TkAlZMuMu-07Aug17-v1/ALCARECO',
'/DoubleMuon/Run2016H-TkAlZMuMu-07Aug17-v1/ALCARECO',

'/NoBPTX/Run2016B-TkAlCosmicsInCollisions-07Aug17_ver1-v1/ALCARECO',
'/NoBPTX/Run2016B-TkAlCosmicsInCollisions-07Aug17_ver2-v1/ALCARECO',
'/NoBPTX/Run2016C-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',
'/NoBPTX/Run2016C-TkAlCosmicsInCollisions-23Sep2016-v1/ALCARECO',
'/NoBPTX/Run2016D-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',
'/NoBPTX/Run2016E-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',
'/NoBPTX/Run2016F-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',
'/NoBPTX/Run2016G-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',
'/NoBPTX/Run2016H-TkAlCosmicsInCollisions-07Aug17-v1/ALCARECO',

'/ZeroBias/Run2016B-TkAlMinBias-07Aug17_ver1-v1/ALCARECO',
'/ZeroBias/Run2016B-TkAlMinBias-07Aug17_ver2-v1/ALCARECO',
'/ZeroBias/Run2016C-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016D-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016E-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016F-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016G-TkAlMinBias-07Aug17-v1/ALCARECO',
'/ZeroBias/Run2016H-TkAlMinBias-07Aug17-v1/ALCARECO',

'/HLTPhysics/Run2016A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2016A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2016B-TkAlMinBias-01Jul2016-v1/ALCARECO',
'/HLTPhysics/Run2016B-TkAlMinBias-01Jul2016-v2/ALCARECO',
'/HLTPhysics/Run2016C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2016D-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2016E-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2016F-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2016G-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2016H-TkAlMinBias-PromptReco-v1/ALCARECO',
'/HLTPhysics/Run2016H-TkAlMinBias-PromptReco-v2/ALCARECO',
'/HLTPhysics/Run2016H-TkAlMinBias-PromptReco-v3/ALCARECO',

'/MinimumBias/Run2016A-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2016A-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2016B-TkAlMinBias-07Aug17_ver1-v1/ALCARECO',
'/MinimumBias/Run2016C-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2016D-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2016E-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2016F-TkAlMinBias-07Aug17-v1/ALCARECO',
'/MinimumBias/Run2016G-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2016H-TkAlMinBias-PromptReco-v1/ALCARECO',
'/MinimumBias/Run2016H-TkAlMinBias-PromptReco-v2/ALCARECO',
'/MinimumBias/Run2016H-TkAlMinBias-PromptReco-v3/ALCARECO',

'/Charmonium/Run2016B-TkAlJpsiMuMu-07Aug17_ver1-v1/ALCARECO',
'/Charmonium/Run2016B-TkAlJpsiMuMu-07Aug17_ver2-v1/ALCARECO',
'/Charmonium/Run2016C-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016D-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016E-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016F-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016G-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016H-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',
'/Charmonium/Run2016H-TkAlJpsiMuMu-07Aug17-v1/ALCARECO',

'/MuOnia/Run2016B-TkAlUpsilonMuMu-07Aug17_ver1-v1/ALCARECO',
'/MuOnia/Run2016B-TkAlUpsilonMuMu-07Aug17_ver2-v1/ALCARECO',
'/MuOnia/Run2016C-TkAlUpsilonMuMu-07Aug17-v1/ALCARECO',
'/MuOnia/Run2016D-TkAlUpsilonMuMu-07Aug17-v1/ALCARECO',
'/MuOnia/Run2016E-TkAlUpsilonMuMu-07Aug17-v1/ALCARECO',
'/MuOnia/Run2016F-TkAlUpsilonMuMu-07Aug17-v1/ALCARECO',
'/MuOnia/Run2016G-TkAlUpsilonMuMu-07Aug17-v2/ALCARECO',
'/MuOnia/Run2016H-TkAlUpsilonMuMu-07Aug17-v1/ALCARECO',

'/SingleMuon/Run2016B-TkAlMuonIsolated-07Aug17_ver1-v1/ALCARECO',
'/SingleMuon/Run2016B-TkAlMuonIsolated-07Aug17_ver2-v1/ALCARECO',
'/SingleMuon/Run2016BBackfill-TkAlMuonIsolated-BACKFILL-v3/ALCARECO',
'/SingleMuon/Run2016C-TkAlMuonIsolated-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016D-TkAlMuonIsolated-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016E-TkAlMuonIsolated-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016F-TkAlMuonIsolated-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016G-TkAlMuonIsolated-07Aug17-v1/ALCARECO',
'/SingleMuon/Run2016H-TkAlMuonIsolated-07Aug17-v1/ALCARECO', 

]


filesize=0

for name in Files3:
    filesize+=cmsweb_get('/dbs/prod/global/DBSReader/filesummaries?dataset=%s' % (name))


print ('Total size is ' +str(filesize/1000000000000.)+' TByte')
