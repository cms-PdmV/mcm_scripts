"""
REST client for McM application.
"""

import os
from pathlib import Path
from typing import Union

import requests

from rest.client.session import SessionFactory
from rest.utils.logger import LoggerFactory
from rest.utils.shell import describe_platform


class McM:
    """
    Initializes the API.

    Arguments:
        id: The authentication mechanism to use. Supported values are 'sso' to
            use auth-get-sso-cookie, 'oidc' for OIDC authentication
            ("new SSO"). Any other value results in no authentication being
            used.
        debug: Controls the amount of logging printed to the terminal.
        cookie: The path of a cookie JAR in Netscape format, to be used for
            authentication.
        dev: Whether to use the dev or production McM instance (default: dev).
    """

    SSO = "sso"
    OIDC = "oidc"
    COOKIE_ENV_VAR = "MCM_COOKIE_PATH"

    def __init__(self, id=SSO, debug=False, cookie=None, dev=True):
        self._id = id
        self._debug = debug
        self._cookie = cookie
        self._dev = dev
        self.credentials_path = self._credentials_path()

        self.logger = LoggerFactory.getLogger("http_client.mcm")
        self.server = self._target_web_application()
        self.credentials_path = self._credentials_path()
        self.session = self._create_session()

    def _target_web_application(self) -> str:
        """
        Sets the production or development web application.
        """
        if self._dev:
            return "https://cms-pdmv-dev.web.cern.ch/mcm/"

        return "https://cms-pdmv-prod.web.cern.ch/mcm/"

    def _credentials_path(self) -> Path:
        """
        Sets the path from which credentials are going to be loaded and saved.
        """
        if self._cookie:
            return Path(self._cookie)

        from_env_var = os.getenv(McM.COOKIE_ENV_VAR)
        if from_env_var:
            return Path(from_env_var)

        private_folder = Path.home() / Path("private")
        private_folder.mkdir(mode=0o700, exist_ok=True)
        suffix: str = "mcm-credential-dev" if self._dev else "mcm-credential-prod"
        return private_folder / Path(suffix)

    def _create_session(self) -> requests.Session:
        """
        Configures the HTTP session depending on the chosen authentication method.
        """
        target_application = "cms-ppd-pdmv-device-flow"
        mcm_session: Union[requests.Session, None] = None
        if self._id == McM.SSO:
            mcm_session = SessionFactory.configure_by_session_cookie(
                url=self.server, credential_path=self.credentials_path
            )
        elif self._id == McM.OIDC:
            mcm_session = SessionFactory.configure_by_id_token(
                url=self.server,
                credential_path=self.credentials_path,
                target_application=target_application,
            )
        else:
            self.logger.warning("Using McM client without providing authentication")
            mcm_session = requests.Session()

        # Include some headers for the session
        user_agent = {"User-Agent": f"PdmV HTTP client (McM): {describe_platform()}"}
        mcm_session.headers.update(user_agent)
        return mcm_session

    def __repr__(self):
        return f"<McM id: {self._id} server: {self.server} cookie: {self._cookie}>"

    def __get(self, url):
        full_url = f"{self.server}{url}"
        response = self.session.get(url=full_url)
        return response.json()

    def __put(self, url, data):
        full_url = f"{self.server}{url}"
        response = self.session.put(url=full_url, json=data)
        return response.json()

    def __post(self, url, data):
        full_url = f"{self.server}{url}"
        response = self.session.post(url=full_url, json=data)
        return response.json()

    def __delete(self, url):
        full_url = f"{self.server}{url}"
        response = self.session.delete(url=full_url)
        return response.json()

    # McM methods
    def get(self, object_type, object_id=None, query="", method="get", page=-1):
        """
        Get data from McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_id - usually prep id of desired object
        query - query to be run in order to receive an object, e.g. tags=M17p1A, multiple parameters can be used with & tags=M17p1A&pwg=HIG
        method - action to be performed, such as get, migrate or inspect
        page - which page to be fetched. -1 means no pagination, return all results
        """
        object_type = object_type.strip()
        if object_id:
            object_id = object_id.strip()
            self.logger.debug(
                "Object ID %s provided, method is %s, database %s",
                object_id,
                method,
                object_type,
            )
            url = "restapi/%s/%s/%s" % (object_type, method, object_id)
            result = self.__get(url).get("results")
            if not result:
                return None

            return result
        elif query:
            if page != -1:
                self.logger.debug(
                    "Fetching page %s of %s for query %s", page, object_type, query
                )
                url = "search/?db_name=%s&limit=50&page=%d&%s" % (
                    object_type,
                    page,
                    query,
                )
                results = self.__get(url).get("results", [])
                self.logger.debug(
                    "Found %s %s in page %s for query %s",
                    len(results),
                    object_type,
                    page,
                    query,
                )
                return results
            else:
                self.logger.debug(
                    "Page not given, will use pagination to build response"
                )
                page_results = [{}]
                results = []
                page = 0
                while page_results:
                    page_results = self.get(
                        object_type=object_type, query=query, method=method, page=page
                    )
                    results += page_results
                    page += 1

                return results
        else:
            self.logger.error("Neither object ID, nor query is given, doing nothing...")

    def update(self, object_type, object_data):
        """
        Update data in McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_data - new JSON of an object to be updated
        """
        return self.put(object_type, object_data, method="update")

    def put(self, object_type, object_data, method="save"):
        """
        Put data into McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_data - new JSON of an object to be updated
        method - action to be performed, default is 'save'
        """
        url = "restapi/%s/%s" % (object_type, method)
        res = self.__put(url, object_data)
        return res

    def approve(self, object_type, object_id, level=None):
        if level is None:
            url = "restapi/%s/approve/%s" % (object_type, object_id)
        else:
            url = "restapi/%s/approve/%s/%d" % (object_type, object_id, level)

        return self.__get(url)

    def clone_request(self, object_data):
        return self.put("requests", object_data, method="clone")

    def get_range_of_requests(self, query):
        res = self.__put("restapi/requests/listwithfile", data={"contents": query})
        return res.get("results", None)

    def delete(self, object_type, object_id):
        url = "restapi/%s/delete/%s" % (object_type, object_id)
        self.__delete(url)

    def forceflow(self, prepid):
        """
        Force a flow on a chained request with given prepid
        """
        res = self.__get("restapi/chained_requests/flow/%s/force" % (prepid))
        return res.get("results", None)

    def reset(self, prepid):
        """
        Reset a request
        """
        res = self.__get("restapi/requests/reset/%s" % (prepid))
        return res.get("results", None)

    def soft_reset(self, prepid):
        """
        Soft reset a request
        """
        res = self.__get("restapi/requests/soft_reset/%s" % (prepid))
        return res.get("results", None)

    def option_reset(self, prepid):
        """
        Option reset a request
        """
        res = self.__get("restapi/requests/option_reset/%s" % (prepid))
        return res.get("results", None)

    def ticket_generate(self, ticket_prepid):
        """
        Generate chains for a ticket
        """
        res = self.__get("restapi/mccms/generate/%s" % (ticket_prepid))
        return res.get("results", None)

    def ticket_generate_reserve(self, ticket_prepid):
        """
        Generate and reserve chains for a ticket
        """
        res = self.__get("restapi/mccms/generate/%s/reserve" % (ticket_prepid))
        return res.get("results", None)

    def rewind(self, chained_request_prepid):
        """
        Rewind a chained request
        """
        res = self.__get(
            "restapi/chained_requests/rewind/%s" % (chained_request_prepid)
        )
        return res.get("results", None)

    def flow(self, chained_request_prepid):
        """
        Flow a chained request
        """
        res = self.__get("restapi/chained_requests/flow/%s" % (chained_request_prepid))
        return res.get("results", None)

    def root_requests_from_ticket(self, ticket_prepid):
        """
        Return list of all root (first ones in the chain) requests of a ticket
        """
        mccm = self.get("mccms", ticket_prepid)
        query = ""
        for root_request in mccm.get("requests", []):
            if isinstance(root_request, str):
                query += "%s\n" % (root_request)
            elif isinstance(root_request, list):
                # List always contains two elements - start and end of a range
                query += "%s -> %s\n" % (root_request[0], root_request[1])
            else:
                self.logger.error(
                    "%s is of unsupported type %s", root_request, type(root_request)
                )

        requests = self.get_range_of_requests(query)
        return requests
