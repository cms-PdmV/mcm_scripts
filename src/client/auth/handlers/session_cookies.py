"""
This module provides a handler
to load a cookie from the filesystem.
"""

from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path

import requests
from requests.sessions import Session

from client.auth.auth_interface import AuthInterface
from utils.shell import run_command


class SessionCookieHandler(AuthInterface):
    """
    Loads a Netscape cookie from a file and configures
    a HTTP session to make use of it.

    Attributes:
        _url: Target web application URL.
        _credential: Session cookie loaded from a Netscape file.
    """

    def __init__(self, url: str, credential_path: Path):
        self._url = url
        self._credential_path = credential_path
        self._credential: MozillaCookieJar | None = None

    def _load_credential(self) -> MozillaCookieJar | None:
        try:
            cookie = MozillaCookieJar(self._credential_path)
            cookie.load()
            return cookie
        except LoadError:
            return None

    def _request_credential(self) -> MozillaCookieJar:
        # Request a session cookie using CERN internal packages.
        command = (
            f"auth-get-sso-cookie -u '{self._url}' -o '{str(self._credential_path)}'"
        )
        _, stderr, exit_code = run_command(command=command)

        # Most likely the package is not available or
        # there's no valid Kerberos ticket.
        if exit_code != 0:
            msg = (
                f"Session cookie requested via: '{command}'\n"
                f"Standard error: {stderr}\n"
            )
            raise RuntimeError(msg)

        # Load the cookie
        return self._load_credential()

    def _save_credential(self) -> None:
        # No operation is performed because `self.request_credential`
        # already saves the valid cookie
        ...

    def authenticate(self) -> None:
        loaded_cookie = self._load_credential()
        if self._validate(cookie=loaded_cookie):
            self._credential = loaded_cookie
            return

        # The credential is not valid anymore, renew it.
        renewed_cookie = self._request_credential()
        if self._validate(cookie=renewed_cookie):
            self._credential = renewed_cookie
            return

        # It is not possible to authenticate a request
        # using session cookies.
        msg = (
            "Unable to consume a resource in the target web application "
            "using session cookies. Remember this method only works if 2FA is not enabled. "
            "If you enforce it, please use another authentication strategy instead."
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

        # Intercepted and redirected to the authentication page.
        if test_response.url.startswith(
            "https://auth.cern.ch/auth/realms/cern"
        ) or test_response.status_code in (401, 403):
            return False

        return True
