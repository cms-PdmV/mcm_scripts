import os

import pytest
from pytest import FixtureRequest


@pytest.fixture
def client_id():
    return os.getenv("ACCESS_TOKEN_CLIENT_ID", "")


@pytest.fixture
def client_secret():
    return os.getenv("ACCESS_TOKEN_CLIENT_SECRET", "")


@pytest.fixture
def web_application() -> str:
    return "https://cms-pdmv-prod.web.cern.ch/mcm/"


@pytest.fixture
def correct_application() -> tuple[str, str]:
    return ("https://cms-pdmv-prod.web.cern.ch/mcm/", "cms-ppd-pdmv-device-flow")


@pytest.fixture
def fails_by_resource_requiring_2fa() -> tuple[str, str]:
    return ("https://judy.cern.ch", "judy-cern-ch")


@pytest.fixture
def fails_by_permissions() -> tuple[str, str]:
    return (
        "https://xsecdb-xsdb-official.app.cern.ch/xsdb/",
        "webframeworks-paas-xsdb-official",
    )


@pytest.fixture
def stdin_enabled(request: FixtureRequest) -> None:
    """
    Check if the current execution allows to
    provide values by `stdin` interactions.

    Args:
        request: Pytest request fixture.
    """
    enabled = request.config.option.capture == "no"
    if not enabled:
        reason = (
            "Standard input is disabled, it is not possible to "
            "capture human interactions to know when they completed "
            "the authentication flow..."
        )
        pytest.skip(reason)


@pytest.fixture
def credentials_available(client_id, client_secret) -> None:
    if not (client_id and client_secret):
        pytest.skip("Client credentials not provided for requesting an access token...")
