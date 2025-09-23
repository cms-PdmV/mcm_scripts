"""
REST client for the McM application.
"""

import warnings
from typing import Union

from rest.applications.base import BaseClient


class McM(BaseClient):
    """
    Initializes an HTTP client for querying McM.
    """

    def __init__(
        self,
        id: str = BaseClient.SSO,
        debug: bool = False,
        cookie: Union[str, None] = None,
        dev: bool = True,
        client_id: str = "",
        client_secret: str = "",
    ):
        # Set the HTTP session
        super().__init__(
            app="mcm",
            id=id,
            debug=debug,
            cookie=cookie,
            dev=dev,
            client_id=client_id,
            client_secret=client_secret,
        )

    def __get(self, url):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._get(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._get(url=url)

    def __put(self, url, data):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._put(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._put(url=url, data=data)

    def __post(self, url, data):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._post(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._post(url=url, data=data)

    def __delete(self, url):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._delete(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._delete(url=url)

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
            result = self._get(url)
            if type(result) == list:
                return result
            elif type(result) == str:
                return result
            result = result.get("results")
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
                results = self._get(url).get("results", [])
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
        res = self._put(url, object_data)
        return res

    def post(self, object_type, object_data, method):
        """
        Post data into McM
        object_type - [chained_campaigns, chained_requests, campaigns, requests, flows, etc.]
        object_data - JSON to be posted
        method - restapi to be called
        """
        url = 'restapi/%s/%s' % (object_type, method)
        res = self._post(url, object_data)
        return res
    
    def approve(self, object_type, object_id, level=None):
        if level is None:
            url = "restapi/%s/approve/%s" % (object_type, object_id)
        else:
            url = "restapi/%s/approve/%s/%d" % (object_type, object_id, level)

        return self._get(url)

    def clone_request(self, object_data):
        return self.put("requests", object_data, method="clone")

    def get_range_of_requests(self, query):
        res = self._put("restapi/requests/listwithfile", data={"contents": query})
        return res.get("results", None)

    def delete(self, object_type, object_id):
        url = "restapi/%s/delete/%s" % (object_type, object_id)
        self._delete(url)

    def forceflow(self, prepid):
        """
        Force a flow on a chained request with given `prepid`
        """
        res = self._get("restapi/chained_requests/flow/%s/force" % (prepid))
        return res.get("results", None)

    def reset(self, prepid):
        """
        Reset a request
        """
        res = self._get("restapi/requests/reset/%s" % (prepid))
        return res.get("results", None)

    def soft_reset(self, prepid):
        """
        Soft reset a request
        """
        res = self._get("restapi/requests/soft_reset/%s" % (prepid))
        return res.get("results", None)

    def option_reset(self, prepid):
        """
        Option reset a request
        """
        res = self._get("restapi/requests/option_reset/%s" % (prepid))
        return res.get("results", None)

    def ticket_generate(self, ticket_prepid):
        """
        Generate chains for a ticket
        """
        res = self._get("restapi/mccms/generate/%s" % (ticket_prepid))
        return res.get("results", None)

    def ticket_generate_reserve(self, ticket_prepid):
        """
        Generate and reserve chains for a ticket
        """
        res = self._get("restapi/mccms/generate/%s/reserve" % (ticket_prepid))
        return res.get("results", None)

    def rewind(self, chained_request_prepid):
        """
        Rewind a chained request
        """
        res = self._get("restapi/chained_requests/rewind/%s" % (chained_request_prepid))
        return res.get("results", None)

    def flow(self, chained_request_prepid):
        """
        Flow a chained request
        """
        res = self._get("restapi/chained_requests/flow/%s" % (chained_request_prepid))
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

    def is_root_request(self, request: Union[str, dict]) -> bool:
        """
        Checks if a request is a root request.

        Args:
            request: Request prepid or request data.
                The request must exists and its data must comply the expected
                schema.
        """
        request_data: dict = {}
        if isinstance(request, str):
            # Received request prepid
            request_data = self.get(object_type="requests", object_id=request) or {}
        elif isinstance(request, dict):
            request_data = request
        else:
            raise ValueError(f"Unexpected value: {request} - {type(request)}")

        return request_data.get("type", "") in ("LHE", "Prod")
