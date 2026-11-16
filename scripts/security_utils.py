"""
Centralized Security, Input Validation, and Redaction Utilities.

Zero-dependency standard-library helpers shared across scanner, clusterer,
knowledge base generator, dashboard generator, query engine, and CLI.
"""

import hashlib
import ipaddress
import json
import os
import re
import urllib.parse
from typing import Any, Iterable, Optional

MAX_CONFIG_BYTES = 1 * 1024 * 1024      # 1 MB
MAX_JSON_DATA_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_REGEX_LENGTH = 256

# ANSI CSI / OSC / single-char escape sequences
_ANSI_ESCAPE_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])"
)
_CONTROL_CHARS_NO_NL_RE = re.compile(r"[\x00-\x1f\x7f]")
_CONTROL_CHARS_KEEP_NL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Known credential / secret token patterns for log redaction
_SECRET_PATTERNS = [
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bsk-proj-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bsk-(?:live|test|)[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bya29\.[0-9A-Za-z_-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[bpas]-[0-9A-Za-z-]{10,}\b"),
    re.compile(r"\b(?:SG|glpat|npm|hf)_[0-9A-Za-z._-]{10,}\b"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+|token\s+)?[^\s,;'\"]+",),
    re.compile(r"(?i)\b(bearer|token)\s+[A-Za-z0-9._~+/=-]{8,}"),
]

# Heuristic detector for nested quantifiers / catastrophic backtracking patterns
_NESTED_QUANTIFIER_RE = re.compile(
    r"\([^)]*(?:\+|\*|\{\d*,\d*\})[^)]*\)\s*(?:\+|\*|\{\d*,\d*\})"
)
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

_PLACEHOLDER_TOKEN_PATTERNS = [
    re.compile(r"^YOUR_.*TOKEN", re.IGNORECASE),
    re.compile(r"^<YOUR_.*>$", re.IGNORECASE),
    re.compile(r"^REPLACE_ME", re.IGNORECASE),
    re.compile(r"^ghp_x+$", re.IGNORECASE),
    re.compile(r"^ghp_your", re.IGNORECASE),
]

# Protected OS / credential directories that generated artifacts must never target
_PROTECTED_SYSTEM_DIRS = (
    "/etc",
    "/bin",
    "/sbin",
    "/boot",
    "/proc",
    "/sys",
    "/dev",
    "/root",
    "/usr/bin",
    "/usr/sbin",
    "/usr/lib",
    "/usr/etc",
    "/var/run",
)


def is_placeholder_token(token: Optional[str]) -> bool:
    """Return True if a token value is empty or an unedited documentation placeholder."""
    if not token or not isinstance(token, str):
        return True
    cleaned = token.strip()
    if not cleaned:
        return True
    return any(p.search(cleaned) for p in _PLACEHOLDER_TOKEN_PATTERNS)


def redact_secrets(text: Any, extra_secrets: Iterable[Optional[str]] = ()) -> str:
    """Scrub known secret patterns and explicit runtime credentials from log/error text."""
    result = str(text)
    for secret in extra_secrets:
        if isinstance(secret, str) and len(secret) >= 4 and not is_placeholder_token(secret):
            result = result.replace(secret, "[REDACTED]")
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            result = pattern.sub(r"\1[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED]", result)
    return result


def strip_control_chars(text: Any, allow_newlines: bool = False) -> str:
    """Remove ANSI escape sequences and non-printable ASCII control characters."""
    if text is None:
        return ""
    cleaned = _ANSI_ESCAPE_RE.sub("", str(text))
    if allow_newlines:
        return _CONTROL_CHARS_KEEP_NL_RE.sub("", cleaned)
    return _CONTROL_CHARS_NO_NL_RE.sub(" ", cleaned)


def sanitize_http_url(url: Any, default: str = "#") -> str:
    """Validate that a URL uses http:// or https:// with a non-empty host; otherwise return default."""
    if not isinstance(url, str):
        return default
    cleaned = url.strip()
    if not cleaned or any(ch in cleaned for ch in ("\r", "\n", "\x00", "\t")):
        return default
    try:
        parsed = urllib.parse.urlsplit(cleaned)
    except ValueError:
        return default
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return default
    return cleaned


def sanitize_hex_color(color: Any, default: str = "#3B82F6") -> str:
    """Allow only strict 3- or 6-digit hexadecimal color codes."""
    if isinstance(color, str) and _HEX_COLOR_RE.match(color.strip()):
        return color.strip()
    return default


def _is_within(path_real: str, dir_real: str) -> bool:
    try:
        return os.path.commonpath([dir_real, path_real]) == dir_real
    except ValueError:
        return False


def validate_path_safe(
    path: str,
    base_dir: Optional[str] = None,
    must_be_within_base: bool = False,
    for_write: bool = False,
) -> str:
    """
    Validate a filesystem path against NUL injection, traversal escapes,
    symlink targets, and protected OS directories.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Path must be a non-empty string.")
    if "\x00" in path:
        raise ValueError("Path contains invalid NUL byte.")

    raw_path = path.strip()
    if base_dir is not None and not os.path.isabs(raw_path):
        candidate = os.path.join(base_dir, raw_path)
    else:
        candidate = raw_path

    real_candidate = os.path.realpath(candidate)

    if must_be_within_base:
        effective_base = os.path.realpath(base_dir or os.getcwd())
        if not _is_within(real_candidate, effective_base):
            raise ValueError(
                f"Path '{raw_path}' escapes allowed base directory '{effective_base}'."
            )

    if for_write:
        if os.path.islink(candidate):
            raise ValueError(f"Refusing to write to symlink path: '{raw_path}'.")

        home_dir = os.path.expanduser("~")
        sensitive_dirs = list(_PROTECTED_SYSTEM_DIRS) + [
            os.path.join(home_dir, ".ssh"),
            os.path.join(home_dir, ".gnupg"),
            os.path.join(home_dir, ".config", "gh"),
        ]
        for protected in sensitive_dirs:
            real_protected = os.path.realpath(protected)
            if _is_within(real_candidate, real_protected):
                raise ValueError(
                    f"Refusing to write into protected system/credential directory: '{raw_path}'."
                )

    return candidate


def assert_not_symlink_file(file_path: str) -> None:
    """Raise ValueError if a specific target file is a symbolic link."""
    if os.path.islink(file_path):
        raise ValueError(f"Refusing to overwrite symlink file: '{file_path}'.")


def load_json_limited(path: str, max_bytes: int = MAX_JSON_DATA_BYTES) -> Any:
    """Safely load a UTF-8 JSON file after enforcing existence and a strict byte-size limit."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    size = os.path.getsize(path)
    if size > max_bytes:
        raise ValueError(
            f"JSON file '{os.path.basename(path)}' exceeds maximum allowed size "
            f"({size} bytes > {max_bytes} bytes)."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_safe_regex(pattern: Any, max_len: int = MAX_REGEX_LENGTH) -> Optional[re.Pattern]:
    """
    Validate and pre-compile a user-supplied regex pattern.
    Rejects overly long patterns, nested-quantifier ReDoS constructs, and invalid syntax.
    """
    if not isinstance(pattern, str):
        return None
    if not pattern or len(pattern) > max_len:
        return None
    if _NESTED_QUANTIFIER_RE.search(pattern):
        return None
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def deterministic_id(key: str, modulo: int = 10_000_000) -> int:
    """Compute a deterministic, cross-process stable integer ID using SHA-256."""
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % modulo


def is_public_ip(ip_str: str) -> bool:
    """Return True only if ip_str parses to a globally routable public IP address."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return bool(
        addr.is_global
        and not addr.is_private
        and not addr.is_loopback
        and not addr.is_link_local
        and not addr.is_multicast
        and not addr.is_reserved
        and not addr.is_unspecified
    )
