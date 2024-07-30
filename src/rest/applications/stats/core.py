"""
REST client for the Stats2 application.
"""

from typing import Union
from rest.applications.base import BaseClient


class Stats2(BaseClient):
    """
    Initializes an HTTP client for querying Stats2.
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
            app="stats",
            id=id,
            debug=debug,
            cookie=cookie,
            dev=dev,
            client_id=client_id,
            client_secret=client_secret,
        )

    def get_workflow(self, workflow_name: str) -> dict:
        """
        Retrieves the Stats2 document related to the given workflow.

        Args:
            workflow_name: ReqMgr2 Request ID (a.k.a workflow in PdmV applications).
        """
        url = f"api/get_json/{workflow_name}"
        return self._get(url=url)

    def get_prepid(self, prepid: str) -> list[dict]:
        """
        Retrieves a list of Stats2 documents related to the given prepid.

        Args:
            prepid: The main identifier for requests in PdmV applications.
        """
        url = f"api/fetch?prepid={prepid}"
        return self._get(url=url)

    def get_input_dataset(self, input_dataset: str) -> list[dict]:
        """
        Retrieves a list of Stats2 documents related to the given input dataset.

        Args:
            input_dataset: Input dataset name. It follows DBS and DAS
                schema.
        """
        url = f"api/fetch?input_dataset={input_dataset}"
        return self._get(url=url)

    def get_output_dataset(self, output_dataset: str) -> list[dict]:
        """
        Retrieves the Stats2 document related to the given output dataset.

        Args:
            output_dataset: Output dataset name. It follows DBS and DAS
                schema.
        """
        url = f"api/fetch?output_dataset={output_dataset}"
        return self._get(url=url)
    
    def get_request(self, prepid: str):
        """
        Retrieves the Stats2 document related to the request.

        Args:
            prepid: Request's prepid. This is only useful for McM requests.
        """
        url = f"api/fetch?request={prepid}"
        return self._get(url=url)
