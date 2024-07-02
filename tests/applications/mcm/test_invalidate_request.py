"""
This module tests the functionality
provided in the `invalidate_request.py`
module to delete requests in cascade.
"""

import pytest
from fixtures.mcm import (
    invalidator_development,
    mcm_development,
    non_root_requests,
    production_manager_or_higher,
    root_request,
)
from fixtures.oauth import stdin_enabled


@pytest.mark.usefixtures("stdin_enabled", "production_manager_or_higher")
class TestInvalidateDeleteRequest:
    """
    Test cases for the class `InvalidateDeleteRequests`.
    """

    # Some McM types required to query.
    chain_request_type = "chained_requests"
    request_type = "requests"

    def test_non_root_requests(
        self, invalidator_development, non_root_requests
    ) -> None:
        """
        Check that non-root requests are processed.
        """
        result = invalidator_development.invalidate_delete_cascade_requests(
            requests_prepid=non_root_requests
        )
        assert result["success"] == [], "No request should be processed"
        assert result["failed"] == [], "No request should be processed"
        assert set(result["filtered"]) == set(
            non_root_requests
        ), "All request should be filtered out"

    def test_root_request_not_exists(self, invalidator_development) -> None:
        """
        Check that the procedure fails gracefully
        if it is attempted to process a root requests
        that doesn't exist.
        """
        non_exists = ["PPD-Run3ThisDoesNotExists23pLHEGS-00001"]
        result = invalidator_development.invalidate_delete_cascade_requests(
            requests_prepid=non_exists
        )
        assert result["success"] == [], "No request should be processed"
        assert result["failed"] == [], "No request should be processed"
        assert set(result["filtered"]) == set(
            non_exists
        ), "All request should be filtered out"

    def test_renable_chain_request(
        self, mcm_development, invalidator_development, root_request
    ) -> None:
        """
        Deletes all the intermediate request for all the
        chained request included into a root request
        without removing the chain request after processing.
        """
        example_root_request_prepid = root_request[0]
        example_chain_requests: list[str] = mcm_development.get(
            object_type=self.request_type,
            object_id=example_root_request_prepid,
        ).get("member_of_chain", [])
        result = invalidator_development.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid]
        )

        # Check it was properly processed.
        assert result["success"] == [
            example_root_request_prepid
        ], "The example request should be processed properly"

        # Check the chain requests still exists.
        validation_chain_request: list[str] = mcm_development.get(
            object_type="requests", object_id=example_root_request_prepid
        ).get("member_of_chain", [])

        assert set(example_chain_requests) == set(
            validation_chain_request
        ), "No chain request should be deleted"

        # Check each chain request.
        for chain_prepid in validation_chain_request:
            chain_request_data: dict = mcm_development.get(
                object_type=self.chain_request_type,
                object_id=chain_prepid,
            )
            assert (
                chain_request_data.get("action_parameters", {}).get("flag") == True
            ), "Flag should be set again"
            assert set(chain_request_data.get("chain", [])) == set(
                [example_root_request_prepid]
            ), "The chain request contains more elements than the root request"

    def test_delete_chain_request_non_root(
        self, mcm_development, invalidator_development, root_request
    ) -> None:
        """
        Deletes all the chain requests related to
        a root request and its intermediate requests.
        """
        example_root_request_prepid = root_request[0]
        example_chain_requests: list[str] = mcm_development.get(
            object_type=self.request_type,
            object_id=example_root_request_prepid,
        ).get("member_of_chain", [])
        result = invalidator_development.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid], remove_chain=True
        )

        # Check it was properly processed.
        assert result["success"] == [
            example_root_request_prepid
        ], "The example request should be processed properly"

        # Check that the chains shouldn't exist anymore.
        validation_root_request: dict = mcm_development.get(
            object_type="requests", object_id=example_root_request_prepid
        )
        assert validation_root_request, "The root request should not be deleted"

        validation_chain_request: list[str] = validation_root_request.get(
            "member_of_chain", []
        )
        assert validation_chain_request == [], "No chain request should appear here."

        deleted_chain_request: list[None] = [
            mcm_development.get(
                object_type=self.chain_request_type,
                object_id=deleted_chain,
            )
            for deleted_chain in example_chain_requests
        ]
        assert (
            any(deleted_chain_request) == False
        ), "No chain request should exist anymore"

    def test_delete_all_from_root(
        self, mcm_development, invalidator_development, root_request
    ) -> None:
        """
        Invalidate and delete a root request and all the requests
        and chain requests linked to it.
        """
        example_root_request_prepid = root_request[0]
        root_request_data: dict = mcm_development.get(
            object_type=self.request_type,
            object_id=example_root_request_prepid,
        )
        linked_chained_requests: list[str] = root_request_data.get(
            "member_of_chain", []
        )

        # Prune the root request.
        invalidator_development.invalidate_delete_cascade_requests(
            requests_prepid=[example_root_request_prepid], remove_root=True
        )

        # The root request shouldn't exists anymore.
        root_request_data: dict = mcm_development.get(
            object_type=self.request_type,
            object_id=example_root_request_prepid,
        )
        assert not root_request_data, "Root request shouldn't exist anymore"

        # Check all the old chained request don't exists anymore.
        for chain_request in linked_chained_requests:
            chain_request_data = mcm_development.get(
                object_type=self.chain_request_type,
                object_id=chain_request,
            )
            assert not chain_request_data, "Chained request shouldn't exist anymore"
