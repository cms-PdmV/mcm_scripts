"""
Configures a request HTTP session so that it handles authentication
to the web service automatically.
"""

from pathlib import Path
from typing import Union

import requests

from rest.client.auth.auth_interface import AuthInterface
from rest.client.auth.handlers.oauth2_tokens import AccessTokenHandler, IDTokenHandler
from rest.client.auth.handlers.session_cookies import SessionCookieHandler
from rest.utils.logger import LoggerFactory


class AuthenticatedSession(requests.Session):
    def __init__(self, handler: AuthInterface) -> None:
        super().__init__()
        self._handler = handler
        self._max_attempts = 3
        self._handler.configure(session=self)
        self._logger = LoggerFactory.getLogger("pdmv-http-client.client")

    def request(
        self, method: Union[str, bytes], url: Union[str, bytes], *args, **kwargs
    ) -> requests.Response:
        response = super().request(method, url, *args, **kwargs)
        for attempt in enumerate(range(self._max_attempts), start=1):
            if self._handler.validate_response(response):
                return response
            else:
                # Re-authenticate and return the response.
                self._logger.debug(
                    "(%s/%s) Credentials expired, renewing them and retrying the request",
                    attempt,
                    self._max_attempts,
                )
                self._handler.authenticate()
                self._handler.configure(session=self)
                response = super().request(method, url, *args, **kwargs)

        self._logger.warning(
            "Unable to renew credentials for (%s) after %s attempts: HTTP code %s",
            response.url,
            self._max_attempts,
            response.status_code,
        )
        return response


class SessionFactory:
    """
    Provides a pre-configured `request.Session` with the
    required authentication method.
    """

    @classmethod
    def configure_by_session_cookie(
        cls, url: str, credential_path: Path
    ) -> requests.Session:
        session_cookie_handler = SessionCookieHandler(
            url=url, credential_path=credential_path
        )
        return AuthenticatedSession(handler=session_cookie_handler)

    @classmethod
    def configure_by_access_token(
        cls,
        url: str,
        credential_path: Path,
        client_id: str,
        client_secret: str,
        target_application: str,
    ) -> requests.Session:
        access_token_handler = AccessTokenHandler(
            url=url,
            credential_path=credential_path,
            client_id=client_id,
            client_secret=client_secret,
            target_application=target_application,
        )
        return AuthenticatedSession(handler=access_token_handler)

    @classmethod
    def configure_by_id_token(
        cls,
        url: str,
        credential_path: Path,
        target_application: str,
    ) -> requests.Session:
        id_token_handler = IDTokenHandler(
            url=url,
            credential_path=credential_path,
            target_application=target_application,
        )
        return AuthenticatedSession(handler=id_token_handler)
