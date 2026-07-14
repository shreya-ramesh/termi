from __future__ import annotations

import getpass
import os
import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemContext:

    os_name: str
    os_version: str
    shell: str
    cwd: str
    username: str

    def as_prompt_context(self) -> str:
        return (
            f"Operating System: {self.os_name} ({self.os_version})\n"
            f"Shell: {self.shell}\n"
            f"Current Directory: {self.cwd}\n"
            f"Username: {self.username}"
        )


def detect_os() -> str:
    return platform.system()


def detect_shell(override: str | None = None) -> str:
    if override:
        return override.lower()

    system = platform.system()

    if system == "Windows":
        # PSModulePath is only set inside PowerShell sessions.
        if os.environ.get("PSModulePath"):  # noqa: SIM112 - real Windows env var name
            return "powershell"
        return "cmd"

    shell_path = os.environ.get("SHELL", "")
    shell_name = os.path.basename(shell_path) if shell_path else ""

    if shell_name in {"bash", "zsh", "fish", "sh", "ksh", "csh", "tcsh"}:
        return shell_name

    # Fall back to a sane default per platform.
    return "zsh" if system == "Darwin" else "bash"


def get_system_context(shell_override: str | None = None) -> SystemContext:
    try:
        username = getpass.getuser()
    except Exception:  # noqa: BLE001 - getpass can fail in odd environments
        username = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    return SystemContext(
        os_name=detect_os(),
        os_version=platform.release(),
        shell=detect_shell(shell_override),
        cwd=os.getcwd(),
        username=username,
    )
