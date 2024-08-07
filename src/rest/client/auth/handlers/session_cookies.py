"""
This module provides a handler
to load a cookie from the file system.
"""

import os
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path
from typing import Union

import requests
from requests.sessions import Session

from rest.client.auth.auth_interface import AuthInterface
from rest.utils.logger import LoggerFactory
from rest.utils.shell import run_command


class SessionCookieHandler(AuthInterface):
    """
    Loads a Netscape cookie from a file and configures
    an HTTP session to make use of it.

    Attributes:
        _url: Target web application URL.
        _credential: Session cookie loaded from a Netscape file.
    """

    def __init__(self, url: str, credential_path: Path):
        self._url = url
        self._credential_path = credential_path
        self._credential: Union[MozillaCookieJar, None] = None
        self._logger = LoggerFactory.getLogger("pdmv-http-client.client")

    def _load_credential(self) -> Union[MozillaCookieJar, None]:
        try:
            cookie = MozillaCookieJar(self._credential_path)
            cookie.load()
            return cookie
        except (LoadError, OSError):
            return None

    def _request_credential(self) -> MozillaCookieJar:
        # Remove the cookie file in case there's available
        self._credential_path.unlink(missing_ok=True)

        # Request a session cookie using CERN internal packages.
        command = (
            f"auth-get-sso-cookie -u '{self._url}' -o '{str(self._credential_path)}'"
        )
        _, stderr, exit_code = run_command(command=command)

        # Most likely the package is not available or
        # there's no valid Kerberos ticket.
        if exit_code != 0 or stderr:
            msg = (
                f"Session cookie requested via: '{command}'\n"
                f"Standard error: {stderr}\n"
            )
            raise RuntimeError(msg)

        # Load the cookie
        return self._load_credential()

    def _save_credential(self) -> None:
        # Credential is already stored, just change its permissions.
        os.chmod(path=self._credential_path, mode=0o600)

    def authenticate(self) -> None:
        loaded_cookie = self._load_credential()
        if self._validate(cookie=loaded_cookie):
            self._credential = loaded_cookie
            self._save_credential()
            return

        # The credential is not valid anymore, renew it.
        self._logger.debug("Session cookie is not valid, requesting a new one")
        renewed_cookie = self._request_credential()
        if self._validate(cookie=renewed_cookie):
            self._credential = renewed_cookie
            self._save_credential()
            return

        # It is not possible to authenticate a request
        # using session cookies.
        msg = (
            f"Unable to consume a resource in the target web application ({self._url}) "
            "using session cookies.\n"
            "Remember this method only works if 2FA is not enabled.\n"
            "Please use another authentication strategy instead."
        )
        raise PermissionError(msg)

    def configure(self, session: Session) -> Session:
        if not self._credential:
            self.authenticate()

        session.cookies.update(self._credential)
        return session

    def _validate(self, cookie: MozillaCookieJar) -> bool:
        """
        Checks if the provided cookie is valid to consume a resource in
        the target web application.

        Args:
            cookie: Cookie to check.
        """
        test_response = requests.get(self._url, cookies=cookie)
        return self.validate_response(test_response)
