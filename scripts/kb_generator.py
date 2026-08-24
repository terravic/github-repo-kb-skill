"""
Knowledge Base Artifact Generator.

Generates structured JSON and Markdown knowledge base documentation from scanned repository
metadata, clusters, and knowledge graph relationships.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


class KnowledgeBaseGenerator:
    """Produces JSON and Markdown knowledge base artifacts."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir

    def generate_all(
        self,
        metadata: Dict[str, Any],
        clusters_data: Dict[str, Any],
        graph_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate knowledge_base.json, knowledge_graph.json, and KNOWLEDGE_BASE.md.
        Returns a dictionary of generated file paths.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        scanned_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        metadata["generated_at"] = scanned_time

        kb_dict = {
            "metadata": metadata,
            "summary": {
                "total_repositories": len(clusters_data.get("repositories", [])),
                "total_clusters": clusters_data.get("cluster_count", 0),
                "total_graph_nodes": graph_data.get("total_nodes", 0),
                "total_graph_edges": graph_data.get("total_edges", 0),
                "cross_cluster_edges": graph_data.get("cross_cluster_edges_count", 0),
                "intra_cluster_edges": graph_data.get("intra_cluster_edges_count", 0),
                "hub_repositories": graph_data.get("hub_repositories", []),
                "bridge_repositories": graph_data.get("bridge_repositories", []),
            },
            "clusters": clusters_data.get("clusters", []),
            "repositories": clusters_data.get("repositories", []),
            "knowledge_graph": {
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", []),
                "cluster_connectivity_matrix": graph_data.get("cluster_connectivity_matrix", {}),
            },
        }

        # 1. Write knowledge_base.json
        kb_json_path = os.path.join(self.output_dir, "knowledge_base.json")
        with open(kb_json_path, "w", encoding="utf-8") as f:
            json.dump(kb_dict, f, indent=2)

        # 2. Write knowledge_graph.json
        graph_json_path = os.path.join(self.output_dir, "knowledge_graph.json")
        with open(graph_json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "nodes": graph_data.get("nodes", []),
                    "links": graph_data.get("edges", []),
                    "metrics": {
                        "total_nodes": graph_data.get("total_nodes", 0),
                        "total_edges": graph_data.get("total_edges", 0),
                        "cross_cluster_edges": graph_data.get("cross_cluster_edges_count", 0),
                    }
                },
                f,
                indent=2
            )

        # 3. Write KNOWLEDGE_BASE.md
        kb_md_path = os.path.join(self.output_dir, "KNOWLEDGE_BASE.md")
        md_content = self._build_markdown_report(kb_dict)
        with open(kb_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {
            "knowledge_base_json": kb_json_path,
            "knowledge_graph_json": graph_json_path,
            "knowledge_base_md": kb_md_path,
        }

    def _build_markdown_report(self, kb: Dict[str, Any]) -> str:
        """
        Format comprehensive technical knowledge base markdown without icons or emojis.
        """
        meta = kb.get("metadata", {})
        summary = kb.get("summary", {})
        clusters = kb.get("clusters", [])
        graph = kb.get("knowledge_graph", {})
        edges = graph.get("edges", [])

        lines: List[str] = []

        target_name = meta.get("owner", "Target Organization")
        lines.append(f"# Knowledge Base: {target_name}")
        lines.append("")
        lines.append(f"Generated on {meta.get('generated_at', 'N/A')} for target `{meta.get('input_url', 'N/A')}`.")
        lines.append("")

        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Target Address | {meta.get('input_url', 'N/A')} |")
        lines.append(f"| Total Repositories | {summary.get('total_repositories', 0)} |")
        lines.append(f"| Functional Clusters | {summary.get('total_clusters', 0)} |")
        lines.append(f"| Architecture Graph Nodes | {summary.get('total_graph_nodes', 0)} |")
        lines.append(f"| Graph Edges (Relationships) | {summary.get('total_graph_edges', 0)} |")
        lines.append(f"| Cross-Cluster Connections | {summary.get('cross_cluster_edges', 0)} |")
        lines.append(f"| Intra-Cluster Connections | {summary.get('intra_cluster_edges', 0)} |")
        lines.append("")

        if summary.get("hub_repositories"):
            hubs = ", ".join([f"`{h}`" for h in summary.get("hub_repositories", [])])
            lines.append(f"**Key Architectural Hubs**: {hubs}")
            lines.append("")

        if summary.get("bridge_repositories"):
            bridges = ", ".join([f"`{b}`" for b in summary.get("bridge_repositories", [])])
            lines.append(f"**Cross-Domain Bridge Repositories**: {bridges}")
            lines.append("")

        # Cluster breakdown section
        lines.append("## Domain Clusters")
        lines.append("")
        lines.append("Repositories are categorized into the following functional domains based on code analysis, topic taxonomy, and dependencies:")
        lines.append("")

        repo_lookup = {r["id"]: r for r in kb.get("repositories", [])}

        for cluster in clusters:
            lines.append(f"### {cluster['name']}")
            lines.append("")
            lines.append(f"**Description**: {cluster['description']}")
            lines.append("")
            lines.append(f"- Repositories: {cluster.get('repo_count', 0)}")
            lines.append(f"- Aggregate Stars: {cluster.get('total_stars', 0)}")
            top_langs = ", ".join(cluster.get("top_languages", [])) or "None specified"
            lines.append(f"- Primary Languages: {top_langs}")
            tech_stack = ", ".join(cluster.get("tech_stack", [])) or "None"
            lines.append(f"- Key Technologies: {tech_stack}")
            lines.append("")

            lines.append("| Repository | Language | Stars | Description |")
            lines.append("|---|---|---|---|")
            for repo_id in cluster.get("repositories", []):
                repo = repo_lookup.get(repo_id)
                if not repo:
                    continue
                name_link = f"[{repo['name']}]({repo.get('html_url', '#')})"
                lang = repo.get("primary_language", "Other")
                stars = repo.get("stars", 0)
                desc = repo.get("description", "No description").replace("|", "\\|")
                lines.append(f"| {name_link} | {lang} | {stars} | {desc} |")
            lines.append("")

        # Knowledge graph relationships section
        lines.append("## Knowledge Graph Relationships")
        lines.append("")
        lines.append("The knowledge graph models direct dependencies, API integrations, client SDK usage, and shared technology stacks:")
        lines.append("")

        # Group edges by type
        edges_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for edge in edges:
            rel = edge.get("type", "related_to")
            edges_by_type.setdefault(rel, []).append(edge)

        for rel_type, type_edges in edges_by_type.items():
            type_title = rel_type.replace("_", " ").title()
            lines.append(f"### {type_title} ({len(type_edges)} relationships)")
            lines.append("")
            lines.append("| Source Repository | Target Repository | Scope | Description |")
            lines.append("|---|---|---|---|")
            for e in type_edges:
                src_repo = repo_lookup.get(e["source"], {}).get("name", str(e["source"]))
                tgt_repo = repo_lookup.get(e["target"], {}).get("name", str(e["target"]))
                scope = "Cross-Cluster" if e.get("is_cross_cluster") else "Intra-Cluster"
                desc = e.get("description", "").replace("|", "\\|")
                lines.append(f"| `{src_repo}` | `{tgt_repo}` | {scope} | {desc} |")
            lines.append("")

        # Cross-Cluster Dependency Matrix
        lines.append("## Cross-Domain Dependency Matrix")
        lines.append("")
        lines.append("Matrix of relationship counts originating from source cluster (rows) to target cluster (columns):")
        lines.append("")

        matrix = graph.get("cluster_connectivity_matrix", {})
        cluster_ids = [c["id"] for c in clusters]
        cluster_name_map = {c["id"]: c["name"] for c in clusters}

        header = "| Source \\ Target | " + " | ".join([cluster_name_map.get(cid, cid) for cid in cluster_ids]) + " |"
        sep = "|---|" + "|".join(["---" for _ in cluster_ids]) + "|"
        lines.append(header)
        lines.append(sep)

        for src_id in cluster_ids:
            row_name = cluster_name_map.get(src_id, src_id)
            row_vals = []
            for tgt_id in cluster_ids:
                count = matrix.get(src_id, {}).get(tgt_id, 0)
                row_vals.append(str(count) if count > 0 else "-")
            lines.append(f"| **{row_name}** | " + " | ".join(row_vals) + " |")

        lines.append("")
        lines.append("## Architecture Notes and Recommendations")
        lines.append("")
        lines.append("1. **Modularity**: Hub repositories with high degree centrality should be prioritized for stability, backwards compatibility, and rigorous test coverage.")
        lines.append("2. **Boundary Contracts**: Cross-cluster dependencies should enforce versioned API contracts or SDK interfaces to prevent breaking changes across domains.")
        lines.append("3. **Shared Tooling**: Shared libraries should maintain minimal third-party dependencies to avoid dependency conflicts across downstream services.")
        lines.append("")

        return "\n".join(lines)
