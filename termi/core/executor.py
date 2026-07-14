from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from termi.core.system import detect_shell
from termi.utils.exceptions import ExecutionError
from termi.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 120
_CD_PATTERN = re.compile(r"^\s*cd\s+(.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class ExecutionResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    succeeded: bool
    timed_out: bool = False


class CommandExecutor:
   
    def __init__(
        self, shell: str | None = None, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS
    ) -> None:
        """Args:
        shell: Shell identifier (e.g. "bash", "powershell", "cmd"). If
            omitted, it is auto-detected.
        timeout_seconds: Maximum seconds to allow a command to run
            before it is forcibly terminated.
        """
        self.shell = shell or detect_shell()
        self.timeout_seconds = timeout_seconds
        self.current_directory: str = os.getcwd()

    def _build_invocation(self, command: str) -> list[str]:
        if self.shell == "powershell":
            return ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
        if self.shell == "cmd":
            return ["cmd", "/c", command]
        shell_bin = self.shell if self.shell in {"bash", "zsh", "fish", "sh"} else "sh"
        return [shell_bin, "-c", command]

    @staticmethod
    def _unquote(path_text: str) -> str:
       
        if len(path_text) >= 2 and path_text[0] == path_text[-1] and path_text[0] in "\"'":
            return path_text[1:-1]
        return path_text

    def _resolve_target_directory(self, raw_target: str) -> str:
        
        target = self._unquote(raw_target.strip())
        expanded = os.path.expanduser(target)

        candidate = Path(expanded)
        if not candidate.is_absolute():
            candidate = Path(self.current_directory) / candidate

        return str(candidate.resolve(strict=False))

    def _execute_cd(self, command: str, raw_target: str) -> ExecutionResult:
        
        logger.info("Handling cd command: %s (shell=%s)", command, self.shell)

        resolved = self._resolve_target_directory(raw_target)

        if not os.path.isdir(resolved):
            logger.warning("cd target does not exist: %s", resolved)
            return ExecutionResult(
                command=command,
                stdout="",
                stderr="Directory does not exist",
                exit_code=1,
                succeeded=False,
            )

        self.current_directory = resolved
        logger.debug("Working directory updated to: %s", self.current_directory)

        return ExecutionResult(
            command=command,
            stdout="",
            stderr="",
            exit_code=0,
            succeeded=True,
        )

    def execute(self, command: str) -> ExecutionResult:
        
        cd_match = _CD_PATTERN.match(command)
        if cd_match:
            return self._execute_cd(command, cd_match.group(1))

        argv = self._build_invocation(command)
        logger.info(
            "Executing command: %s (shell=%s, cwd=%s)",
            command,
            self.shell,
            self.current_directory,
        )

        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=self.current_directory,
            )
        except subprocess.TimeoutExpired as exc:
            logger.warning("Command timed out after %ss: %s", self.timeout_seconds, command)
            return ExecutionResult(
                command=command,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "")
                + f"\n[Termi] Command timed out after {self.timeout_seconds}s.",
                exit_code=-1,
                succeeded=False,
                timed_out=True,
            )
        except (FileNotFoundError, OSError) as exc:
            raise ExecutionError(f"Failed to launch shell '{self.shell}': {exc}") from exc

        result = ExecutionResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            succeeded=completed.returncode == 0,
        )
        logger.debug("Command finished with exit_code=%s", result.exit_code)
        return result