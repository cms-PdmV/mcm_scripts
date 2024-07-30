"""
REST client default structure.
This sets the default schema for creating a HTTP client
object for PdmV applications.
"""

import os
import warnings
from pathlib import Path
from typing import Union

import requests

from rest.client.session import SessionFactory
from rest.utils.logger import LoggerFactory
from rest.utils.shell import describe_platform


class BaseClient:
    """
    Configures the internal HTTP client session.
    """

    # Authentication mechanisms
    SSO = "sso"
    OIDC = "oidc"
    OAUTH = "oauth2"
    COOKIE_ENV_VAR = "PDMV_COOKIE_PATH"

    def __init__(
        self,
        app: str,
        id: str = SSO,
        debug: bool = False,
        cookie: Union[str, None] = None,
        dev: bool = True,
        client_id: str = "",
        client_secret: str = "",
    ):
        """
        Initializes the HTTP client session configuring the
        authentication approach and the logger.

        Arguments:
            app: PdmV application's endpoint. This is used to
                construct the target URL.

            id: The authentication mechanism to use. Supported values are:
                'sso': Request Session cookies via CERN 'auth-get-sso-cookie'
                    package. This approach does not work if the user's account
                    enforces 2FA. Make sure to provide a Kerberos ticket to consume
                    CERN resources in your runtime environment.
                'oidc': Request an ID token via Device Authorization Grant to consume
                    resources. This requires human input to complete the flow.
                'oauth': Request an Access token via Client Credentials Grant to consume
                    resources. This requires the user to provide the `client_id` and `client_secret`
                    to requests tokens. Please see the `API Access` tutorial in CERN
                    Authentication docs for more details.

                Otherwise, the HTTP session will be configured with no credentials.

            debug: Logger's level.
            cookie: The target path to store/load the credential. This is a legacy
                argument from the old McM REST client. To keep compatibility, the name
                of the argument remains the same.
            dev: Whether to use the dev or production instance.
            client_id: This is an optional argument only used if `id = OAUTH`, this
                is the client ID for requesting an access token.
            client_secret: This is an optional argument only used if `id = OAUTH`, this
                is the client secret for requesting an access token.
        """
        self._app = app
        self._id = id
        self._debug = debug
        self._cookie = cookie
        self._dev = dev
        self._client_id = client_id
        self._client_secret = client_secret
        
        self.logger = LoggerFactory.getLogger(f"pdmv-http-client.{self._app}")
        self.credentials_path = self._credentials_path()
        self.server = self._target_web_application()
        self.credentials_path = self._credentials_path()
        self.session = self._create_session()

    def _target_web_application(self) -> str:
        """
        Sets the production or development web application URL.
        """
        if self._dev:
            return f"https://cms-pdmv-dev.web.cern.ch/{self._app}/"

        return f"https://cms-pdmv-prod.web.cern.ch/{self._app}/"

    def _credential_name(self) -> str:
        """
        Provides the credential's file name.
        """
        suffix = "credential-dev" if self._dev else "credential-prod"
        prefix = self._app
        return f"{prefix}-{suffix}"

    def _credentials_path(self) -> Path:
        """
        Sets the path from which credentials are going to be loaded and saved.
        """
        # If a path is provided in the `cookie` argument, use it.
        if self._cookie:
            self.logger.info(
                "Settting the credential's path (%s) as provided in arguments",
                self._cookie,
            )
            return Path(self._cookie)

        # If the user attempts to force the `cookie` argument
        # via runtime variables, use it.
        from_env_var = os.getenv(self.COOKIE_ENV_VAR)
        if from_env_var:
            self.logger.info(
                "Settting the credential's path (%s) from environment variables",
                from_env_var,
            )
            return Path(from_env_var)

        # Otherwise, use a `private` folder in the user's home
        # to create the credential.
        private_folder = Path.home() / Path("private")
        private_folder.mkdir(mode=0o700, exist_ok=True)
        path = private_folder / Path(self._credential_name())
        self.logger.info("Setting default credential's path (%s)", path)

        return path

    def _create_session(self) -> requests.Session:
        """
        Configures the HTTP session depending on the chosen authentication method.
        """
        session: Union[requests.Session, None] = None
        if self._id == self.SSO:
            session = SessionFactory.configure_by_session_cookie(
                url=self.server, credential_path=self.credentials_path
            )
        elif self._id == self.OIDC:
            target_application = "cms-ppd-pdmv-device-flow"
            session = SessionFactory.configure_by_id_token(
                url=self.server,
                credential_path=self.credentials_path,
                target_application=target_application,
            )
        elif self._id == self.OAUTH:
            target_application = "cms-ppd-pdmv-dev" if self._dev else "cms-ppd-pdmv"
            session = SessionFactory.configure_by_access_token(
                url=self.server,
                credential_path=self.credentials_path,
                target_application=target_application,
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
        else:
            self.logger.warning("Using HTTP client without providing authentication")
            session = requests.Session()

        # Include some headers for the session
        user_agent = {
            "User-Agent": f"PdmV HTTP client (For: {self._app}): {describe_platform()}"
        }
        session.headers.update(user_agent)
        return session

    def __repr__(self):
        return f"<HTTP client (For: {self._app}) id: {self._id} server: {self.server} cookie: {self._cookie}>"

    def __get(self, url):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._get(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._get(url=url)

    def __put(self, url, data):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._put(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._put(url=url, data=data)

    def __post(self, url, data):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._post(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._post(url=url, data=data)

    def __delete(self, url):
        warnings.warn(
            "This name mangled method will be removed in the future, use self._delete(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._delete(url=url)

    def _get(self, url: str) -> dict:
        """
        Performs a GET request to the target resource.
        This assumes the target resource's response format is JSON.

        Args:
            url: Resource URL. Do not include a slash at the beginning.
                For example: restapi/requests/get/B2G-Run3Summer22wmLHEGS-00033.

        Returns:
            Target resource response.
        """
        full_url = f"{self.server}{url}"
        response = self.session.get(url=full_url)
        return response.json()

    def _put(self, url: str, data: dict) -> dict:
        """
        Performs a PUT request to the target resource.
        This assumes the target resource's response format is JSON.

        Args:
            url: Resource URL. Do not include a slash at the beginning.
                For example: restapi/requests/get/B2G-Run3Summer22wmLHEGS-00033.
            data: Request's body.

        Returns:
            Target resource response.
        """
        full_url = f"{self.server}{url}"
        response = self.session.put(url=full_url, json=data)
        return response.json()

    def _post(self, url: str, data: dict) -> dict:
        """
        Performs a POST request to the target resource.
        This assumes the target resource's response format is JSON.

        Args:
            url: Resource URL. Do not include a slash at the beginning.
                For example: restapi/requests/get/B2G-Run3Summer22wmLHEGS-00033.
            data: Request's body.

        Returns:
            Target resource response.
        """
        full_url = f"{self.server}{url}"
        response = self.session.post(url=full_url, json=data)
        return response.json()

    def _delete(self, url: str) -> dict:
        """
        Performs a DELETE request to the target resource.
        This assumes the target resource's response format is JSON.

        Args:
            url: Resource URL. Do not include a slash at the beginning.
                For example: restapi/requests/get/B2G-Run3Summer22wmLHEGS-00033.

        Returns:
            Target resource response.
        """
        full_url = f"{self.server}{url}"
        response = self.session.delete(url=full_url)
        return response.json()
