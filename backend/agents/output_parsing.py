"""
Shared helpers for parsing and normalizing LLM agent output.
Every agent runs its raw model response through these so that downstream
consumers (risk scoring, DB persistence, PR comments) see consistent values.
"""

import json
import re
from typing import Any

VALID_SEVERITIES = ("critical", "high", "medium", "low")
DEFAULT_SEVERITY = "medium"

# Postgres INTEGER upper bound — larger values would fail the DB insert
_MAX_LINE_NUMBER = 2_147_483_647
_MAX_FILE_PATH_LENGTH = 500
_FIRST_INT = re.compile(r"\d+")


def extract_text(content: Any) -> str:
    """Return the text of an LLM response, which may be a string or a list of content parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type", "text") == "text":
                parts.append(str(part.get("text", "")))
        return "".join(parts)
    return str(content)


def parse_json_object(content: Any) -> dict[str, Any]:
    """
    Parse a JSON object from raw LLM output.
    Tolerates markdown code fences and prose around the object.
    Raises ValueError (or its subclass json.JSONDecodeError) if no object can be parsed.
    """
    text = extract_text(content).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("No JSON object found in model response")
    return json.loads(text[start:end + 1])


def normalize_severity(value: Any) -> str:
    """Map a model-supplied severity onto one of VALID_SEVERITIES (case-insensitive)."""
    if isinstance(value, str):
        severity = value.strip().lower()
        if severity in VALID_SEVERITIES:
            return severity
    return DEFAULT_SEVERITY


def coerce_line_number(value: Any) -> int | None:
    """
    Coerce a model-supplied line number to a positive int, or None.
    Accepts ints, floats and strings such as "12" or "12-14" (first number wins).
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        value = int(value)
    if isinstance(value, str):
        match = _FIRST_INT.search(value)
        value = int(match.group()) if match else None
    if isinstance(value, int) and 0 < value <= _MAX_LINE_NUMBER:
        return value
    return None


def _as_text(value: Any) -> str | None:
    """Return a stripped string for non-empty values, else None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_issue(
    issue: Any,
    default_description: str,
    default_suggestion: str,
) -> dict[str, Any] | None:
    """
    Normalize a single issue dict from model output.
    Returns None if the entry is not a dict and should be dropped.
    """
    if not isinstance(issue, dict):
        return None

    file_path = _as_text(issue.get("file_path"))
    return {
        "severity": normalize_severity(issue.get("severity")),
        "description": _as_text(issue.get("description")) or default_description,
        "line_number": coerce_line_number(issue.get("line_number")),
        "file_path": file_path[:_MAX_FILE_PATH_LENGTH] if file_path else None,
        "suggestion": _as_text(issue.get("suggestion")) or default_suggestion,
    }
