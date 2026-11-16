"""
GitHub Repository Scanner and Ingestion Module.

Fetches and normalizes repository metadata from any public GitHub account (organization or user),
individual repository, or offline synthetic fixtures.
"""

import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from scripts.security_utils import (
    MAX_JSON_DATA_BYTES,
    deterministic_id,
    is_placeholder_token,
    is_public_ip,
    load_json_limited,
    redact_secrets,
    sanitize_http_url,
    validate_path_safe,
)

ALLOWED_GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})
ALLOWED_API_HOST = "api.github.com"
_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,38})$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
MAX_API_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB per API page
MAX_ERROR_BODY_BYTES = 4096
MAX_ALLOWED_REPOS = 1000
MAX_PAGES = 50


def _assert_safe_api_url(url: str, check_dns: bool = False) -> None:
    """Ensure outbound API requests target HTTPS api.github.com and non-private IPs."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"Blocked non-HTTPS API URL scheme: '{parsed.scheme}'")
    host = (parsed.hostname or "").lower()
    if host != ALLOWED_API_HOST:
        raise ValueError(f"Blocked outbound request to disallowed host: '{host}'")
    if parsed.port not in (None, 443):
        raise ValueError(f"Blocked outbound request to non-standard port: '{parsed.port}'")
    if check_dns:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not infos:
            raise ValueError(f"Unable to resolve host '{host}'")
        for info in infos:
            ip_str = info[4][0]
            if not is_public_ip(ip_str):
                raise ValueError(f"Blocked SSRF resolution to non-public IP: {ip_str}")


class _SafeGitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Restrict HTTP redirects strictly to HTTPS api.github.com (max 3 hops)."""

    max_redirections = 3
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        _assert_safe_api_url(resolved, check_dns=True)
        return super().redirect_request(req, fp, code, msg, headers, resolved)


class GitHubScanner:
    """Scanner for extracting repository data from any GitHub organization, user, or fixture."""

    def __init__(self, token: Optional[str] = None, user_agent: str = "github-repo-kb-scanner/1.0"):
        candidate_token = token if not is_placeholder_token(token) else None
        env_token = os.environ.get("GITHUB_TOKEN")
        if candidate_token is None and not is_placeholder_token(env_token):
            candidate_token = env_token
        self.token = candidate_token.strip() if isinstance(candidate_token, str) else None
        self.user_agent = user_agent

    @staticmethod
    def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Parse GitHub URL or handle to determine target type (org/user vs single repo).
        Returns tuple: (target_type, owner, repo_name)
        target_type is either 'owner' (for user or org) or 'repo'.
        """
        if not isinstance(url, str):
            raise ValueError("GitHub URL or identifier must be a string.")
        cleaned = url.strip()
        if not cleaned or any(ch in cleaned for ch in ("\r", "\n", "\x00", "\t", " ")):
            raise ValueError(f"Invalid GitHub URL or identifier: '{url}'")

        if "://" in cleaned:
            parsed = urllib.parse.urlsplit(cleaned)
            if parsed.scheme.lower() not in ("http", "https"):
                raise ValueError(f"Unsupported URL scheme '{parsed.scheme}': only http/https github.com URLs are allowed.")
            host = (parsed.hostname or "").lower()
            if host not in ALLOWED_GITHUB_HOSTS:
                raise ValueError(f"Unsupported host '{host}': only github.com targets are allowed.")
            if parsed.query or parsed.fragment:
                raise ValueError("GitHub target URL must not contain query parameters or fragments.")
            path = parsed.path
        else:
            if ":" in cleaned or "?" in cleaned or "#" in cleaned:
                raise ValueError(f"Invalid GitHub URL or identifier: '{url}'")
            raw_parts = [p for p in cleaned.split("/") if p]
            if not raw_parts:
                raise ValueError(f"Invalid GitHub URL or identifier: '{url}'")
            first_lower = raw_parts[0].lower()
            if first_lower in ALLOWED_GITHUB_HOSTS:
                path = "/".join(raw_parts[1:])
            elif "." in raw_parts[0]:
                raise ValueError(f"Unsupported host '{raw_parts[0]}': only github.com targets are allowed.")
            else:
                path = cleaned

        raw_segments = [p for p in path.strip("/").split("/") if p]
        if any(seg in (".", "..") or "%" in seg or "\\" in seg for seg in raw_segments):
            raise ValueError(f"Path traversal or encoded segment rejected in GitHub target: '{url}'")

        if raw_segments and raw_segments[0].lower() in ("orgs", "users"):
            raw_segments = raw_segments[1:]
        if len(raw_segments) >= 2 and raw_segments[-1].lower() == "repositories":
            raw_segments = raw_segments[:-1]

        if not raw_segments:
            raise ValueError(f"Invalid GitHub URL or identifier: '{url}'")

        owner = raw_segments[0]
        if not _OWNER_RE.match(owner):
            raise ValueError(f"Invalid GitHub owner handle: '{owner}'")

        if len(raw_segments) == 1:
            return ("owner", owner, None)

        repo_name = raw_segments[1]
        if repo_name in (".", "..") or not _REPO_RE.match(repo_name):
            raise ValueError(f"Invalid GitHub repository name: '{repo_name}'")

        return ("repo", owner, repo_name)

    def _build_opener(self) -> urllib.request.OpenerDirector:
        """Build an HTTPS-only opener with TLS >= 1.2 and restricted redirect handling."""
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
        return urllib.request.build_opener(https_handler, _SafeGitHubRedirectHandler())

    def _make_api_request(self, url: str) -> Tuple[int, Any, Dict[str, str]]:
        """Perform a hardened HTTPS GET request against the GitHub REST API."""
        try:
            _assert_safe_api_url(url, check_dns=True)
        except Exception as e:
            return (0, {"error": redact_secrets(e, [self.token])}, {})

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        opener = self._build_opener()
        try:
            with opener.open(req, timeout=30) as response:
                status = response.status
                headers_dict = dict(response.headers)
                raw_bytes = response.read(MAX_API_RESPONSE_BYTES + 1)
                if len(raw_bytes) > MAX_API_RESPONSE_BYTES:
                    return (
                        0,
                        {"error": f"GitHub API response exceeded {MAX_API_RESPONSE_BYTES} byte limit."},
                        headers_dict,
                    )
                data = json.loads(raw_bytes.decode("utf-8"))
                return (status, data, headers_dict)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read(MAX_ERROR_BODY_BYTES).decode("utf-8", errors="replace")
            except Exception:
                pass
            return (
                e.code,
                {
                    "error": redact_secrets(e, [self.token]),
                    "body": redact_secrets(error_body, [self.token]),
                },
                dict(e.headers) if e.headers else {},
            )
        except Exception as e:
            return (0, {"error": redact_secrets(e, [self.token])}, {})

    def scan_online(
        self,
        url: str,
        include_forks: bool = False,
        include_archived: bool = True,
        max_repos: int = 100,
    ) -> Dict[str, Any]:
        """
        Scan any live public GitHub URL (organization, user, or single repository).
        """
        if not isinstance(max_repos, int) or max_repos <= 0:
            raise ValueError("max_repos must be a positive integer.")
        bounded_max_repos = min(max_repos, MAX_ALLOWED_REPOS)

        target_type, owner, repo_name = self.parse_github_url(url)
        owner_q = urllib.parse.quote(owner, safe="")
        repo_q = urllib.parse.quote(repo_name, safe="") if repo_name else None

        repos: List[Dict[str, Any]] = []
        target_info: Dict[str, Any] = {
            "input_url": url,
            "target_url": (
                f"https://github.com/{owner_q}"
                if target_type == "owner"
                else f"https://github.com/{owner_q}/{repo_q}"
            ),
            "target_type": target_type,
            "owner": owner,
            "repo_name": repo_name,
            "scanned_at": None,
            "is_offline_fixture": False,
        }

        if target_type == "repo":
            api_url = f"https://api.github.com/repos/{owner_q}/{repo_q}"
            status, data, headers = self._make_api_request(api_url)
            if status == 200 and isinstance(data, dict):
                normalized = self._normalize_repo(data)
                repos.append(normalized)
            else:
                err_msg = redact_secrets(data.get("error", "Unknown error") if isinstance(data, dict) else "Unknown error", [self.token])
                if status == 403 or "rate limit" in str(data).lower():
                    raise PermissionError(
                        f"GitHub API rate limit exceeded ({status}). "
                        "Provide a GITHUB_TOKEN environment variable or use an offline fixture."
                    )
                raise RuntimeError(f"Failed to fetch repository {owner}/{repo_name} (HTTP {status}): {err_msg}")
        else:
            page = 1
            is_org = True
            while len(repos) < bounded_max_repos and page <= MAX_PAGES:
                api_url = f"https://api.github.com/orgs/{owner_q}/repos?per_page=100&page={page}&sort=updated"
                status, data, headers = self._make_api_request(api_url)

                if status == 404 and page == 1:
                    # Fallback to user repos if org returned 404
                    is_org = False
                    api_url = f"https://api.github.com/users/{owner_q}/repos?per_page=100&page={page}&sort=updated"
                    status, data, headers = self._make_api_request(api_url)

                if status != 200:
                    if status == 403 or "rate limit" in str(data).lower():
                        raise PermissionError(
                            f"GitHub API rate limit exceeded ({status}). "
                            "Provide a GITHUB_TOKEN environment variable or use a fixture."
                        )
                    if page == 1 and status == 404:
                        raise ValueError(f"GitHub public account '{owner}' not found as an organization or user.")
                    break

                if not isinstance(data, list) or len(data) == 0:
                    break

                for raw_repo in data:
                    if not isinstance(raw_repo, dict):
                        continue
                    if not include_forks and raw_repo.get("fork", False):
                        continue
                    if not include_archived and raw_repo.get("archived", False):
                        continue
                    repos.append(self._normalize_repo(raw_repo))
                    if len(repos) >= bounded_max_repos:
                        break

                page += 1

            target_info["entity_type"] = "organization" if is_org else "user"

        return {
            "metadata": target_info,
            "repositories": repos,
            "total_count": len(repos),
        }

    def load_fixture(self, fixture_path: str) -> Dict[str, Any]:
        """
        Load synthetic repository dataset from a local JSON fixture file.
        """
        safe_path = validate_path_safe(fixture_path)
        if not os.path.isfile(safe_path):
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

        raw_data = load_json_limited(safe_path, max_bytes=MAX_JSON_DATA_BYTES)

        if isinstance(raw_data, list):
            repos = [self._normalize_repo(r) for r in raw_data if isinstance(r, dict)]
            meta = {
                "input_url": "fixture://" + os.path.basename(safe_path),
                "target_url": "fixture://" + os.path.basename(safe_path),
                "target_type": "fixture",
                "owner": "synthetic-org",
                "is_offline_fixture": True,
            }
        elif isinstance(raw_data, dict):
            raw_repos = raw_data.get("repositories", raw_data.get("repos", []))
            if not isinstance(raw_repos, list):
                raise ValueError(f"Fixture 'repositories' must be a list: {fixture_path}")
            repos = [self._normalize_repo(r) for r in raw_repos if isinstance(r, dict)]
            raw_meta = raw_data.get("metadata", {})
            if not isinstance(raw_meta, dict):
                raw_meta = {}
            input_url = (
                raw_meta.get("input_url")
                or raw_meta.get("target_url")
                or raw_data.get("target_url")
                or ("fixture://" + os.path.basename(safe_path))
            )
            owner = raw_meta.get("owner") or raw_data.get("owner") or "synthetic-org"
            meta = {
                "input_url": input_url,
                "target_url": input_url,
                "target_type": raw_meta.get("target_type", "organization"),
                "owner": owner,
                "description": raw_meta.get("description", "Synthetic repository dataset"),
                "is_offline_fixture": True,
            }
        else:
            raise ValueError(f"Unexpected JSON format in fixture: {fixture_path}")

        return {
            "metadata": meta,
            "repositories": repos,
            "total_count": len(repos),
        }

    def _normalize_repo(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize repository metadata dictionary and infer technology stack."""
        name = str(raw.get("name", "unnamed-repo"))
        full_name = str(raw.get("full_name", f"account/{name}"))
        raw_html_url = raw.get("html_url", f"https://github.com/{full_name}")
        html_url = sanitize_http_url(raw_html_url, default=f"https://github.com/{urllib.parse.quote(full_name, safe='/')}")
        description = str(raw.get("description") or "No description provided.")
        language = str(raw.get("language") or raw.get("primary_language") or "Other")
        topics = raw.get("topics") or []
        if not isinstance(topics, list):
            topics = []
        stars = raw.get("stargazers_count", raw.get("stars", 0))
        forks = raw.get("forks_count", raw.get("forks", 0))
        open_issues = raw.get("open_issues_count", raw.get("open_issues", 0))
        updated_at = raw.get("updated_at", "")
        created_at = raw.get("created_at", "")
        default_branch = raw.get("default_branch", "main")
        is_fork = bool(raw.get("fork", False))
        is_archived = bool(raw.get("archived", False))

        license_info = raw.get("license")
        if isinstance(license_info, dict):
            license_name = license_info.get("spdx_id") or license_info.get("name", "None")
        elif isinstance(license_info, str):
            license_name = license_info
        else:
            license_name = "None"

        dependencies = raw.get("dependencies", [])
        if isinstance(dependencies, dict):
            dependencies = list(dependencies.keys())
        elif not isinstance(dependencies, list):
            dependencies = []

        tags = sorted(set(str(t).lower() for t in topics))

        # Automatically extract tech stack from language, topics, and description
        raw_tech = raw.get("tech_stack", [])
        tech_set = set(str(t) for t in raw_tech) if isinstance(raw_tech, list) else set()
        if language and language != "Other":
            tech_set.add(language)

        common_tech_keywords = [
            "react", "vue", "angular", "next.js", "tailwind", "fastapi", "django", "flask",
            "express", "spring", "grpc", "graphql", "kafka", "flink", "postgres", "postgresql",
            "redis", "docker", "kubernetes", "terraform", "pytorch", "tensorflow", "clickhouse"
        ]
        text_corpus = f"{name} {description} {' '.join(tags)}".lower()
        for kw in common_tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_corpus):
                tech_set.add(kw.title())

        return {
            "id": raw.get("id") if raw.get("id") is not None else deterministic_id(full_name),
            "name": name,
            "full_name": full_name,
            "html_url": html_url,
            "description": description,
            "primary_language": language,
            "topics": tags,
            "stars": stars,
            "forks": forks,
            "open_issues": open_issues,
            "updated_at": updated_at,
            "created_at": created_at,
            "default_branch": default_branch,
            "is_fork": is_fork,
            "is_archived": is_archived,
            "license": license_name,
            "dependencies": dependencies,
            "tech_stack": sorted(list(tech_set)),
            "readme_summary": str(raw.get("readme_summary", "")),
        }
