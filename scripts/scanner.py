"""
GitHub Repository Scanner and Ingestion Module.

Fetches and normalizes repository metadata from any public GitHub account (organization or user),
individual repository, or offline synthetic fixtures.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class GitHubScanner:
    """Scanner for extracting repository data from any GitHub organization, user, or fixture."""

    def __init__(self, token: Optional[str] = None, user_agent: str = "github-repo-kb-scanner/1.0"):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.user_agent = user_agent

    @staticmethod
    def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Parse GitHub URL or handle to determine target type (org/user vs single repo).
        Returns tuple: (target_type, owner, repo_name)
        target_type is either 'owner' (for user or org) or 'repo'.
        """
        cleaned = url.strip()
        cleaned = re.sub(r"^https?://", "", cleaned)
        cleaned = re.sub(r"^github\.com/", "", cleaned)
        cleaned = re.sub(r"^orgs/", "", cleaned)
        cleaned = cleaned.rstrip("/")
        cleaned = re.sub(r"/repositories$", "", cleaned)

        parts = [p for p in cleaned.split("/") if p]
        if not parts:
            raise ValueError(f"Invalid GitHub URL or identifier: '{url}'")

        if len(parts) == 1:
            return ("owner", parts[0], None)
        elif len(parts) >= 2:
            return ("repo", parts[0], parts[1])
        else:
            raise ValueError(f"Unable to parse target from: '{url}'")

    def _make_api_request(self, url: str) -> Tuple[int, Any, Dict[str, str]]:
        """Perform an HTTP GET request against the GitHub API."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status = response.status
                headers_dict = dict(response.headers)
                data = json.loads(response.read().decode("utf-8"))
                return (status, data, headers_dict)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            return (e.code, {"error": str(e), "body": error_body}, dict(e.headers))
        except Exception as e:
            return (0, {"error": str(e)}, {})

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
        target_type, owner, repo_name = self.parse_github_url(url)
        repos: List[Dict[str, Any]] = []
        target_info: Dict[str, Any] = {
            "input_url": url,
            "target_url": f"https://github.com/{owner}" if target_type == "owner" else f"https://github.com/{owner}/{repo_name}",
            "target_type": target_type,
            "owner": owner,
            "repo_name": repo_name,
            "scanned_at": None,
            "is_offline_fixture": False,
        }

        if target_type == "repo":
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            status, data, headers = self._make_api_request(api_url)
            if status == 200 and isinstance(data, dict):
                normalized = self._normalize_repo(data)
                repos.append(normalized)
            else:
                err_msg = data.get("error", "Unknown error")
                if status == 403 or "rate limit" in str(data).lower():
                    raise PermissionError(
                        f"GitHub API rate limit exceeded ({status}). "
                        "Provide a GITHUB_TOKEN or use an offline fixture."
                    )
                raise RuntimeError(f"Failed to fetch repository {owner}/{repo_name} (HTTP {status}): {err_msg}")
        else:
            page = 1
            is_org = True
            while len(repos) < max_repos:
                api_url = f"https://api.github.com/orgs/{owner}/repos?per_page=100&page={page}&sort=updated"
                status, data, headers = self._make_api_request(api_url)

                if status == 404 and page == 1:
                    # Fallback to user repos if org returned 404
                    is_org = False
                    api_url = f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}&sort=updated"
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
                    if not include_forks and raw_repo.get("fork", False):
                        continue
                    if not include_archived and raw_repo.get("archived", False):
                        continue
                    repos.append(self._normalize_repo(raw_repo))
                    if len(repos) >= max_repos:
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
        if not os.path.isfile(fixture_path):
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

        with open(fixture_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, list):
            repos = [self._normalize_repo(r) for r in raw_data]
            meta = {
                "input_url": "fixture://" + os.path.basename(fixture_path),
                "target_url": "fixture://" + os.path.basename(fixture_path),
                "target_type": "fixture",
                "owner": "synthetic-org",
                "is_offline_fixture": True,
            }
        elif isinstance(raw_data, dict):
            raw_repos = raw_data.get("repositories", raw_data.get("repos", []))
            repos = [self._normalize_repo(r) for r in raw_repos]
            raw_meta = raw_data.get("metadata", {})
            input_url = raw_meta.get("input_url") or raw_meta.get("target_url") or raw_data.get("target_url") or ("fixture://" + os.path.basename(fixture_path))
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
        name = raw.get("name", "unnamed-repo")
        full_name = raw.get("full_name", f"account/{name}")
        html_url = raw.get("html_url", f"https://github.com/{full_name}")
        description = raw.get("description") or "No description provided."
        language = raw.get("language") or "Other"
        topics = raw.get("topics") or []
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

        tags = list(set([t.lower() for t in topics]))

        # Automatically extract tech stack from language, topics, and description
        tech_set = set(raw.get("tech_stack", []))
        if language and language != "Other":
            tech_set.add(language)

        common_tech_keywords = [
            "react", "vue", "angular", "next.js", "tailwind", "fastapi", "django", "flask",
            "express", "spring", "grpc", "graphql", "kafka", "spark", "postgres", "postgresql",
            "redis", "docker", "kubernetes", "terraform", "pytorch", "tensorflow", "clickhouse"
        ]
        text_corpus = f"{name} {description} {' '.join(tags)}".lower()
        for kw in common_tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_corpus):
                tech_set.add(kw.title())

        return {
            "id": raw.get("id") or abs(hash(full_name)) % 10000000,
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
            "readme_summary": raw.get("readme_summary", ""),
        }
