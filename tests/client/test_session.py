"""
Provides some tests for the module
`src/client/session.py` to verify its
correctness.
"""

import pytest
from fixtures.files import writable_file
from fixtures.oauth import (
    session_cookie_issues,
    access_token_credentials,
    correct_application,
    fails_by_permissions,
    fails_by_resource_requiring_2fa,
    stdin_enabled,
)
from requests.exceptions import SSLError

from rest.client.auth.auth_interface import AuthInterface
from rest.client.session import SessionFactory
from rest.utils.logger import LoggerFactory

# Logger instance
logger = LoggerFactory.getLogger("http_client.tests")


class TestSessionFactory:
    """
    Check that all authentication methods configure
    properly a `request.Session` and renew the credentials
    when required.
    """
    @session_cookie_issues
    def test_session_cookie_handler(self, correct_application, writable_file):
        web_application, _ = correct_application
        by_session_cookie = SessionFactory.configure_by_session_cookie(
            url=web_application, credential_path=writable_file
        )
        assert len(by_session_cookie.cookies) != 0

        # Perform an authenticated request
        index_page = by_session_cookie.get(web_application)
        assert (
            "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        )
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

        # Delete the credentials and perform the same request.
        by_session_cookie.cookies.clear()
        assert len(by_session_cookie.cookies) == 0

        index_page = by_session_cookie.get(web_application)
        assert len(by_session_cookie.cookies) != 0
        assert (
            "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        )
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

    def test_access_token_handler(
        self,
        access_token_credentials,
        correct_application,
        writable_file
    ):
        client_id, client_secret = access_token_credentials
        web_application, target_application = correct_application
        by_access_token = SessionFactory.configure_by_access_token(
            url=web_application,
            credential_path=writable_file,
            client_id=client_id,
            client_secret=client_secret,
            target_application=target_application,
        )
        assert by_access_token.headers.get("Authorization", "") != ""

        # Perform an authenticated request
        index_page = by_access_token.get(web_application)
        assert "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

        # Delete the credentials and perform the same request.
        by_access_token.headers.clear()
        assert len(by_access_token.headers) == 0

        index_page = by_access_token.get(web_application)
        assert by_access_token.headers.get("Authorization", "") != ""
        assert "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

    def test_id_token_handler(
        self,
        correct_application,
        writable_file,
        stdin_enabled,
    ):
        web_application, target_application = correct_application
        logger.warning("Accept the following request in the CERN Authentication page")
        by_id_token = SessionFactory.configure_by_id_token(
            url=web_application,
            credential_path=writable_file,
            target_application=target_application,
        )
        assert by_id_token.headers.get("Authorization", "") != ""

        # Perform an authenticated request
        index_page = by_id_token.get(web_application)
        assert "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

        # Delete the credentials and perform the same request.
        by_id_token.headers.clear()
        assert len(by_id_token.headers) == 0

        index_page = by_id_token.get(web_application)
        assert by_id_token.headers.get("Authorization", "") != ""
        assert "Welcome to the McM Monte-Carlo Request Management" in index_page.text
        assert index_page.status_code == 200
        assert AuthInterface.validate_response(index_page)

    @session_cookie_issues
    def test_fails_by_resource_requiring_2fa(self, writable_file, fails_by_resource_requiring_2fa):
        web_application, _ = fails_by_resource_requiring_2fa
        try:
            with pytest.raises(RuntimeError):
                _ = SessionFactory.configure_by_session_cookie(
                    url=web_application, credential_path=writable_file
                )
        except SSLError:
            msg = "Make sure to configure the host to accept CERN signed certificates"
            pytest.skip(msg)

    def test_fails_by_permissions(
        self,
        writable_file,
        access_token_credentials,
        fails_by_permissions,
    ):
        with pytest.raises(PermissionError):
            client_id, client_secret = access_token_credentials
            web_application, target_application = fails_by_permissions
            _ = SessionFactory.configure_by_access_token(
                url=web_application,
                credential_path=writable_file,
                client_id=client_id,
                client_secret=client_secret,
                target_application=target_application,
            )
