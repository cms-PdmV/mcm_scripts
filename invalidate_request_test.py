"""
This module tests the functionality
provided in the `invalidate_request.py`
module to delete requests in cascade.
"""

import unittest
import os
import random
from rest import McM
from invalidate_request import InvalidateDeleteRequests


class InvalidateDeleteRequestTest(unittest.TestCase):
    """
    Test cases for the class `InvalidateDeleteRequests`.
    """

    # Some McM types required to query.
    chain_request_type = "chained_requests"
    request_type = "requests"

    def _remove_cookies(self):
        """
        This tries to remove the session cookies if they are
        available in the filesystem.
        """
        home = os.getenv("HOME")
        dev_cookie_path = "%s/private/mcm-dev-cookie.txt" % (home)
        try:
            os.remove(dev_cookie_path)
        except OSError:
            # Supress the error if some file doesn't exist
            pass

    def _get_test_request(self, mcm: McM, size: int) -> list[str]:
        """
        Get some example requests to use in the tests.
        Return only its prepid.
        Raises an error if it is not possible to retrieve
        this test set.
        """
        samples = mcm.get(
            object_type=InvalidateDeleteRequestTest.request_type,
            query="prepid=*Run3Summer22*GS*&status=done",
            page=2,
        )
        random.shuffle(samples)
        if not samples:
            raise ValueError("Unable to retrieve a test set.")

        return [
            el.get("prepid") for idx, el in enumerate(samples, start=1) if idx <= size
        ]

    def setUp(self) -> None:
        """
        Build the test environment.
        """
        self._remove_cookies()
        self.mcm = McM(id=McM.SSO, dev=True)
        self.samples = self._get_test_request(mcm=self.mcm, size=5)
        self.invalidator = InvalidateDeleteRequests(mcm=self.mcm)

    def test_non_root_requests(self) -> None:
        """
        Check that non root requests are processed.
        """
        non_root_req = [
            "B2G-Run3Summer19MiniAOD-00012",
            "B2G-Run3Summer19NanoAOD-00012",
            "B2G-Run3Summer19DRPremix-00001",
            "B2G-Run3Summer19DR-00006",
        ]
        result = self.invalidator.invalidate_delete_cascade_requests(
            requests_prepid=non_root_req
        )
        self.assertEqual(result.get("sucess"), [], "No request should be processed")
        self.assertEqual(result.get("failed"), [], "No request should be processed")
        self.assertEqual(
            set(result.get("filtered")),
            set(non_root_req),
            "All request should be filtered out",
        )

    def test_root_request_not_exists(self) -> None:
        """
        Check that the procedure fails gracefully
        if it is attempted to process a root requests
        that doesn't exists.
        """
        non_exists = ["PPD-Run3HeheNotExists23pLHEGS-00001"]
        result = self.invalidator.invalidate_delete_cascade_requests(
            requests_prepid=non_exists
        )
        self.assertEqual(result.get("sucess"), [], "No request should be processed")
        self.assertEqual(result.get("failed"), [], "No request should be processed")
        self.assertEqual(
            set(result.get("filtered")),
            set(non_exists),
            "All request should be filtered out",
        )

    def test_renable_chain_request(self) -> None:
        """
        Deletes all the intermediate request for all the
        chained request included into a root request
        without removing the chain request after processing.
        """
        example_root_request_prepid = self.samples[0]
        example_chain_requests: list[str] = self.mcm.get(
            object_type=InvalidateDeleteRequestTest.request_type,
            object_id=example_root_request_prepid,
        ).get("member_of_chain", [])
        result = self.invalidator.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid]
        )

        # Check it was properly processed.
        self.assertEqual(
            result.get("sucess"),
            [example_root_request_prepid],
            "The example request should be processed properly",
        )

        # Check the chain requests still exists.
        validation_chain_request: list[str] = self.mcm.get(
            object_type="requests", object_id=example_root_request_prepid
        ).get("member_of_chain", [])
        self.assertEqual(
            set(example_chain_requests),
            set(validation_chain_request),
            "No chain request should be deleted",
        )

        # Check each chain request.
        for chain_prepid in validation_chain_request:
            chain_request_data: dict = self.mcm.get(
                object_type=InvalidateDeleteRequestTest.chain_request_type,
                object_id=chain_prepid,
            )
            self.assertEqual(
                chain_request_data.get("action_parameters", {}).get("flag"),
                True,
                "Flag should be set again",
            )
            self.assertEqual(
                set(chain_request_data.get("chain", [])),
                set([example_root_request_prepid]),
                "The chain request contains more elements than the root request",
            )

    def test_delete_chain_request_non_root(self) -> None:
        """
        Deletes all the chain requests related to
        a root request and its intermediate requests.
        """
        example_root_request_prepid = self.samples[0]
        example_chain_requests: list[str] = self.mcm.get(
            object_type=InvalidateDeleteRequestTest.request_type,
            object_id=example_root_request_prepid,
        ).get("member_of_chain", [])
        result = self.invalidator.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid], remove_chain=True
        )

        # Check it was properly processed.
        self.assertEqual(
            result.get("sucess"),
            [example_root_request_prepid],
            "The example request should be processed properly",
        )

        # Check that the chains shouldn't exist anymore.
        validation_root_request: dict = self.mcm.get(
            object_type="requests", object_id=example_root_request_prepid
        )
        self.assertIsNotNone(
            validation_root_request, "The root request should be deleted"
        )

        validation_chain_request: list[str] = validation_root_request.get(
            "member_of_chain", []
        )
        self.assertEqual(
            [],
            validation_chain_request,
            "No chain request should appear here.",
        )

        deleted_chain_request: list[None] = [
            self.mcm.get(
                object_type=InvalidateDeleteRequestTest.chain_request_type,
                object_id=deleted_chain,
            )
            for deleted_chain in example_chain_requests
        ]
        self.assertEqual(
            any(deleted_chain_request), False, "No chain request should exist anymore"
        )

    def test_delete_all_from_root(self) -> None:
        """
        Invalidate and delete a root request and all the requests
        and chain requests linked to it.
        """
        example_root_request_prepid = self.samples[0]
        root_request_data: dict = self.mcm.get(
            object_type=InvalidateDeleteRequestTest.request_type,
            object_id=example_root_request_prepid,
        )
        linked_chained_requests: list[str] = root_request_data.get(
            "member_of_chain", []
        )

        # Prune the root request.
        self.invalidator.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid], remove_root=True
        )

        # The root request shouldn't exists anymore.
        root_request_data: dict = self.mcm.get(
            object_type=InvalidateDeleteRequestTest.request_type,
            object_id=example_root_request_prepid,
        )
        self.assertIsNone(root_request_data, "Root request shouldn't exist anymore")

        # Check all the old chained request don't exists anymore.
        for chain_request in linked_chained_requests:
            chain_request_data = self.mcm.get(
                object_type=InvalidateDeleteRequestTest.chain_request_type,
                object_id=chain_request,
            )
            self.assertIsNone(
                chain_request_data, "Chained request shouldn't exist anymore"
            )


if __name__ == "__main__":
    unittest.main()
