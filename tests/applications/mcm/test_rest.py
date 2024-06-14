"""
This module includes some test to check
the McM REST module and the authentication mechanisms.
"""

import os

import pytest
from fixtures.files import create_empty_file

from rest import McM
from utils.logger import LoggerFactory

# Logger
logger = LoggerFactory.getLogger("http_client.tests")

# Cases for McM
mcm_instance_cases: list[tuple[str, bool]] = [
    (McM.SSO, True),
    (McM.SSO, False),
    (McM.OIDC, True),
    (McM.OIDC, False),
]

mcm_only_no_auth: list[tuple[str, bool]] = [
    ("", True),
    ("", False),
]


@pytest.mark.parametrize("mcm_id,dev", mcm_instance_cases + mcm_only_no_auth)
def test_public_api(mcm_id, dev):
    """
    Check that McM module is able to execute requests
    to the public API independently if authentication
    is provided or not.
    """
    temp_file = create_empty_file(0o700)
    try:
        assert isinstance(mcm_id, str)
        assert isinstance(dev, bool)

        mcm = McM(id=mcm_id, dev=dev, cookie=temp_file)
        request_public_endpoint = "public/restapi/requests/get"
        test_prepid = "TOP-Summer12-00368"
        request_from_public = "%s/%s" % (request_public_endpoint, test_prepid)

        raw_result = mcm._McM__get(request_from_public)
        single_request = raw_result.get("results", {})
        assert single_request
        assert isinstance(single_request, dict)
        assert single_request.get("prepid") == test_prepid

    except OSError as e:
        stdin_disabled = "pytest: reading from stdin while output is captured!"
        msg = str(e)
        if stdin_disabled in msg:
            reason = (
                "Standard input is disabled, it is not possible to "
                "capture human interactions to know when they completed "
                "the authentication flow..."
            )
            pytest.skip(reason)
        else:
            raise e
    finally:
        os.remove(temp_file)


@pytest.mark.parametrize("mcm_id,dev", mcm_instance_cases)
def test_api(mcm_id, dev):
    """
    Check that McM module is able to execute requests
    to the public API independently if authentication
    is provided or not.
    """
    temp_file = create_empty_file(0o700)
    try:
        assert isinstance(mcm_id, str)
        assert isinstance(dev, bool)

        mcm = McM(id=mcm_id, dev=dev, cookie=temp_file)
        test_prepid = "TOP-Summer12-00368"
        single_request = mcm.get("requests", test_prepid, method="get")

        assert single_request
        assert isinstance(single_request, dict)
        assert single_request.get("prepid") == test_prepid

    except OSError as e:
        stdin_disabled = "pytest: reading from stdin while output is captured!"
        msg = str(e)
        if stdin_disabled in msg:
            reason = (
                "Standard input is disabled, it is not possible to "
                "capture human interactions to know when they completed "
                "the authentication flow..."
            )
            pytest.skip(reason)
        else:
            raise e
    finally:
        os.remove(temp_file)
