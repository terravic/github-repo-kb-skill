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
from scripts.security_utils import (
    MAX_CONFIG_BYTES,
    is_placeholder_token,
    load_json_limited,
    redact_secrets,
    strip_control_chars,
    validate_path_safe,
)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate scanner configuration JSON file with size limits."""
    try:
        safe_path = validate_path_safe(config_path, for_write=False)
    except ValueError as e:
        print(f"[Warning] Invalid config path '{config_path}': {redact_secrets(e)}", file=sys.stderr)
        return {}

    if not os.path.isfile(safe_path):
        return {}
    try:
        data = load_json_limited(safe_path, max_bytes=MAX_CONFIG_BYTES)
        if not isinstance(data, dict):
            print(f"[Warning] Config file '{config_path}' root must be a JSON object.", file=sys.stderr)
            return {}
        if "scan_options" in data and not isinstance(data["scan_options"], dict):
            print("[Warning] Ignoring non-object 'scan_options' in config file.", file=sys.stderr)
            data["scan_options"] = {}
        if "output" in data and not isinstance(data["output"], dict):
            print("[Warning] Ignoring non-object 'output' in config file.", file=sys.stderr)
            data["output"] = {}
        if "clustering_rules" in data:
            if not isinstance(data["clustering_rules"], list):
                print("[Warning] Ignoring non-list 'clustering_rules' in config file.", file=sys.stderr)
                data["clustering_rules"] = []
            else:
                data["clustering_rules"] = [r for r in data["clustering_rules"] if isinstance(r, dict)]
        return data
    except Exception as e:
        print(f"[Warning] Failed to parse config file '{config_path}': {redact_secrets(e)}", file=sys.stderr)
        return {}


def query_knowledge_base(user_query: str, kb_path: str = "output/knowledge_base.json") -> Dict[str, Any]:
    """
    Search a generated knowledge base for the best matching repository for a given query.
    """
    safe_kb_path = validate_path_safe(kb_path, for_write=False)
    if not os.path.isfile(safe_kb_path):
        # Check sample output fallback
        sample_path = os.path.join("examples", "sample_output", "knowledge_base.json")
        if os.path.isfile(sample_path):
            safe_kb_path = sample_path
        else:
            raise FileNotFoundError(
                f"Knowledge base file not found at '{kb_path}'. "
                "Please run a repository scan first to generate the knowledge base."
            )

    engine = RepositoryQueryEngine(kb_path=safe_kb_path)
    result = engine.query(user_query)

    print(f"\nQuery: \"{strip_control_chars(user_query)}\"")
    print("-" * 60)
    if result.get("matched"):
        best = result["best_match"]
        print(f"Best Matched Repository: {strip_control_chars(best.get('name'))}")
        print(f"Confidence: {strip_control_chars(best.get('confidence'))} (Score: {best.get('match_score')})")
        print(f"Domain Cluster: {strip_control_chars(best.get('cluster_name'))}")
        print(f"Primary Language: {strip_control_chars(best.get('primary_language'))}")
        print(f"GitHub URL: {strip_control_chars(best.get('html_url'))}")
        print(f"Description: {strip_control_chars(best.get('description'))}")
        print(f"Why this repo fits: {strip_control_chars(best.get('justification'))}")

        candidates = result.get("candidates", [])
        if len(candidates) > 1:
            print("\nAlternative Candidates:")
            for cand in candidates[1:]:
                print(
                    f"- {strip_control_chars(cand.get('name'))} "
                    f"({strip_control_chars(cand.get('primary_language'))}, "
                    f"{strip_control_chars(cand.get('cluster_name'))}) - "
                    f"{strip_control_chars(cand.get('description'))}"
                )
    else:
        print(f"Result: {strip_control_chars(result.get('message'))}")

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
    config_base_dir = os.getcwd()
    if config_path and os.path.isfile(config_path):
        config = load_config(config_path)
        config_base_dir = os.path.dirname(os.path.abspath(config_path))

    scan_opts = config.get("scan_options", {}) if isinstance(config.get("scan_options"), dict) else {}

    # Credential resolution with placeholder filtering and non-breaking security warnings
    cli_token = None if is_placeholder_token(token) else token.strip() if isinstance(token, str) else None
    cfg_raw_token = config.get("auth_token")
    cfg_token = None if is_placeholder_token(cfg_raw_token) else cfg_raw_token.strip() if isinstance(cfg_raw_token, str) else None
    env_raw_token = os.environ.get("GITHUB_TOKEN")
    env_token = None if is_placeholder_token(env_raw_token) else env_raw_token.strip() if isinstance(env_raw_token, str) else None

    if cli_token:
        print(
            "[Security Warning] Passing a GitHub token via --token exposes it in process listings "
            "and shell history. Prefer setting the GITHUB_TOKEN environment variable instead.",
            file=sys.stderr,
        )
    elif cfg_token:
        print(
            "[Security Warning] Plaintext 'auth_token' detected in configuration file. "
            "Prefer setting the GITHUB_TOKEN environment variable and leaving 'auth_token' empty.",
            file=sys.stderr,
        )

    resolved_token = cli_token or cfg_token or env_token
    active_secrets = [s for s in (cli_token, cfg_token, env_token, resolved_token) if s]

    raw_max_repos = max_repos or scan_opts.get("max_repos", 100)
    try:
        resolved_max_repos = max(1, min(int(raw_max_repos), 1000))
    except (TypeError, ValueError):
        resolved_max_repos = 100

    resolved_include_forks = bool(include_forks or scan_opts.get("include_forks", False))
    resolved_include_archived = include_archived if include_archived is not None else bool(scan_opts.get("include_archived", True))

    out_cfg = config.get("output", {}) if isinstance(config.get("output"), dict) else {}
    if output_dir is not None:
        resolved_out_dir = validate_path_safe(output_dir, for_write=True)
    else:
        cfg_out_dir = out_cfg.get("output_dir", "output")
        resolved_out_dir = validate_path_safe(
            cfg_out_dir,
            base_dir=config_base_dir,
            must_be_within_base=True,
            for_write=True,
        )

    custom_rules = config.get("clustering_rules", [])

    print("[Step 1/5] Ingesting repository metadata...")
    scanner = GitHubScanner(token=resolved_token)

    if fixture_path:
        # User explicitly passed a fixture
        safe_fixture = validate_path_safe(fixture_path, for_write=False)
        print(f"Loading offline synthetic dataset: {safe_fixture}")
        raw_result = scanner.load_fixture(safe_fixture)
    elif target_url:
        # User explicitly passed a GitHub URL
        print(f"Scanning public GitHub target: {strip_control_chars(target_url)}")
        try:
            raw_result = scanner.scan_online(
                url=target_url,
                include_forks=resolved_include_forks,
                include_archived=resolved_include_archived,
                max_repos=resolved_max_repos,
            )
        except Exception as e:
            print(f"[Notice] Online scan encountered: {redact_secrets(e, active_secrets)}")
            fallback_fixture = os.path.join("examples", "synthetic_sample_org.json")
            if os.path.isfile(fallback_fixture):
                print(f"[Fallback] Using synthetic dataset for demonstration: {fallback_fixture}")
                raw_result = scanner.load_fixture(fallback_fixture)
            else:
                raise e
    elif scan_opts.get("offline_fixture"):
        # Config specifies an offline fixture -- confine within config base directory
        safe_cfg_fixture = validate_path_safe(
            scan_opts.get("offline_fixture"),
            base_dir=config_base_dir,
            must_be_within_base=True,
            for_write=False,
        )
        print(f"Loading configured offline dataset: {safe_cfg_fixture}")
        raw_result = scanner.load_fixture(safe_cfg_fixture)
    else:
        # Use target_url from config or fallback to synthetic sample
        resolved_target = config.get("target_url")
        if resolved_target:
            print(f"Scanning public GitHub target: {strip_control_chars(resolved_target)}")
            try:
                raw_result = scanner.scan_online(
                    url=resolved_target,
                    include_forks=resolved_include_forks,
                    include_archived=resolved_include_archived,
                    max_repos=resolved_max_repos,
                )
            except Exception as e:
                print(f"[Notice] Online scan encountered: {redact_secrets(e, active_secrets)}")
                fallback_fixture = os.path.join("examples", "synthetic_sample_org.json")
                if os.path.isfile(fallback_fixture):
                    print(f"[Fallback] Using synthetic dataset for demonstration: {fallback_fixture}")
                    raw_result = scanner.load_fixture(fallback_fixture)
                else:
                    raise e
        else:
            fallback_fixture = os.path.join("examples", "synthetic_sample_org.json")
            if os.path.isfile(fallback_fixture):
                print(f"No target URL specified. Loading sample demonstration dataset: {fallback_fixture}")
                raw_result = scanner.load_fixture(fallback_fixture)
            else:
                raise ValueError("No target GitHub URL or fixture specified. Please provide --url <github-address>.")

    repositories = raw_result.get("repositories", [])
    metadata = raw_result.get("metadata", {})
    total_repos = len(repositories)
    print(f"Successfully processed {total_repos} repositories.")

    if total_repos == 0:
        print("[Warning] No repositories found matching the filter criteria.")
        return {"status": "empty", "total_repos": 0}

    print("[Step 2/5] Performing domain clustering and taxonomy assignment...")
    clusterer = RepositoryClusterer(custom_rules=custom_rules)
    clusters_data = clusterer.cluster_repositories(repositories)
    print(f"Categorized into {clusters_data.get('cluster_count', 0)} functional domains.")

    print("[Step 3/5] Building architecture knowledge graph and calculating centrality...")
    graph_builder = KnowledgeGraphBuilder()
    graph_data = graph_builder.build_graph(
        repositories=clusters_data.get("repositories", []),
        clusters=clusters_data.get("clusters", []),
    )
    print(f"Constructed {graph_data.get('total_nodes', 0)} nodes and {graph_data.get('total_edges', 0)} graph relationships.")
    print(f"Detected {len(graph_data.get('hub_repositories', []))} hub architectures and {graph_data.get('cross_cluster_edges_count', 0)} cross-domain links.")

    print("[Step 4/5] Generating structured Knowledge Base files (JSON, Markdown)...")
    kb_gen = KnowledgeBaseGenerator(output_dir=resolved_out_dir)
    kb_files = kb_gen.generate_all(
        metadata=metadata,
        clusters_data=clusters_data,
        graph_data=graph_data,
    )
    print(f"Created: {kb_files.get('knowledge_base_json')}")
    print(f"Created: {kb_files.get('knowledge_graph_json')}")
    print(f"Created: {kb_files.get('knowledge_base_md')}")

    print("[Step 5/5] Generating interactive summary dashboard...")
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
        help="GitHub Personal Access Token (prefer GITHUB_TOKEN environment variable to avoid exposing tokens in process listings)"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=100,
        help="Maximum repositories to scan (default: 100, max: 1000)"
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
    runtime_secrets = [args.token, os.environ.get("GITHUB_TOKEN")]

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
        print(f"\n[Error] Operation failed: {redact_secrets(e, runtime_secrets)}", file=sys.stderr)
        if args.verbose:
            import traceback
            print(redact_secrets(traceback.format_exc(), runtime_secrets), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
