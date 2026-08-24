"""
Repository Clustering and Thematic Domain Taxonomy Classifier.

Groups repositories into meaningful thematic clusters based on domain purpose,
subject matter, topics, keywords, and custom configuration rules rather than
merely technical frameworks or programming languages.
"""

import re
from typing import Any, Dict, List, Optional


THEMATIC_TAXONOMY = [
    {
        "id": "medical-healthcare",
        "name": "Medical & Healthcare",
        "description": "Clinical workflows, electronic health records (EHR/EMR), patient portals, FHIR/HL7 interoperability, medical imaging (DICOM), and telehealth systems.",
        "color": "#0EA5E9",  # Sky Blue
        "priority": 10,
        "keywords": [
            "medical", "healthcare", "clinical", "patient", "health", "ehr", "emr",
            "fhir", "hl7", "dicom", "radiology", "hospital", "telehealth", "telemedicine",
            "hipaa", "diagnosis", "pathology", "vital", "prescription", "pharmacy",
            "care", "medication", "doctor", "nurse", "clinic"
        ],
        "languages": [],
    },
    {
        "id": "life-sciences-bio",
        "name": "Life Sciences & Bioinformatics",
        "description": "Genomics analysis, DNA/RNA sequencing pipelines, molecular biology, clinical trials, proteomics, and biotechnology research.",
        "color": "#14B8A6",  # Teal
        "priority": 10,
        "keywords": [
            "genomics", "bioinformatics", "biology", "dna", "rna", "sequencing",
            "protein", "crispr", "pharma", "biotech", "molecular", "chemistry",
            "clinical-trials", "laboratory", "specimen", "genetics", "assay", "biomarker"
        ],
        "languages": ["Python", "R", "Julia", "C++"],
    },
    {
        "id": "finance-billing",
        "name": "Finance, Billing & Commerce",
        "description": "Payment processing, subscription billing, invoicing, banking integrations, accounting ledgers, and e-commerce checkout systems.",
        "color": "#10B981",  # Emerald
        "priority": 9,
        "keywords": [
            "billing", "payment", "invoice", "subscription", "stripe", "checkout",
            "finance", "banking", "accounting", "tax", "ecommerce", "order",
            "cart", "currency", "wallet", "ledger", "transaction", "pricing"
        ],
        "languages": [],
    },
    {
        "id": "security-identity",
        "name": "Security, Identity & Access",
        "description": "Authentication, OAuth2/OIDC identity providers, access management (RBAC/ABAC), cryptographic services, token management, and security compliance.",
        "color": "#EC4899",  # Pink / Rose
        "priority": 9,
        "keywords": [
            "auth", "authentication", "oauth", "oauth2", "oidc", "identity",
            "security", "rbac", "abac", "iam", "jwt", "token", "encryption",
            "compliance", "audit", "firewall", "crypto", "keycloak", "secrets",
            "sso", "login", "credentials", "permission"
        ],
        "languages": [],
    },
    {
        "id": "data-ai-analytics",
        "name": "Data Intelligence & AI/ML",
        "description": "Machine learning models, inference engines, vector search, streaming data pipelines, ETL workflows, and business intelligence analytics.",
        "color": "#8B5CF6",  # Purple
        "priority": 8,
        "keywords": [
            "ai", "ml", "analytics", "pipeline", "etl", "kafka", "spark", "warehouse",
            "lake", "embeddings", "rag", "llm", "model", "inference", "nlp", "vision",
            "dataset", "clickhouse", "dbt", "vector", "telemetry", "prediction", "forecast"
        ],
        "languages": ["Python", "Scala", "SQL", "R", "Julia"],
    },
    {
        "id": "developer-tooling",
        "name": "Developer Tooling & SDKs",
        "description": "Client SDKs, CLI command-line tools, API wrappers, code generators, testing harnesses, and developer plugins.",
        "color": "#F59E0B",  # Amber
        "priority": 7,
        "keywords": [
            "sdk", "cli", "client-library", "tooling", "generator", "plugin",
            "agent", "skill", "linter", "mock", "test", "benchmark", "devtools",
            "compiler", "extension", "wrapper", "action", "bindings"
        ],
        "languages": [],
    },
    {
        "id": "infrastructure-devops",
        "name": "Infrastructure & Cloud Operations",
        "description": "Cloud infrastructure as code, Terraform configs, Kubernetes manifests, CI/CD automation, Docker containers, and operational monitoring.",
        "color": "#EF4444",  # Red
        "priority": 7,
        "keywords": [
            "infra", "infrastructure", "terraform", "k8s", "kubernetes", "docker",
            "helm", "ansible", "ci-cd", "actions", "monitoring", "prometheus",
            "grafana", "cloud", "aws", "gcp", "azure", "deployment", "cluster", "gitops"
        ],
        "languages": ["HCL", "Dockerfile", "Shell", "Yaml"],
    },
    {
        "id": "core-platform",
        "name": "Core Platform & Business Services",
        "description": "Core routing gateways, user management, organization tenancy, notification dispatchers, and foundational backend domain engines.",
        "color": "#3B82F6",  # Blue
        "priority": 6,
        "keywords": [
            "gateway", "proxy", "user-service", "tenancy", "notification", "email",
            "sms", "dispatch", "engine", "core-service", "backend-service", "router",
            "membership", "tenant", "organization"
        ],
        "languages": [],
    },
    {
        "id": "frontend-applications",
        "name": "User Applications & Web Portals",
        "description": "User-facing web applications, administrative dashboards, customer portals, mobile apps, and interactive web interfaces.",
        "color": "#06B6D4",  # Cyan
        "priority": 6,
        "keywords": [
            "portal", "app", "ui", "dashboard", "web", "frontend", "client-app",
            "mobile", "ios", "android", "viewer", "console", "interface", "react", "vue"
        ],
        "languages": ["TypeScript", "JavaScript", "HTML", "CSS", "Swift", "Dart"],
    },
    {
        "id": "utilities-libraries",
        "name": "Utilities & Shared Libraries",
        "description": "Cross-cutting shared utilities, protocol buffers, common data schemas, serialization helpers, and shared base contracts.",
        "color": "#64748B",  # Slate
        "priority": 5,
        "keywords": [
            "utils", "utilities", "common", "shared", "core-lib", "proto",
            "contracts", "schemas", "helpers", "types", "base-lib", "constants"
        ],
        "languages": [],
    },
    {
        "id": "documentation-specs",
        "name": "Documentation & Specifications",
        "description": "Architectural blueprints, technical guides, OpenAPI specifications, RFC standards, and research documentation.",
        "color": "#475569",  # Slate Dark
        "priority": 5,
        "keywords": [
            "docs", "documentation", "spec", "specification", "rfc", "guide",
            "tutorial", "architecture", "standard", "wiki", "book", "papers", "manual"
        ],
        "languages": ["Markdown", "TeX"],
    },
]


class RepositoryClusterer:
    """Classifies repositories into domain clusters using thematic rules and keyword scoring."""

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.taxonomy = [dict(c) for c in THEMATIC_TAXONOMY]
        self.custom_rules = custom_rules or []
        self.taxonomy_by_id = {c["id"]: c for c in self.taxonomy}

    def classify_repository(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the best thematic cluster for a single repository.
        Returns cluster metadata dictionary.
        """
        name = repo.get("name", "").lower()
        description = (repo.get("description") or "").lower()
        readme = (repo.get("readme_summary") or "").lower()
        topics = [t.lower() for t in repo.get("topics", [])]
        lang = repo.get("primary_language", "")

        # 1. Custom User Rules from Config (Highest Precedence)
        for rule in self.custom_rules:
            pattern = rule.get("pattern", "")
            cluster_id = rule.get("cluster_id", "")
            if pattern and re.search(pattern, name, re.IGNORECASE):
                if cluster_id in self.taxonomy_by_id:
                    return self.taxonomy_by_id[cluster_id]
                else:
                    return {
                        "id": cluster_id,
                        "name": rule.get("name", cluster_id.replace("-", " ").title()),
                        "description": rule.get("description", "Custom configured thematic domain."),
                        "color": rule.get("color", "#6366F1"),
                    }

        # 2. Thematic Scoring across predefined taxonomy
        scores: Dict[str, float] = {c["id"]: 0.0 for c in self.taxonomy}
        tokens = set(re.findall(r"\b[a-z0-9_\-]+\b", f"{name} {' '.join(topics)}"))
        desc_tokens = set(re.findall(r"\b[a-z0-9_\-]+\b", f"{description} {readme}"))

        for cluster in self.taxonomy:
            cid = cluster["id"]
            priority = cluster.get("priority", 5)
            kw_set = set(cluster["keywords"])

            # Exact matching in repo name or topics (Weight 8.0 * priority factor)
            name_topic_matches = tokens.intersection(kw_set)
            if name_topic_matches:
                scores[cid] += len(name_topic_matches) * (6.0 + priority * 0.5)

            # Keyword matching in description/readme (Weight 3.0 * priority factor)
            desc_matches = desc_tokens.intersection(kw_set)
            if desc_matches:
                scores[cid] += len(desc_matches) * (2.0 + priority * 0.2)

            # Specialized Language affinity (Weight 1.5)
            if lang in cluster.get("languages", []):
                scores[cid] += 1.5

        # Pick the highest-scoring thematic cluster
        best_cluster_id = max(scores, key=lambda k: scores[k])
        if scores[best_cluster_id] > 0:
            return self.taxonomy_by_id[best_cluster_id]

        # 3. Fallback: Generic Cluster
        return {
            "id": "general-utilities",
            "name": "General & Utilities",
            "description": "General purpose repositories and multi-disciplinary tools.",
            "color": "#64748B",
        }

    def cluster_repositories(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classifies all repositories and aggregates them into active thematic clusters.
        """
        cluster_map: Dict[str, Dict[str, Any]] = {}
        classified_repos: List[Dict[str, Any]] = []

        for repo in repositories:
            cluster = self.classify_repository(repo)
            cid = cluster["id"]

            if cid not in cluster_map:
                cluster_map[cid] = {
                    "id": cid,
                    "name": cluster["name"],
                    "description": cluster["description"],
                    "color": cluster.get("color", "#3B82F6"),
                    "repositories": [],
                    "total_stars": 0,
                    "languages": {},
                }

            repo_copy = dict(repo)
            repo_copy["cluster_id"] = cid
            repo_copy["cluster_name"] = cluster["name"]
            repo_copy["cluster_color"] = cluster.get("color", "#3B82F6")

            cluster_map[cid]["repositories"].append(repo_copy["id"])
            cluster_map[cid]["total_stars"] += repo_copy.get("stars", 0)

            lang = repo_copy.get("primary_language", "Other")
            cluster_map[cid]["languages"][lang] = cluster_map[cid]["languages"].get(lang, 0) + 1

            classified_repos.append(repo_copy)

        active_clusters: List[Dict[str, Any]] = []
        for cid, cdata in cluster_map.items():
            top_langs = sorted(cdata["languages"].items(), key=lambda x: x[1], reverse=True)
            active_clusters.append({
                "id": cid,
                "name": cdata["name"],
                "description": cdata["description"],
                "color": cdata["color"],
                "repo_count": len(cdata["repositories"]),
                "repositories": cdata["repositories"],
                "total_stars": cdata["total_stars"],
                "top_languages": [l[0] for l in top_langs[:3]],
            })

        active_clusters.sort(key=lambda x: x["repo_count"], reverse=True)

        return {
            "clusters": active_clusters,
            "repositories": classified_repos,
            "cluster_count": len(active_clusters),
        }
