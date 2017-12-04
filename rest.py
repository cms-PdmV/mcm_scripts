import sys
import os
import json
import httplib
import pycurl
import cStringIO
import traceback

class restful:
    def __init__(self, id='sso', debug=False, cookie=None, dev=True, int=False):
        self.dev = dev
        if self.dev:
            self.server = 'cms-pdmv-dev.cern.ch/mcm/'
        else:
            if int:
                self.server = 'cms-pdmv-int.cern.ch/mcm/'
            else:
                self.server = 'cms-pdmv.cern.ch/mcm/'

        ## once secured
        self.headers = {}
        self.id = id
        self.debug = debug
        self.connect(cookie)

    def connect(self, cookie=None):
        if self.id == 'cert':
            self.__http = httplib.HTTPSConnection(self.server,
                    cert_file = os.getenv('X509_USER_PROXY'),
                    key_file = os.getenv('X509_USER_PROXY'))

        elif self.id == 'sso':
            if cookie:
                self.cookieFilename = cookie
            else:
                if self.dev:
                    self.cookieFilename = '%s/private/dev-cookie.txt' % (os.getenv('HOME'))
                else:
                    self.cookieFilename = '%s/private/prod-cookie.txt' % (os.getenv('HOME'))

            if not os.path.isfile(self.cookieFilename):
                print "The required sso cookie file is absent. Trying to make one for you"
                os.system('cern-get-sso-cookie -u https://%s -o %s --krb' % (self.server,
                        self.cookieFilename))

                if not os.path.isfile(self.cookieFilename):
                    print "The required sso cookie file cannot be made."
                    sys.exit(1)

            self.curl = pycurl.Curl()
            print "Using sso-cookie file", self.cookieFilename

            self.curl.setopt(pycurl.COOKIEFILE,self.cookieFilename)
            self.output = cStringIO.StringIO()
            self.curl.setopt(pycurl.SSL_VERIFYPEER, 1)
            self.curl.setopt(pycurl.SSL_VERIFYHOST, 2)
            self.curl.setopt(pycurl.CAPATH, '/etc/pki/tls/certs')
            self.curl.setopt(pycurl.WRITEFUNCTION, self.output.write)
        else:
            self.__http = httplib.HTTPConnection(self.server)

    #################
    ### generic methods for GET,PUT,DELETE
    def get(self, url):
        fullurl = 'https://' +self.server + url
        if self.debug:
            print 'url=|' + fullurl + '|'
        if self.id == 'sso':
            self.curl.setopt(pycurl.HTTPGET, 1)
            self.curl.setopt(pycurl.URL, str(fullurl))
            self.curl.perform()
        else:
            self.__http.request("GET", url, headers=self.headers)

        try:
            d = json.loads(self.response())
            return d
        except:
            print "ERROR"
            print traceback.format_exc()
            print self._response
            return None

    def put(self, url, data):
        fullurl = 'https://' + self.server + url
        if self.debug:
            print 'url=|' + fullurl + '|'
        if self.id == 'sso':
            self.curl.setopt(pycurl.URL, str(fullurl))
            p_data = cStringIO.StringIO(json.dumps(data))
            self.curl.setopt(pycurl.UPLOAD, 1)
            self.curl.setopt(pycurl.READFUNCTION, cStringIO.StringIO(json.dumps(data)).read)
            if self.debug:
                print 'message=|' + p_data.read() + '|'
            self.curl.perform()
        else:
            self.__http.request("PUT", url, json.dumps(data), headers=self.headers)

        try:
            d = json.loads(self.response())
            return d
        except:
            print "ERROR"
            return None

    def delete(self, url):
        fullurl = 'https://' + self.server + url
        if self.debug:
            print 'url=|' + fullurl + '|'
        if self.id == 'sso':
            self.curl.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
            self.curl.setopt(pycurl.URL, str(fullurl))
            self.curl.perform()
        else:
            print "Not implemented Yet ?"
            self.__http.request("DELETE", url, headers=self.headers)

    #####################
    #### generic methods for i/o
    def clear(self):
        if self.id == 'sso':
            self.output = cStringIO.StringIO()
            self.curl.setopt(pycurl.WRITEFUNCTION, self.output.write)

    def response(self):
        if self.id == 'sso':
            self._response = self.output.getvalue()
            self.clear()
            return self._response
        else:
            return self.__http.getresponse().read()
    #####################

    def getA(self, something, someone=None, query='', method='get', page=-1):
        if someone:
            url = 'restapi/%s/%s/%s' % (something, method, someone.strip())
        else:
            url = 'search/?db_name=%s&page=%d&%s' % (something, page, query)

        d = self.get(url)
        if d:
            return d['results']
        else:
            return None

    def migrate(self, someone):
        return self.getA('requests', someone, method='migrate')

    def manageA(self, something, what):
        return self.putA(something, what, update='manage')

    def updateA(self, something, what):
        return self.putA(something, what, update='update')

    def putA(self, something, what, update='save'):
        url = 'restapi/%s/%s' % (something, update)

        d = self.put(url, what)
        return d

    def flowA(self, data):
        url = 'restapi/chained_requests/flow'
        self.put(url, data)
        print self.response()
        return

    def inject(self, someone):
        url = 'restapi/requests/inject/%s' % (someone)
        self.get(url)

    def approve(self, something, someone, level):
        url = 'restapi/%s/approve/%s/%d' % (something, someone, level)
        return self.get(url)

    def generate(self, something, someone):
        ###something can be 'actions' or 'chained_campaigns' as in the web interface
        url = 'restapi/%s/generate_chained_requests/%s' % (something, someone)
        self.get(url)
        junk = self.response()

    def detect(self):
        url = '/restapi/actions/detect_chains'
        return self.get(url)

    def clone(self, pid, data):
        return self.putA('requests', data, update='clone')

    def deleteA(self, something, someone):
        url = 'restapi/%s/delete/%s' % (something, someone)
        self.delete(url)

    def option_reset(self, rid):
        return self.get('restapi/requests/option_reset/%s/1' % (rid))
