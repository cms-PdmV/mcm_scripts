from enum import Enum
from typing import Union

from rest import McM
from rest.applications.mcm.invalidate_request import InvalidateDeleteRequests
from rest.utils.miscellaneous import pformat


class RootRequestReset(Enum):
    """
    Describes how a root request was reset so that
    it is reusable in later steps to recreate its
    chained requests.
    """

    # Root request was soft reset.
    SOFT_RESET = 1

    # Root request was fully reset.
    # This request was validated before, so
    # instead of repeating the validation,
    # old results are reincluded again.
    FULL_RESET = 2

    # Root request keeps output
    # (it created a big "RAW" dataset being used in other steps, chains, ...)
    # Handle it so that it is not required to recreate it
    # again.
    KEEPS_OUTPUT = 3


class ChainRequestResubmitter:
    """
    Rewinds a chained request to its root
    so that you can recreate the chain and attempt to
    inject it again.

    The scenario to use this is the following: Some configuration
    applied in a campaign or chained campaign was wrong so that, after
    applying a patch on these elements (that work as a template) you
    need to recreate all the requests using this new change and reinject them.

    Attributes:
        mcm: McM client instance
    """

    def __init__(self, mcm: McM) -> None:
        self._mcm = mcm
        self._invalidator = InvalidateDeleteRequests(mcm=self._mcm)
        self.logger = self._mcm.logger

    def _root_request_to_approve(self, root_prepid: str) -> RootRequestReset:
        """
        This is a customization for resetting a root request so
        that it ends up in an 'approve/approved' status and could
        be easily reused to recreate a chained request and inject it
        again.

        Args:
            root_prepid: Root request's prepid

        Returns:
            An attribute describing how the root request was processed.
        """
        data: Union[dict, None] = self._mcm.get(
            object_type="requests", object_id=root_prepid
        )
        if not data:
            raise ValueError(f"Root request {root_prepid} not found")

        approval = data.get("approval")
        status = data.get("status")
        if approval == "submit" and status == "done":
            keep_output: Union[list[bool], None] = data.get("keep_output")
            if not keep_output:
                raise ValueError("Keep output is not defined")

            if all(keep_output):
                # Avoid resetting this kind of root request
                # Just reuse it as it is
                return RootRequestReset.KEEPS_OUTPUT
            else:
                self.logger.warning(
                    (
                        "Root request (%s) is already done, resetting it, "
                        "announcing the invalidation, and setting it to approve/approved"
                    ),
                    root_prepid,
                )
                validation: Union[dict, None] = data.get("validation")
                self.logger.debug("Validation results: %s", validation)
                if not validation:
                    raise ValueError("Validation results not available")

                # Reset the request.
                reset_result = self._mcm.reset(prepid=root_prepid)
                if not reset_result:
                    msg = f"Unable to reset the root request: {root_prepid}"
                    self.logger.error(msg)
                    raise RuntimeError(msg)

                # Announce the invalidation.
                self._invalidator._process_invalidation(request_prepids=[root_prepid])

                # Force its status to approve/approved, re-including the validation.
                data: dict = self._mcm.get(
                    object_type="requests", object_id=root_prepid
                )
                assert isinstance(data, dict)

                data["validation"] = validation
                data["approval"] = "approve"
                data["status"] = "approved"

                updated_result = self._mcm.update(
                    object_type="requests", object_data=data
                )
                if not updated_result or not updated_result.get("results"):
                    msg = f"Error forcing the root request status: {root_prepid}"
                    self.logger.error(msg)
                    raise RuntimeError(msg)

                return RootRequestReset.FULL_RESET
        else:
            # Soft reset request
            soft_reset_result = self._mcm.soft_reset(prepid=root_prepid)
            self.logger.info("Soft reset result: %s", soft_reset_result)
            if not soft_reset_result:
                msg = (
                    f"Unable to soft reset the request ({root_prepid}) "
                    "and set its status to approve/approved"
                )
                self.logger.error(msg)
                raise RuntimeError(msg)

            return RootRequestReset.SOFT_RESET

    def _include_tag(self, request_prepid: str, tag: str) -> None:
        """
        Includes a new tag for the `request`

        Args:
            request_prepid (str): Request identifier
            tag (str): New tag to include
        """
        request_data: dict = self._mcm.get("requests", object_id=request_prepid)
        assert isinstance(request_data, dict)

        request_data["tags"] += [tag]
        tag_result = self._mcm.update("requests", request_data)
        self.logger.debug("Include `tag` result: %s", tag_result)
        if not tag_result or not tag_result.get("results"):
            msg = f"Unable to include a tracking tag for the root request: {request_prepid}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def _pick_target_campaign(
        self, chained_campaign_prepid: str, datatier: str
    ) -> Union[str, None]:
        """
        Retrieves the campaign related to the desired data tier for a given chained campaign

        Args:
            chained_campaign_prepid: Chained campaign identifier.
            datatier: Data tier related to the campaign to retrieve.

        Returns:
            Campaign related to the data tier, None if not found
        """
        chained_campaign: Union[dict, None] = self._mcm.get(
            object_type="chained_campaigns", object_id=chained_campaign_prepid
        )
        if not chained_campaign:
            raise ValueError(f"Chained campaign not found: {chained_campaign_prepid}")

        campaigns: list[list[str]] = chained_campaign.get("campaigns", [])
        for campaign_range in campaigns:
            for c in campaign_range:
                c_str = c or ""
                if c_str.startswith("Run") and datatier.lower() in c_str.lower():
                    return c_str

        self.logger.debug(
            "There's no campaign related to the data tier %s for the chained campaign %s: %s",
            datatier,
            chained_campaign_prepid,
            campaigns,
        )
        return None

    def _reserve_chain_request(self, chain_request_prepid: str, datatier: str) -> None:
        """
        Reserve a chained request up to a desired data tier. This creates the
        remaining requests in the chained request based on a chained campaign
        definition (template).

        Args:
            chain_request_prepid: Chained request identifier.
            datatier: Limits the requests created up to this data tier.
        """
        chained_request: Union[dict, None] = self._mcm.get(
            object_type="chained_requests", object_id=chain_request_prepid
        )
        if not chained_request:
            raise ValueError(f"Chain request not found: {chain_request_prepid}")

        # Pick the `member_of_campaign` attribute and look
        # for the chained campaign. This has the info for the correct
        # campaign modifications (campaigns and flows, customizations)
        member_of_campaign = chained_request.get("member_of_campaign")
        if not member_of_campaign:
            raise ValueError(
                f"Member of campaign is not set for {chain_request_prepid}"
            )

        target_campaign = self._pick_target_campaign(
            chained_campaign_prepid=member_of_campaign, datatier=datatier
        )
        if not target_campaign:
            msg = (
                f"There's no campaign related to the desired data tier ({datatier}) in "
                f"the linked chained campaign ({member_of_campaign}) that could "
                "be used to reserve the chained request"
            )
            raise ValueError(msg)

        # Reserve the chain
        reserve_endpoint = f"restapi/chained_requests/flow/{chain_request_prepid}/reserve/{target_campaign}"
        reserve_result = self._mcm._get(url=reserve_endpoint)
        if not reserve_result or not reserve_result.get("results", False):
            raise RuntimeError(
                f"Unable to reserve the chained request ({chain_request_prepid}). Details: {reserve_result}"
            )

    def _approve_request_until(
        self, request_prepid: str, approval: str, status: str
    ) -> None:
        """
        Approves one request until a desired state.

        Args:
            request_prepid: Request identifier.
            approval: Desired approval for the request.
            status: Desired status for the request.
        """
        request: Union[dict, None] = self._mcm.get(
            object_type="requests", object_id=request_prepid
        )
        if not request:
            raise ValueError(f"Request not found: {request_prepid}")

        is_root: bool = self._mcm.is_root_request(request=request)
        attempts = 10
        for _ in range(attempts):
            request = self._mcm.get(object_type="requests", object_id=request_prepid)
            req_approval = request.get("approval")
            req_status = request.get("status")

            if approval == req_approval and status == req_status:
                return

            approve_result = self._mcm.approve(
                object_type="requests", object_id=request_prepid
            )
            if not approve_result or not approve_result.get("results"):
                if approve_result and is_root:
                    message = approve_result.get("message", "")
                    if "Illegal Approval Step: 5" in message:
                        return

                msg = (
                    "Unable to approve the request to the next status - "
                    f"Request PrepID: {request_prepid} - "
                    f"Current approval/status: {req_approval}/{req_status} - "
                    f"Details: {pformat(approve_result)}"
                )
                self.logger.error(msg)
                raise RuntimeError(msg)

        raise RuntimeError("Unable to get the desired approval status")

    def _perform_chain_request_injection(
        self, chain_request_prepid: str, root_request_processing: RootRequestReset
    ) -> None:
        """
        Injects a chained request based on how its root request was reset.
        This MUST BE executed only after rewinding a chained request to root and reserving it again.

        Args:
            chain_request_prepid: Chained request identifier.
            root_request_processing: Describes how the root request was reset.
        """
        chained_request: Union[dict, None] = self._mcm.get(
            object_type="chained_requests", object_id=chain_request_prepid
        )
        if not chained_request:
            raise ValueError(f"Chain request not found: {chain_request_prepid}")

        if root_request_processing == RootRequestReset.KEEPS_OUTPUT:
            # Just flow the chained request
            flow_result = self._mcm.flow(chained_request_prepid=chain_request_prepid)
            if not flow_result:
                msg = f"Unable to flow the following chained request: {chain_request_prepid}"
                self.logger.error(msg)
                raise RuntimeError(msg)

        elif root_request_processing in (
            RootRequestReset.SOFT_RESET,
            RootRequestReset.FULL_RESET,
        ):
            # Retrieve the newly created requests and
            # make sure their approval/state is approve/approved
            requests_in_chain = chained_request.get("chain", [])
            to_approve = requests_in_chain[1:]
            root_request_in_chain = requests_in_chain[0]
            self.logger.info("Making sure non-root requests are approve/approved")
            for req_prepid in to_approve:
                self._approve_request_until(
                    request_prepid=req_prepid,
                    approval="approve",
                    status="approved",
                )

            # Operate the root request in the chain and
            # make sure its state is submit/submitted.
            # INFO: This takes time ~3 to 5 min.
            self.logger.info("Injecting chained request")
            self._approve_request_until(
                request_prepid=root_request_in_chain,
                approval="submit",
                status="submitted",
            )

        else:
            raise NotImplementedError(
                "There's no way to inject a chained request based on: %s",
                root_request_processing,
            )

    def resubmit_chain_request(
        self,
        root_request_prepid: str,
        datatier: str = "nanoaod",
        tracking_tag: Union[str, None] = None,
    ) -> None:
        """
        Resubmit all the chained requests that reference a particular root request.
        To achieve this, this procedure rewinds all the chained requests to the root step,
        deleting and invalidating all the found requests except for the root one.
        Then, it recreates them by reserving the chain to the desired data tier and finally reinjects them.

        Args:
            root_request_prepid: Root request identifier.
            datatier: Limit data tier for reserving all the chained requests.
            tracking_tag: Includes a tracking tag for the root request
                to monitor its progress after patching this.
        """
        if not self._mcm.is_root_request(request=root_request_prepid):
            raise ValueError(
                f"Provided request ({root_request_prepid}) is not a root request"
            )

        chained_requests: list[dict] = self._mcm.get(
            object_type="chained_requests", query=f"contains={root_request_prepid}"
        )
        chained_requests_prepid: list[str] = [
            ch["prepid"] for ch in chained_requests if ch.get("prepid")
        ]
        self.logger.info(
            "Resubmitting the following chained request related to %s: %s",
            root_request_prepid,
            pformat(chained_requests_prepid),
        )

        # Operate the chained requests so that only the root request remains
        self.logger.info(
            "Rewinding chained requests to root and deleting intermediate requests"
        )
        self._invalidator.invalidate_delete_cascade_requests(
            requests_prepid=[root_request_prepid]
        )

        # Reset the root request and include the tag
        root_processing = self._root_request_to_approve(root_prepid=root_request_prepid)
        if tracking_tag:
            self.logger.info(
                "Including tracking tag (%s) for the root request: %s",
                tracking_tag,
                root_request_prepid,
            )
            self._include_tag(request_prepid=root_request_prepid, tag=tracking_tag)

        # Reserve the chained requests
        for ch_r in chained_requests_prepid:
            self.logger.info(
                "Reserving chained requests (%s) up to data tier: %s", ch_r, datatier
            )
            self._reserve_chain_request(chain_request_prepid=ch_r, datatier=datatier)

        # Reinject the chained requests
        for ch_r in chained_requests_prepid:
            self.logger.info("Reinjecting chained requests: %s", ch_r)
            self._perform_chain_request_injection(
                chain_request_prepid=ch_r, root_request_processing=root_processing
            )
