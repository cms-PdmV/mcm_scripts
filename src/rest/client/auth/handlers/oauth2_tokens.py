"""
This module provides a handler
to authenticate requests using OAuth2 tokens.
"""

import json
import os
from json import JSONDecodeError
from pathlib import Path

import requests
from requests.sessions import Session

from rest.client.auth.auth_interface import AuthInterface
from rest.utils.logger import LoggerFactory


class AccessTokenHandler(AuthInterface):
    """
    Loads an access token from a JSON file and configures
    a HTTP session to make use of it. This implements the API
    access procedure described in:

        - https://auth.docs.cern.ch/user-documentation/oidc/api-access/

    Attributes:
        _url: Target web application URL.
        _credential: A JSON object including the access token, the refresh token
            and some metadata.
        _credential_path: Path to load the access token from or to persist in.
        _client_id: ID for the client application, registered in the application portal,
            to be use
        -client_secret: Secret for the client application.
        _target_application: Client ID linked to the target web
            application.
    """

    TOKEN_ENDPOINT = "https://auth.cern.ch/auth/realms/cern/api-access/token"

    def __init__(
        self,
        url: str,
        credential_path: Path,
        client_id: str,
        client_secret: str,
        target_application: str,
    ) -> None:
        self._url = url
        self._credential_path = credential_path
        self._client_id = client_id
        self._client_secret = client_secret
        self._target_application = target_application
        self._credential: dict = {}
        self._logger = LoggerFactory.getLogger("http_client.client")

    def _load_credential(self) -> dict:
        try:
            with open(file=self._credential_path, encoding="utf-8") as f:
                credential = json.load(f)
                return credential
        except (OSError, JSONDecodeError):
            return {}

    def _request_credential(self) -> dict:
        access_token = requests.post(
            url=AccessTokenHandler.TOKEN_ENDPOINT,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "audience": self._target_application,
            },
        )

        if access_token.status_code != 200:
            msg = (
                f"Error requesting access token ({access_token.status_code}): "
                f"{json.dumps(access_token.json(), indent=4)}"
            )
            raise PermissionError(msg)

        return access_token.json()

    def _save_credential(self) -> None:
        with open(file=self._credential_path, mode="w", encoding="utf-8") as f:
            json.dump(obj=self._credential, fp=f, indent=4)

        os.chmod(path=self._credential_path, mode=0o600)

    def authenticate(self) -> None:
        loaded_access_token = self._load_credential()
        if self._validate(access_token=loaded_access_token):
            self._credential = loaded_access_token
            return

        # Access token is not valid anymore, request another one
        self._logger.debug("Access token is not valid, requesting a new one")
        new_access_token = self._request_credential()
        if self._validate(access_token=new_access_token):
            self._credential = new_access_token
            self._save_credential()
            return

    def configure(self, session: Session) -> Session:
        if not self._credential:
            self.authenticate()

        raw_access_token = self._credential.get("access_token", "")
        session.headers.update({"Authorization": f"Bearer {raw_access_token}"})
        return session

    def _validate(self, access_token: dict) -> bool:
        """
        Checks if the provided cookie is valid to consume a resource in
        the target web application.

        Args:
            access_token: OAuth2 access token retrieve from
                CERN Authentication service.
        """
        raw_access_token = access_token.get("access_token", "")
        test_response = requests.get(
            self._url, headers={"Authorization": f"Bearer {raw_access_token}"}
        )
        return self.validate_response(test_response)


class IDTokenHandler(AuthInterface):
    """
    Loads an ID token from a file or requests a new one
    via Device Code Authorization Grant or refresh tokens (in case it is
    provided in a token file). This implements the process described at:

    - https://auth.docs.cern.ch/user-documentation/oidc/device-code/

    Attributes:
        _url: Target web application URL.
        _credential: A JSON object including the access token, the refresh token
            and some metadata.
        _credential_path: Path to load the access token from or to persist in.
        _client_id: ID for the client application, registered in the application portal,
            to be use. This application MUST be configured as a public client, so that no
            client secret is required.
        _target_application: Client ID linked to the target web
            application.
    """

    TOKEN_ENDPOINT = (
        "https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/token"
    )
    DEVICE_ENDPOINT = (
        "https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/auth/device"
    )

    def __init__(
        self,
        url: str,
        credential_path: Path,
        target_application: str,
    ) -> None:
        self._url = url
        self._credential_path = credential_path
        self._target_application = target_application
        self._credential: dict = {}
        self._logger = LoggerFactory.getLogger("http_client.client")

    def _load_credential(self) -> dict:
        try:
            with open(file=self._credential_path, encoding="utf-8") as f:
                credential = json.load(f)
                return credential
        except (OSError, JSONDecodeError):
            return {}

    def _refresh_token(self) -> dict:
        """
        Renews the current ID token by requesting a new one
        using the available refresh token.

        Returns:
            dict: ID token.
        """
        refresh_request = requests.post(
            url=IDTokenHandler.TOKEN_ENDPOINT,
            data={
                "grant_type": "refresh_token",
                "client_id": self._target_application,
                "refresh_token": self._credential.get("refresh_token", ""),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        details = refresh_request.json()
        if refresh_request.status_code != 200:
            self._logger.debug(
                "Unable to refresh ID token (HTTP code: %s), details: %s",
                refresh_request.status_code,
                json.dumps(refresh_request.json(), indent=4),
            )
            return {}

        id_token = details
        return id_token

    def _request_new_id_token(self) -> dict:
        """
        Request a new ID token to the authentication service
        using a Device Code Authorization Grant. This requires
        human interaction to complete the flow

        Returns:
            dict: ID token.
        """
        # Request a device code pre-authentication.
        device_code = requests.post(
            url=IDTokenHandler.DEVICE_ENDPOINT,
            data={"client_id": self._target_application},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self._logger.info(
            "Go to: %s\n", device_code.json()["verification_uri_complete"]
        )
        input("Press Enter once you have authenticated...")

        code_details: dict = device_code.json()
        if device_code.status_code == 401:
            msg = (
                f"Make sure the application ({self._target_application}) is configured as a public client"
                f"Error: {json.dumps(code_details, indent=4)}"
            )
            raise PermissionError(msg)

        # Request the ID token
        device_completion = requests.post(
            url=IDTokenHandler.TOKEN_ENDPOINT,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": code_details["device_code"],
                "client_id": self._target_application,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        completion_details = device_completion.json()
        if device_completion.status_code != 200:
            msg = (
                f"Unable to request an ID token\n"
                f"Error: {json.dumps(completion_details, indent=4)}"
            )
            raise PermissionError(msg)

        id_token = completion_details
        return id_token

    def _request_credential(self) -> dict:
        # Attempt to refresh the token
        id_token = self._refresh_token()
        if id_token:
            return id_token

        # Request a new ID token
        self._logger.debug(
            "Requesting new ID token asking the user to manually complete the flow"
        )
        return self._request_new_id_token()

    def _save_credential(self) -> None:
        with open(file=self._credential_path, mode="w", encoding="utf-8") as f:
            json.dump(obj=self._credential, fp=f, indent=4)

        os.chmod(path=self._credential_path, mode=0o600)

    def authenticate(self) -> None:
        loaded_id_token = self._load_credential()
        if self._validate(id_token=loaded_id_token):
            self._credential = loaded_id_token
            return

        # ID token is not valid anymore, request another one
        self._logger.debug("ID token is not valid, requesting a new one")
        new_id_token = self._request_credential()
        if self._validate(id_token=new_id_token):
            self._credential = new_id_token
            self._save_credential()
            return

    def configure(self, session: Session) -> Session:
        if not self._credential:
            self.authenticate()

        raw_access_token = self._credential.get("access_token", "")
        session.headers.update({"Authorization": f"Bearer {raw_access_token}"})
        return session

    def _validate(self, id_token: dict) -> bool:
        """
        Checks if the provided cookie is valid to consume a resource in
        the target web application.

        Args:
            access_token: OAuth2 access token retrieve from
                CERN Authentication service.
        """
        raw_access_token = id_token.get("access_token", "")
        test_response = requests.get(
            self._url, headers={"Authorization": f"Bearer {raw_access_token}"}
        )
        return self.validate_response(test_response)
