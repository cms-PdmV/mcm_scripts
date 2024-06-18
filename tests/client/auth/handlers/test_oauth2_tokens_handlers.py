"""
Provides some tests for the module
`src/auth/handlers/oauth2_tokens.py` to verify its
correctness.
"""

import json
import os
import stat

import pytest
import requests
from fixtures.files import create_empty_file, empty_json_file, read_only_file
from fixtures.oauth import (
    client_id,
    client_secret,
    correct_application,
    credentials_available,
    stdin_enabled,
)

from rest.client.auth.handlers.oauth2_tokens import AccessTokenHandler, IDTokenHandler
from rest.utils.logger import LoggerFactory

# Logger instance
logger = LoggerFactory.getLogger("http_client.tests")


class TestAccessTokenHandler:
    def test_access_token_handler(
        self, client_id, client_secret, correct_application, credentials_available
    ):
        temp_file = create_empty_file(0o700)
        web_application, target_application = correct_application
        session = requests.Session()
        access_token_handler = AccessTokenHandler(
            url=web_application,
            credential_path=temp_file,
            client_id=client_id,
            client_secret=client_secret,
            target_application=target_application,
        )
        access_token_handler.configure(session)

        # The token is stored properly
        stored_token = {}
        with open(file=temp_file, encoding="utf-8") as f:
            stored_token = json.load(fp=f)

        assert stored_token == access_token_handler._credential
        assert stat.S_IMODE(temp_file.stat().st_mode) == 0o600
        os.remove(temp_file)

    def test_invalid_permissions(
        self,
        client_id,
        client_secret,
        correct_application,
        read_only_file,
        credentials_available,
    ):
        """
        Checks a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        web_application, target_application = correct_application
        with pytest.raises(OSError):
            session = requests.Session()
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
        client_id,
        client_secret,
        correct_application,
        empty_json_file,
        credentials_available,
    ):
        """
        Checks the request a PermissionError is raised in case the credentials
        path makes reference to a file without the relevant permissions.
        This also expects the authentication flow is completed successfully.
        """
        session = requests.Session()
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


class TestIDTokenHandler:
    def test_id_token_handler(self, correct_application, stdin_enabled):
        """
        Checks it is possible to request a new ID token.
        It expects the authentication flow is successfully completed.
        """
        temp_file = create_empty_file(0o700)
        web_application, target_application = correct_application
        session = requests.Session()
        id_token_handler = IDTokenHandler(
            url=web_application,
            credential_path=temp_file,
            target_application=target_application,
        )

        logger.warning("Accept the following request in the CERN Authentication page")
        id_token_handler.configure(session)

        # The token is stored properly
        stored_token = {}
        with open(file=temp_file, encoding="utf-8") as f:
            stored_token = json.load(fp=f)

        assert stored_token == id_token_handler._credential
        assert stat.S_IMODE(temp_file.stat().st_mode) == 0o600
        os.remove(temp_file)

    def test_invalid_permissions(
        self, correct_application, read_only_file, stdin_enabled
    ):
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

    def test_empty_credentials_file(
        self, correct_application, empty_json_file, stdin_enabled
    ):
        """
        Checks the request a PermissionError is raised in case the credentials
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

    def test_user_rejects_flow(self, correct_application, stdin_enabled):
        """
        Check that a PermissionError is raised in case the user denies the request.
        It expects the authentication request is denied by the authentication service.
        Just click to `No` to the request prompted in the page.
        """
        temp_file = create_empty_file(0o700)
        session = requests.Session()
        web_application, target_application = correct_application
        id_token_handler = IDTokenHandler(
            url=web_application,
            credential_path=temp_file,
            target_application=target_application,
        )

        with pytest.raises(PermissionError):
            logger.warning(
                "Reject the following request in the CERN Authentication page"
            )
            id_token_handler.configure(session)
