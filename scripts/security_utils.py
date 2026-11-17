"""
Centralized Security, Input Validation, and Redaction Utilities.

Zero-dependency standard-library helpers shared across scanner, clusterer,
knowledge base generator, dashboard generator, query engine, and CLI.
"""

import csv
import errno
import hashlib
import io
import ipaddress
import json
import os
import re
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional

MAX_CONFIG_BYTES = 1 * 1024 * 1024      # 1 MB
MAX_JSON_DATA_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_REGEX_LENGTH = 256
MAX_STRING_FIELD_LENGTH = 4096
MAX_TOPIC_ITEMS = 100

_ALLOWED_CONFIG_ROOT_KEYS = frozenset(
    {"target_url", "auth_token", "scan_options", "clustering_rules", "output"}
)
_ALLOWED_SCAN_OPTION_KEYS = frozenset(
    {"include_forks", "include_archived", "max_repos", "offline_fixture"}
)
_ALLOWED_OUTPUT_KEYS = frozenset(
    {"output_dir", "generate_dashboard", "generate_markdown", "generate_json"}
)
_ALLOWED_RULE_KEYS = frozenset(
    {"pattern", "cluster_id", "name", "description", "color"}
)

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
    re.compile(r"\bsk-(?:live-|test-|)?[A-Za-z0-9_-]{16,}\b"),
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


def write_text_safe(file_path: str, content: str) -> None:
    """Write UTF-8 text to file_path while atomically refusing symlink targets via O_NOFOLLOW."""
    assert_not_symlink_file(file_path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(file_path, flags, 0o644)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError(f"Refusing to overwrite symlink file: '{file_path}'.") from exc
        raise
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def validate_config_schema(data: Any) -> Dict[str, Any]:
    """Validate configuration JSON against strict allowed keys and expected value types."""
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object.")

    unknown_root = set(data.keys()) - _ALLOWED_CONFIG_ROOT_KEYS
    if unknown_root:
        raise ValueError(f"Undefined top-level configuration keys: {sorted(unknown_root)}")

    cleaned: Dict[str, Any] = dict(data)

    if "target_url" in cleaned and not isinstance(cleaned["target_url"], str):
        raise ValueError("'target_url' must be a string.")
    if "auth_token" in cleaned and not isinstance(cleaned["auth_token"], str):
        raise ValueError("'auth_token' must be a string.")

    if "scan_options" in cleaned:
        scan_opts = cleaned["scan_options"]
        if not isinstance(scan_opts, dict):
            raise ValueError("'scan_options' must be a JSON object.")
        unknown_scan = set(scan_opts.keys()) - _ALLOWED_SCAN_OPTION_KEYS
        if unknown_scan:
            raise ValueError(f"Undefined 'scan_options' keys: {sorted(unknown_scan)}")

    if "output" in cleaned:
        out_opts = cleaned["output"]
        if not isinstance(out_opts, dict):
            raise ValueError("'output' must be a JSON object.")
        unknown_out = set(out_opts.keys()) - _ALLOWED_OUTPUT_KEYS
        if unknown_out:
            raise ValueError(f"Undefined 'output' keys: {sorted(unknown_out)}")

    if "clustering_rules" in cleaned:
        rules = cleaned["clustering_rules"]
        if not isinstance(rules, list):
            raise ValueError("'clustering_rules' must be a list of rule objects.")
        validated_rules: List[Dict[str, Any]] = []
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Clustering rule at index {idx} must be an object.")
            unknown_rule = set(rule.keys()) - _ALLOWED_RULE_KEYS
            if unknown_rule:
                raise ValueError(
                    f"Undefined keys in clustering rule at index {idx}: {sorted(unknown_rule)}"
                )
            validated_rules.append(rule)
        cleaned["clustering_rules"] = validated_rules

    return cleaned


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


def _repo_belongs_to_user(repo: Dict[str, Any], user_lower: str) -> bool:
    """Return True if a normalized repository record belongs to user_lower."""
    full_name = str(repo.get("full_name") or "").lower()
    if full_name.startswith(user_lower + "/"):
        return True
    html_url = str(repo.get("html_url") or "").lower()
    for prefix in (
        f"https://github.com/{user_lower}/",
        f"http://github.com/{user_lower}/",
        f"https://www.github.com/{user_lower}/",
    ):
        if html_url.startswith(prefix):
            return True
    return False


def export_user_data(
    user_id: str,
    output_dir: str = "output",
    fmt: str = "json",
) -> Dict[str, Any]:
    """
    Export all stored repository records associated with a GitHub account handle
    in machine-readable JSON or CSV format (GDPR Art. 20 data portability).
    """
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty GitHub handle.")
    clean_uid = strip_control_chars(user_id).strip()
    if not clean_uid:
        raise ValueError("user_id must be a non-empty GitHub handle.")

    fmt_lower = (fmt or "json").strip().lower()
    if fmt_lower not in ("json", "csv"):
        raise ValueError("Export format must be 'json' or 'csv'.")

    safe_dir = validate_path_safe(output_dir, for_write=False)
    kb_path = os.path.join(safe_dir, "knowledge_base.json")
    if not os.path.isfile(kb_path):
        return {
            "user_id": clean_uid,
            "matched_owner": False,
            "record_count": 0,
            "metadata": {},
            "records": [],
            "format": fmt_lower,
            "serialized": "[]" if fmt_lower == "json" else "",
        }

    kb_data = load_json_limited(kb_path, max_bytes=MAX_JSON_DATA_BYTES)
    if not isinstance(kb_data, dict):
        raise ValueError("Knowledge base JSON root must be an object.")

    meta = kb_data.get("metadata", {}) if isinstance(kb_data.get("metadata"), dict) else {}
    repos = kb_data.get("repositories", []) if isinstance(kb_data.get("repositories"), list) else []
    uid_lower = clean_uid.lower()
    matched_owner = str(meta.get("owner") or "").strip().lower() == uid_lower

    if matched_owner:
        matched_repos = [r for r in repos if isinstance(r, dict)]
    else:
        matched_repos = [
            r for r in repos if isinstance(r, dict) and _repo_belongs_to_user(r, uid_lower)
        ]

    if fmt_lower == "json":
        payload = {
            "user_id": clean_uid,
            "metadata": meta if matched_owner else {},
            "record_count": len(matched_repos),
            "records": matched_repos,
        }
        serialized = json.dumps(payload, indent=2)
    else:
        csv_fields = [
            "id",
            "name",
            "full_name",
            "html_url",
            "primary_language",
            "cluster_id",
            "cluster_name",
            "stars",
            "forks",
            "open_issues",
            "license",
            "topics",
            "description",
        ]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=csv_fields)
        writer.writeheader()
        for r in matched_repos:
            row = {}
            for k in csv_fields:
                val = r.get(k, "")
                if isinstance(val, list):
                    val = ";".join(str(x) for x in val)
                row[k] = val
            writer.writerow(row)
        serialized = buf.getvalue()

    return {
        "user_id": clean_uid,
        "matched_owner": matched_owner,
        "record_count": len(matched_repos),
        "metadata": meta if matched_owner else {},
        "records": matched_repos,
        "format": fmt_lower,
        "serialized": serialized,
    }


def delete_user_data(user_id: str, output_dir: str = "output") -> Dict[str, Any]:
    """
    Permanently purge all stored metadata and generated artifacts associated with a
    GitHub user/owner handle across output files without soft-delete remnants (GDPR Art. 17).
    """
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty GitHub handle.")
    clean_uid = strip_control_chars(user_id).strip()
    if not clean_uid:
        raise ValueError("user_id must be a non-empty GitHub handle.")

    safe_dir = validate_path_safe(output_dir, for_write=True)
    artifact_names = (
        "knowledge_base.json",
        "knowledge_graph.json",
        "KNOWLEDGE_BASE.md",
        "dashboard.html",
        "knowledge_base_export.json",
    )
    kb_path = os.path.join(safe_dir, "knowledge_base.json")
    if not os.path.isfile(kb_path):
        return {
            "user_id": clean_uid,
            "purged": False,
            "deleted_repositories": 0,
            "removed_files": [],
            "regenerated_files": [],
        }

    kb_data = load_json_limited(kb_path, max_bytes=MAX_JSON_DATA_BYTES)
    if not isinstance(kb_data, dict):
        raise ValueError("Knowledge base JSON root must be an object.")

    meta = kb_data.get("metadata", {}) if isinstance(kb_data.get("metadata"), dict) else {}
    repos = kb_data.get("repositories", []) if isinstance(kb_data.get("repositories"), list) else []
    uid_lower = clean_uid.lower()
    owner_matches = str(meta.get("owner") or "").strip().lower() == uid_lower

    remaining_repos = [
        r for r in repos if isinstance(r, dict) and not _repo_belongs_to_user(r, uid_lower)
    ]
    deleted_count = len(repos) - len(remaining_repos)

    if not owner_matches and deleted_count == 0:
        return {
            "user_id": clean_uid,
            "purged": False,
            "deleted_repositories": 0,
            "removed_files": [],
            "regenerated_files": [],
        }

    if owner_matches or len(remaining_repos) == 0:
        removed_files: List[str] = []
        for fname in artifact_names:
            fpath = os.path.join(safe_dir, fname)
            if os.path.lexists(fpath):
                assert_not_symlink_file(fpath)
                os.remove(fpath)
                removed_files.append(fpath)
        return {
            "user_id": clean_uid,
            "purged": True,
            "deleted_repositories": len(repos) if owner_matches else deleted_count,
            "removed_files": removed_files,
            "regenerated_files": [],
        }

    # Partial purge within a multi-owner dataset: re-cluster and regenerate all artifacts cleanly
    from scripts.clusterer import RepositoryClusterer
    from scripts.dashboard_generator import DashboardGenerator
    from scripts.graph_builder import KnowledgeGraphBuilder
    from scripts.kb_generator import KnowledgeBaseGenerator

    clusterer = RepositoryClusterer()
    clusters_data = clusterer.cluster_repositories(remaining_repos)
    graph_data = KnowledgeGraphBuilder().build_graph(
        repositories=clusters_data.get("repositories", []),
        clusters=clusters_data.get("clusters", []),
    )
    kb_files = KnowledgeBaseGenerator(output_dir=safe_dir).generate_all(
        metadata=dict(meta),
        clusters_data=clusters_data,
        graph_data=graph_data,
    )
    dash_path = DashboardGenerator(output_dir=safe_dir).generate(
        metadata=dict(meta),
        clusters_data=clusters_data,
        graph_data=graph_data,
    )
    regenerated = [
        kb_files["knowledge_base_json"],
        kb_files["knowledge_graph_json"],
        kb_files["knowledge_base_md"],
        dash_path,
    ]
    return {
        "user_id": clean_uid,
        "purged": True,
        "deleted_repositories": deleted_count,
        "removed_files": [],
        "regenerated_files": regenerated,
    }


deleteUserData = delete_user_data
