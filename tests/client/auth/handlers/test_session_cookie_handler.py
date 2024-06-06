"""
Provides some tests for the module
`src/auth/handlers/session_cookies.py` to verify its
correctness.
"""

import tempfile
from pathlib import Path

import pytest
import requests

from client.auth.handlers.session_cookies import SessionCookieHandler


def test_session_cookie_handler() -> None:
    with tempfile.NamedTemporaryFile() as file:
        session = requests.Session()
        cookie_handler = SessionCookieHandler(
            url="https://cms-pdmv-prod.web.cern.ch/mcm/",
            credential_path=Path(file.name),
        )
        try:
            cookie_handler.configure(session)
        except PermissionError:
            pytest.skip("Credential related to account enforcing 2FA, skipping...")
    pass
