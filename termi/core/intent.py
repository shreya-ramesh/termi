from __future__ import annotations

import re

from termi.utils.exceptions import IntentError

_CODE_FENCE_RE = re.compile(r"^```(?:[a-zA-Z]*)\n?(.*?)```$", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"^`([^`]+)`$")
_LEADING_PROMPT_RE = re.compile(r"^\s*[$#>]\s+")


def extract_command(raw_text: str) -> str:
   
    if raw_text is None:
        raise IntentError("Received no output from the model.")

    text = raw_text.strip()
    if not text:
        raise IntentError("Model returned an empty response.")

    fence_match = _CODE_FENCE_RE.match(text)
    if fence_match:
        text = fence_match.group(1).strip()

    inline_match = _INLINE_CODE_RE.match(text)
    if inline_match:
        text = inline_match.group(1).strip()

    
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise IntentError("Model returned an empty response after cleaning.")

    command_lines = [line for line in lines if not line.strip().startswith("#")]
    command = command_lines[-1] if command_lines else lines[-1]

    command = _LEADING_PROMPT_RE.sub("", command).strip()

    if not command:
        raise IntentError("Could not extract a command from the model's response.")

    return command


def build_command_system_prompt(system_context: str) -> str:
    
    return (
        "You are Termi, an expert terminal assistant. Convert the user's "
        "natural language request into a single, correct, directly "
        "executable shell command for their environment.\n\n"
        f"{system_context}\n\n"
        "Rules:\n"
        "- Respond with ONLY the shell command, nothing else.\n"
        "- Do not use markdown code fences.\n"
        "- Do not add explanations, comments, or a leading '$' prompt.\n"
        "- Use syntax appropriate for the detected shell and operating system.\n"
        "- Use previous turns in the conversation to resolve context such as "
        "'it', 'that folder', or 'go inside it'.\n"
        "- If a request is ambiguous, choose the most common, safe interpretation."
    )
