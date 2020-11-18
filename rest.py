import sys
import os
import json
import traceback
import logging
import time

try:
    import cookielib
except:
    import http.cookiejar as cookielib

try:
    import urllib2 as urllib
except:
    import urllib.request as urllib


class MethodRequest(urllib.Request):
    """
    Custom request, so it would support different HTTP methods
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method

        return urllib.Request.get_method(self, *args, **kwargs)


class McM:
    def __init__(self, id='sso', debug=False, cookie=None, dev=True, int=False):
        if dev:
            self.host = 'cms-pdmv-dev.cern.ch'
        elif int:
            self.host = 'cms-pdmv-int.cern.ch'
        else:
            self.host = 'cms-pdmv.cern.ch'

        self.dev = dev
        self.server = 'https://' + self.host + '/mcm/'
        self.id = id
        # Set up logging
        if debug:
            logging_level = logging.DEBUG
        else:
            logging_level = logging.INFO

        if cookie:
            self.cookie = cookie
        else:
            home = os.getenv('HOME')
            if dev:
                self.cookie = '%s/private/mcm-dev-cookie.txt' % (home)
            elif int:
                self.cookie = '%s/private/mcm-int-cookie.txt' % (home)
            else:
                self.cookie = '%s/private/mcm-prod-cookie.txt' % (home)

        # Set up logging
        logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging_level)
        self.logger = logging.getLogger()
        # Create opener
        self.__connect()
        # Request retries
        self.max_retries = 3

    def __connect(self):
        if self.id == 'sso':
            if not os.path.isfile(self.cookie):
                self.logger.info('SSO cookie file is absent. Will try to make one for you...')
                self.__generate_cookie()
                if not os.path.isfile(self.cookie):
                    self.logger.error('Missing cookie file %s, quitting', self.cookie)
                    sys.exit(1)
            else:
                self.logger.info('Using SSO cookie file %s' % (self.cookie))

            cookie_jar = cookielib.MozillaCookieJar(self.cookie)
            cookie_jar.load()
            for cookie in cookie_jar:
                self.logger.debug('Cookie %s', cookie)

            self.opener = urllib.build_opener(urllib.HTTPCookieProcessor(cookie_jar))
        else:
            self.opener = urllib.build_opener()

    def __generate_cookie(self):
        # use env to have a clean environment
        command = 'env -i KRB5CCNAME="$KRB5CCNAME" cern-get-sso-cookie -u %s -o %s --reprocess --krb' % (self.server, self.cookie)
        self.logger.debug(command)
        output = os.popen(command).read()
        self.logger.debug(output)
        if not os.path.isfile(self.cookie):
            self.logger.error('Could not generate SSO cookie.\n%s', output)

    # Generic methods for GET, PUT, DELETE HTTP methods
    def __http_request(self, url, method, data=None, parse_json=True):
        url = self.server + url
        self.logger.debug('[%s] %s', method, url)
        headers = {'User-Agent': 'McM Scripting'}
        if data:
            data = json.dumps(data)
            headers['Content-type'] = 'application/json'

        request = MethodRequest(url, data=data, headers=headers, method='GET')
        retries = 0
        response = None
        while retries < self.max_retries:
            try:
                retries += 1
                response = self.opener.open(request)
                response = response.read()
                response = response.decode('utf-8')
                self.logger.debug('Response from %s length %s', url, len(response))
                if parse_json:
                    return json.loads(response)
                else:
                    return response

            except ValueError:
                wait_time = retries ** 3
                if self.id == 'sso':
                    self.logger.warning('Most likely SSO cookie is expired, will remake it after %s seconds',
                                        wait_time)
                    time.sleep(wait_time)
                    self.__generate_cookie()
                    self.__connect()
                else:
                    self.logger.warning('Error getting response, will retry after %s seconds', wait_time)
                    time.sleep(wait_time)

        self.logger.error('Error while making a %s request to %s. Response: %s',
                          method,
                          url,
                          response)
        return None

    def __get(self, url, parse_json=True):
        return self.__http_request(url, 'GET', parse_json=parse_json)

    def __put(self, url, data, parse_json=True):
        return self.__http_request(url, 'PUT', data, parse_json=parse_json)

    def __post(self, url, data, parse_json=True):
        return self.__http_request(url, 'POST', data, parse_json=parse_json)

    def __delete(self, url, parse_json=True):
        return self.__http_request(url, 'DELETE', parse_json=parse_json)

    # McM methods
    def get(self, object_type, object_id=None, query='', method='get', page=-1):
        """
        Get data from McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_id - usually prep id of desired object
        query - query to be run in order to receive an object, e.g. tags=M17p1A, multiple parameters can be used with & tags=M17p1A&pwg=HIG
        method - action to be performed, such as get, migrate or inspect
        page - which page to be fetched. -1 means no paginantion, return all results
        """
        object_type = object_type.strip()
        if object_id:
            object_id = object_id.strip()
            self.logger.debug('Object ID %s provided, method is %s, database %s',
                              object_id,
                              method,
                              object_type)
            url = 'restapi/%s/%s/%s' % (object_type, method, object_id)
            result = self.__get(url).get('results')
            if not result:
                return None

            return result
        elif query:
            if page != -1:
                self.logger.debug('Fetching page %s of %s for query %s',
                                  page,
                                  object_type,
                                  query)
                url = 'search/?db_name=%s&limit=50&page=%d&%s' % (object_type, page, query)
                results = self.__get(url).get('results', [])
                self.logger.debug('Found %s %s in page %s for query %s',
                                  len(results),
                                  object_type,
                                  page,
                                  query)
                return results
            else:
                self.logger.debug('Page not given, will use pagination to build response')
                page_results = [{}]
                results = []
                page = 0
                while page_results:
                    page_results = self.get(object_type=object_type,
                                            query=query,
                                            method=method,
                                            page=page)
                    results += page_results
                    page += 1

                return results
        else:
            self.logger.error('Neither object ID, nor query is given, doing nothing...')

    def update(self, object_type, object_data):
        """
        Update data in McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_data - new JSON of an object to be updated
        """
        return self.put(object_type, object_data, method='update')

    def put(self, object_type, object_data, method='save'):
        """
        Put data into McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_data - new JSON of an object to be updated
        method - action to be performed, default is 'save'
        """
        url = 'restapi/%s/%s' % (object_type, method)
        res = self.__put(url, object_data)
        return res

    def approve(self, object_type, object_id, level=None):
        if level is None:
            url = 'restapi/%s/approve/%s' % (object_type, object_id)
        else:
            url = 'restapi/%s/approve/%s/%d' % (object_type, object_id, level)

        return self.__get(url)

    def clone_request(self, object_data):
        return self.put('requests', object_data, method='clone')

    def get_range_of_requests(self, query):
        res = self.__put('restapi/requests/listwithfile', data={'contents': query})
        return res.get('results', None)

    def delete(self, object_type, object_id):
        url = 'restapi/%s/delete/%s' % (object_type, object_id)
        self.__delete(url)

    def forceflow(self, prepid):
        """
        Forceflow a chained request with given prepid
        """
        res = self.__get('restapi/chained_requests/flow/%s/force' % (prepid))
        return res.get('results', None)
