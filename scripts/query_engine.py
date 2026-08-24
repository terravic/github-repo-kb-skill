"""
Repository Query and Semantic Matcher Engine.

Analyzes user software requests against a scanned repository knowledge base to identify
the best-suited repository or determine that no repository matches the query.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple


GENERIC_TERMS: Set[str] = {
    "service", "engine", "system", "app", "application", "platform",
    "manager", "data", "tool", "module", "base", "core", "handler", "worker"
}

STOP_WORDS: Set[str] = {
    "a", "an", "the", "in", "on", "of", "for", "to", "with", "and", "or",
    "is", "are", "do", "does", "have", "has", "want", "need", "looking",
    "find", "which", "repo", "repository", "software", "program", "code",
    "project", "i", "we", "can", "should", "me", "there", "any", "best",
    "tell", "show", "give", "help", "about", "handling", "suited"
}

# Semantic synonym mappings
SYNONYMS: Dict[str, Set[str]] = {
    "auth": {"authentication", "oauth", "oauth2", "oidc", "login", "identity", "jwt", "rbac", "security", "sso"},
    "authentication": {"auth", "oauth", "oauth2", "oidc", "login", "identity", "jwt", "security"},
    "login": {"auth", "authentication", "oauth", "identity", "session", "signin"},
    "sdk": {"client", "library", "bindings", "api-client"},
    "client": {"sdk", "library", "frontend", "ui"},
    "ui": {"frontend", "portal", "dashboard", "interface", "react", "vue", "web"},
    "dashboard": {"ui", "portal", "frontend", "console", "admin"},
    "database": {"db", "sql", "postgres", "postgresql", "redis", "warehouse", "store"},
    "stream": {"streaming", "kafka", "pipeline", "queue", "events", "real-time"},
    "streaming": {"stream", "kafka", "pipeline", "events", "real-time"},
    "ai": {"ml", "model", "llm", "embeddings", "rag", "neural", "deep-learning"},
    "ml": {"ai", "model", "inference", "prediction", "anomaly"},
    "infra": {"infrastructure", "terraform", "kubernetes", "k8s", "helm", "devops", "deploy"},
    "infrastructure": {"infra", "terraform", "kubernetes", "k8s", "helm", "devops", "cloud"},
    "docs": {"documentation", "spec", "guide", "tutorial", "rfc", "openapi"},
    "documentation": {"docs", "spec", "guide", "reference"},
}


class RepositoryQueryEngine:
    """Matches user capability queries against repository metadata and returns ranked recommendations."""

    def __init__(self, knowledge_base: Optional[Dict[str, Any]] = None, kb_path: Optional[str] = None):
        if knowledge_base:
            self.kb = knowledge_base
        elif kb_path and os.path.isfile(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
        else:
            self.kb = {}

        self.repositories: List[Dict[str, Any]] = self.kb.get("repositories", [])
        self.clusters: List[Dict[str, Any]] = self.kb.get("clusters", [])

    def load_kb_file(self, kb_path: str) -> None:
        """Load knowledge base from a JSON file path."""
        if not os.path.isfile(kb_path):
            raise FileNotFoundError(f"Knowledge base file not found: {kb_path}")
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)
        self.repositories = self.kb.get("repositories", [])
        self.clusters = self.kb.get("clusters", [])

    def query(self, user_query: str, top_k: int = 3, min_score_threshold: float = 3.5) -> Dict[str, Any]:
        """
        Evaluate user query against all repositories in the knowledge base.
        Returns match status, best suited repository, candidates, and reasoning.
        """
        cleaned_query = user_query.strip().lower()
        if not cleaned_query:
            return {
                "matched": False,
                "query": user_query,
                "message": "Query string is empty. Please describe the program or software capability you are looking for.",
                "best_match": None,
                "candidates": [],
            }

        if not self.repositories:
            return {
                "matched": False,
                "query": user_query,
                "message": "No repositories are loaded in the knowledge base.",
                "best_match": None,
                "candidates": [],
            }

        # Tokenize query into keywords
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.\+]+\b", cleaned_query)
        search_terms = [t for t in raw_tokens if t not in STOP_WORDS and len(t) > 1]

        if not search_terms:
            return {
                "matched": False,
                "query": user_query,
                "message": "No specific keywords found in query. Please describe specific functionality or technology.",
                "best_match": None,
                "candidates": [],
            }

        specific_terms = [t for t in search_terms if t not in GENERIC_TERMS]

        # Expand search terms with synonyms
        expanded_terms = set(search_terms)
        for term in search_terms:
            if term in SYNONYMS:
                expanded_terms.update(SYNONYMS[term])

        scored_results: List[Tuple[float, Dict[str, Any], List[str], int]] = []

        for repo in self.repositories:
            score = 0.0
            reasons: List[str] = []
            matched_specific_count = 0

            repo_name = repo.get("name", "").lower()
            repo_desc = (repo.get("description") or "").lower()
            readme = (repo.get("readme_summary") or "").lower()
            lang = (repo.get("primary_language") or "").lower()
            topics = [t.lower() for t in repo.get("topics", [])]
            tech_stack = [t.lower() for t in repo.get("tech_stack", [])]
            cluster_name = (repo.get("cluster_name") or "").lower()
            name_parts = set(repo_name.split("-") + repo_name.split("_") + [repo_name])

            # Exact phrase match bonus
            if len(cleaned_query) > 5 and (cleaned_query in repo_desc or cleaned_query in repo_name):
                score += 8.0
                reasons.append("Exact phrase match in repository title or description")

            for term in search_terms:
                is_generic = term in GENERIC_TERMS
                term_matched = False
                synonyms = SYNONYMS.get(term, set())

                # 1. Exact match in name
                if term in name_parts:
                    val = 2.0 if is_generic else 6.0
                    score += val
                    reasons.append(f"Repository name includes '{term}'")
                    term_matched = True
                elif any(syn in name_parts for syn in synonyms):
                    matched_syn = next(syn for syn in synonyms if syn in name_parts)
                    val = 1.5 if is_generic else 5.0
                    score += val
                    reasons.append(f"Repository name matches '{matched_syn}' (related to '{term}')")
                    term_matched = True
                elif term in repo_name:
                    val = 1.0 if is_generic else 3.5
                    score += val
                    reasons.append(f"Repository name contains keyword '{term}'")
                    term_matched = True

                # 2. Topic tag match
                if term in topics:
                    val = 1.5 if is_generic else 5.0
                    score += val
                    reasons.append(f"Topic tag matches '{term}'")
                    term_matched = True
                elif any(syn in topics for syn in synonyms):
                    matched_syn = next(syn for syn in synonyms if syn in topics)
                    val = 1.0 if is_generic else 4.0
                    score += val
                    reasons.append(f"Topic tag matches '{matched_syn}' (related to '{term}')")
                    term_matched = True

                # 3. Tech stack match
                if term in tech_stack:
                    val = 1.5 if is_generic else 4.0
                    score += val
                    reasons.append(f"Tech stack includes '{term}'")
                    term_matched = True
                elif any(syn in tech_stack for syn in synonyms):
                    matched_syn = next(syn for syn in synonyms if syn in tech_stack)
                    val = 1.0 if is_generic else 3.5
                    score += val
                    reasons.append(f"Tech stack includes '{matched_syn}' (related to '{term}')")
                    term_matched = True

                # 4. Primary language match
                if term == lang:
                    score += 4.0
                    reasons.append(f"Primary programming language is '{term.title()}'")
                    term_matched = True

                # 5. Description match
                if re.search(r"\b" + re.escape(term) + r"\b", repo_desc):
                    val = 1.0 if is_generic else 3.5
                    score += val
                    reasons.append(f"Description mentions '{term}'")
                    term_matched = True
                elif any(re.search(r"\b" + re.escape(syn) + r"\b", repo_desc) for syn in synonyms):
                    matched_syn = next(syn for syn in synonyms if re.search(r"\b" + re.escape(syn) + r"\b", repo_desc))
                    val = 0.5 if is_generic else 2.5
                    score += val
                    reasons.append(f"Description mentions '{matched_syn}' (related to '{term}')")
                    term_matched = True

                # 6. Readme summary match
                if re.search(r"\b" + re.escape(term) + r"\b", readme):
                    val = 0.5 if is_generic else 2.0
                    score += val
                    reasons.append(f"Readme mentions '{term}'")
                    term_matched = True

                # 7. Cluster domain match
                if term in cluster_name:
                    val = 0.5 if is_generic else 2.0
                    score += val
                    reasons.append(f"Belongs to domain '{term}'")
                    term_matched = True

                if term_matched and not is_generic:
                    matched_specific_count += 1

            if score > 0:
                scored_results.append((score, repo, list(dict.fromkeys(reasons)), matched_specific_count))

        # Filter out cases where specific terms were requested but none matched
        if specific_terms:
            scored_results = [r for r in scored_results if r[3] > 0]

        scored_results.sort(key=lambda x: x[0], reverse=True)

        if not scored_results or scored_results[0][0] < min_score_threshold:
            available_domains = [c.get("name") for c in self.clusters]
            domain_list_str = ", ".join(available_domains) if available_domains else "None"
            return {
                "matched": False,
                "query": user_query,
                "message": (
                    f"No repository in this organization can answer your need for '{user_query}'. "
                    f"The scanned organization contains repositories across these domains: {domain_list_str}."
                ),
                "best_match": None,
                "candidates": [],
                "available_domains": available_domains,
            }

        best_score, best_repo, best_reasons, _ = scored_results[0]
        confidence = "High" if best_score >= 6.0 else ("Moderate" if best_score >= 3.5 else "Low")

        candidates: List[Dict[str, Any]] = []
        for s, r, r_reasons, _ in scored_results[:top_k]:
            candidates.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "html_url": r.get("html_url"),
                "description": r.get("description"),
                "primary_language": r.get("primary_language"),
                "cluster_name": r.get("cluster_name"),
                "stars": r.get("stars", 0),
                "match_score": round(s, 2),
                "confidence": "High" if s >= 6.0 else ("Moderate" if s >= 3.5 else "Low"),
                "reasons": r_reasons,
            })

        best_match_payload = {
            "name": best_repo.get("name"),
            "html_url": best_repo.get("html_url"),
            "description": best_repo.get("description"),
            "primary_language": best_repo.get("primary_language"),
            "cluster_name": best_repo.get("cluster_name"),
            "stars": best_repo.get("stars", 0),
            "topics": best_repo.get("topics", []),
            "tech_stack": best_repo.get("tech_stack", []),
            "match_score": round(best_score, 2),
            "confidence": confidence,
            "justification": f"Repository '{best_repo.get('name')}' is best suited because: " + "; ".join(best_reasons[:3]) + ".",
            "reasons": best_reasons,
        }

        return {
            "matched": True,
            "query": user_query,
            "message": f"Found best-suited repository: '{best_repo.get('name')}' ({confidence} confidence).",
            "best_match": best_match_payload,
            "candidates": candidates,
        }
