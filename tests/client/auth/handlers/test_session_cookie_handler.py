"""
Provides some tests for the module
`src/auth/handlers/session_cookies.py` to verify its
correctness.
"""

import os
import stat

import pytest
import requests
from fixtures.files import create_empty_file
from fixtures.oauth import correct_application

from rest.client.auth.handlers.session_cookies import SessionCookieHandler


class TestSessionCookieHandler:

    def test_session_cookie_handler(self, correct_application) -> None:
        url, _ = correct_application
        temp_file = create_empty_file(0o700)
        session = requests.Session()
        cookie_handler = SessionCookieHandler(
            url=url,
            credential_path=temp_file,
        )
        try:
            cookie_handler.configure(session)
            assert stat.S_IMODE(temp_file.stat().st_mode) == 0o600
        except PermissionError:
            pytest.skip("Credential related to account enforcing 2FA, skipping...")
        except RuntimeError as e:
            if "auth-get-sso-cookie: command not found" in str(e):
                pytest.skip("Session cookie package not available")
            else:
                raise e
        finally:
            os.remove(temp_file)
