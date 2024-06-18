"""
Provides some pure-functions to interact with
the OS via shell executions.
"""

import platform
import subprocess
import sys


def run_command(
    command: str | list[str], env: dict[str, str] = {}
) -> tuple[str, str, int]:
    """
    Executes a command or a list of commands
    via shell.

    Args:
        command: Command to execute, in case a list
            is provided, the result command to execute will be
            concatenated.
        env: Environment variables for the process
            to spawn.

    Returns:
        tuple: Standard output, standard error and exit code.
    """
    full_command: str = ""

    if isinstance(command, list):
        full_command = ";".join(command)
    else:
        full_command = command

    result = subprocess.run(
        full_command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
    )
    stdout: str = result.stdout
    stderr: str = result.stderr
    exit_code: int = result.returncode
    return stdout, stderr, exit_code


def describe_platform() -> str:
    """
    Retrieves an identifier for describing the current
    execution environment. This is useful for including
    User-Agent headers.
    """
    version = sys.version_info
    python_version = f"{version.major}.{version.minor}.{version.micro}"
    return f"(Python: {python_version}) ({platform.system()}: {platform.machine()})"
