"""
Provides some tests for the module
`src/auth/handlers/session_cookies.py` to verify its
correctness.
"""

import os
import stat

import requests
from fixtures.files import create_empty_file, writable_file
from fixtures.oauth import correct_application, session_cookie_issues

from pathlib import Path

from rest.client.auth.handlers.session_cookies import SessionCookieHandler


class TestSessionCookieHandler:

    @session_cookie_issues
    def test_session_cookie_handler(self, correct_application, writable_file) -> None:
        url, _ = correct_application
        session = requests.Session()
        cookie_handler = SessionCookieHandler(
            url=url,
            credential_path=writable_file,
        )
        cookie_handler.configure(session)
        assert stat.S_IMODE(writable_file.stat().st_mode) == 0o600

    @session_cookie_issues
    def test_invalid_file(self, correct_application, writable_file) -> None:
        url, _ = correct_application
        os.remove(writable_file)
        assert isinstance(writable_file, Path)
        assert not writable_file.exists()

        session = requests.Session()
        cookie_handler = SessionCookieHandler(
            url=url,
            credential_path=writable_file,
        )
        cookie_handler.configure(session)
        assert writable_file.exists()
        assert stat.S_IMODE(writable_file.stat().st_mode) == 0o600
