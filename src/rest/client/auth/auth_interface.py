"""
Main operations to load, save and renew credentials
for a HTTP client session.
"""

from abc import ABC, abstractmethod

from requests import Response, Session


class AuthInterface(ABC):
    """
    Defines the main operations to set a credential
    to authenticate and authorize HTTP requests targeting CERN
    web applications.

    For this context, a credential could be:
        - OAuth2 token: Requested via `Client Credentials` or `Device Authorization` grants.
            - Format: Json Web Tokens (JWT)
        - HTTP cookie: A cookie file requested using CERN internal packages.
            - Format: Netscape Cookie

    For more details, check the `handlers` module.
    """

    @abstractmethod
    def _load_credential(self):
        """
        Loads a credential from the given path.

        Returns:
            None: In case it was not possible to load a credential
                from the given path.
        """
        ...

    @abstractmethod
    def _request_credential(self):
        """
        Requests a credential to the CERN Auth service.

        Raises:
            PermissionError: If it is not possible to obtain a credential
                because the CERN Auth service refused the request.
            RuntimeError: Wrapper for any other possible error cause, the
                original exception must be chained with this one.
        """
        ...

    @abstractmethod
    def _save_credential(self) -> None:
        """
        Saves a valid credential in a file into the provided path.

        Raises:
            OSError: In case it is not possible to store the file
                in the provided path because lack of permissions to write
                in the destination.
        """
        ...

    @abstractmethod
    def authenticate(self) -> None:
        """
        Provides an entrypoint to automatically scan if it is possible
        to set credentials by picking them from default locations
        or requests them to the CERN Auth service. Also, this is useful
        for renewing credentials when they are expired.
        """
        ...

    @abstractmethod
    def configure(self, session: Session) -> Session:
        """
        Configures the given `request.Session` instance to set
        the credential to perform authenticated requests.
        """
        ...

    @classmethod
    def validate_response(cls, response: Response) -> bool:
        """
        Checks that a given response has been redirected to
        the CERN Authentication login server or been rejected by it
        server because a lack of permissions.

        Args:
            response: Response to check

        Returns:
            True: If the response was resolved by the requested web server
                and its status code is not 401 nor 403.
            False: If the response code was 401 or 403 or the resolver
                was the CERN Authentication service.
        """
        # Intercepted and redirected to the authentication page.
        if response.url.startswith(
            "https://auth.cern.ch/auth/realms/cern"
        ) or response.status_code in (401, 403):
            return False

        return True
