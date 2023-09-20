import sys
# Add path to code that allow easy access to McM
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

import logging
import pprint
import datetime
import time
import re
from typing import List, Dict, Optional, Set
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

# Include some regex to check some constraints
belongs_to_ee = re.compile(r'^chain_Run3Summer22EE')


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def create_chained_campaign(
        mcm: McM,
        chained_campaign_prepid: str, 
        clean_chain_up_to: str,
        new_chain_section: List[List[str]],
        create: bool = False
    ) -> Optional[Dict]:
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
        dict: This returns the McM response to the transaction. This could include the
            new chain_campaign prepid or an error message related to the chain_campaign
            creation.
        None: If creation mode is not enabled.
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

    logger.info('Chained campaign to be created')
    logger.info(
        pprint.pformat(
            chained_campaign, 
            width=50,
            compact=True
        )
    )

    if create:
        logger.info('Creating ....')
        response = mcm.put('chained_campaigns', chained_campaign)
        logger.info(response)
        return response
    return None        


def create_chain_campaings(
        mcm: McM, 
        chain_campaign_queries: Dict[str, List[List[str]]],
        clean_chain_up_to: str, 
        create: bool = False
    ) -> List[Optional[Dict]]:
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
        list[dict[str, str | bool] | None]: List of creation results.
    """
    results: List[Dict] = []
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
            result = create_chained_campaign(
                mcm=mcm, 
                chained_campaign_prepid=chain_to_change['prepid'], 
                clean_chain_up_to=clean_chain_up_to,
                new_chain_section=replacement,
                create=create
            )
            results.append(result)
    
    return results


def retrieve_chain_campaign_prepid(
        mcm_ch_campaign_result: List[Dict], 
        skip_already_exist: bool
    ) -> List[str]:
    """
    Parses the `chain_campaign` prepid from the result message
    used given in the McM response.

    Args:
        mcm_ch_campaign_result (list[dict]): List of all creation transactions
        skip_already_exist (bool): If True, this will skip checking `chain_campaigns`
            which already existed.

    Returns:
        list[str]: Chain campaign prepids.
    """
    ch_campaings: List[str] = []
    for transaction in mcm_ch_campaign_result:
        created: bool = transaction.get('results')
        if created:
            ch_campaings.append(transaction.get('prepid', ''))
            continue
        if skip_already_exist:
            continue
        else:
            error_message: str = transaction.get('message', '')
            if error_message.endswith('already exists'):
                begin_ch_name: int = error_message.index('"') + 1
                end_ch_name: int = error_message.index('"', begin_ch_name + 1)
                ch_campaings.append(error_message[begin_ch_name:end_ch_name])
    return ch_campaings


def create_mccm_tickets(
        mcm: McM,
        root_requests: List[Dict], 
        chain_campaigns: List[str],
        create_tickets: bool = False
    ) -> List[Dict]:
    """
    Creates an MccM ticket to create requests related to the new `chain_campaign`
    and root requests to inject them to start the MonteCarlo simulation in
    computing

    Args:
        root_requests (list[dict]): Root request data object
        chain_campaigns (list[str]): List of all created `chain_campaing` to include in the
            new ticket.
        create_tickets (bool): Create the tickets in McM
    
    Returns:
        List[dict]: List of all MccM ticket to include in McM or the result of submitting
            its creation to McM.
    """
    def __retrieve_chain_campaign_id__(chain_request: str) -> str:
        """
        Retrieve the `chain_campaign` prepid for grouping several root request on it
        by using the `chain_request` attribute. Skip flow names related with MiniAOD
        and NanoAOD data tiers.

        For instance: 
            - B2G-chain_Run3Summer22EEwmLHEGS_flowRun3Summer22EEDRPremix_flowRun3Summer22EEMiniAOD_flowRun3Summer22EENanoAODv11-00001
        Will return
            - chain_Run3Summer22EEwmLHEGS_flowRun3Summer22EEDRPremix

        Args:
            str: Chain campaing identifier to group root requests.
        """
        try:
            chain_request_components: str = chain_request.strip().split('-')
            chain_campaign: str = chain_request_components[1]
            chain_campaign_components: List[str] = []
            for ch_c in chain_campaign.strip().split('_'):
                if 'MiniAOD' in ch_c:
                    continue
                elif 'NanoAOD' in ch_c:
                    continue
                else:
                    chain_campaign_components.append(ch_c)
            return '_'.join(chain_campaign_components)
        except IndexError:
            return ''


    def __expected_chain_campaign__(
            chain_campaign_group: str, 
            chain_campaigns: Set[str]
        ) -> str:
        """
        Verifies and checks that the new chain_campaign already exists before
        including it in the ticket.
        """
        related_to_ee: bool = belongs_to_ee.match(chain_campaign_group)
        expected_ch_c: str = ''
        if related_to_ee:
            expected_ch_c = f'{chain_campaign_group}_flowRun3Summer22EEMiniAODv4_flowRun3Summer22EENanoAODv12'
        else:
            expected_ch_c = f'{chain_campaign_group}_flowRun3Summer22MiniAODv4_flowRun3Summer22NanoAODv12'

        is_already_created: bool = expected_ch_c in chain_campaigns
        if not is_already_created:
            logger.error('Chain campaign: %s should already exist', expected_ch_c)
            return f'{chain_campaign_group}_<NotExists>'
        return expected_ch_c
        

    # Group all root request and `chain_campaign` by using the `chain_request`
    # attribute. Filter on root request in statuses `submitted` and `done`
    logger.info('Grouping all root request with its chain_campaign')
    chain_campaings_root_requests: Dict[List[str]] = {}
    for root_req in root_requests:
        if root_req.get('status') not in ('done', 'submitted'):
            # Not desired status
            continue
        
        # Retrieve chain_campaign and group
        # INFO: For root request use only the first member of chain
        member_of_chain = root_req.get('member_of_chain', '')
        if isinstance(member_of_chain, list):
            member_of_chain = member_of_chain[0]
        
        root_ch_campaign: str = __retrieve_chain_campaign_id__(chain_request=member_of_chain)
        current_group: List[str] = chain_campaings_root_requests.get(root_ch_campaign, [])
        current_group += [root_req.get('prepid')]
        chain_campaings_root_requests[root_ch_campaign] = current_group

    # There is a limit and McM can process only a ticket of 50 root requests
    tickets: List[Dict] = []
    chain_campaigns_set: Set[str] = set(chain_campaigns)
    logger.info('Creating tickets object ...')
    for chained_campaign, root_requests in chain_campaings_root_requests.items():
        new_chained_campaign: str = __expected_chain_campaign__(
            chain_campaign_group=chained_campaign, 
            chain_campaigns=chain_campaigns_set
        )
        for root_request_chunk in chunks(root_requests, 50):
            mccm_ticket: Dict = {
                'prepid': 'PPD',
                'pwg': 'PPD',
                'requests': root_request_chunk,
                'repetitions': 1, # Not sure about this attribute, please give more details
                'notes': 'Ticket related to [PDMVMCPROD-98]. Available at: https://its.cern.ch/jira/browse/PDMVMCPROD-98',
                'chains': [new_chained_campaign],
                'block': 1
            }
            tickets.append(mccm_ticket)

    total_tickets: int = len(tickets)
    submission_result: List[Dict] = []

    for idx, ticket in enumerate(tickets):
        logger.info('%d of %d - New ticket', idx, total_tickets)
        logger.info(
            pprint.pformat(
                ticket, 
                width=50,
                compact=True
            )
        )

        if create_tickets:
            logger.info('Creating ticket ....')
            res = mcm.put('mccms', ticket)
            logger.info('Transaction result: %s', res)
            submission_result.append(res)
            time.sleep(1) # Avoid killing McM application

    return submission_result if create_tickets else tickets


if __name__ == '__main__':
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(dev=True)

    # Step 1: Create new `chain_campaigns` based on some that already
    # exists, changing the last campaigns and flow related to the data tiers
    # MiniAOD and NanoAOD

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
    created_chain_campaigns: List[Dict] = create_chain_campaings(
        mcm=mcm, 
        chain_campaign_queries=chain_campaigns,
        clean_chain_up_to=clean_chain_up_to,
        create=True
    )
    created_ch_campaigns: List[str] = retrieve_chain_campaign_prepid(
        mcm_ch_campaign_result=created_chain_campaigns,
        skip_already_exist=False
    )
    created_ch_campaigns = list(set(created_ch_campaigns))
    logger.info('New chained campaigns to use: %d', len(created_ch_campaigns))

    # Step 2: Retrieve the list of all root requests to link with the new chain_campaign
    root_requests_query: str = 'prepid=*Run3Summer22*GS*'
    root_requests: List[Dict] = mcm.get('requests', query=root_requests_query)
    logger.info('Matching new chain_campaigns for %d root requests', len(root_requests))

    # Step 3: Create a McM tickets 
    _ = create_mccm_tickets(
        mcm=mcm,
        root_requests=root_requests,
        chain_campaigns=created_ch_campaigns,
        create_tickets=True
    )
    end_time: datetime.datetime = datetime.datetime.now()
    logger.info('Elapsed time: %s', end_time - start_time)