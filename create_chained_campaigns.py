import sys
# Add path to code that allow easy access to McM
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

import logging
import pprint
import datetime
from typing import List, Dict
from rest import McM


# Removal order for deleting data tiers for the request.
# Scan the request in the following order and remove them
# from the bottom of the campaign list in the chain campaign
REMOVAL_ORDER: List[str] = [
    'NanoAOD',
    'MiniAOD'
]

logger: logging.Logger = logging.getLogger(name=__name__)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
fh: logging.Handler = logging.FileHandler('execution.log')
fh.setFormatter(formatter)
logger.addHandler(fh)
# If you want more messages, enable the DEBUG mode
# logger.setLevel(level=logging.DEBUG)

def create_chained_campaign(
        mcm: McM,
        chained_campaign_prepid: str, 
        clean_chain_up_to: str,
        new_chain_section: List[List[str]],
        create: bool = False
    ):
    """
    Creates a new chained campaing into McM based on another that
    already exists. Also, removes some campaigns linked into the chain
    campaign related to some specific data tiers.

    Args:
        mcm (McM): McM SDK to perform requests to this application
        chained_campaign_prepid (str): Chain campaign to scan and modify
            to use as a blueprint for the new one.
        clean_chain_up_to (str): Scan the chain campaigns and delete the
            campaigns linked to a data tier. For example:
                - NanoAOD will delete from the end all campaign linked with this data tier
                - MiniAOD will delete from the end all 
                  the campaigns related to MiniAOD and NanoAOD.
        new_chain_section (List[List[str]]): New list of campaigns and flows to add in replacement
            of the campaigns cleaned before.
        create (bool): If True, this will create the chain_campaign in McM. Otherwise, it will
            print the request content related to this creation.

    Returns:
        None: This function does not return anything.
    """
    chained_campaign: dict = mcm.get('chained_campaigns', chained_campaign_prepid)
    logger.debug('%s chain looks like this:', chained_campaign_prepid)
    for campaign, flow in chained_campaign['campaigns']:
        logger.debug('%s -> %s', flow if flow else '...', campaign)

    remove_up_to_idx: int = REMOVAL_ORDER.index(clean_chain_up_to)
    for remove_datatier in REMOVAL_ORDER[:remove_up_to_idx + 1]:
        request_to_check: str = chained_campaign['campaigns'][-1][0] 
        if remove_datatier in request_to_check:
            logger.warning(
                'Removing %s from current chain campaign from the last position - Campaign to remove: %s',
                remove_datatier,
                request_to_check
            )
            chained_campaign['campaigns'] = chained_campaign['campaigns'][:-1]

    # Include the new section for the chain_campaign
    logger.debug('Including the following chain section: %s', new_chain_section)
    chained_campaign['campaigns'] += new_chain_section

    # Set the attribute `do_not_check_cmssw_versions` to `True`
    chained_campaign['do_not_check_cmssw_versions'] = True
    
    for campaign, flow in chained_campaign['campaigns']:
        logger.info(
            'Campaigns and flows included in this chained campaign - Flow: %s -> Campaign: %s',
            flow if flow else '...',
            campaign
        )

    # Delete some fields before creating the element
    for el in ['_rev', '_id', 'prepid', 'alias']:
        _ = chained_campaign.pop(el)

    if create:
        response = mcm.put('chained_campaigns', chained_campaign)
        logger.info(response)
    else:
        logger.info('Chained campaign to be created')
        logger.info(
            pprint.pformat(
                chained_campaign, 
                width=50,
                compact=True
            )
        )
        

def create_chain_campaings(
        mcm: McM, 
        chain_campaign_queries: Dict[str, List[List[str]]],
        clean_chain_up_to: str, 
        create: bool = False
    ):
    """
    Creates a new chain campaign removing all the campaigns related to a
    data tier and replacing them with the content given.

    Args:
        mcm (McM): McM SDK
        chain_campaign_queries (dict[str, list[list[str]]]): A query that scans
            all the chain campaigns that contains an specific campaign of interest and the 
            campaigns and flows to replace to the bottom of the chain.
        clean_chain_up_to (str): Scan the chain campaigns and delete the
            campaigns linked to a data tier. For example:
                - NanoAOD will delete from the end all campaign linked with this data tier
                - MiniAOD will delete from the end all 
                  the campaigns related to MiniAOD and NanoAOD.
        create (bool): If True, this will create the chain_campaign in McM. Otherwise, it will
            print the request content related to this creation.
        
    Returns:
        None: This function does not return anything.
    """
    for query_chain_campaign, replacement in chain_campaign_queries.items():
        chains_to_change: dict = mcm.get('chained_campaigns', query=query_chain_campaign)
        total_chains_to_change: int = len(chains_to_change)
        logger.info('Query: %s has returned %d chain request to check', query_chain_campaign, total_chains_to_change)
        for idx_campaign, chain_to_change in enumerate(chains_to_change):
            print('\n')
            logger.info(
                '%s of %s -> Checking McM Chain Campaign: %s', 
                idx_campaign, total_chains_to_change, chain_to_change['prepid']
            )
            create_chained_campaign(
                mcm=mcm, 
                chained_campaign_prepid=chain_to_change['prepid'], 
                clean_chain_up_to=clean_chain_up_to,
                new_chain_section=replacement,
                create=create
            )


if __name__ == '__main__':
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(dev=True)

    # Clean up to MiniAOD
    clean_chain_up_to: str = REMOVAL_ORDER[1]
    chain_campaigns: Dict[str, List[List[str]]] = {
        'contains=Run3Summer22MiniAODv3': [
            ['Run3Summer22MiniAODv4', 'flowRun3Summer22MiniAODv4'],
            ['Run3Summer22NanoAODv12', 'flowRun3Summer22NanoAODv12']
        ],
        'contains=Run3Summer22EEMiniAODv3': [
            ['Run3Summer22EEMiniAODv4', 'flowRun3Summer22EEMiniAODv4'],
            ['Run3Summer22EENanoAODv12', 'flowRun3Summer22EENanoAODv12']
        ]
    }
    create_chain_campaings(
        mcm=mcm, 
        chain_campaign_queries=chain_campaigns,
        clean_chain_up_to=clean_chain_up_to
    )
    end_time: datetime.datetime = datetime.datetime.now()
    logger.info('Elapsed time: %s', end_time - start_time)