"""
This module provides a handler
to authenticate requests using OAuth2 tokens.
"""

from pathlib import Path

import requests
from requests.sessions import Session

from client.auth.auth_interface import AuthInterface


class AccessTokenHandler(AuthInterface):
    # TODO: Implement a handler to load and retrieve access tokens by
    # client credentials grant.
    pass


class IDTokenHandler(AuthInterface):
    # TODO: Implement a handler to load and retrieve id tokens by
    # device authorization grant.
    pass
