from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import metadata

from termi.core.system import SystemContext

SYSTEM_INFO_TRIGGERS: frozenset[str] = frozenset(
    {
        # Shell
        "which shell is this",
        "what shell am i using",
        "current shell",
        # OS
        "which os is this",
        "what operating system am i using",
        "current os",
        # Current directory
        "where am i",
        "current directory",
        "pwd",
        "current working directory",
        # Provider
        "what provider am i using",
        "current provider",
        # Model
        "which model am i using",
        "current model",
        # Version
        "version",
        "termi version",
    }
)

_TRAILING_PUNCTUATION_RE = re.compile(r"[?!.\s]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    lowered = text.strip().lower()
    lowered = _TRAILING_PUNCTUATION_RE.sub("", lowered)
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def detect_system_info_query(prompt: str) -> bool:
    return _normalize(prompt) in SYSTEM_INFO_TRIGGERS


def get_version() -> str:
    try:
        return metadata.version("termi")
    except metadata.PackageNotFoundError:
        from termi import __version__

        return __version__


@dataclass(frozen=True)
class SystemInfoSnapshot:
    os_name: str
    shell: str
    cwd: str
    provider: str
    model: str
    version: str


def build_system_info_snapshot(
    system_context: SystemContext,
    cwd: str,
    provider: str,
    model: str,
) -> SystemInfoSnapshot:
    return SystemInfoSnapshot(
        os_name=system_context.os_name,
        shell=system_context.shell,
        cwd=cwd,
        provider=provider,
        model=model,
        version=get_version(),
    )