"""
This module includes some tests to check the Stats2 REST module 
and the authentication mechanisms.
"""

import pytest
from fixtures.oauth import (
    access_token_credentials,
    session_cookie_issues,
    stdin_enabled,
)

from rest import Stats2
from rest.utils.logger import LoggerFactory

# Logger
logger = LoggerFactory.getLogger("pdmv-http-client.tests")


def api_scenarios(stats: Stats2) -> None:
    """
    Check that the Stats2 module can query the same document
    properly independent of the authentication approach used.

    Args:
        stats: Stats2 HTTP client.
    """
    workflow = "pdmvserv_Run2022E_ZeroBias_30May2023v2_230608_061801_6461"
    prepid = "ReReco-Run2022E-ZeroBias-30May2023v2-00001"
    input_dataset = "/ZeroBias/Run2022E-v1/RAW"

    # The following is just one of the possible options.
    output_dataset = "/ZeroBias/Run2022E-30May2023v2-v1/MINIAOD"

    # Check the related links are available in the document
    by_workflow = stats.get_workflow(workflow_name=workflow)
    assert by_workflow and isinstance(by_workflow, dict)
    assert by_workflow["RequestType"] == "ReReco"
    assert by_workflow["RequestName"] == workflow
    assert by_workflow["PrepID"] == prepid
    assert by_workflow["InputDataset"] == input_dataset
    assert output_dataset in by_workflow["OutputDatasets"]

    # Several workflows could be related with the same request
    by_prepid = stats.get_prepid(prepid=prepid)
    assert by_workflow in by_prepid

    # Several workflows could be related with the same
    # input dataset.
    by_input_dataset = stats.get_input_dataset(input_dataset=input_dataset)
    assert by_workflow in by_input_dataset

    # Several workflows could be related with the same
    # output dataset.
    by_output_dataset = stats.get_output_dataset(output_dataset=output_dataset)
    assert by_workflow in by_output_dataset


def test_api_access_token(access_token_credentials):
    """
    Test Stats2 REST client configured with access tokens.
    """
    client_id, client_secret = access_token_credentials
    stats = Stats2(
        id=Stats2.OAUTH, dev=False, client_id=client_id, client_secret=client_secret
    )
    api_scenarios(stats=stats)


@pytest.mark.usefixtures("stdin_enabled")
def test_api_id_tokens():
    """
    Test Stats2 REST client configured with id tokens.
    """
    stats = Stats2(id=Stats2.OIDC, dev=False)
    api_scenarios(stats=stats)

@session_cookie_issues
def test_api_session_cookie():
    """
    Test Stats2 REST client configured with session cookies
    """
    stats = Stats2(id=Stats2.SSO, dev=False)
    api_scenarios(stats=stats)
