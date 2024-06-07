"""
Provides some tests for the module
`src/client/session.py` to verify its
correctness.
"""

import os
import pytest
from requests.exceptions import SSLError
from client.session import SessionFactory
from client.auth.auth_interface import AuthInterface
from fixtures.files import create_empty_file, empty_json_file, read_only_file
from fixtures.oauth import (
    correct_application,
    fails_by_resource_requiring_2fa,
    fails_by_permissions,
    client_id,
    client_secret,
    credentials_available,
    stdin_enabled,
)
from utils.logger import LoggerFactory

# Logger instance
logger = LoggerFactory.getLogger("http_client.tests")


class TestSessionFactory:
    """
    Check that all authentication methods configure
    properly a `request.Session` and renew the credentials
    when required.
    """

    def test_session_cookie_handler(self, correct_application):
        temp_file = create_empty_file(0o700)
        web_application, _ = correct_application
        try:
            by_session_cookie = SessionFactory.configure_by_session_cookie(
                url=web_application, credential_path=temp_file
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

        except PermissionError:
            pytest.skip("Credential related to account enforcing 2FA, skipping...")
        finally:
            os.remove(temp_file)

    def test_access_token_handler(
        self,
        client_id,
        client_secret,
        correct_application,
        credentials_available,
    ):
        temp_file = create_empty_file(0o700)
        web_application, target_application = correct_application
        by_access_token = SessionFactory.configure_by_access_token(
            url=web_application,
            credential_path=temp_file,
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

        os.remove(temp_file)

    def test_id_token_handler(
        self,
        correct_application,
        stdin_enabled,
    ):
        temp_file = create_empty_file(0o700)
        web_application, target_application = correct_application
        logger.warning("Accept the following request in the CERN Authentication page")
        by_id_token = SessionFactory.configure_by_id_token(
            url=web_application,
            credential_path=temp_file,
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

        os.remove(temp_file)

    def test_fails_by_resource_requiring_2fa(self, fails_by_resource_requiring_2fa):
        temp_file = create_empty_file(0o700)
        web_application, _ = fails_by_resource_requiring_2fa
        try:
            with pytest.raises(RuntimeError):
                _ = SessionFactory.configure_by_session_cookie(
                    url=web_application, credential_path=temp_file
                )
        except SSLError:
            msg = "Make sure to configure the host to accept CERN signed certificates"
            pytest.skip(msg)
        finally:
            os.remove(temp_file)

    def test_fails_by_permissions(
        self,
        client_id,
        client_secret,
        fails_by_permissions,
        credentials_available,
    ):
        with pytest.raises(PermissionError):
            temp_file = create_empty_file(0o700)
            web_application, target_application = fails_by_permissions
            _ = SessionFactory.configure_by_access_token(
                url=web_application,
                credential_path=temp_file,
                client_id=client_id,
                client_secret=client_secret,
                target_application=target_application,
            )
            os.remove(temp_file)
