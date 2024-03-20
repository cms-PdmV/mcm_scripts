"""
This script invalidates all the requests
included in one campaign and performs some update
before re-injecting it.

For more details, please see:
https://its.cern.ch/jira/projects/PDMVDEV/issues/PDMVDEV-106
"""

import datetime
import logging
import pprint
import re
import sys
import time
from typing import Dict, List, Optional, Set
from urllib.error import HTTPError
from copy import deepcopy

from rest import McM

# Add path to code that allow easy access to McM
# sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")


# Check if version is >= 3.11, otherwise raise an exception.
if sys.version_info < (3, 11):
    msg = (
        "Unsuported Python version.\n"
        "Please use a version equal of higher than Python 3.11.\n"
        f"Current version: {sys.version}"
    )
    raise RuntimeError(msg)

logger: logging.Logger = logging.getLogger(name=__name__)
formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
fh: logging.Handler = logging.FileHandler(
    f"invalidate_new_gt_execution_{str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M'))}.log"
)
fh.setFormatter(formatter)
logger.addHandler(fh)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def pretty(obj: Dict) -> str:
    """
    Pretty print an object in console
    """
    return pprint.pformat(obj, width=50, compact=True)


def get(mcm: McM, endpoint: str) -> dict:
    """
    Execute a raw GET operation for a resource in McM.
    """
    return mcm._McM__get(endpoint)


def get_invalidations(mcm: McM, requests: list[str]) -> list[dict]:
    """
    Get all the invalidation records related to request given by
    parameter.

    Args:
        mcm (McM): McM client instance.
        requests (list[str]): List of `prepids` used to retrieve its invalidations.

    Returns:
        list[str]: Invalidations related to the requests.
    """
    results: list[dict] = []
    for req in requests:
        inv_req = mcm.get("invalidations", query=f"prepid={req}")
        results += inv_req

    return results


def announce_invalidations(mcm: McM, invalidations: list[dict]) -> dict:
    """
    Announce an invalidation for the given invalidation records

    Args:
        mcm (McM): McM client instance.
        invalidations (list[dict]): List of `invalidation` records to announce.

    Returns:
        list[str]: Invalidations related to the requests.
    """
    # 1. Flatten and just get the `_id` field
    inv_ids: list[str] = [i.get("_id") for i in invalidations if i.get("_id")]
    announce_result = mcm.put(
        object_type="invalidations", object_data=inv_ids, method="announce"
    )

    return announce_result


def reserve_chain_request(mcm: McM, chain_request_data: dict, data_tier: str) -> bool:
    """
    Reserve a `chain` request up to a desired data tier.

    Args:
        mcm (McM): McM instance
        chain_request_data (dict): Chain request data object
        data_tier (str): Datatier to reserve.
    """
    # 1. Pick the `member_of_campaign` attribute and look
    # for the chained campaign. This has the info for the correct
    # campaign modifications (campaigns and flows, customizations)
    member_of_camp = chain_request_data.get("member_of_campaign")
    chr_prepid = chain_request_data.get("prepid")
    target_campaign: str = ""
    if not member_of_camp:
        logger.error("Member of campaign is not set for %s", chr_prepid)
        return False

    chain_campaign = mcm.get(object_type="chained_campaigns", object_id=member_of_camp)
    campaigns: list[list[str]] = chain_campaign.get("campaigns", [])

    def pick_campaign(campaigns_range):
        """
        Scan the campaign range array and pick the
        target campaign.
        """
        for c_range in campaigns_range:
            for c in c_range:
                c_el = c or ""
                if c_el.startswith("Run") and data_tier.lower() in c_el.lower():
                    return c_el

    target_campaign: str | None = pick_campaign(campaigns)
    if not target_campaign:
        logger.error("Unable to find a target campaign for data tier: %s", data_tier)
        return False

    # 2. Reserve the chain
    reserve_endpoint = (
        f"/restapi/chained_requests/flow/{chr_prepid}/reserve/{target_campaign}"
    )
    reserve_result = get(mcm=mcm, endpoint=reserve_endpoint)
    return reserve_result.get("results", False)


def approve_until(
    mcm: McM,
    request_prepid: str,
    approval: str,
    status: str,
    root_request: bool = False,
) -> None:
    """
    Approves one request to the desired stated

    Args:
        mcm (McM): McM instance
        request_prepid (str): Request PrepID to operate
        approval (str): Level of desired approval
        status (str): Desired status
        root_request (bool): Special signal to supress errors for root requests.

    Raises:
        RuntimeError: In case the transition fails.
    """
    attempts = 10
    for _ in range(attempts):
        req_data = mcm.get(object_type="requests", object_id=request_prepid)
        req_approval = req_data.get("approval")
        req_status = req_data.get("status")

        if req_approval == approval and req_status == status:
            return

        approve_result = mcm.approve(object_type="requests", object_id=request_prepid)
        if not approve_result or not approve_result.get("results"):
            if approve_result and root_request:
                message = approve_result.get("message", "")
                if "Illegal Approval Step: 5" in message:
                    return

            msg = (
                "Unable to approve the request to the next status - "
                f"Request PrepID: {request_prepid} - "
                f"Current approval/status: {req_approval}/{req_status}"
            )
            logger.error(msg)
            logger.error("Approve result: %s", approve_result)
            raise RuntimeError(msg)

    raise RuntimeError("Unable to get the desired approval status")


def elapsed_time(
    start_time: datetime.datetime, end_time: datetime.datetime, extra_msg: str = ""
):
    """
    Helper function just to print the elapsed time
    """
    if extra_msg:
        logger.info("%s -> Elapsed time: %s", extra_msg, end_time - start_time)
    else:
        logger.info("Elapsed time: %s", end_time - start_time)

    logger.info("\n")


def campaigns_to_check(
    mcm: McM, campaign_query: str, condition_gt: str, includes: bool
) -> list[str]:
    """
    For a given query, retrieve all the campaigns and filter based on the condition
    GT available in its sequences.

    Args:
        campaign_query (str): Campaign pattern to query based on prepid. For instance: Run3Summer23DR*
        condition_gt (str): AlCa GlobalTag to check, this can be a regex pattern
        includes (bool): Determines whether to retrieve the request that comply
            with the GlobalTag (if True), or exclude them (if False).

    Returns:
        list[str]: List of campaign prepids that comply
    """
    result: list[str] = []
    global_tag_regex = re.compile(pattern=condition_gt)
    campaigns_data: list[dict] = mcm.get(
        object_type="campaigns", query=f"prepid={campaign_query}"
    )
    for campaign in campaigns_data:
        sequences = campaign.get("sequences", [])
        for seq_bundle in sequences:
            seq = seq_bundle["default"]
            condition = seq.get("conditions")
            if not condition:
                raise ValueError(
                    f"Invalid campaign: {campaign.get('prepid')}. Condition GlobalTag is not set"
                )

            # Check the match or its exclusion
            campaign_prepid: str = campaign.get("prepid", "")
            if includes:
                check_regex = global_tag_regex.findall(condition)
                if check_regex:
                    result.append(campaign_prepid)
                    break
            else:
                check_regex = global_tag_regex.findall(condition)
                if not check_regex:
                    result.append(campaign_prepid)
                    break

    return result


def get_campaign_condition(
    mcm: McM, campaign_prepid: str, condition_gt: str, includes: bool
) -> list[str]:
    """
    For a given campaign, retrieve all its request and filter based on the condition
    GT available in its sequences.

    Args:
        campaign_prepid (str): Campaign ID
        condition_gt (str): AlCa GlobalTag to check, this can be a regex pattern
        includes (bool): Determines whether to retrieve the request that comply
            with the GlobalTag (if True), or exclude them (if False).

    Returns:
        list[str]: List of requests prepids that comply
    """
    result: list[str] = []
    global_tag_regex = re.compile(pattern=condition_gt)
    requests_data = mcm.get(
        object_type="requests", query=f"member_of_campaign={campaign_prepid}"
    )
    for req in requests_data:
        req_sequences = req.get("sequences", [])
        for seq in req_sequences:
            condition = seq.get("conditions")
            if not condition:
                raise ValueError(
                    f"Invalid request: {req.get('prepid')}. Condition GlobalTag is not set"
                )

            # Check the match or its exclusion
            request_prepid = req.get("prepid", "")
            if includes:
                check_regex = global_tag_regex.findall(condition)
                if check_regex:
                    result.append(request_prepid)
                    break
            else:
                check_regex = global_tag_regex.findall(condition)
                if not check_regex:
                    result.append(request_prepid)
                    break

    return result


def patch_chain_request(
    mcm: McM, request_prepid: str, tracking_tag: str, operate: bool = False
) -> None:
    """
    Retrieves all the `chain_request` for the given request and applies the patch

    Args:
        mcm (McM): McM instance.
        request_prepid (str): Request PrepID
        tracking_tag (str): Tag to include in the patched `root` requests.
        operate (bool): Apply the patch or just display the `chain_requests`
    """
    chain_req_type = "chained_requests"
    chain_req: list[dict] = mcm.get(
        object_type=chain_req_type, query=f"contains={request_prepid}"
    )
    logger.info(
        "Request (%s), patching chain requests: %s",
        request_prepid,
        pretty([ch.get("prepid") for ch in chain_req]),
    )

    if operate:
        for ch_r in chain_req:
            updated_ch_r = deepcopy(ch_r)
            ch_req_prepid = ch_r.get("prepid")

            # 1. Set the flag to `False` and save
            updated_ch_r["action_parameters"]["flag"] = False
            updated_ch_r = mcm.update(
                object_type=chain_req_type, object_data=updated_ch_r
            )
            logger.info("Disable 'flag' response: %s", updated_ch_r)
            if not updated_ch_r or not updated_ch_r.get("results"):
                msg = f"Error updating chain requests: {ch_req_prepid}"
                logger.error(msg)
                raise RuntimeError(msg)

            # 2. Rewind the chain request to `root`.
            rewind_endpoint = (
                f"/restapi/chained_requests/rewind_to_root/{ch_req_prepid}"
            )
            rewind_response = get(mcm=mcm, endpoint=rewind_endpoint)
            logger.info("Rewind chain request response: %s", rewind_response)
            if not rewind_response or not rewind_response.get("results"):
                msg = f"Unable to rewind chain request to root ({ch_r}) - Details: {rewind_response}"
                logger.error(msg)
                raise RuntimeError(msg)

            # 3. Announce the invalidation.
            ch_req_requests: list[str] = ch_r.get("chain")
            ch_invs = get_invalidations(mcm=mcm, requests=ch_req_requests)
            if ch_invs:
                announce_result = announce_invalidations(mcm=mcm, invalidations=ch_invs)
                logger.info("Invalidation result: %s", announce_result)
                if not announce_result.get("results"):
                    msg = f"Unable to invalidate records for chain request: {ch_req_prepid}"
                    logger.error(msg)
                    logger.error("Invalidation records: %s", ch_invs)
                    raise RuntimeError(msg)

            # 4. Delete the other requests EXCEPT for the `root`
            # The first record in this list is the `root` request
            chain_delete = ch_req_requests[1:]

            # INFO: They must be deleted in order from the deepest
            # data tier to upwards
            chain_delete = reversed(chain_delete)

            for rd in chain_delete:
                mcm.delete(object_type="requests", object_id=rd)

            # 5. Re-enable the flag to `True` and save.
            updated_ch_r = mcm.get(object_type=chain_req_type, object_id=ch_req_prepid)
            updated_ch_r["action_parameters"]["flag"] = True
            updated_ch_r = mcm.update(
                object_type=chain_req_type, object_data=updated_ch_r
            )
            logger.info("Re-enable the flag to `True` response: %s", updated_ch_r)
            if not updated_ch_r or not updated_ch_r.get("results"):
                msg = f"Error updating chain requests: {ch_req_prepid}"
                logger.error(msg)
                raise RuntimeError(msg)

            # 6. Pick the `root` request and set its status to `approve/approved`.
            ch_rr_prepid: str = ch_req_requests[0]
            soft_reset_result = mcm.soft_reset(prepid=ch_rr_prepid)
            logger.info("Soft reset result: %s", soft_reset_result)
            if not soft_reset_result:
                msg = (
                    f"Unable to soft reset the request ({ch_rr_prepid}) "
                    "and set its status to approve/approved"
                )
                logger.error(msg)
                raise RuntimeError(msg)

            # 7. Pick the `root` request and include a tag for tracking and save it.
            ch_rr_data: dict = mcm.get("requests", object_id=ch_rr_prepid)
            ch_rr_data["tags"] += [tracking_tag]
            tag_result = mcm.update("requests", ch_rr_data)
            logger.info("Include `Tag` result: %s", tag_result)
            if not tag_result or not tag_result.get("results"):
                msg = f"Unable to include a tracking tag for the root request: {ch_rr_prepid}"
                logger.error(msg)
                raise RuntimeError(msg)

            # 8. After applying the patch, reserve the chain request again (flow it).
            reserve_result = reserve_chain_request(
                mcm=mcm, chain_request_data=ch_r, data_tier="nanoaod"
            )
            logger.info("Reserve result: %s", reserve_result)
            if not reserve_result:
                msg = (
                    f"Unable to reserve the following chained request: {ch_req_prepid}"
                )
                logger.error(msg)
                raise RuntimeError(msg)

            # 9. Retrieve the new created requests and make sure their state
            # is approve/approved
            updated_ch_r = mcm.get(object_type=chain_req_type, object_id=ch_req_prepid)
            ch_req_requests = updated_ch_r.get("chain")
            to_approve = ch_req_requests[1:]
            ch_rr_prepid: str = ch_req_requests[0]
            logger.info("Making sure non-root request are approve/approved")
            for req_prepid in to_approve:
                approve_until(
                    mcm=mcm,
                    request_prepid=req_prepid,
                    approval="approve",
                    status="approved",
                )

            # 10. Operate the `root` request in the chain and
            # make sure its state is submit/submitted.
            # INFO: This takes time ~3 to 5 min.
            logger.info("Injecting chain request")
            approve_until(
                mcm=mcm,
                request_prepid=ch_rr_prepid,
                approval="submit",
                status="submitted",
                root_request=True,
            )


if __name__ == "__main__":
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(dev=True, id=McM.SSO)

    # Some control variables
    campaigns_operate: str = "Run3Summer23DR*"
    global_tag_regex: str = r"130X_mcRun3_2023_realistic_postBPix"
    include: bool = True
    apply_patch: bool = True
    tracking_tag: str = "PPD_OPS_GT"
    process_campaigns_idx = 1
    process_ch_req_idx = 1

    # 1. Retrieve the campaigns based on the GlobalTag
    logger.info(
        "Scanning campaigns based on query (%s), GlobalTag filter on conditions (%s), include if match (%s)",
        campaigns_operate,
        global_tag_regex,
        include,
    )
    campaigns = campaigns_to_check(
        mcm=mcm,
        campaign_query=campaigns_operate,
        condition_gt=global_tag_regex,
        includes=include,
    )
    logger.info("Campaigns retrieved: %s", pretty(campaigns))

    # 2. Scan all the root requests linked.
    for c_idx, campaign_prepid in enumerate(campaigns):
        logger.info(
            "Scanning requests for campaign (%s), GlobalTag filter on conditions (%s), include if match (%s)",
            campaign_prepid,
            global_tag_regex,
            include,
        )
        linked_requests: list[str] = get_campaign_condition(
            mcm=mcm,
            campaign_prepid=campaign_prepid,
            condition_gt=global_tag_regex,
            includes=include,
        )

        if c_idx >= process_campaigns_idx:
            break

        # 3. Apply the patch.
        for r_idx, request_prepid in enumerate(linked_requests):
            logger.info("Patching request (%s)", request_prepid)
            try:
                patch_chain_request(
                    mcm=mcm,
                    request_prepid=request_prepid,
                    tracking_tag=tracking_tag,
                    operate=apply_patch,
                )

            except Exception as e:
                logger.critical(
                    "Unable to patch the following request: %s - Details: %s",
                    request_prepid,
                    e,
                    stack_info=True,
                )

            finally:
                if r_idx >= process_ch_req_idx:
                    break

    end_time: datetime.datetime = datetime.datetime.now()
    logger.info("Total elapsed time: %s", end_time - start_time)
