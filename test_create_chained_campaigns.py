import sys
import logging
import pprint
import datetime
import time
import re
from urllib.error import HTTPError
from typing import List, Dict, Optional, Set

# Add path to code that allow easy access to McM
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM-QA/')
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
fh: logging.Handler = logging.FileHandler('check_test_1.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

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
            logger.info('%s of %s -> Root request: %s - Events: %s', idx, total_root_requests, ticket_root_req_prepid, root_req_events)
            total_events_from_root_req += root_req_events
        
        logger.info('Total events for ticket: %s - Events: %s', ticket_prepid, total_events_from_root_req)
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
            logger.warning('Could not retrieve data for ticket: %s', ticket_prepid)
            continue
        ticket = ticket.get('results', {})

        # Our created tickets just have one chain
        ticket_chain: str = ticket.get('chains', [])
        if not len(ticket_chain) == 1:
            logger.critical('Ticket: %s should have only one chain_campaign', )
            continue
        ticket_chain = ticket_chain[0]
        ticket_chain_regex = DESIRED_CHECK_CAMPAIGN.match(ticket_chain)
        ticket_chain_match: str = ticket_chain_regex[0] if ticket_chain_regex else ''
        if not ticket_chain_match:
            logger.critical(
                'Ticket: %s - Chain campaign: <%s> does not match the desired pattern', 
                ticket_prepid,
                ticket_chain_match
            )
            continue

        # Inspect root requests
        ticket_root_reqs: List[str] = ticket.get('requests', [])
        if not ticket_root_reqs:
            logger.warning('Ticket %s does not have root requests attached', ticket_prepid)
            continue

        total_root_requests: int = len(ticket_root_reqs)
        for idx, ticket_root_req_prepid in enumerate(ticket_root_reqs):
            logger.info('%s of %s -> Root request: %s', idx, total_root_requests, ticket_root_req_prepid)
            root_req: dict = mcm_sdk._McM__get('restapi/requests/get/%s' % (ticket_root_req_prepid))
            if not root_req:
                logger.warning('Could not retrieve info for root request: %s', ticket_root_req_prepid)
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
    # Create McM controller
    start_time: datetime.datetime = datetime.datetime.now()
    mcm: McM = McM(id=McM.OIDC, dev=True)

    # Tickets to check
    tickets_to_check: List[str] = [
        f"PPD-2023Sep27-00{tk_id}"
        for tk_id in list(range(362,490))
    ]

    # Execute
    # inspect_ticket(mcm_sdk=mcm, tickets=tickets_to_check)

    logger.info('\n\n')
    logger.info('.............................................')
    logger.info('Inspecting chain campaigns from root requests via chain_request')
    logger.info('.............................................')

    # Check inspect `chain_campaign`
    complies: bool = inspect_chain_request_pattern(mcm_sdk=mcm, tickets=tickets_to_check)
    logger.info('Tickets comply with pattern: %s', complies)

    logger.info('\n\n')
    end_time: datetime.datetime = datetime.datetime.now()
    logger.info('Elapsed time: %s', end_time - start_time)