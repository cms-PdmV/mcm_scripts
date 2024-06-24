"""
This module includes some test to check
the McM REST module and the authentication mechanisms.
"""

import pytest
from fixtures.oauth import session_cookie_issues, access_token_credentials, stdin_enabled

from rest import McM
from rest.utils.logger import LoggerFactory

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


def public_test_api(mcm: McM) -> None:
    """
    Check that McM module is able to execute requests
    to the public API independently if authentication
    is provided or not.
    """
    request_public_endpoint = "public/restapi/requests/get"
    test_prepid = "TOP-Summer12-00368"
    request_from_public = "%s/%s" % (request_public_endpoint, test_prepid)

    raw_result = mcm._McM__get(request_from_public)
    single_request = raw_result.get("results", {})
    assert single_request
    assert isinstance(single_request, dict)
    assert single_request.get("prepid") == test_prepid


def private_test_api(mcm: McM) -> None:
    """
    Check that McM module is able to execute requests
    to the public API independently if authentication
    is provided or not.
    """
    test_prepid = "TOP-Summer12-00368"
    single_request = mcm.get("requests", test_prepid, method="get")

    assert single_request
    assert isinstance(single_request, dict)
    assert single_request.get("prepid") == test_prepid

@pytest.mark.parametrize("mcm_id,dev", [(McM.OAUTH, True), (McM.OAUTH, False)])
def test_api_access_token(mcm_id, dev, access_token_credentials):
    assert isinstance(mcm_id, str)
    assert isinstance(dev, bool)
    client_id, client_secret = access_token_credentials
    
    mcm = McM(id=mcm_id, dev=dev, client_id=client_id, client_secret=client_secret)
    public_test_api(mcm=mcm)
    private_test_api(mcm=mcm)

@pytest.mark.parametrize("mcm_id,dev", [(McM.OIDC, True), (McM.OIDC, False)])
@pytest.mark.usefixtures("stdin_enabled")
def test_api_id_token(mcm_id, dev):
    assert isinstance(mcm_id, str)
    assert isinstance(dev, bool)
    
    mcm = McM(id=mcm_id, dev=dev)
    public_test_api(mcm=mcm)
    private_test_api(mcm=mcm)

@pytest.mark.parametrize("mcm_id,dev", [(McM.SSO, True), (McM.SSO, False)])
@session_cookie_issues
def test_api_session_cookie(mcm_id, dev):
    assert isinstance(mcm_id, str)
    assert isinstance(dev, bool)
    
    mcm = McM(id=mcm_id, dev=dev)
    public_test_api(mcm=mcm)
    private_test_api(mcm=mcm)
