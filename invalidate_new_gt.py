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


def patch_chain_request(mcm: McM, request_prepid: str, operate: bool = False) -> None:
    """
    Retrieves all the `chain_request` for the given request and applies the path

    Args:
        request_prepid (str): Request PrepID
        operate (bool): Apply the patch or just display the `chain_requests`
    """
    chain_req = mcm.get(
        object_type="chained_requests", query=f"contains={request_prepid}"
    )
    logger.info("Request (%s), chain requests: %s", request_prepid, pretty(chain_req))

    if operate:
        # TODO: Apply the patch.
        pass


if __name__ == "__main__":
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(dev=True, id=McM.OIDC)

    # Some control variables
    campaigns_operate: str = "Run3Summer23DR*"
    global_tag_regex: str = "130X_mcRun3_2023_realistic_v15"
    include: bool = True
    apply_path: bool = False

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
    for campaign_prepid in campaigns:
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

        # 3. Apply the patch.
        for request_prepid in linked_requests:
            logger.info("Patching request (%s)", request_prepid)
            patch_chain_request(
                mcm=mcm, request_prepid=request_prepid, operate=apply_path
            )
