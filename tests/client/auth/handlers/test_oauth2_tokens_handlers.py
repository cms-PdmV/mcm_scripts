"""
Provides some tests for the module
`src/rest/client/auth/handlers/oauth2_tokens.py` to verify its
correctness.
"""

import json
import os
import stat

import pytest
import requests
from fixtures.files import empty_json_file, read_only_file, writable_file
from fixtures.oauth import access_token_credentials, correct_application, stdin_enabled

from rest.client.auth.handlers.oauth2_tokens import AccessTokenHandler, IDTokenHandler
from rest.utils.logger import LoggerFactory

# Logger instance
logger = LoggerFactory.getLogger("pdmv-http-client.tests")


class TestAccessTokenHandler:
    def test_access_token_handler(
        self, access_token_credentials, correct_application, writable_file
    ):
        client_id, client_secret = access_token_credentials
        web_application, target_application = correct_application
        session = requests.Session()
        access_token_handler = AccessTokenHandler(
            url=web_application,
            credential_path=writable_file,
            client_id=client_id,
            client_secret=client_secret,
            target_application=target_application,
        )
        access_token_handler.configure(session)

        # The token is stored properly
        stored_token = {}
        with open(file=writable_file, encoding="utf-8") as f:
            stored_token = json.load(fp=f)

        assert stored_token == access_token_handler._credential
        assert stat.S_IMODE(writable_file.stat().st_mode) == 0o600

    def test_invalid_permissions(
        self,
        access_token_credentials,
        correct_application,
        read_only_file,
    ):
        """
        Checks a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        web_application, target_application = correct_application
        with pytest.raises(OSError):
            session = requests.Session()
            client_id, client_secret = access_token_credentials
            access_token_handler = AccessTokenHandler(
                url=web_application,
                credential_path=read_only_file,
                client_id=client_id,
                client_secret=client_secret,
                target_application=target_application,
            )
            access_token_handler.configure(session)

        # Remove the temporal file
        os.remove(read_only_file)

    def test_empty_credentials_file(
        self,
        access_token_credentials,
        correct_application,
        empty_json_file,
    ):
        """
        Checks a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        session = requests.Session()
        client_id, client_secret = access_token_credentials
        web_application, target_application = correct_application
        access_token_handler = AccessTokenHandler(
            url=web_application,
            credential_path=empty_json_file,
            client_id=client_id,
            client_secret=client_secret,
            target_application=target_application,
        )
        access_token_handler.configure(session)
        os.remove(empty_json_file)


@pytest.mark.usefixtures("stdin_enabled")
class TestIDTokenHandler:
    def test_id_token_handler(self, correct_application, writable_file):
        """
        Checks it is possible to request a new ID token.
        It expects the authentication flow is successfully completed.
        """
        web_application, target_application = correct_application
        session = requests.Session()
        id_token_handler = IDTokenHandler(
            url=web_application,
            credential_path=writable_file,
            target_application=target_application,
        )

        logger.warning("Accept the following request in the CERN Authentication page")
        id_token_handler.configure(session)

        # The token is stored properly
        stored_token = {}
        with open(file=writable_file, encoding="utf-8") as f:
            stored_token = json.load(fp=f)

        assert stored_token == id_token_handler._credential
        assert stat.S_IMODE(writable_file.stat().st_mode) == 0o600

    def test_invalid_permissions(self, correct_application, read_only_file):
        """
        Checks a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        web_application, target_application = correct_application
        with pytest.raises(OSError):
            session = requests.Session()
            id_token_handler = IDTokenHandler(
                url=web_application,
                credential_path=read_only_file,
                target_application=target_application,
            )

            logger.warning(
                "Accept the following request in the CERN Authentication page"
            )
            id_token_handler.configure(session)

        # Remove the temporal file
        os.remove(read_only_file)

    def test_empty_credentials_file(self, correct_application, empty_json_file):
        """
        Checks a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        web_application, target_application = correct_application
        session = requests.Session()
        id_token_handler = IDTokenHandler(
            url=web_application,
            credential_path=empty_json_file,
            target_application=target_application,
        )

        logger.warning("Accept the following request in the CERN Authentication page")
        id_token_handler.configure(session)
        os.remove(empty_json_file)

    def test_user_rejects_flow(self, correct_application, writable_file):
        """
        Check that a PermissionError is raised in case the user denies the request.
        It expects the authentication request is denied by the authentication service.
        Just click to `No` to the request prompted in the page.
        """
        session = requests.Session()
        web_application, target_application = correct_application
        id_token_handler = IDTokenHandler(
            url=web_application,
            credential_path=writable_file,
            target_application=target_application,
        )

        with pytest.raises(PermissionError):
            logger.warning(
                "Reject the following request in the CERN Authentication page"
            )
            id_token_handler.configure(session)
