"""
Some fixtures to test the McM REST client.
"""

import pytest
from fixtures.oauth import stdin_enabled

from rest.applications.mcm.core import McM
from rest.applications.mcm.invalidate_request import InvalidateDeleteRequests
from rest.utils.miscellaneous import shuffle_pick


@pytest.fixture
def mcm_development() -> McM:
    return McM(id=McM.OIDC, dev=True)


@pytest.fixture
def invalidator_development(mcm_development: McM) -> InvalidateDeleteRequests:
    return InvalidateDeleteRequests(mcm=mcm_development)


@pytest.fixture
def root_request(mcm_development: McM) -> list[str]:
    """
    Get some example requests to use in the tests.
    Return only its prepid. Request retrieve are related to
    Run3Summer22*GS* campaigns and its status is `done`.

    Raises an error if it is not possible to retrieve
    this test set.
    """
    samples = mcm_development.get(
        object_type="requests",
        query="prepid=*Run3Summer22*GS*&status=done",
        page=2,
    )
    assert isinstance(samples, list)
    return shuffle_pick(samples, size=5, attribute="prepid")


@pytest.fixture
def non_root_requests(mcm_development: McM) -> list[str]:
    """
    Retrieve a list of 5 non-root requests. The list only
    contains request's prepids related to Run3Summer22 campaign.
    """
    samples = []
    for pattern in ("MiniAOD", "NanoAOD", "DR"):
        samples_pattern = mcm_development.get(
            object_type="requests",
            query=f"prepid=*Run3Summer22*{pattern}*&status=done",
            page=2,
        )
        assert isinstance(samples_pattern, list)
        samples += samples_pattern

    return shuffle_pick(samples, size=5, attribute="prepid")


@pytest.fixture
def production_manager_or_higher(mcm_development: McM) -> None:
    """
    Checks if the current user has production_manager or administrator
    permissions.
    """
    user_permissions: dict = mcm_development._get(url="restapi/users/get_role")
    accepted_roles = ("production_manager", "administrator")
    current_role: str = user_permissions.get("role", "")
    username: str = user_permissions.get("username", "")

    if current_role not in accepted_roles:
        pytest.skip(
            f"User ({username}) with role ({current_role}) does not have the right permissions to execute this. Expected: {accepted_roles}"
        )
