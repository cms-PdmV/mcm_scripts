"""
This module tests the functionality
provided in the `resubmission.py`
module to resubmit chained requests.
"""

import pytest
from fixtures.mcm import (
    invalidator_development,
    mcm_development,
    chain_request_resubmitter_dev as chain_resubmitter,
    non_root_requests,
    production_manager_or_higher,
    root_request,
)
from fixtures.oauth import stdin_enabled
from rest.applications.mcm.resubmission import ChainRequestResubmitter
from rest.applications.mcm.core import McM


@pytest.mark.usefixtures("stdin_enabled", "production_manager_or_higher")
class TestChainRequestResubmitter:
    """
    Test cases for the class `ChainRequestResubmitter`.
    """

    # Some McM types required to query.
    chain_request_type = "chained_requests"
    request_type = "requests"

    def scan_root_request_on_depth(
        self, mcm_development: McM, root_request_ids: list[str]
    ) -> dict[str, dict[str, list[str]]]:
        """
        Given a list of root requests, scans its chained requests
        and stores the list of requests each one has.
        """
        result = {}
        for root_request in root_request_ids:
            chained_requests = mcm_development.get(
                object_type="chained_requests", query=f"contains={root_request}"
            )
            chained_request_info = {
                ch_r["prepid"]: ch_r["chain"] for ch_r in chained_requests
            }
            result.update({root_request: chained_request_info})

        return result

    def compare_reconstruction(
        self,
        mcm: McM,
        root_requests: list[str],
        pre_chained_structure: dict[str, dict[str, list[str]]],
        post_chained_structure: dict[str, dict[str, list[str]]],
        datatier: str,
        soft_datatier: bool,
    ) -> None:
        """
        Compares the structure of a root request before and after
        being resubmitted.
        """
        assert (
            pre_chained_structure.keys() == pre_chained_structure.keys()
        ), "Some root requests were not processed"

        for root_request_prepid in root_requests:
            root_request_pre = pre_chained_structure[root_request_prepid]
            root_request_post = post_chained_structure[root_request_prepid]
            assert (
                root_request_pre.keys() == root_request_post.keys()
            ), "Some chained requests are missing"

            # Request level
            for chained_request in root_request_pre:
                request_chain_pre = root_request_pre[chained_request]
                request_chain_post = root_request_post[chained_request]

                # Check the root request is the same
                assert (
                    request_chain_pre[0] == request_chain_post[0]
                ), "Root request is not the same"
                assert (
                    root_request_prepid == request_chain_post[0]
                ), "Root request is not the same"

                # Check all the request in the chain were recreated
                request_set_post = set(request_chain_post[1:])
                request_set_pre = set(request_chain_pre[1:])
                assert (
                    request_set_post - request_set_pre
                ) == request_set_post, (
                    "Some internal requests in the chain remain the same"
                )

                # Check the latest request in the chain is related to the
                # desired datatier.
                if not soft_datatier:
                    assert (
                        datatier.upper() in request_chain_post[-1].upper()
                    ), "Reference to the target data tier not found in the new chained request"

                # Check all the request are in submit/submitted status
                request_in_chain: list[dict] = [
                    mcm.get(object_type="requests", object_id=request_prepid)
                    for request_prepid in request_chain_post
                ]
                request_status = [
                    req["approval"] == "submit" and req["status"] == "submitted"
                    for req in request_in_chain
                ]
                assert all(request_status), "Not all requests are in the final status"
        pass

    def test_non_root_requests(
        self, chain_resubmitter: ChainRequestResubmitter, non_root_requests
    ) -> None:
        """
        Check that non-root requests are not processed.
        """
        for request_prepid in non_root_requests:
            with pytest.raises(ValueError):
                chain_resubmitter.resubmit_chain_request(
                    root_request_prepid=request_prepid
                )

    @pytest.mark.parametrize("datatier", ["miniaod", "nanoaod"])
    def test_resubmit_root_requests(
        self, chain_resubmitter: ChainRequestResubmitter, datatier, root_request
    ) -> None:
        """
        Check that all chained requests related to a root request
        have been properly recreated and reinjected.
        """
        root_request_set = [root_request[0]]
        chained_structure_pre = self.scan_root_request_on_depth(
            mcm_development=chain_resubmitter._mcm, root_request_ids=root_request_set
        )

        for root_request_prepid in root_request_set:
            chain_resubmitter.resubmit_chain_request(
                root_request_prepid=root_request_prepid, datatier=datatier
            )

        chained_structure_post = self.scan_root_request_on_depth(
            mcm_development=chain_resubmitter._mcm, root_request_ids=root_request_set
        )

        # Check assertions
        self.compare_reconstruction(
            mcm=chain_resubmitter._mcm,
            root_requests=root_request_set,
            pre_chained_structure=chained_structure_pre,
            post_chained_structure=chained_structure_post,
            datatier=datatier,
            soft_datatier=False,
        )

    def test_resubmit_invalid_datatier(
        self, chain_resubmitter: ChainRequestResubmitter, root_request
    ) -> None:
        """
        Check an exception is raised when it is not possible to
        reserve the chained requests up to the desired data tier.
        """
        root_request_set = [root_request[0]]
        datatier = "notexists"
        with pytest.raises(
            ValueError, match="no campaign related to the desired data tier"
        ):
            for root_request_prepid in root_request_set:
                chain_resubmitter.resubmit_chain_request(
                    root_request_prepid=root_request_prepid, datatier=datatier
                )

    def test_resubmit_soft_datatier(
        self, chain_resubmitter: ChainRequestResubmitter, root_request
    ) -> None:
        """
        Checks the chained requests are reserved with the latest campaign
        if `soft data tier` option is provided instead of raising an exception.
        """
        root_request_set = [root_request[0]]
        datatier = "notexists"
        soft_datatier = True

        chained_structure_pre = self.scan_root_request_on_depth(
            mcm_development=chain_resubmitter._mcm, root_request_ids=root_request_set
        )

        for root_request_prepid in root_request_set:
            chain_resubmitter.resubmit_chain_request(
                root_request_prepid=root_request_prepid,
                datatier=datatier,
                soft_datatier=soft_datatier,
            )

        chained_structure_post = self.scan_root_request_on_depth(
            mcm_development=chain_resubmitter._mcm, root_request_ids=root_request_set
        )

        # Check assertions
        self.compare_reconstruction(
            mcm=chain_resubmitter._mcm,
            root_requests=root_request_set,
            pre_chained_structure=chained_structure_pre,
            post_chained_structure=chained_structure_post,
            datatier=datatier,
            soft_datatier=soft_datatier,
        )
