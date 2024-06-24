import os

import pytest
import functools
from pytest import FixtureRequest

@pytest.fixture
def access_token_credentials() -> tuple[str, str]:
    client_id = os.getenv("ACCESS_TOKEN_CLIENT_ID", "")
    client_secret = os.getenv("ACCESS_TOKEN_CLIENT_SECRET", "")
    if not (client_id and client_secret):
        pytest.skip("Client credentials not provided for requesting an access token...")
    return client_id, client_secret

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

def session_cookie_issues(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PermissionError:
            pytest.skip("Credential related to account enforcing 2FA, skipping...")
        except RuntimeError as e:
            if "auth-get-sso-cookie: command not found" in str(e):
                pytest.skip("Session cookie package not available")
            if "No Kerberos credentials available" in str(e):
                pytest.skip("No Kerberos credentials available, request a Kerberos ticket to CERN realm...")
            else:
                raise e
    return wrapper