"""
REST client for the ReReco application
"""

from typing import Union

from rest.applications.base import BaseClient

class ReReco(BaseClient):
    """
    Initializes an HTTP client for querying ReReco.
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
            app="rereco",
            id=id,
            debug=debug,
            cookie=cookie,
            dev=dev,
            client_id=client_id,
            client_secret=client_secret,
        )

    def get(self, object_type, object_id=None, query=None ,method="get", page=-1):
        object_type = object_type.strip()
        if object_id:
            object_id = object_id.strip()
            url = "api/%s/%s/%s" % (object_type, method, object_id)
            result = self._get(url).get("response")
            if not result:
                return None
            return result
        elif query:
            if page != -1:
                url = "api/search/?db_name=%s&page=%d&%s" % (
                    object_type,
                    page,
                    query,
                )
                results = self._get(url).get("response",{}).get("results", [])
                return results
            else:
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
            #nothing to do
            return None

    def put(self, object_type, object_data, method="create"):
        url = "api/%s/%s" % (object_type, method)
        res = self._put(url, object_data)
        return res
    def post(self, object_type, object_data, method="update"):
        url = "api/%s/%s" % (object_type, method)
        res = self._post(url, object_data)
        return res
