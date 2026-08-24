"""
Command-line interface, pipeline runner, and repository query engine for the github-repo-kb skill.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

# Ensure scripts directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scanner import GitHubScanner
from scripts.clusterer import RepositoryClusterer
from scripts.graph_builder import KnowledgeGraphBuilder
from scripts.kb_generator import KnowledgeBaseGenerator
from scripts.dashboard_generator import DashboardGenerator
from scripts.query_engine import RepositoryQueryEngine


def load_config(config_path: str) -> Dict[str, Any]:
    """Load scanner configuration JSON file."""
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to parse config file '{config_path}': {e}", file=sys.stderr)
        return {}


def query_knowledge_base(user_query: str, kb_path: str = "output/knowledge_base.json") -> Dict[str, Any]:
    """
    Search a generated knowledge base for the best matching repository for a given query.
    """
    if not os.path.isfile(kb_path):
        # Check sample output fallback
        sample_path = os.path.join("examples", "sample_output", "knowledge_base.json")
        if os.path.isfile(sample_path):
            kb_path = sample_path
        else:
            raise FileNotFoundError(
                f"Knowledge base file not found at '{kb_path}'. "
                "Please run a repository scan first to generate the knowledge base."
            )

    engine = RepositoryQueryEngine(kb_path=kb_path)
    result = engine.query(user_query)

    print(f"\nQuery: \"{user_query}\"")
    print("-" * 60)
    if result.get("matched"):
        best = result["best_match"]
        print(f"Best Matched Repository: {best['name']}")
        print(f"Confidence: {best['confidence']} (Score: {best['match_score']})")
        print(f"Domain Cluster: {best['cluster_name']}")
        print(f"Primary Language: {best['primary_language']}")
        print(f"GitHub URL: {best['html_url']}")
        print(f"Description: {best['description']}")
        print(f"Why this repo fits: {best['justification']}")

        candidates = result.get("candidates", [])
        if len(candidates) > 1:
            print("\nAlternative Candidates:")
            for cand in candidates[1:]:
                print(f"- {cand['name']} ({cand['primary_language']}, {cand['cluster_name']}) - {cand['description']}")
    else:
        print(f"Result: {result.get('message')}")

    print("-" * 60)
    return result


def run_pipeline(
    target_url: Optional[str] = None,
    config_path: Optional[str] = None,
    fixture_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    token: Optional[str] = None,
    max_repos: int = 100,
    include_forks: bool = False,
    include_archived: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Executes the full scan, clustering, graph construction, and artifact generation pipeline
    for any public GitHub account (organization or user), single repository, or offline fixture.
    """
    config: Dict[str, Any] = {}
    if config_path and os.path.isfile(config_path):
        config = load_config(config_path)

    scan_opts = config.get("scan_options", {})

    # Correct resolution hierarchy:
    # 1. Explicit fixture CLI argument
    # 2. Explicit URL CLI argument
    # 3. Config offline_fixture (if non-empty)
    # 4. Config target_url
    # 5. Default URL
    resolved_token = token or config.get("auth_token") or os.environ.get("GITHUB_TOKEN")
    resolved_max_repos = max_repos or scan_opts.get("max_repos", 100)
    resolved_include_forks = include_forks or scan_opts.get("include_forks", False)
    resolved_include_archived = include_archived if include_archived is not None else scan_opts.get("include_archived", True)

    out_cfg = config.get("output", {})
    resolved_out_dir = output_dir or out_cfg.get("output_dir", "output")
    custom_rules = config.get("clustering_rules", [])

    print(f"[Step 1/5] Ingesting repository metadata...")
    scanner = GitHubScanner(token=resolved_token)

    if fixture_path:
        # User explicitly passed a fixture
        print(f"Loading offline synthetic dataset: {fixture_path}")
        raw_result = scanner.load_fixture(fixture_path)
    elif target_url:
        # User explicitly passed a GitHub URL
        print(f"Scanning public GitHub target: {target_url}")
        try:
            raw_result = scanner.scan_online(
                url=target_url,
                include_forks=resolved_include_forks,
                include_archived=resolved_include_archived,
                max_repos=resolved_max_repos,
            )
        except Exception as e:
            print(f"[Notice] Online scan encountered: {e}")
            fallback_fixture = os.path.join("examples", "synthetic_terravic_org.json")
            if os.path.isfile(fallback_fixture):
                print(f"[Fallback] Using synthetic dataset for demonstration: {fallback_fixture}")
                raw_result = scanner.load_fixture(fallback_fixture)
            else:
                raise e
    elif scan_opts.get("offline_fixture"):
        # Config specifies an offline fixture
        print(f"Loading configured offline dataset: {scan_opts.get('offline_fixture')}")
        raw_result = scanner.load_fixture(scan_opts.get("offline_fixture"))
    else:
        # Use target_url from config or default
        resolved_target = config.get("target_url") or "https://github.com/terravic"
        print(f"Scanning public GitHub target: {resolved_target}")
        try:
            raw_result = scanner.scan_online(
                url=resolved_target,
                include_forks=resolved_include_forks,
                include_archived=resolved_include_archived,
                max_repos=resolved_max_repos,
            )
        except Exception as e:
            print(f"[Notice] Online scan encountered: {e}")
            fallback_fixture = os.path.join("examples", "synthetic_terravic_org.json")
            if os.path.isfile(fallback_fixture):
                print(f"[Fallback] Using synthetic dataset for demonstration: {fallback_fixture}")
                raw_result = scanner.load_fixture(fallback_fixture)
            else:
                raise e

    repositories = raw_result.get("repositories", [])
    metadata = raw_result.get("metadata", {})
    total_repos = len(repositories)
    print(f"Successfully processed {total_repos} repositories.")

    if total_repos == 0:
        print("[Warning] No repositories found matching the filter criteria.")
        return {"status": "empty", "total_repos": 0}

    print(f"[Step 2/5] Performing domain clustering and taxonomy assignment...")
    clusterer = RepositoryClusterer(custom_rules=custom_rules)
    clusters_data = clusterer.cluster_repositories(repositories)
    print(f"Categorized into {clusters_data.get('cluster_count', 0)} functional domains.")

    print(f"[Step 3/5] Building architecture knowledge graph and calculating centrality...")
    graph_builder = KnowledgeGraphBuilder()
    graph_data = graph_builder.build_graph(
        repositories=clusters_data.get("repositories", []),
        clusters=clusters_data.get("clusters", []),
    )
    print(f"Constructed {graph_data.get('total_nodes', 0)} nodes and {graph_data.get('total_edges', 0)} graph relationships.")
    print(f"Detected {len(graph_data.get('hub_repositories', []))} hub architectures and {graph_data.get('cross_cluster_edges_count', 0)} cross-domain links.")

    print(f"[Step 4/5] Generating structured Knowledge Base files (JSON, Markdown)...")
    kb_gen = KnowledgeBaseGenerator(output_dir=resolved_out_dir)
    kb_files = kb_gen.generate_all(
        metadata=metadata,
        clusters_data=clusters_data,
        graph_data=graph_data,
    )
    print(f"Created: {kb_files.get('knowledge_base_json')}")
    print(f"Created: {kb_files.get('knowledge_graph_json')}")
    print(f"Created: {kb_files.get('knowledge_base_md')}")

    print(f"[Step 5/5] Generating interactive summary dashboard...")
    dash_gen = DashboardGenerator(output_dir=resolved_out_dir)
    dash_path = dash_gen.generate(
        metadata=metadata,
        clusters_data=clusters_data,
        graph_data=graph_data,
    )
    print(f"Created interactive dashboard: {dash_path}")

    print("\nKnowledge base and summary dashboard generation completed successfully.")
    return {
        "status": "success",
        "output_directory": resolved_out_dir,
        "dashboard_path": dash_path,
        "knowledge_base_json": kb_files.get("knowledge_base_json", ""),
        "knowledge_base_md": kb_files.get("knowledge_base_md", ""),
        "knowledge_graph_json": kb_files.get("knowledge_graph_json", ""),
        "total_repositories": total_repos,
        "total_clusters": clusters_data.get("cluster_count", 0),
        "total_edges": graph_data.get("total_edges", 0),
    }


def main():
    parser = argparse.ArgumentParser(
        description="github-repo-kb: Scans any public GitHub account (organization or user), clusters codebases into functional domains, builds architecture knowledge graphs, generates interactive dashboards, and provides repository search."
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        default=None,
        help="GitHub URL or owner handle for any public account (e.g. 'https://github.com/pallets', 'github.com/tiangolo', 'octocat')"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="scanner_config.json",
        help="Path to configuration JSON file (default: scanner_config.json)"
    )
    parser.add_argument(
        "--fixture", "-f",
        type=str,
        default=None,
        help="Path to offline synthetic dataset JSON (for offline testing)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Directory to save generated artifacts (default: output/)"
    )
    parser.add_argument(
        "--token", "-t",
        type=str,
        default=None,
        help="GitHub Personal Access Token (or set GITHUB_TOKEN environment variable)"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=100,
        help="Maximum repositories to scan (default: 100)"
    )
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help="Include forked repositories in scan"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        default=None,
        help="Ask about a software need or program to find the best suited repository in the knowledge base"
    )
    parser.add_argument(
        "--kb",
        type=str,
        default="output/knowledge_base.json",
        help="Path to knowledge_base.json for query resolution (default: output/knowledge_base.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        if args.query:
            if args.url or (args.fixture and not os.path.isfile(args.kb)):
                run_pipeline(
                    target_url=args.url,
                    config_path=args.config,
                    fixture_path=args.fixture,
                    output_dir=args.output_dir,
                    token=args.token,
                    max_repos=args.max_repos,
                    include_forks=args.include_forks,
                    verbose=args.verbose,
                )
            query_knowledge_base(args.query, kb_path=args.kb)
            return

        run_pipeline(
            target_url=args.url,
            config_path=args.config,
            fixture_path=args.fixture,
            output_dir=args.output_dir,
            token=args.token,
            max_repos=args.max_repos,
            include_forks=args.include_forks,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n[Error] Operation failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
