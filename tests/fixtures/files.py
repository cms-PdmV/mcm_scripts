import os
import tempfile
from pathlib import Path

import pytest
import json


def create_empty_file(permissions) -> Path:
    """
    Creates an empty writable file.

    Returns:
        Path: Temporal file path
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_name = Path(temp_file.name)
    temp_file.close()
    os.chmod(temp_file_name, permissions)
    return temp_file_name


@pytest.fixture
def read_only_file() -> Path:
    """
    Creates a temporal file with read only permissions.

    Returns:
        Path: Temporal file path
    """
    return create_empty_file(0o400)


@pytest.fixture
def empty_json_file() -> Path:
    """
    Creates a temporal file with an empty JSON object.

    Returns:
        Path: Temporal file path
    """
    temp_file_name = create_empty_file(0o700)
    with open(file=temp_file_name, mode="w") as f:
        json.dump(obj={}, fp=f)
    return temp_file_name
