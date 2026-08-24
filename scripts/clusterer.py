"""
Repository Clustering and Domain Taxonomy Classifier.

Groups repositories into meaningful functional clusters based on keywords,
topics, languages, architectural roles, and custom configuration rules.
"""

import re
from typing import Any, Dict, List, Optional


DEFAULT_TAXONOMY = [
    {
        "id": "core-services",
        "name": "Core Services & Backend APIs",
        "description": "Foundational backend services, microservices, gRPC/REST APIs, authentication, and core business engines.",
        "color": "#3B82F6",  # Blue
        "keywords": [
            "api", "backend", "service", "server", "microservice", "grpc", "rest",
            "fastapi", "express", "django", "spring", "auth", "gateway", "engine",
            "middleware", "graphql", "oauth", "jwt", "identity"
        ],
        "languages": ["Go", "Java", "Python", "Rust", "C#", "Kotlin", "Scala"],
    },
    {
        "id": "frontend-ui",
        "name": "Frontend & User Interfaces",
        "description": "Client applications, web portals, dashboards, mobile apps, and interactive UI component design systems.",
        "color": "#10B981",  # Emerald Green
        "keywords": [
            "ui", "frontend", "web", "react", "vue", "svelte", "angular", "nextjs",
            "dashboard", "portal", "client", "app", "mobile", "flutter", "swift",
            "electron", "tailwind", "css", "html", "storybook", "design-system"
        ],
        "languages": ["TypeScript", "JavaScript", "HTML", "CSS", "Swift", "Dart", "Vue"],
    },
    {
        "id": "data-analytics",
        "name": "Data Engineering & AI/ML",
        "description": "Data pipelines, ETL workflows, stream processing, machine learning models, and analytics infrastructure.",
        "color": "#8B5CF6",  # Purple
        "keywords": [
            "data", "pipeline", "etl", "kafka", "spark", "warehouse", "analytics",
            "ml", "ai", "model", "dataset", "embeddings", "llm", "rag", "stream",
            "dbt", "airflow", "flink", "vector", "sql", "databricks"
        ],
        "languages": ["Python", "Scala", "SQL", "R", "Julia"],
    },
    {
        "id": "developer-tooling",
        "name": "Developer Tooling & SDKs",
        "description": "Client SDKs, CLI utilities, code generators, testing harnesses, linters, plugins, and agent skills.",
        "color": "#F59E0B",  # Amber
        "keywords": [
            "sdk", "cli", "client-library", "tooling", "generator", "plugin",
            "agent", "skill", "linter", "mock", "test", "benchmark", "devtools",
            "compiler", "extension", "wrapper", "action"
        ],
        "languages": ["TypeScript", "Python", "Go", "Rust", "Shell"],
    },
    {
        "id": "infrastructure-devops",
        "name": "Infrastructure & DevOps",
        "description": "Cloud infrastructure as code, Kubernetes deployment manifests, CI/CD pipelines, Docker, and monitoring.",
        "color": "#EF4444",  # Red / Rose
        "keywords": [
            "infra", "infrastructure", "terraform", "k8s", "kubernetes", "docker",
            "helm", "ansible", "ci-cd", "actions", "monitoring", "prometheus",
            "grafana", "cloud", "aws", "gcp", "azure", "deployment", "cluster"
        ],
        "languages": ["HCL", "Dockerfile", "Shell", "Yaml", "Jsonnet"],
    },
    {
        "id": "libraries-shared",
        "name": "Shared Libraries & Utilities",
        "description": "Common utilities, protocol definitions, shared data contracts, helper packages, and cross-cutting libraries.",
        "color": "#06B6D4",  # Cyan
        "keywords": [
            "utils", "common", "core-lib", "shared", "helpers", "types",
            "protocols", "proto", "contracts", "schema", "base", "logging",
            "crypto", "events"
        ],
        "languages": [],
    },
    {
        "id": "documentation-specs",
        "name": "Documentation & Specifications",
        "description": "Architectural blueprints, technical documentation, API specifications, guides, and project roadmaps.",
        "color": "#64748B",  # Slate
        "keywords": [
            "docs", "documentation", "spec", "specification", "rfc", "guide",
            "tutorial", "architecture", "standard", "wiki", "book", "papers"
        ],
        "languages": ["Markdown", "TeX", "Asciidoctor"],
    },
]


class RepositoryClusterer:
    """Classifies repositories into domain clusters using rule-based and keyword scoring."""

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.taxonomy = DEFAULT_TAXONOMY
        self.custom_rules = custom_rules or []

    def cluster_repositories(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assign each repository to a cluster and compute cluster-level metrics.
        """
        cluster_map: Dict[str, Dict[str, Any]] = {
            c["id"]: {
                "id": c["id"],
                "name": c["name"],
                "description": c["description"],
                "color": c["color"],
                "repositories": [],
                "total_stars": 0,
                "total_forks": 0,
                "languages": {},
                "tech_stack": set(),
            }
            for c in self.taxonomy
        }

        # Catch-all cluster for unassigned
        cluster_map["general"] = {
            "id": "general",
            "name": "General & Other Projects",
            "description": "Standalone utilities, experimental repositories, and projects outside primary domains.",
            "color": "#94A3B8",
            "repositories": [],
            "total_stars": 0,
            "total_forks": 0,
            "languages": {},
            "tech_stack": set(),
        }

        for repo in repositories:
            assigned_cluster_id = self._classify_repository(repo)
            repo["cluster_id"] = assigned_cluster_id
            repo["cluster_name"] = cluster_map[assigned_cluster_id]["name"]
            repo["cluster_color"] = cluster_map[assigned_cluster_id]["color"]

            c_entry = cluster_map[assigned_cluster_id]
            c_entry["repositories"].append(repo["id"])
            c_entry["total_stars"] += repo.get("stars", 0)
            c_entry["total_forks"] += repo.get("forks", 0)

            lang = repo.get("primary_language", "Other")
            if lang and lang != "Other":
                c_entry["languages"][lang] = c_entry["languages"].get(lang, 0) + 1

            for tech in repo.get("tech_stack", []):
                c_entry["tech_stack"].add(tech)

        # Convert sets to lists and filter out empty clusters
        active_clusters: List[Dict[str, Any]] = []
        for c_id, c_data in cluster_map.items():
            if len(c_data["repositories"]) > 0:
                c_data["repo_count"] = len(c_data["repositories"])
                c_data["tech_stack"] = sorted(list(c_data["tech_stack"]))
                # Sort languages by frequency
                sorted_langs = sorted(
                    [{"language": k, "count": v} for k, v in c_data["languages"].items()],
                    key=lambda x: x["count"],
                    reverse=True
                )
                c_data["top_languages"] = [x["language"] for x in sorted_langs[:3]]
                c_data["language_breakdown"] = sorted_langs
                active_clusters.append(c_data)

        # Sort clusters by repository count descending
        active_clusters.sort(key=lambda x: x["repo_count"], reverse=True)

        return {
            "clusters": active_clusters,
            "cluster_count": len(active_clusters),
            "repositories": repositories,
        }

    def _classify_repository(self, repo: Dict[str, Any]) -> str:
        """Score repository against taxonomy and return best cluster ID."""
        # Check custom override rules first
        for rule in self.custom_rules:
            pattern = rule.get("pattern")
            target_cluster = rule.get("cluster_id")
            if pattern and target_cluster:
                if re.search(pattern, repo.get("name", ""), re.IGNORECASE):
                    return target_cluster
                if re.search(pattern, repo.get("description", ""), re.IGNORECASE):
                    return target_cluster

        # Compute match scores across taxonomy
        scores: Dict[str, float] = {c["id"]: 0.0 for c in self.taxonomy}

        name_lower = repo.get("name", "").lower()
        desc_lower = (repo.get("description") or "").lower()
        topics_lower = [t.lower() for t in repo.get("topics", [])]
        tech_lower = [t.lower() for t in repo.get("tech_stack", [])]
        lang = repo.get("primary_language", "")

        for cluster in self.taxonomy:
            cid = cluster["id"]
            keywords = cluster.get("keywords", [])
            primary_langs = cluster.get("languages", [])

            # Topic match (high weight: 3.0)
            for kw in keywords:
                if kw in topics_lower:
                    scores[cid] += 3.0

            # Tech stack match (high weight: 2.5)
            for kw in keywords:
                if kw in tech_lower:
                    scores[cid] += 2.5

            # Name match (medium-high weight: 2.5)
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", name_lower) or kw in name_lower.split("-") or kw in name_lower.split("_"):
                    scores[cid] += 2.5

            # Description match (medium weight: 1.5)
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", desc_lower):
                    scores[cid] += 1.5

            # Primary language affinity (weight: 1.0)
            if lang in primary_langs:
                scores[cid] += 1.0

        best_cluster = max(scores, key=lambda k: scores[k])
        if scores[best_cluster] > 1.2:
            return best_cluster

        return "general"
