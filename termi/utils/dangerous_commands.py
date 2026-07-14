from __future__ import annotations

import re
from dataclasses import dataclass


_DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\s+/(\s|$)"),
        "Recursive force-delete of root filesystem",
    ),
    (re.compile(r"\brm\s+-rf\s+~"), "Recursive force-delete of home directory"),
    (re.compile(r"\brm\s+-rf\s+\*"), "Recursive force-delete using a wildcard"),
    (re.compile(r"\bmkfs(\.\w+)?\b"), "Formats a filesystem, destroying all data on it"),
    (re.compile(r"\bdd\s+.*of=/dev/"), "Writes raw data directly to a block device"),
    (re.compile(r">\s*/dev/sd[a-z]"), "Overwrites a raw disk device"),
    (re.compile(r"\bshutdown\b"), "Shuts down the system"),
    (re.compile(r"\breboot\b"), "Reboots the system"),
    (re.compile(r"\bhalt\b"), "Halts the system"),
    (re.compile(r":\(\)\s*\{\s*:\|\s*:&\s*\};\s*:"), "Fork bomb"),
    (re.compile(r"\bchmod\s+-R\s+000\b"), "Recursively removes all permissions"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/"), "Recursively opens permissions on the root filesystem"),
    (
        re.compile(r"\bchown\s+-R\b.*\s+/(\s|$)"),
        "Recursively changes ownership of the root filesystem",
    ),
    (re.compile(r"\bdel\s+/[sqf]\b", re.IGNORECASE), "Windows recursive/forced delete"),
    (re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE), "Formats a Windows drive"),
    (re.compile(r"remove-item\s+.*-recurse", re.IGNORECASE), "PowerShell recursive delete"),
    (re.compile(r"\bdrop\s+(table|database)\b", re.IGNORECASE), "Destructive SQL statement"),
    (re.compile(r"\bgit\s+push\s+.*--force\b"), "Force push may overwrite remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "Hard reset discards local changes irreversibly"),
    (re.compile(r"\bgit\s+clean\s+-\w*f\w*d\b"), "Force-deletes untracked files and directories"),
    (re.compile(r"\bkill\s+-9\s+-?1\b"), "Kills every process the user owns"),
    (re.compile(r"curl.*\|\s*(sudo\s+)?(bash|sh)\b"), "Pipes remote content directly into a shell"),
    (re.compile(r"wget.*\|\s*(sudo\s+)?(bash|sh)\b"), "Pipes remote content directly into a shell"),
]


@dataclass(frozen=True)
class DangerAssessment:

    is_dangerous: bool
    reasons: list[str]

    def __bool__(self) -> bool:  
        return self.is_dangerous


def assess_command(command: str) -> DangerAssessment:
    reasons = [
        description for pattern, description in _DANGEROUS_PATTERNS if pattern.search(command)
    ]
    return DangerAssessment(is_dangerous=bool(reasons), reasons=reasons)


def is_dangerous(command: str) -> bool:
    return assess_command(command).is_dangerous
