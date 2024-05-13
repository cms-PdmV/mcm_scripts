"""
This module allows to invalidate a 
root requests and its generated chains.
This is intended to be used only for
`production_manager` users or `administrators`.
"""

# Add path to code that allow easy access to McM
# sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")

import datetime
import logging
import pprint
import sys
from itertools import groupby
from copy import deepcopy
from rest import McM

# Check if version is >= 3.11, otherwise raise an exception.
if sys.version_info < (3, 11):
    msg = (
        "Unsuported Python version.\n"
        "Please use a version equal of higher than Python 3.11.\n"
        "Current version: %s " % (sys.version)
    )
    raise RuntimeError(msg)


class InvalidateDeleteRequests:
    """
    Invalidate and delete all the chain requests in McM
    linked to a root request in McM and delete the
    root requests if required.
    """

    def __init__(self, mcm: McM) -> None:
        self.mcm = mcm
        self.logger = self._get_logger()
        self._chain_request_type = "chained_requests"
        self._request_type = "requests"
        self.logger.warning("Sending requests to target environment: %s", self.mcm.host)

    def _get_logger(self) -> logging.Logger:
        """
        Creates a logger to record the performed steps.
        """
        logger: logging.Logger = logging.getLogger(__name__)
        formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        current_date = str(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M"))
        fh: logging.Handler = logging.FileHandler(
            f"mcm_invalidate_requests_{current_date}.log"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def _pretty(self, obj: dict) -> str:
        """
        Pretty print an object in console
        """
        return pprint.pformat(obj, width=50, compact=True)

    def _get(self, endpoint: str) -> dict:
        """
        Execute a raw GET operation for a resource in McM.
        """
        return self.mcm._McM__get(endpoint)

    def _get_invalidations(self, requests: list[str]) -> list[dict]:
        """
        Get all the invalidation records related to request given by
        parameter.

        Args:
            requests (list[str]): List of `prepids` used to retrieve its invalidations.

        Returns:
            list[str]: Invalidations related to the requests.
        """
        results: list[dict] = []
        for req in requests:
            inv_req = self.mcm.get("invalidations", query=f"prepid={req}")
            results += inv_req

        return results

    def _announce_invalidations(self, invalidations: list[dict]) -> dict:
        """
        Announce an invalidation for the given invalidation records.

        Args:
            invalidations (list[dict]): List of `invalidation` records to announce.

        Returns:
            list[str]: Invalidations related to the requests.
        """
        # Flatten and just get the `_id` field
        inv_ids: list[str] = [i.get("_id") for i in invalidations if i.get("_id")]
        announce_result = self.mcm.put(
            object_type="invalidations", object_data=inv_ids, method="announce"
        )

        return announce_result

    def _process_invalidation(self, request_prepids: list[str]) -> None:
        """
        Get all the invalidations related to a request and announces them
        in case they exists.

        Args:
            requests (list[str]): List of request's prepid to process its
                invalidation.
        """
        invalidations_to_announce = self._get_invalidations(requests=request_prepids)
        if invalidations_to_announce:
            announce_result = self._announce_invalidations(
                invalidations=invalidations_to_announce
            )
            self.logger.info("Invalidation result: %s", announce_result)
            if not announce_result.get("results"):
                msg = f"Unable to invalidate records for all the following requests: {request_prepids}"
                self.logger.error(msg)
                self.logger.error("Invalidation records: %s", invalidations_to_announce)
                raise RuntimeError(msg)
        pass

    def _invalidate_delete_chain_requests(
        self, chain_req_data: list[dict], remove_chain: bool = False
    ) -> None:
        """
        Rewinds the chain request to the root request
        invalidating and deleting all the intermediate requests.
        Deletes the chain request also if required.

        Args:
            chain_req_data (list[dict]): Chain requests data objects
                to process.
            remove_chain (bool): Deletes the chain request after
                perform the invalidation. If False, the chain request
                disable `flag` is re-enabled.
        """
        chain_req_operate: list[dict] = []
        chain_request_only_with_root: list[dict] = []
        chain_request_more_than_root: list[dict] = []

        # Filter the chain requests that only have the root request.
        for chain_request in chain_req_data:
            if len(chain_request.get("chain")) == 1:
                chain_request_only_with_root.append(chain_request)
            else:
                chain_request_more_than_root.append(chain_request)

        # 1. Group the chained request by the second request in the chain
        # (The first that is not the `root` request).
        if chain_request_more_than_root:
            grouped_chain = {
                k: list(g)
                for k, g in groupby(
                    chain_request_more_than_root, lambda el: el["chain"][1]
                )
            }
            if len(grouped_chain) != 1:
                msg = f"There should be only one group. Group result: {grouped_chain}"
                self.logger.error(msg)
                raise ValueError(msg)

            # Include in the list to operate.
            chain_req_operate += list(grouped_chain.values())[0]

        if chain_request_only_with_root:
            only_prepids = [el.get("prepid") for el in chain_request_only_with_root]
            self.logger.warning(
                "The following chain request only contain the root request in its chain: %s",
                self._pretty(only_prepids),
            )
            chain_req_operate += chain_request_only_with_root

        # 2. Order the chain requests by `step` descending
        chain_req_operate = sorted(
            chain_req_operate, key=lambda el: el["step"], reverse=True
        )
        self.logger.info(
            "Chain request pre-reset order (after sort): %s",
            [el.get("prepid") for el in chain_req_operate],
        )

        # 3. Set the flag to `False` and save
        for ch_r in chain_req_operate:
            ch_req_prepid = ch_r.get("prepid")
            updated_ch_r = self.mcm.get(
                object_type=self._chain_request_type, object_id=ch_req_prepid
            )
            updated_ch_r["action_parameters"]["flag"] = False
            updated_ch_r = self.mcm.update(
                object_type=self._chain_request_type, object_data=updated_ch_r
            )
            self.logger.info("Disable 'flag' response: %s", updated_ch_r)

            if not updated_ch_r or not updated_ch_r.get("results"):
                msg = f"Error updating chain requests: {ch_req_prepid}"
                self.logger.error(msg)
                raise RuntimeError(msg)

        for ch_r in chain_req_operate:
            ch_req_prepid = ch_r.get("prepid")

            # 4. Rewind the chain request to `root`.
            rewind_endpoint = (
                f"/restapi/chained_requests/rewind_to_root/{ch_req_prepid}"
            )
            rewind_response = self._get(endpoint=rewind_endpoint)
            self.logger.info("Rewind chain request response: %s", rewind_response)
            if not rewind_response or not rewind_response.get("results"):
                msg = f"Unable to rewind chain request to root ({ch_r}) - Details: {rewind_response}"
                self.logger.error(msg)
                raise RuntimeError(msg)

            # 5. Announce the invalidation.
            ch_req_requests: list[str] = ch_r.get("chain")
            self._process_invalidation(request_prepids=ch_r.get("chain"))

            # 6. Delete the other requests EXCEPT for the `root`
            # The first record in this list is the `root` request
            chain_delete = ch_req_requests[1:]

            # INFO: They must be deleted in order from the deepest
            # data tier to upwards
            chain_delete = reversed(chain_delete)

            for rd in chain_delete:
                self.mcm.delete(object_type=self._request_type, object_id=rd)

        # 7. Process the chain request
        if remove_chain:
            # Precondition: All the chained request share the same
            # root request.
            root_request_prepid: str = chain_req_operate[0].get("chain", [])[0]
            self.logger.warning(
                "Full resetting the root request (%s) as it is required to properly delete the chains",
                root_request_prepid,
            )
            result = self.mcm.reset(prepid=root_request_prepid)
            if not result:
                raise RuntimeError("Unable to reset the root request", result)

            # Process the root request invalidation.
            self._process_invalidation([root_request_prepid])

            # Remove all the chain requests
            for ch_r in chain_req_operate:
                ch_req_prepid = ch_r.get("prepid")
                self.mcm.delete(
                    object_type=self._chain_request_type, object_id=ch_req_prepid
                )
        else:
            # Re-enable the `flag`
            for ch_r in chain_req_operate:
                ch_req_prepid = ch_r.get("prepid")
                updated_ch_r = self.mcm.get(
                    object_type=self._chain_request_type, object_id=ch_req_prepid
                )
                updated_ch_r["action_parameters"]["flag"] = True
                updated_ch_r = self.mcm.update(
                    object_type=self._chain_request_type, object_data=updated_ch_r
                )
                self.logger.info("Disable 'flag' response: %s", updated_ch_r)
                if not updated_ch_r or not updated_ch_r.get("results"):
                    msg = f"Error updating chain requests: {ch_req_prepid}"
                    self.logger.error(msg)
                    raise RuntimeError(msg)

    def _invalidate_delete_root_request(
        self, root_prepid: str, remove_root: bool = False, remove_chain: bool = False
    ) -> None:
        """
        Invalidates and deletes all the chained request
        linked to a root request and remove the root
        request if required.

        Args:
            root_prepid (str): Root request prepid
            remove_root (bool): Invalidate and delete the root
                request after processing its chains. If True,
                the parameter `remove_chains` will be forced to
                `True`
            remove_chain (bool): Delete the chain request after
                processing it. If False, the chained requests
                `flag` is re-enabled.
        """
        self.logger.info(
            "Processing root request: %s, remove root: %s, remove chains: %s",
            root_prepid,
            remove_root,
            remove_chain,
        )

        if remove_root and not remove_chain:
            self.logger.warning(
                "Setting `remove_chain` to True as a cascade delete is requested"
            )
            remove_chain = True

        if remove_chain:
            self.logger.warning(
                (
                    "Root request will be FULL RESET "
                    "and its output dataset will be invalidated! "
                    "This is required to delete all its related chained requests."
                )
            )

        # 1. Get all the chained requests and process them.
        chain_req: list[dict] = self.mcm.get(
            object_type=self._chain_request_type, query=f"contains={root_prepid}"
        )
        self.logger.info(
            "Request (%s), operating chain requests: %s",
            root_prepid,
            self._pretty([ch.get("prepid") for ch in chain_req]),
        )
        self._invalidate_delete_chain_requests(
            chain_req_data=chain_req, remove_chain=remove_chain
        )

        # 2. Remove the root request if required.
        if remove_root:
            self.mcm.delete(object_type=self._request_type, object_id=root_prepid)

    def _filter_root_requests(self, requests_prepid: list[str]) -> list[str]:
        """
        Filter the given request's prepids and only pick
        those related only to root requests.
        """
        root_requests: list[str] = []
        for rid in requests_prepid:
            data: dict | None = self.mcm.get(
                object_type=self._request_type, object_id=rid
            )
            if data:
                is_root_request: bool = (data.get("type") == "LHE") and bool(
                    data.get("validation", {}).get("results", {})
                )
                if is_root_request:
                    root_requests.append(rid)

        return root_requests

    def invalidate_delete_cascade_requests(
        self,
        requests_prepid: list[str],
        remove_root: bool = False,
        remove_chain: bool = False,
        limit: int = 2**64,
    ) -> dict[str, list[str]]:
        """
        Invalidate and delete all the request including into the
        chain requests related to the provided root request.
        This could be considered as a "delete in cascade" process.

        Args:
            requests_prepid (list[str]): List of root requests to process.
                In case a non-root request is provided, it will be
                filtered.
            remove_root (bool): After processing the chained requests,
                invalidate the dataset related to the root request and
                delete it.
            remove_chain (bool): After removing the intermediate requests,
                remove the chain or re-enable it chain again.
            limit (int): Process root requests until the limit is reached.

        Returns:
            dict[str, list[str]]: Details about the requests processed in
                three categories: Success, Failed, Filtered.
        """
        root_request_prepids: list[str] = self._filter_root_requests(
            requests_prepid=deepcopy(requests_prepid)
        )
        discarded_prepids = list(set(requests_prepid) - set(root_request_prepids))
        if discarded_prepids:
            self.logger.info(
                "Following requests are not valid root requests (%s): %s",
                len(discarded_prepids),
                self._pretty(discarded_prepids),
            )

        failed_requests: list[str] = []
        success_requests: list[str] = []
        total_to_process = len(root_request_prepids)
        for idx, root_prepid in enumerate(root_request_prepids, start=1):
            try:
                self.logger.info(
                    "(%s/%s) Processing root request", idx, total_to_process
                )
                self._invalidate_delete_root_request(
                    root_prepid=root_prepid,
                    remove_root=remove_root,
                    remove_chain=remove_chain,
                )
                success_requests.append(root_prepid)
            except Exception as e:
                self.logger.error(
                    "Unable to process root request (%s): %s",
                    root_prepid,
                    e,
                    exc_info=True,
                )
                failed_requests.append(root_prepid)
            finally:
                if limit <= idx:
                    self.logger.info("Early stopping processing root requests...")
                    break

        return {
            "success": success_requests,
            "failed": failed_requests,
            "filtered": discarded_prepids,
        }
