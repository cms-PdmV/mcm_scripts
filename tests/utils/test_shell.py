"""
Provides some tests for the module
`src/rest/utils/shell.py` to verify its
correctness.
"""

import getpass

import rest.utils.shell as sh


def test_run_command() -> None:
    # 1. Success execution.
    current_user = getpass.getuser()
    stdout, stderr, exit_code = sh.run_command(command="whoami")
    assert current_user == stdout.strip()
    assert stderr == ""
    assert exit_code == 0

    # 2. Fail execution.
    stdout, stderr, exit_code = sh.run_command(command="notexists")
    assert stdout == ""
    assert "command not found" in stderr
    assert exit_code != 0
