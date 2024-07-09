"""
This examples shows some alternatives to patch several chained
requests when it is required to apply changes on its
the chained campaign.
"""

import random
from datetime import datetime

from rest import McM
from rest.applications.mcm.resubmission import (
    ChainRequestResubmitter,
    InvalidateDeleteRequests,
)

# Instances for the client.
mcm = McM(id=McM.OIDC, dev=True)
chain_resubmitter = ChainRequestResubmitter(mcm=mcm)
invalidator = InvalidateDeleteRequests(mcm=mcm)

# For this example, let's modify the block number for a chained campaign
# and resubmit all the chained request linked to it by using the related
# root request.
chained_campaign_prepid = "chain_Run3Summer22EEFSGenPremix_flowRun3Summer22EEFSMiniAODv4_flowRun3Summer22EEFSNanoAODv12"
chained_campaign = mcm.get(
    object_type="chained_campaigns", object_id=chained_campaign_prepid
)
assert isinstance(chained_campaign, dict), "Chained campaign not found"

block_number = random.randint(1, 6)
print("Setting block number to: ", block_number)
chained_campaign["action_parameters"]["block_number"] = block_number
chained_campaign[
    "notes"
] += f"Updated via McM scripts for example 'chain_request_resubmission.py': {datetime.now().isoformat()}\n"
result = mcm.update(object_type="chained_campaigns", object_data=chained_campaign)
assert result and result.get("results"), "Issue updating chained campaign"

# Pick the chained request linked to this chained campaign
chained_requests = mcm.get(
    object_type="chained_requests",
    query=f"member_of_campaign={chained_campaign_prepid}",
)
assert isinstance(chained_requests, list), "Chained requests not found"
only_chain_prepids: list[str] = [
    ch["prepid"] for ch in chained_requests if ch.get("prepid")
]

# Only retrieve the root request included in these chained requests.
only_root_request: list[str] = list(
    set([ch["chain"][0] for ch in chained_requests if ch.get("chain")])
)
assert only_root_request, "Root request's list is empty"

chain_resubmitter.resubmit_chain_request(
    root_request_prepid=only_root_request[0],
    tracking_tag="McM_Scripts_Example_Resubmission",
)
print("Chained requests resubmitted: ", only_chain_prepids)
