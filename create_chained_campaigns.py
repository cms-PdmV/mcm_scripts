import sys
# Add path to code that allow easy access to McM
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

import logging
import pprint
import datetime
import time
import re
from urllib.error import HTTPError
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

# Valid root requests and campaigns
valid_requests_campaigns: str = r'Run3Summer[0-9]{2}(?!FS)'
valid_root_requests_prefix: str = r'^[A-Z0-9]{3}'
valid_root_requests: str = f'{valid_root_requests_prefix}-{valid_requests_campaigns}'
valid_chain_campaigns: str = f'^chain_{valid_requests_campaigns}'

# Regex validators
ROOT_REQUEST_VALIDATOR = re.compile(valid_root_requests)
CHAIN_CAMPAIGNS_VALIDATOR = re.compile(valid_chain_campaigns)

# Checks for some constraints
# Include some regex to check some constraints
exact_miniaod_nanoaod_termination: str = (
    '^chain_Run3Summer22[a-z|A-Z|0-9|_]*'
    '_flowRun3Summer22(EE)?MiniAOD'
    '_flowRun3Summer22(EE)?NanoAOD(v[0-9]{2})?$'
)

# Just the beginning
just_root_section: str = (
    '^chain_Run3Summer22([a-z|A-Z|0-9]*'
    '(?!MiniAOD)[_]){1,2}'
)
DESIRED_CHECK_CAMPAIGN = re.compile(just_root_section)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def pretty(obj: Dict) -> str:
    """
    Pretty print an object in console
    """
    return pprint.pformat(
        obj, 
        width=50,
        compact=True
    )


def elapsed_time(
        start_time: datetime.datetime, 
        end_time: datetime.datetime, 
        extra_msg: str = ''
    ):
    """
    Helper function just to print the elapsed time
    """
    if extra_msg:
        logger.info('%s -> Elapsed time: %s', extra_msg, end_time - start_time)
    else:
        logger.info('Elapsed time: %s', end_time - start_time)
    
    logger.info('\n')


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
    logger.info(pretty(chained_campaign))

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
        chains_to_change: List[Dict] = mcm.get('chained_campaigns', query=query_chain_campaign)
        # Filter the chain campaigns to only process valid patterns
        chains_to_change = [ch for ch in chains_to_change if CHAIN_CAMPAIGNS_VALIDATOR.match(ch.get('prepid', ''))]
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
        discard_chain_campaign: List[str],
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
        discard_chain_campaign (list[str]): List of chain campaigns to avoid creating a ticket 
            because they already exist and there are some requests already injected in production.
        create_tickets (bool): Create the tickets in McM
    
    Returns:
        List[dict]: List of all MccM ticket to include in McM or the ticket data after
            being created in to McM.
    """

    discard_chain_campaign_set: Set[str] = set(discard_chain_campaign)

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
        Verifies and checks that the new `chain_campaign` already exists before
        including it in the ticket. Returns a blank string if the `chain_campaign`
        is not related with the desired MiniAOD and NanoAOD campaigns.
        """
        related_to_ee: bool = belongs_to_ee.match(chain_campaign_group)
        expected_ch_c: str = ''
        if related_to_ee:
            expected_ch_c = f'{chain_campaign_group}_flowRun3Summer22EEMiniAODv4_flowRun3Summer22EENanoAODv12'
        else:
            expected_ch_c = f'{chain_campaign_group}_flowRun3Summer22MiniAODv4_flowRun3Summer22NanoAODv12'

        is_already_created: bool = expected_ch_c in chain_campaigns
        if not is_already_created:
            logger.warning(
                (
                    'Chain campaign: %s does not exist. It means is is not related with the desired MiniAOD and NanoAOD campaigns.\n'
                    'Skip it.\n'
                    'Chain campaign constructed based on: %s group key'
                ), 
                expected_ch_c,
                chain_campaign_group
            )
            return ''
        
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
        
        if not new_chained_campaign:
            # Avoid creating a ticket for this
            logger.warning(
                (
                    'Skipping the following root requests due to are not related '
                    'with desired MiniAOD and NanoAOD campaigns: \n'
                    '%s \n'
                    'Total: %s'
                ),
                pretty(root_requests),
                f'{len(root_requests):,}'
            )
            continue

        if new_chained_campaign in discard_chain_campaign_set:
            logger.warning(
                (
                    'Skipping creating a ticket for the chain_campaign: %s. '
                    'There are tickets and requests injected in production. \n'
                    'Root requests skipped: %s \n'
                    'Total: %s'
                ),
                new_chained_campaign,
                pretty(root_requests),
                f'{len(root_requests):,}'
            )
            continue

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
    new_ticket_data: List[dict] = []

    if create_tickets:
        # Create the ticket
        for idx, ticket in enumerate(tickets):
            logger.debug(pretty(ticket))
            logger.info('%d of %d - Creating new ticket', idx, total_tickets)
            start_time_ticket: datetime.datetime = datetime.datetime.now()
            res = mcm.put('mccms', ticket)
            ticket_prepid = res.get('prepid', None)
            logger.info('Transaction result: %s', res)

            # Updating total events for the ticket
            if not ticket_prepid:
                logger.error('There was an error trying to create this ticket, its information was: ')
                logger.error(pretty(ticket))
                continue
                
            logger.info('Updating events ...')
            _ = mcm._McM__get('restapi/mccms/update_total_events/%s' % (ticket_prepid))

            # Retrieve ticket data
            logger.info('Retriving ticket information ...')
            ticket_info = mcm._McM__get('restapi/mccms/get/%s' % (ticket_prepid))
            new_ticket_data.append(ticket_info)
            
            end_time_ticket: datetime.datetime = datetime.datetime.now()
            elapsed_time(start_time=start_time_ticket, end_time=end_time_ticket)
        
    return new_ticket_data if create_tickets else tickets


def reserve_tickets(mcm_sdk: McM, tickets_prepid: List[str]) -> List[Dict]:
    """
    Reserve the desired tickets to generate the chains and start
    the automatic submission to computing.

    Args:
        mcm_sdk (McM): McM SDK to perform API operations
        tickets_prepid (List[str]): List of ticket prepid's to reserve the
            desired tickets.

    Returns:
        List[dict]: Data for all the tickets that were operated.
    """
    # Make sure the list is clean and there are only strings
    tickets_prepid = [tk for tk in tickets_prepid if tk and isinstance(tk, str)]
    total_tickets: int = len(tickets_prepid)
    submission_result: List[Dict] = []

    
    for idx, ticket_prepid in enumerate(tickets_prepid):
        logger.info('%d of %d - Operating ticket: %s', idx, total_tickets, ticket_prepid)
        start_time_ticket: datetime.datetime = datetime.datetime.now()
        try:
            # Reserve the ticket
            logger.info('Reserving ticket ...')
            _ = mcm_sdk._McM__get('restapi/mccms/generate/%s?reserve=true&skip_existing=true' % (ticket_prepid))

            # Updating total events for the ticket
            logger.info('Updating events ...')
            _ = mcm_sdk._McM__get('restapi/mccms/update_total_events/%s' % (ticket_prepid))

            # Retrieve ticket information
            logger.info('Retriving ticket information ...')
            ticket_info = mcm_sdk._McM__get('restapi/mccms/get/%s' % (ticket_prepid))
            logger.debug(pretty(ticket_info))
            submission_result.append(ticket_info)
        except HTTPError as http_error:
            logger.error(
                'Server error processing the current ticket - Index: %s',
                idx
            )
            logger.error(http_error, exc_info=True)
                
        finally:
            end_time_ticket: datetime.datetime = datetime.datetime.now()
            elapsed_time(
                start_time=start_time_ticket, 
                end_time=end_time_ticket,
                extra_msg='Ticket processing time'
            )
            time.sleep(2) # Avoid killing McM application

    return submission_result


def summary_tickets(created_tickets: List[Dict]) -> int:
    """
    Create a little summary related to the ticket creation.
    Display the number of total events linked to a ticket, its
    generated_chains and the total number of events related to
    this whole process.

    Args:
        created_tickets (List[dict]): Ticket's data for all created
            tickets.

    Returns:
        int: Total number of events related to all created tickets.
    """
    logger.info('....................................')
    logger.info('Final summary')
    logger.info('\n')

    total_events: int = 0
    total_created_tickets: int = len(created_tickets)

    for idx, ticket in enumerate(created_tickets):
        ticket_data = ticket.get('results', {})
        ticket_prepid: str = ticket_data.get('prepid', '<InvalidData>')
        ticket_total_events: int = int(ticket_data.get('total_events', 0))
        generated_chains: Dict = ticket_data.get('generated_chains', {})
        logger.info('Displaying summary for %s ticket of %s', idx, total_created_tickets)
        logger.info(
            (
                'Ticket: %s \n'
                'Total events for the ticket: %s \n'
                'Generated chains: \n'
                '%s'
            ),
            ticket_prepid,
            f'{ticket_total_events:,}',
            pretty(generated_chains)
        )
        total_events += ticket_total_events
    
    logger.info('....................................')
    logger.info(
        'Total number of events: %s - Scientific notation: %s',
        f'{total_events:,}',
        f'{total_events:E}',
    )
    return total_events


def inspect_ticket(mcm_sdk: McM, tickets: List[str]) -> int:
    """
    For the new created tickets, inspect their `root_requests`
    and display its total number of events. Then, compute the total
    number of events for the ticket based on its root requests and finally
    sum up all the events for all the tickets.

    Args:
        mcm_sdk (McM): McM SDK to perform queries
        tickets (List[str]): List of ticket prepids to inspect.

    Returns:
        int: Total number of events for all the tickets
            desired to be inspected.
    """
    total_events_inspection: int = 0
    total_tickets: int = len(tickets)
    for idx, ticket_prepid in enumerate(tickets):
        total_events_from_root_req: int = 0 
        logger.info('\n %s of %s -> Checking ticket: %s \n', idx, total_tickets, ticket_prepid)
        ticket = mcm_sdk._McM__get('restapi/mccms/get/%s' % (ticket_prepid))
        
        if not ticket:
            logger.warning('Could not retrieve data for ticket: %s', ticket_prepid)
            continue
        
        ticket_root_reqs: List[str] = ticket.get('results', {}).get('requests', [])
        if not ticket_root_reqs:
            logger.warning('Ticket %s does not have root requests attached', ticket_prepid)
            continue

        total_root_requests: int = len(ticket_root_reqs)
        for idx, ticket_root_req_prepid in enumerate(ticket_root_reqs):
            root_req: dict = mcm_sdk._McM__get('restapi/requests/get/%s' % (ticket_root_req_prepid))
            if not root_req:
                logger.warning('Could not retrieve info for root request: %s', ticket_root_req_prepid)
                continue
            
            root_req_events: int = root_req.get('results', {}).get('total_events', 0)
            logger.debug('%s of %s -> Root request: %s - Events: %s', idx, total_root_requests, ticket_root_req_prepid, root_req_events)
            total_events_from_root_req += root_req_events
        
        logger.info('Total events for ticket inspected: %s - Events: %s', ticket_prepid, total_events_from_root_req)
        total_events_inspection += total_events_from_root_req
    
    logger.info(
        '\n Total number of events for all the inspection: %s - Scientific notation: %s \n',
        f'{total_events_inspection:,}',
        f'{total_events_inspection:E}',
    )
    return total_events_inspection


def inspect_chain_request_pattern(mcm_sdk: McM, tickets: List[str]) -> bool:
    """
    Scan all the root requests per ticket. For each root request,
    scan the `chain_requests` that contain this request and verify that
    the `chain_campaign` linked to this chain_requests is related with the
    desired campaign.

    Args:
        mcm_sdk (McM): McM SDK to perform queries
        tickets (List[str]): List of ticket prepids to inspect.

    Returns:
        bool: True if all root_requests comply with the desired pattern 
            False, otherwise.
    """
    all_complies: bool = True
    total_tickets: int = len(tickets)
    for idx, ticket_prepid in enumerate(tickets):
        logger.info('\n %s of %s -> Checking ticket: %s \n', idx, total_tickets, ticket_prepid)
        ticket = mcm_sdk._McM__get('restapi/mccms/get/%s' % (ticket_prepid))

        if not ticket:
            logger.error('Could not retrieve data for ticket: %s', ticket_prepid)
            all_complies = False
            break
        ticket = ticket.get('results', {})

        # Our created tickets just have one chain
        ticket_chain: str = ticket.get('chains', [])
        if not len(ticket_chain) == 1:
            logger.error('Ticket: %s should have only one chain_campaign', )
            all_complies = False
            break
        ticket_chain = ticket_chain[0]
        ticket_chain_regex = DESIRED_CHECK_CAMPAIGN.match(ticket_chain)
        ticket_chain_match: str = ticket_chain_regex[0] if ticket_chain_regex else ''
        if not ticket_chain_match:
            logger.critical(
                'Ticket: %s - Chain campaign: <%s> does not match the desired pattern', 
                ticket_prepid,
                ticket_chain_match
            )
            all_complies = False
            break

        # Inspect root requests
        ticket_root_reqs: List[str] = ticket.get('requests', [])
        if not ticket_root_reqs:
            logger.error('Ticket %s does not have root requests attached', ticket_prepid)
            all_complies = False
            break

        total_root_requests: int = len(ticket_root_reqs)
        for idx, ticket_root_req_prepid in enumerate(ticket_root_reqs):
            logger.debug('%s of %s -> Root request: %s', idx, total_root_requests, ticket_root_req_prepid)
            root_req: dict = mcm_sdk._McM__get('restapi/requests/get/%s' % (ticket_root_req_prepid))
            if not root_req:
                logger.error('Could not retrieve info for root request: %s', ticket_root_req_prepid)
                all_complies = False
                continue
            root_req = root_req.get('results', {})
            
            # member_of_campaign
            chain_requests_root_req: dict = mcm.get('chained_requests', query=f'contains={ticket_root_req_prepid}')
            if not len(chain_requests_root_req) == 1:
                logger.warning(
                    '[BEWARE] Root request: %s has more than one chain_request to check',
                    ticket_root_req_prepid
                )
                at_least_one_complies: bool = False
                for chain_req in chain_requests_root_req:
                    member_of_campaign: str = chain_req.get('member_of_campaign', '')
                    complies_pattern_regex = DESIRED_CHECK_CAMPAIGN.match(member_of_campaign)
                    complies_pattern_match: str = complies_pattern_regex[0] if complies_pattern_regex else '<NotFound>'

                    if complies_pattern_match == ticket_chain_match:
                        at_least_one_complies = True
                        logger.debug(
                            (
                                'Chain request: %s \n'
                                'Included in root request: %s \n'
                                'Analyzed chain campaign: %s \n'
                                'Complies with the pattern'
                            ),
                            chain_req.get('prepid', '<ChainRequestNotAvailable>'),
                            ticket_root_req_prepid,
                            member_of_campaign_check
                        )
                        break

                if not at_least_one_complies:
                    logger.error(
                        (
                            'Root request: %s \n'
                            'Does not have any `chain_request` that complies with the pattern'
                        ),
                        chain_req.get('prepid', '<ChainRequestNotAvailable>'),
                        ticket_root_req_prepid,
                        member_of_campaign_check
                    )
                    all_complies = False
            else:
                member_of_campaign_check = chain_requests_root_req[0].get('member_of_campaign', '')
                complies_pattern_regex = DESIRED_CHECK_CAMPAIGN.match(member_of_campaign_check)
                complies_pattern_match: str = complies_pattern_regex[0] if complies_pattern_regex else '<NotFound>'

                if not complies_pattern_match == ticket_chain_match:
                    logger.error(
                        (
                            'Chain request: %s \n'
                            'Included in root request: %s \n'
                            'Analyzed chain campaign: %s \n'
                            'Does not comply with the pattern'
                        ),
                        chain_req.get('prepid', '<ChainRequestNotAvailable>'),
                        ticket_root_req_prepid,
                        member_of_campaign_check
                    )
                    all_complies = False

    return all_complies


if __name__ == '__main__':
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(dev=True)
    
    # Create all the elements
    CREATE: bool = True

    # Reserve the tickets
    RESERVE: bool = False

    # Skip this chained champaigns for creating a ticket
    skip_ch_campaigns_ticket: List[str] = []

    # Step 1: Create new `chain_campaigns` based on some that already
    # exists, changing the last campaigns and flow related to the data tiers
    # MiniAOD and NanoAOD
    st_step1: datetime.datetime = datetime.datetime.now()

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
        create=CREATE
    )
    created_ch_campaigns: List[str] = retrieve_chain_campaign_prepid(
        mcm_ch_campaign_result=created_chain_campaigns,
        skip_already_exist=False
    )
    created_ch_campaigns = list(set(created_ch_campaigns))
    logger.info('New chained campaigns to use: %d', len(created_ch_campaigns))
    et_step1: datetime.datetime = datetime.datetime.now()
    elapsed_time(start_time=st_step1, end_time=et_step1, extra_msg='Step 1')


    # Step 2: Retrieve the list of all root requests to link with the new chain_campaign
    st_step2: datetime.datetime = datetime.datetime.now()
    root_requests_query: str = 'prepid=*Run3Summer22*GS*'
    root_requests: List[Dict] = mcm.get('requests', query=root_requests_query)
    # Filter the root requests
    root_requests = [root_req for root_req in root_requests if ROOT_REQUEST_VALIDATOR.match(root_req.get('prepid', ''))]
    logger.info('Matching new chain_campaigns for %d root requests', len(root_requests))
    et_step2: datetime.datetime = datetime.datetime.now()
    elapsed_time(start_time=st_step2, end_time=et_step2, extra_msg='Step 2')


    # Step 3: Create a MccM tickets without reserve them
    st_step3: datetime.datetime = datetime.datetime.now()
    ticket_result: List[Dict] = create_mccm_tickets(
        mcm=mcm,
        root_requests=root_requests,
        chain_campaigns=created_ch_campaigns,
        discard_chain_campaign=skip_ch_campaigns_ticket,
        create_tickets=CREATE
    )
    et_step3: datetime.datetime = datetime.datetime.now()
    elapsed_time(start_time=st_step3, end_time=et_step3, extra_msg='Step 3')


    if CREATE:
        creation_successful: bool = True
        created_ticket_prepids: List[str] = [
            ticket.get('results', {}).get('prepid', '')
            for ticket in ticket_result
            if ticket
        ]
        created_ticket_prepids = [tk for tk in created_ticket_prepids if tk]
        if not len(created_ticket_prepids) == len(ticket_result):
            logger.warning(
                (
                    'There is a mismatch between ticket prepids and created tickets. '
                    'Check that `create_mccm_tickets(...)` does not include `None` values'
                )
            )
            creation_successful = False

        if creation_successful:
            proceed_to_reserve: bool = True

            # Step 4: Retrieve the total number of events
            # related to the tickets and make sure it is the same as
            # the sum of total number of events.
            st_step4: datetime.datetime = datetime.datetime.now()
            total_events_from_tickets: int = summary_tickets(created_tickets=ticket_result)
            total_events_from_root_req: int = inspect_ticket(mcm_sdk=mcm, tickets=created_ticket_prepids)

            if not total_events_from_tickets == total_events_from_root_req:
                logger.warning(
                    (
                        'There is a mismatch between the total events taken '
                        'from the `ticket` and the sum from `root_requests`. \n'
                        'Total events from all tickets: %s \n'
                        'Total events from the sum of all root requests: %s \n'
                    ),
                    f'{total_events_from_tickets:,}',
                    f'{total_events_from_root_req:,}',
                )
                proceed_to_reserve = False
            et_step4: datetime.datetime = datetime.datetime.now()
            elapsed_time(start_time=st_step4, end_time=et_step4, extra_msg='Step 4')


            # Step 5: Check that all root request and its `chain_request` have
            # at least one `chain_request` related to the new `chain_campaign`
            # linked to the new ticket.
            st_step5: datetime.datetime = datetime.datetime.now()
            ticket_constructed_well: bool = inspect_chain_request_pattern(
                mcm_sdk=mcm,
                tickets=created_ticket_prepids
            )
            proceed_to_reserve = proceed_to_reserve and ticket_constructed_well
            et_step5: datetime.datetime = datetime.datetime.now()
            elapsed_time(start_time=st_step5, end_time=et_step5, extra_msg='Step 5')

            if proceed_to_reserve and RESERVE:
                # Step 6: Reserve all the tickets and start the automatic submission
                st_step6: datetime.datetime = datetime.datetime.now()
                ticket_data_after_reserve = reserve_tickets(
                    mcm_sdk=mcm, 
                    tickets_prepid=created_ticket_prepids
                )
                et_step6: datetime.datetime = datetime.datetime.now()
                elapsed_time(start_time=st_step6, end_time=et_step6, extra_msg='Step 6')

                # Step 7: Print a final summary
                _ = summary_tickets(created_tickets=ticket_data_after_reserve)

    end_time: datetime.datetime = datetime.datetime.now()
    elapsed_time(
        start_time=start_time, 
        end_time=end_time, 
        extra_msg='Total required time to process this script'
    )