"""
Knowledge Graph Construction and Centrality Analysis Engine.

Generates nodes and relationships (intra-cluster and inter-cluster) between repositories,
calculates centrality metrics, detects architecture hubs, and produces clean edge descriptions
for any public GitHub organization, user, or repository collection.
"""

import re
from typing import Any, Dict, List, Set, Tuple


class KnowledgeGraphBuilder:
    """Builds a structured knowledge graph representing repository relationships and architecture."""

    def __init__(self, min_shared_tech_threshold: int = 1):
        self.min_shared_tech_threshold = min_shared_tech_threshold

    def build_graph(
        self,
        repositories: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Construct nodes and edges from repository metadata, dependencies, and cluster domains.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        repo_by_name: Dict[str, Dict[str, Any]] = {
            r["name"].lower(): r for r in repositories
        }
        repo_by_id: Dict[Any, Dict[str, Any]] = {
            r["id"]: r for r in repositories
        }

        # Track degrees for centrality
        in_degree: Dict[Any, int] = {r["id"]: 0 for r in repositories}
        out_degree: Dict[Any, int] = {r["id"]: 0 for r in repositories}
        connected_clusters: Dict[Any, Set[str]] = {r["id"]: set() for r in repositories}
        edge_keys_seen: Set[Tuple[Any, Any, str]] = set()

        def add_edge(
            source_id: Any,
            target_id: Any,
            rel_type: str,
            label: str,
            description: str,
            weight: float = 1.0,
        ):
            if source_id == target_id:
                return
            edge_key = (source_id, target_id, rel_type)
            rev_key = (target_id, source_id, rel_type)
            if edge_key in edge_keys_seen or (rel_type == "shares_tech" and rev_key in edge_keys_seen):
                return

            edge_keys_seen.add(edge_key)
            src_repo = repo_by_id.get(source_id, {})
            tgt_repo = repo_by_id.get(target_id, {})

            src_cluster = src_repo.get("cluster_id", "general")
            tgt_cluster = tgt_repo.get("cluster_id", "general")
            is_cross = src_cluster != tgt_cluster

            edges.append({
                "source": source_id,
                "target": target_id,
                "type": rel_type,
                "label": label,
                "description": description,
                "weight": weight,
                "is_cross_cluster": is_cross,
                "source_cluster": src_cluster,
                "target_cluster": tgt_cluster,
            })

            out_degree[source_id] = out_degree.get(source_id, 0) + 1
            in_degree[target_id] = in_degree.get(target_id, 0) + 1
            if is_cross:
                connected_clusters[source_id].add(tgt_cluster)
                connected_clusters[target_id].add(src_cluster)

        # 1. Direct Name & Dependency matching
        for repo in repositories:
            repo_id = repo["id"]
            repo_name = repo["name"].lower()
            repo_desc = (repo.get("description") or "").lower()
            deps = [d.lower() for d in repo.get("dependencies", [])]

            for dep in deps:
                matched_target = None
                if dep in repo_by_name:
                    matched_target = repo_by_name[dep]
                else:
                    clean_dep = dep.split("/")[-1]
                    if clean_dep in repo_by_name:
                        matched_target = repo_by_name[clean_dep]

                if matched_target and matched_target["id"] != repo_id:
                    add_edge(
                        source_id=repo_id,
                        target_id=matched_target["id"],
                        rel_type="depends_on",
                        label="Depends on",
                        description=f"{repo['name']} imports and depends on {matched_target['name']}.",
                        weight=2.5,
                    )

            # Check if other repositories in the org are mentioned in description
            for other_name, other_repo in repo_by_name.items():
                if other_repo["id"] == repo_id or len(other_name) < 3:
                    continue
                # Look for whole word mention of other repo
                if re.search(r"\b" + re.escape(other_name) + r"\b", repo_desc):
                    add_edge(
                        source_id=repo_id,
                        target_id=other_repo["id"],
                        rel_type="integrates_with",
                        label="Integrates with",
                        description=f"{repo['name']} references and integrates with {other_repo['name']}.",
                        weight=2.0,
                    )

            # 2. Architectural Role Relationships
            if "sdk" in repo_name or "client" in repo_name:
                for other in repositories:
                    if other["id"] == repo_id:
                        continue
                    if other.get("cluster_id") == "core-services" and any(
                        term in other["name"].lower() for term in ["api", "gateway"]
                    ):
                        add_edge(
                            source_id=repo_id,
                            target_id=other["id"],
                            rel_type="interfaces_with",
                            label="Client SDK for",
                            description=f"{repo['name']} provides client bindings for {other['name']}.",
                            weight=1.8,
                        )

            if "gateway" in repo_name or "proxy" in repo_name:
                for other in repositories:
                    if other["id"] == repo_id:
                        continue
                    if other.get("cluster_id") == "core-services" and "gateway" not in other["name"].lower():
                        add_edge(
                            source_id=repo_id,
                            target_id=other["id"],
                            rel_type="routes_to",
                            label="Routes API to",
                            description=f"{repo['name']} routes API requests to {other['name']}.",
                            weight=2.0,
                        )

            if repo.get("cluster_id") == "frontend-ui":
                for other in repositories:
                    if other["id"] == repo_id:
                        continue
                    if "sdk" in other["name"].lower() or "client" in other["name"].lower():
                        add_edge(
                            source_id=repo_id,
                            target_id=other["id"],
                            rel_type="depends_on",
                            label="Consumes SDK",
                            description=f"{repo['name']} uses {other['name']} for API integration.",
                            weight=2.0,
                        )

            if repo.get("cluster_id") == "infrastructure-devops":
                for other in repositories:
                    if other["id"] == repo_id:
                        continue
                    if other.get("cluster_id") in ["core-services", "data-analytics"]:
                        if any(term in other["name"].lower() for term in ["gateway", "pipeline", "auth", "server", "app"]):
                            add_edge(
                                source_id=repo_id,
                                target_id=other["id"],
                                rel_type="provisions",
                                label="Provisions & Deploys",
                                description=f"{repo['name']} manages infrastructure and deployment for {other['name']}.",
                                weight=1.2,
                            )

            if repo.get("cluster_id") == "libraries-shared":
                for other in repositories:
                    if other["id"] == repo_id:
                        continue
                    if other.get("cluster_id") in ["core-services"]:
                        add_edge(
                            source_id=other["id"],
                            target_id=repo_id,
                            rel_type="depends_on",
                            label="Uses Shared Lib",
                            description=f"{other['name']} leverages common utilities from {repo['name']}.",
                            weight=1.5,
                        )

        # 3. Shared Architectural Tech & Ecosystem Relationships
        high_value_tech = {
            "kafka", "redis", "postgresql", "postgres", "grpc", "rabbitmq", "docker", "kubernetes", "fastapi", "flask", "react"
        }
        for i, repo_a in enumerate(repositories):
            tech_a = set(t.lower() for t in repo_a.get("tech_stack", []) if t.lower() in high_value_tech)
            for repo_b in repositories[i + 1:]:
                tech_b = set(t.lower() for t in repo_b.get("tech_stack", []) if t.lower() in high_value_tech)
                common = tech_a.intersection(tech_b)
                if common and len(common) >= self.min_shared_tech_threshold:
                    tech_list_str = ", ".join(sorted(list(common)))
                    if (repo_a["id"], repo_b["id"], "depends_on") not in edge_keys_seen and (
                        repo_b["id"], repo_a["id"], "depends_on"
                    ) not in edge_keys_seen:
                        add_edge(
                            source_id=repo_a["id"],
                            target_id=repo_b["id"],
                            rel_type="shares_tech",
                            label=f"Shared Tech ({tech_list_str})",
                            description=f"{repo_a['name']} and {repo_b['name']} both utilize {tech_list_str}.",
                            weight=1.0,
                        )

        # 4. Fallback Shared Tech or Cluster Affinity for Small / Monolithic Orgs
        if len(edges) < len(repositories) and len(repositories) > 1:
            for i, repo_a in enumerate(repositories):
                lang_a = (repo_a.get("primary_language") or "").lower()
                cluster_a = repo_a.get("cluster_id")
                for repo_b in repositories[i + 1:]:
                    lang_b = (repo_b.get("primary_language") or "").lower()
                    cluster_b = repo_b.get("cluster_id")

                    # Connect if same cluster or same primary language (if not already connected)
                    if (cluster_a == cluster_b and cluster_a != "general") or (lang_a and lang_a == lang_b and lang_a != "other"):
                        if (repo_a["id"], repo_b["id"], "shares_tech") not in edge_keys_seen and (
                            repo_b["id"], repo_a["id"], "shares_tech"
                        ) not in edge_keys_seen and (
                            repo_a["id"], repo_b["id"], "depends_on"
                        ) not in edge_keys_seen:
                            reason = f"Shared {repo_a.get('primary_language')} stack" if lang_a == lang_b else f"Shared domain ({repo_a.get('cluster_name')})"
                            add_edge(
                                source_id=repo_a["id"],
                                target_id=repo_b["id"],
                                rel_type="shares_tech",
                                label=reason,
                                description=f"{repo_a['name']} and {repo_b['name']} share {reason.lower()}.",
                                weight=0.8,
                            )
                            if len(edges) >= len(repositories) * 2:
                                break

        # Calculate Centrality and Hub Classification
        total_repos = len(repositories)
        cluster_lookup = {c["id"]: c for c in clusters}

        for repo in repositories:
            rid = repo["id"]
            in_deg = in_degree.get(rid, 0)
            out_deg = out_degree.get(rid, 0)
            total_deg = in_deg + out_deg

            centrality_score = 0.0
            if total_repos > 1:
                centrality_score = round(total_deg / (total_repos - 1), 3)

            cluster_info = cluster_lookup.get(repo.get("cluster_id"), {})
            cluster_color = cluster_info.get("color", "#3B82F6")
            cluster_name = cluster_info.get("name", "General")

            is_hub = (total_deg >= 4) or (centrality_score >= 0.35 and total_deg >= 2)
            is_bridge = len(connected_clusters.get(rid, set())) >= 2

            nodes.append({
                "id": rid,
                "name": repo.get("name", f"repo-{rid}"),
                "full_name": repo.get("full_name", repo.get("name", f"repo-{rid}")),
                "html_url": repo.get("html_url", f"https://github.com/{repo.get('name', '')}"),
                "description": repo.get("description", "No description provided."),
                "primary_language": repo.get("primary_language", "Other"),
                "topics": repo.get("topics", []),
                "tech_stack": repo.get("tech_stack", []),
                "stars": repo.get("stars", 0),
                "forks": repo.get("forks", 0),
                "open_issues": repo.get("open_issues", 0),
                "cluster_id": repo.get("cluster_id", "general"),
                "cluster_name": cluster_name,
                "cluster_color": cluster_color,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": total_deg,
                "centrality_score": centrality_score,
                "is_hub": is_hub,
                "is_bridge": is_bridge,
            })

        # Inter-cluster connectivity matrix
        connectivity_matrix: Dict[str, Dict[str, int]] = {}
        for c1 in clusters:
            connectivity_matrix[c1["id"]] = {c2["id"]: 0 for c2 in clusters}

        cross_cluster_count = 0
        intra_cluster_count = 0

        for e in edges:
            src_c = e["source_cluster"]
            tgt_c = e["target_cluster"]
            if src_c in connectivity_matrix and tgt_c in connectivity_matrix[src_c]:
                connectivity_matrix[src_c][tgt_c] += 1
            if e["is_cross_cluster"]:
                cross_cluster_count += 1
            else:
                intra_cluster_count += 1

        hubs = [n["name"] for n in nodes if n["is_hub"]]
        bridges = [n["name"] for n in nodes if n["is_bridge"]]

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "hub_repositories": hubs,
            "bridge_repositories": bridges,
            "cross_cluster_edges_count": cross_cluster_count,
            "intra_cluster_edges_count": intra_cluster_count,
            "cluster_connectivity_matrix": connectivity_matrix,
        }
