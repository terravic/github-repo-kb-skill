#!/usr/bin/env python3
"""
Offline Pre-Deployment Security, Supply-Chain, and CSP Verification Gate.

Checks:
  1. Pinned SHA-256 integrity of vendored client-side dependencies (d3@7.9.0).
  2. Secret pattern scan across repository text files.
  3. Generated dashboard CSP hash integrity, Referrer-Policy, zero inline event handlers,
     and zero unauthorized third-party script/CDN hosts.
  4. Presence of required security, license, and governance files.

Exit status: 0 if all checks pass, 1 if any check fails.
"""

import base64
import hashlib
import os
import re
import sys
from typing import List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_VENDOR_HASHES = {
    os.path.join("scripts", "vendor", "d3.v7.min.js"): (
        "f2094bbf6141b359722c4fe454eb6c4b0f0e42cc10cc7af921fc158fceb86539"
    ),
    os.path.join("scripts", "vendor", "D3_LICENSE"): (
        "3e6849627f74ff73c257a3ae1efb574015d94fc1035c05ec3c15805165efcbc4"
    ),
}

REQUIRED_FILES = [
    "THIRD_PARTY_LICENSES.md",
    ".env.example",
    "DESIGN.md",
    "prd.md",
    os.path.join("scripts", "security_utils.py"),
    os.path.join("docs", "legal", "PRIVACY_POLICY.md"),
    os.path.join("docs", "legal", "TERMS_OF_USE.md"),
    os.path.join("docs", "legal", "COOKIE_AND_STORAGE_POLICY.md"),
    os.path.join("docs", "legal", "ROPA_AND_GOVERNANCE.md"),
    os.path.join("docs", "legal", "ACCESSIBILITY_STATEMENT.md"),
]

# High-confidence credential patterns (skipping vendor minified bundle and binary files)
SECRET_REGEXES: List[Tuple[str, re.Pattern]] = [
    ("GitHub Classic PAT", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{12,}\b")),
    ("GitHub Fine-Grained PAT", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Provider API Key (sk-ant)", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}\b")),
    ("Provider API Key (sk-proj)", re.compile(r"\bsk-proj-[A-Za-z0-9_-]{16,}\b")),
    ("Cloud Access Key (AKIA)", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Cloud API Key (AIza)", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Workspace Token (xox)", re.compile(r"\bxox[bpas]-[0-9A-Za-z-]{10,}\b")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}
SKIP_SECRET_SCAN_RELPATHS = {
    os.path.join("scripts", "vendor", "d3.v7.min.js"),
}
BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2", ".zip"}

INLINE_HANDLER_RE = re.compile(
    r"\son(?:click|dblclick|keydown|keyup|keypress|input|change|submit|focus|blur|mouseover|mousemove|mouseout|load|error)\s*=",
    re.IGNORECASE,
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_required_files(errors: List[str]) -> None:
    for rel in REQUIRED_FILES:
        full = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(full):
            errors.append(f"[MISSING] Required compliance/security file missing: {rel}")


def check_vendor_integrity(errors: List[str]) -> None:
    for rel, expected in EXPECTED_VENDOR_HASHES.items():
        full = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(full):
            errors.append(f"[VENDOR] Missing vendored file: {rel}")
            continue
        actual = sha256_file(full)
        if actual != expected:
            errors.append(
                f"[VENDOR] SHA-256 mismatch for {rel}: expected {expected}, got {actual}"
            )


def check_secrets(errors: List[str]) -> None:
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext.lower() in BINARY_EXTS:
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, REPO_ROOT)
            if rel in SKIP_SECRET_SCAN_RELPATHS:
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            for label, pat in SECRET_REGEXES:
                for match in pat.finditer(content):
                    line_no = content.count("\n", 0, match.start()) + 1
                    errors.append(
                        f"[SECRET] Potential {label} detected in {rel}:{line_no}"
                    )


ALLOWED_RUNTIME_HOSTS = {"api.github.com", "github.com", "www.github.com"}


def check_dashboard_html(rel_path: str, errors: List[str]) -> None:
    full = os.path.join(REPO_ROOT, rel_path)
    if not os.path.isfile(full):
        errors.append(f"[DASHBOARD] Missing dashboard artifact: {rel_path}")
        return

    with open(full, "r", encoding="utf-8") as f:
        html_text = f.read()

    # 1. External script / stylesheet checks
    if re.search(r"<script[^>]+src\s*=", html_text, re.IGNORECASE):
        errors.append(f"[DASHBOARD] External <script src=...> tag found in {rel_path}")
    if re.search(r"<link[^>]+href\s*=\s*[\"']https?://", html_text, re.IGNORECASE):
        errors.append(f"[DASHBOARD] External <link href=http...> found in {rel_path}")

    # 2. Referrer-Policy meta check
    if not re.search(
        r'<meta\s+name="referrer"\s+content="no-referrer"\s*/?>', html_text, re.IGNORECASE
    ):
        errors.append(f"[DASHBOARD] Missing Referrer-Policy no-referrer meta tag in {rel_path}")

    # 3. CSP meta & exact SHA-256 script hash validation
    csp_match = re.search(
        r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"\s*/?>',
        html_text,
        re.IGNORECASE,
    )
    if not csp_match:
        errors.append(f"[DASHBOARD] Missing Content-Security-Policy meta tag in {rel_path}")
        return

    csp_val = csp_match.group(1)
    script_src_match = re.search(r"script-src\s+([^;]+)", csp_val)
    if not script_src_match:
        errors.append(f"[DASHBOARD] Missing script-src directive in CSP in {rel_path}")
        return

    script_src = script_src_match.group(1)
    if "'unsafe-inline'" in script_src or "'unsafe-eval'" in script_src:
        errors.append(
            f"[DASHBOARD] Unsafe directive in CSP script-src in {rel_path}: {script_src}"
        )

    allowed_hashes = set(re.findall(r"'sha256-[A-Za-z0-9+/=]+'", script_src))
    expected_d3_hex = EXPECTED_VENDOR_HASHES[os.path.join("scripts", "vendor", "d3.v7.min.js")]
    found_vendored_d3 = False

    script_blocks = list(
        re.finditer(r"<script([^>]*)>(.*?)</script>", html_text, re.DOTALL | re.IGNORECASE)
    )
    exec_script_count = 0
    non_vendor_parts: List[str] = []
    last_end = 0

    for m in script_blocks:
        attrs, body = m.group(1), m.group(2)
        non_vendor_parts.append(html_text[last_end : m.start()])
        last_end = m.end()

        if re.search(r'type\s*=\s*["\']application/json["\']', attrs, re.IGNORECASE):
            continue

        exec_script_count += 1
        raw_bytes = body.encode("utf-8")
        hex_digest = hashlib.sha256(raw_bytes).hexdigest()
        b64_digest = base64.b64encode(hashlib.sha256(raw_bytes).digest()).decode("ascii")
        token = f"'sha256-{b64_digest}'"
        if token not in allowed_hashes:
            errors.append(
                f"[DASHBOARD] Executable <script> block #{exec_script_count} hash {token} "
                f"not listed in CSP script-src in {rel_path}"
            )
        if hex_digest == expected_d3_hex:
            found_vendored_d3 = True
        else:
            non_vendor_parts.append(body)

    non_vendor_parts.append(html_text[last_end:])

    if exec_script_count < 2:
        errors.append(
            f"[DASHBOARD] Expected at least 2 executable script blocks (D3 + app) in {rel_path}, found {exec_script_count}"
        )
    if not found_vendored_d3:
        errors.append(
            f"[DASHBOARD] Verified vendored D3 v7.9.0 script block not found in {rel_path}"
        )

    # 4. Verify all external URLs outside vendored D3/data block belong strictly to runtime host allowlist
    non_vendor_text = "\n".join(non_vendor_parts)
    for url_match in re.finditer(r"https?://([A-Za-z0-9._-]+)", non_vendor_text, re.IGNORECASE):
        host = url_match.group(1).lower()
        if host not in ALLOWED_RUNTIME_HOSTS:
            errors.append(
                f"[DASHBOARD] Unauthorized third-party host '{host}' referenced in {rel_path}"
            )

    # 5. Verify zero inline HTML event handlers outside <script> blocks
    html_without_scripts = re.sub(
        r"<script\b[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE
    )
    handler_match = INLINE_HANDLER_RE.search(html_without_scripts)
    if handler_match:
        errors.append(
            f"[DASHBOARD] Inline HTML event handler '{handler_match.group(0).strip()}' found in {rel_path}"
        )


def main() -> int:
    errors: List[str] = []
    check_required_files(errors)
    check_vendor_integrity(errors)
    check_secrets(errors)
    check_dashboard_html(os.path.join("output", "dashboard.html"), errors)
    check_dashboard_html(os.path.join("examples", "sample_output", "dashboard.html"), errors)

    if errors:
        print("SECURITY CHECK FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("SECURITY CHECK PASSED: vendored SHA-256, secret scan, CSP hashes, Referrer-Policy, and offline checks all succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
