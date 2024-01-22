"""
This module allows users to change the time/event
attribute for requests that already completed 
the validation step.
"""
import sys
# Add path to code that allow easy access to McM
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

import logging
import pprint
import datetime
from urllib.error import HTTPError
from typing import List, Dict, Optional
from copy import deepcopy
from rest import McM


logger: logging.Logger = logging.getLogger(name=__name__)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
fh: logging.Handler = logging.FileHandler('execution.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

# If you want more messages, enable the DEBUG mode
# logger.setLevel(level=logging.DEBUG)

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


def ok_result(result: Optional[Dict]) -> bool:
    """
    Checks if the McM operation finished successfully

    Args:
        result (dict | None): Potential McM result for 
            a query.
    
    Returns:
        True if the operation finished successfully, false
            otherwise.
    """
    if result is None:
        return False
    return result.get('results', False)


def get_announce_invalidation(mcm: McM, request: Dict) -> List[str]:
    """
    Retrieves the latest workflow submitted by PdmV, checks that it
    exists and, if so, announces its invalidation to ReqMgr2.
    
    Args:
        mcm (McM): McM client instance.
        request (Dict): Request data.

    Returns:
        list[str]: Workflows invalidated in ReqMgr2
    """
    # Get all the workflow names and just take the 'new' ones.
    prepid: str = request.get('prepid', '')
    invalidations = mcm.get(
        object_type='invalidations',
        query=f'prepid={prepid}'
    ) or []
    
    # Get only the _id field if its status is 'new'
    invalidations: List[str] = [
        i.get('_id')
        for i in invalidations 
        if i.get('status') == 'new'
    ]

    if not invalidations:
        logger.error(
            "There are no invalidations in 'new' status to process for request: %s",
            prepid
        )
        return
    
    # Announce the required invalidations
    inv_result: Dict = mcm.put(object_type='invalidations', object_data=invalidations, method='announce')
    logger.info('Invalidation result: %s', pretty(inv_result))
    if not ok_result(inv_result):
        logger.warning('Unable to invalidate elements: %s', invalidations)
        
    return invalidations


def update_time_event(ratio: float, request: Dict) -> Dict:
    """
    Updates the time/event for a validated request.

    Args:
        ratio (float): Multiplier ratio for increasing the time/event.
        request (Dict): McM request to modify.

    Returns:
        dict: Request with its time/event modified.
    """
    cloned_req = deepcopy(request)
    prepid: str = cloned_req.get('prepid')
    logger.info('Updating request %s', prepid)

    # Update global time/event.
    time_event: List[float] = cloned_req.get('time_event')
    logger.info('Updating time/event: Initial value - %s', time_event)
    time_event = [v * ratio for v in time_event]
    logger.info('Updating time/event: Final value - %s', time_event)
    cloned_req['time_event'] = time_event

    # Scan all the validation results.
    validation_results: Dict = cloned_req.get('validation', {}).get('results', {})
    for thread, val_data_list in validation_results.items():
        val_data = val_data_list[0]
        time_event_thread: float = val_data.get('time_per_event', 0.0)
        logger.info('Thread: %s - Initial value: %s', thread, time_event_thread)
        time_event_thread *= ratio
        logger.info('Thread: %s - Updated value: %s', thread, time_event_thread)
        val_data['time_per_event'] = time_event_thread

        # Update them
        cloned_req['validation']['results'][thread] = [val_data]

    logger.info('Update finished')
    return cloned_req


def update_validation_time_event(mcm: McM, prepids_ratio: List[Dict]) -> List[str]:
    """
    For each given request, updates the validation time/event in ReqMgr2.
    To achieve this, the request data is retrieved and the validation time/event
    is updated with the given ratio.

    Args:
        mcm (McM): McM client instance.
        prepids_ratio (list[dict]): List with all the prepids to change.
            The dictionary format expected is:
            {
                "prepid": <Request prepid>,
                "ratio": <Multiplier ratio, e.g: 5.00>
            }

    Returns:
        List[str]: Requests prepid successfully updated
    """
    success: List[str] = []
    submitted = ('submit', 'submitted')
    approved = ('approve', 'approved')

    # Retrieve all the requests data, grouping them by status and approval
    for pid in prepids_ratio:
        prepid: str = pid.get('prepid')
        ratio: float = pid.get('ratio')
        req_data: Optional[Dict] = mcm.get(object_type='requests', object_id=prepid)
        if not req_data:
            logger.error("Request %s doesn't exist", prepid)
            continue

        # Check for the status
        req_approval = req_data.get('approval')
        req_status = req_data.get('status')
        req_type = (req_approval, req_status)

        if not req_type == approved and not req_type == submitted:
            logger.warning(
                'Discarding request: %s - Approval: %s - Status: %s',
                prepid,
                req_approval,
                req_status
            )
            continue
        
        # 1. Update the time/event
        req_updated = update_time_event(ratio=ratio, request=req_data)
        logger.debug("Request - New validation values: %s", pretty(req_updated))

        # 2. Save the data
        logger.info('Updating time/event for request: %s', prepid)
        success_update = None
        try:
            success_update = mcm.update(object_type='requests', object_data=req_updated)
        except HTTPError as h:
            logger.critical(h, exc_info=True)

        logger.info(pretty(success_update))
        if not ok_result(success_update):
            logger.error(
                'Unable to save request: %s - Details: %s',
                success_update,
                pretty(success_update)
            )
        else:
            logger.info('Request: %s has been successfully updated in McM', prepid)
            success.append(prepid)

        return success


def reset_invalidate_submit(mcm: McM, prepids: List[str]) -> List[str]:
    """
    For each given request prepid, soft reset the request, invalidate the workflows
    and datasets in ReqMgr2 and submit the request again.

    Args:
        mcm (McM): McM client instance.
        prepids (list[str]): Prepids to operate

    Returns:
        List[str]: Requests prepid successfully submitted
    """
    submitted_req: List[Dict] = []
    approved_req: List[Dict] = []
    submitted = ('submit', 'submitted')
    approved = ('approve', 'approved')
    success_processed: List[str] = []

    # Retrieve all the requests data, grouping them by status and approval
    for pid in prepids:
        req_data: Optional[Dict] = mcm.get(object_type='requests', object_id=pid)
        if not req_data:
            logger.error("Request %s doesn't exist", pid)
            continue
        
        # Check for the status
        req_approval = req_data.get('approval')
        req_status = req_data.get('status')
        req_type = (req_approval, req_status)

        if req_type == approved:
            approved_req.append(req_data)
        elif req_type == submitted:
            submitted_req.append(req_data)
        else:
            logger.warning(
                'Discarding request: %s - Approval: %s - Status: %s',
                pid,
                req_approval,
                req_status
            )

    # Process all the request with submitted status
    for sub_req in submitted_req:
        # 1. Soft reset the request
        soft_result = None
        sub_prepid = sub_req.get('prepid')
        try:
            soft_result = mcm.soft_reset(prepid=sub_prepid)
        except HTTPError as h:
            logger.critical(h, exc_info=True)

        if not soft_result:
            logger.warning('Unable to soft reset request: %s, skipping', sub_prepid)
            continue

        # 2. Invalidate the workflow
        invalidated_workflow = None
        try:
            invalidated_workflow = get_announce_invalidation(mcm=mcm, request=sub_req)
        except HTTPError as h:
            logger.critical(h, exc_info=True)
        
        if not invalidated_workflow:
            error_inv: str = f'Unable to invalidate workflows linked to the request: {sub_prepid}, skipping'
            logger.warning(error_inv)
            continue
        else:
            logger.info(
                'Request: %s has been soft reset and its workflows/datasets invalidated in McM',
                sub_prepid
            )
            success_processed.append(sub_prepid)

    # Process all request with approved status
    # INFO: This assumes they have been already modified with the desired values!
    logger.info(
        "Processing 'approved' request. It is assumed its time/event has been already modified"
    )

    for apr_req in approved_req:
        apr_prepid: str = apr_req.get('prepid')
        logger.info('Submitting request: %s', apr_prepid)
        approved = None
        try:
            approved = mcm.approve(object_type='requests', object_id=apr_prepid)
        except HTTPError as h:
            logger.critical(h, exc_info=True)

        if not ok_result(approved):
            logger.error(
                'Unable to submit request: %s - Details: %s', 
                apr_prepid, 
                pretty(approved)
            )
        else:
            logger.info('Request: %s has been successfully submitted in McM', apr_prepid)
            success_processed.append(apr_prepid)

    return success_processed


# Run the script, for example
if __name__ == '__main__':
    mcm: McM = McM(dev=False)
    start_time = datetime.datetime.now()
    
    '''
    # For example, to increase the time/event for validation

    requests = ["SMP-RunIISummer20UL16wmLHENanoGENpruned-00018"]
    prepid_data: List[Dict] = []
    for req in requests:
        prepid_data.append({"prepid": req, "ratio": 5.0})
    
    # Start execution
    updated_req: List[str] = update_validation_time_event(
        mcm=mcm,
        prepids_ratio=prepid_data
    )
    '''

    # Resubmit the following requests again
    requests = ["SMP-RunIISummer20UL16wmLHENanoGENpruned-00018"]

    # Start execution
    updated_req: List[str] = reset_invalidate_submit(
        mcm=mcm,
        prepids=requests
    )

    # End of execution
    end_time = datetime.datetime.now()
    logger.info('Elapsed time: %s', end_time - start_time)
    logger.info('%s request have been processed', len(updated_req))
    logger.info('%s', pretty(updated_req))
