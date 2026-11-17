import base64
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from scripts.cli import _peek_config_secret, load_config, query_knowledge_base, run_pipeline
from scripts.clusterer import RepositoryClusterer
from scripts.dashboard_generator import DashboardGenerator
from scripts.graph_builder import KnowledgeGraphBuilder
from scripts.kb_generator import KnowledgeBaseGenerator
from scripts.query_engine import RepositoryQueryEngine
from scripts.scanner import GitHubScanner, _SafeGitHubRedirectHandler, _assert_safe_api_url
from scripts.security_utils import (
    deleteUserData,
    export_user_data,
    is_placeholder_token,
    load_json_limited,
    redact_secrets,
    sanitize_hex_color,
    sanitize_http_url,
    strip_control_chars,
    validate_config_schema,
    validate_path_safe,
)


def _relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    rgb = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast_ratio(fg: str, bg: str) -> float:
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _extract_css_vars(css_block: str) -> dict:
    return {
        m.group(1): m.group(2).strip()
        for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", css_block)
    }


class TestSecurityAndAccessibility(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Dashboard XSS, Script Breakout, Attribute & Placeholder Injection
    # ------------------------------------------------------------------
    def test_dashboard_blocks_script_breakout_and_attribute_injection(self):
        gen = DashboardGenerator(output_dir=self.temp_dir)
        evil_owner = 'evil"</title></script><img src=x onerror=alert(1)>__EMBEDDED_JSON__'
        evil_url = 'https://github.com/org" autofocus onfocus="alert(2)'
        evil_repo_name = '</script><script>window.__xss=1</script>'
        evil_desc = '<img src=x onerror="window.__xss=2"> & \u2028 line-sep'

        metadata = {"owner": evil_owner, "input_url": evil_url}
        clusters_data = {
            "clusters": [
                {
                    "id": "evil-cluster",
                    "name": '<b>Evil</b>',
                    "description": '<svg onload=alert(3)>',
                    "color": "#fff;background:url(https://evil.example)",
                    "repo_count": 1,
                    "total_stars": 5,
                    "repositories": [1],
                }
            ],
            "repositories": [
                {
                    "id": 1,
                    "name": evil_repo_name,
                    "html_url": "javascript:alert(4)",
                    "description": evil_desc,
                    "primary_language": "Python",
                    "stars": 5,
                    "cluster_id": "evil-cluster",
                    "cluster_name": "<b>Evil</b>",
                    "cluster_color": "red;xss:1",
                    "topics": ["<script>x</script>"],
                    "tech_stack": ["<img src=x>"],
                }
            ],
        }
        graph_data = {
            "nodes": [dict(clusters_data["repositories"][0], is_hub=True, is_bridge=False, total_degree=1)],
            "edges": [],
            "cluster_connectivity_matrix": {},
            "hub_repositories": [evil_repo_name],
            "bridge_repositories": [],
            "cross_cluster_edges_count": 0,
            "intra_cluster_edges_count": 0,
        }

        dash_path = gen.generate(metadata, clusters_data, graph_data)
        with open(dash_path, "r", encoding="utf-8") as f:
            html_out = f.read()

        # Verify JSON data block is safely escaped and parses back cleanly
        data_match = re.search(
            r'<script id="kb-data" type="application/json">(.*?)</script>',
            html_out,
            re.DOTALL,
        )
        self.assertIsNotNone(data_match)
        raw_json_block = data_match.group(1)
        self.assertNotIn("</script", raw_json_block.lower())
        self.assertNotIn("<img", raw_json_block.lower())
        self.assertNotIn("\u2028", raw_json_block)
        parsed = json.loads(raw_json_block)
        self.assertEqual(parsed["repositories"][0]["name"], evil_repo_name)

        # Verify title and input attribute escaping (single-pass prevents placeholder chaining)
        self.assertNotIn("<img src=x onerror=alert(1)>", html_out)
        self.assertNotIn('" autofocus onfocus="alert(2)', html_out)
        self.assertIn("&quot; autofocus onfocus=&quot;alert(2)", html_out)
        # Ensure __EMBEDDED_JSON__ inside owner stayed literal (not expanded into JSON inside <title>)
        title_match = re.search(r"<title>(.*?)</title>", html_out, re.DOTALL)
        self.assertIsNotNone(title_match)
        self.assertIn("__EMBEDDED_JSON__", title_match.group(1))
        self.assertNotIn('"repositories":', title_match.group(1))

    # ------------------------------------------------------------------
    # 2. CSP SHA-256 Hash Integrity, Referrer-Policy & Vendored D3 Check
    # ------------------------------------------------------------------
    def test_dashboard_csp_hashes_and_offline_integrity(self):
        gen = DashboardGenerator(output_dir=self.temp_dir)
        dash_path = gen.generate(
            {"owner": "demo", "input_url": "https://github.com/demo"},
            {"clusters": [], "repositories": []},
            {"nodes": [], "edges": [], "cluster_connectivity_matrix": {}},
        )
        with open(dash_path, "r", encoding="utf-8") as f:
            html_out = f.read()

        # No external scripts or stylesheets
        self.assertIsNone(re.search(r"<script[^>]+src\s*=", html_out, re.IGNORECASE))
        self.assertIsNone(re.search(r'<link[^>]+href\s*=\s*["\']https?://', html_out, re.IGNORECASE))

        # Referrer-Policy meta tag
        self.assertIn('<meta name="referrer" content="no-referrer" />', html_out)

        # Strict CSP without unsafe-inline / unsafe-eval in script-src
        csp_match = re.search(
            r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"\s*/?>',
            html_out,
        )
        self.assertIsNotNone(csp_match)
        csp = csp_match.group(1)
        script_src = re.search(r"script-src\s+([^;]+)", csp).group(1)
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertNotIn("'unsafe-eval'", script_src)
        self.assertIn("connect-src https://api.github.com", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'none'", csp)
        self.assertIn("form-action 'none'", csp)

        # Every executable <script> block matches its exact SHA-256 hash in CSP
        allowed_hashes = set(re.findall(r"'sha256-[A-Za-z0-9+/=]+'", script_src))
        scripts = re.findall(r"<script([^>]*)>(.*?)</script>", html_out, re.DOTALL)
        exec_count = 0
        for attrs, body in scripts:
            if 'type="application/json"' in attrs:
                continue
            exec_count += 1
            digest = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode("ascii")
            self.assertIn(f"'sha256-{digest}'", allowed_hashes)
        self.assertEqual(exec_count, 2)

        # Zero inline HTML event handlers outside <script>
        html_no_scripts = re.sub(r"<script\b[^>]*>.*?</script>", "", html_out, flags=re.DOTALL)
        self.assertIsNone(
            re.search(
                r"\son(?:click|keydown|keyup|input|change|mouseover|mouseout|load|error)\s*=",
                html_no_scripts,
                re.IGNORECASE,
            )
        )

    def test_vendored_d3_integrity_check_detects_tampering(self):
        with mock.patch.object(DashboardGenerator, "VENDOR_D3_SHA256", "0" * 64):
            with self.assertRaises(RuntimeError):
                DashboardGenerator._load_vendored_d3()

    # ------------------------------------------------------------------
    # 3. SSRF, URL Parsing, Redirects, TLS & Deterministic IDs
    # ------------------------------------------------------------------
    def test_scanner_rejects_ssrf_and_invalid_urls(self):
        scanner = GitHubScanner()
        bad_inputs = [
            "",
            "   ",
            "file:///etc/passwd",
            "http://169.254.169.254/latest/meta-data",
            "https://evil.example/org",
            "https://github.com.evil.example/org",
            "https://github.com/org?per_page=1",
            "https://github.com/org#frag",
            "https://github.com/../etc",
            "https://github.com/org/..",
            "javascript:alert(1)",
            "evil.com/org",
            "bad handle with spaces",
            "-leading-hyphen",
        ]
        for bad in bad_inputs:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    scanner.parse_github_url(bad)

    def test_scanner_accepts_valid_github_urls(self):
        scanner = GitHubScanner()
        self.assertEqual(scanner.parse_github_url("pallets"), ("owner", "pallets", None))
        self.assertEqual(
            scanner.parse_github_url("https://www.github.com/pallets/flask"),
            ("repo", "pallets", "flask"),
        )
        self.assertEqual(
            scanner.parse_github_url("github.com/orgs/pallets"),
            ("owner", "pallets", None),
        )

    def test_scanner_assert_safe_api_url_blocks_non_github_and_private_ip(self):
        with self.assertRaises(ValueError):
            _assert_safe_api_url("http://api.github.com/orgs/pallets/repos")
        with self.assertRaises(ValueError):
            _assert_safe_api_url("https://evil.example/orgs/pallets/repos")
        with self.assertRaises(ValueError):
            _assert_safe_api_url("https://127.0.0.1/repos")

        # Simulate DNS rebinding api.github.com -> link-local metadata IP
        fake_dns = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443))]
        with mock.patch("socket.getaddrinfo", return_value=fake_dns):
            with self.assertRaises(ValueError):
                _assert_safe_api_url("https://api.github.com/orgs/pallets/repos", check_dns=True)

        # Simulate valid public IP
        public_dns = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("140.82.114.6", 443))]
        with mock.patch("socket.getaddrinfo", return_value=public_dns):
            _assert_safe_api_url("https://api.github.com/orgs/pallets/repos", check_dns=True)

    def test_scanner_redirect_handler_blocks_offhost_and_excess_hops(self):
        handler = _SafeGitHubRedirectHandler()
        self.assertLessEqual(handler.max_redirections, 3)
        req = mock.Mock()
        req.full_url = "https://api.github.com/orgs/pallets/repos"
        req.headers = {}
        req.unredirected_hdrs = {}
        req.origin_req_host = "api.github.com"

        with self.assertRaises(ValueError):
            handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/steal")
        with self.assertRaises(ValueError):
            handler.redirect_request(req, None, 302, "Found", {}, "http://api.github.com/downgrade")

    def test_scanner_tls_context_enforces_tls12(self):
        import urllib.request
        scanner = GitHubScanner()
        opener = scanner._build_opener()
        https_handlers = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPSHandler)]
        self.assertTrue(https_handlers, "HTTPSHandler must be installed on scanner opener")
        ctx = https_handlers[0]._context
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)
        if hasattr(ssl, "TLSVersion"):
            self.assertGreaterEqual(ctx.minimum_version, ssl.TLSVersion.TLSv1_2)

    def test_scanner_deterministic_id_and_url_sanitization(self):
        scanner = GitHubScanner()
        raw = {
            "name": "repo-no-id",
            "full_name": "org/repo-no-id",
            "html_url": "javascript:alert(1)",
            "primary_language": "Rust",
        }
        norm1 = scanner._normalize_repo(raw)
        norm2 = scanner._normalize_repo(raw)
        self.assertEqual(norm1["id"], norm2["id"])
        self.assertIsInstance(norm1["id"], int)
        self.assertFalse(norm1["html_url"].lower().startswith("javascript:"))
        self.assertTrue(norm1["html_url"].startswith("https://github.com/"))
        self.assertEqual(norm1["primary_language"], "Rust")

    # ------------------------------------------------------------------
    # 4. Path Traversal, Symlink Overwrite & Bounded JSON Loading
    # ------------------------------------------------------------------
    def test_validate_path_safe_blocks_escape_symlink_and_protected_dirs(self):
        with self.assertRaises(ValueError):
            validate_path_safe("../../etc/passwd", base_dir=self.temp_dir, must_be_within_base=True)
        with self.assertRaises(ValueError):
            validate_path_safe("/etc/evil_output", for_write=True)
        with self.assertRaises(ValueError):
            validate_path_safe(os.path.expanduser("~/.ssh/authorized_keys"), for_write=True)
        with self.assertRaises(ValueError):
            validate_path_safe("bad\x00path", for_write=True)

        # Allowed temp dir
        self.assertEqual(validate_path_safe(self.temp_dir, for_write=True), self.temp_dir)

    def test_generators_refuse_symlink_overwrite(self):
        victim = os.path.join(self.temp_dir, "victim.txt")
        with open(victim, "w", encoding="utf-8") as f:
            f.write("DO NOT OVERWRITE")

        out_sub = os.path.join(self.temp_dir, "out")
        os.makedirs(out_sub, exist_ok=True)
        os.symlink(victim, os.path.join(out_sub, "dashboard.html"))
        os.symlink(victim, os.path.join(out_sub, "KNOWLEDGE_BASE.md"))

        dash_gen = DashboardGenerator(output_dir=out_sub)
        with self.assertRaises(ValueError):
            dash_gen.generate({"owner": "x"}, {"clusters": [], "repositories": []}, {"nodes": [], "edges": []})

        kb_gen = KnowledgeBaseGenerator(output_dir=out_sub)
        with self.assertRaises(ValueError):
            kb_gen.generate_all({"owner": "x"}, {"clusters": [], "repositories": []}, {"nodes": [], "edges": []})

        with open(victim, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "DO NOT OVERWRITE")

    def test_cli_blocks_config_path_traversal(self):
        cfg_path = os.path.join(self.temp_dir, "evil_config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"output": {"output_dir": "../../outside_escape"}}, f)

        with self.assertRaises(ValueError):
            run_pipeline(config_path=cfg_path)

    def test_bounded_json_rejects_oversized_file(self):
        big_file = os.path.join(self.temp_dir, "oversized.json")
        with open(big_file, "w", encoding="utf-8") as f:
            json.dump({"data": "A" * 500}, f)

        with self.assertRaises(ValueError):
            load_json_limited(big_file, max_bytes=64)

        # Query engine also validates root type
        list_file = os.path.join(self.temp_dir, "list.json")
        with open(list_file, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        with self.assertRaises(ValueError):
            RepositoryQueryEngine(kb_path=list_file)

    # ------------------------------------------------------------------
    # 5. ReDoS Protection & Hex Color Sanitization in Clusterer
    # ------------------------------------------------------------------
    def test_clusterer_rejects_redos_and_sanitizes_custom_color(self):
        stderr_buf = io.StringIO()
        rules = [
            {"pattern": "(a+)+$", "cluster_id": "redos-bad"},
            {"pattern": "a" * 300, "cluster_id": "too-long"},
            {"pattern": "[invalid-regex", "cluster_id": "syntax-bad"},
            {"pattern": "^custom-.*", "cluster_id": "custom-domain", "color": "javascript:alert(1)"},
        ]
        with contextlib.redirect_stderr(stderr_buf):
            clusterer = RepositoryClusterer(custom_rules=rules)

        # Verify warnings logged and ReDoS/invalid rules dropped
        warnings_text = stderr_buf.getvalue()
        self.assertIn("redos-bad", warnings_text)
        self.assertIn("too-long", warnings_text)
        self.assertIn("syntax-bad", warnings_text)

        # Must finish near-instantly even on adversarial backtracking input
        start = time.monotonic()
        res_adv = clusterer.classify_repository({"name": "a" * 40 + "!"})
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 0.25)
        self.assertNotEqual(res_adv["id"], "redos-bad")

        # Valid rule still works and bad color is sanitized to safe hex
        res_custom = clusterer.classify_repository({"name": "custom-service"})
        self.assertEqual(res_custom["id"], "custom-domain")
        self.assertEqual(res_custom["color"], "#6366F1")

    # ------------------------------------------------------------------
    # 6. Secret Redaction, Placeholder Filtering, CLI Warning & ANSI Strip
    # ------------------------------------------------------------------
    def test_secret_redaction_and_placeholders(self):
        # Dynamically construct synthetic tokens so no literal secret patterns exist in test source
        fake_ghp = "ghp_" + ("A" * 36)
        fake_pat = "github_pat_" + ("B" * 32)
        msg = f"Failed with {fake_ghp} and {fake_pat} and Authorization: Bearer supersecret999"
        redacted = redact_secrets(msg, extra_secrets=["myCustomSecret"])
        self.assertNotIn(fake_ghp, redacted)
        self.assertNotIn(fake_pat, redacted)
        self.assertNotIn("supersecret999", redacted)
        self.assertIn("[REDACTED]", redacted)

        self.assertTrue(is_placeholder_token(""))
        self.assertTrue(is_placeholder_token("YOUR_GITHUB_TOKEN"))
        self.assertTrue(is_placeholder_token("<YOUR_GITHUB_TOKEN>"))
        self.assertFalse(is_placeholder_token(fake_ghp))

        self.assertEqual(sanitize_http_url("https://github.com/org/repo"), "https://github.com/org/repo")
        self.assertEqual(sanitize_http_url("javascript:alert(1)"), "#")
        self.assertEqual(sanitize_hex_color("#0EA5E9"), "#0EA5E9")
        self.assertEqual(sanitize_hex_color("red;background:url(x)"), "#3B82F6")
        self.assertNotIn("\x1b", strip_control_chars("\x1b[31mRed\x1b[0m\x1b]0;title\x07"))

    def test_cli_warns_on_cli_token_and_redacts_secrets(self):
        fixture_path = os.path.join("examples", "synthetic_sample_org.json")
        fake_token = "ghp_" + ("Z" * 36)
        stderr_buf = io.StringIO()
        stdout_buf = io.StringIO()
        with contextlib.redirect_stderr(stderr_buf), contextlib.redirect_stdout(stdout_buf):
            run_pipeline(fixture_path=fixture_path, output_dir=self.temp_dir, token=fake_token)

        self.assertIn("[Security Warning]", stderr_buf.getvalue())
        self.assertNotIn(fake_token, stderr_buf.getvalue())
        self.assertNotIn(fake_token, stdout_buf.getvalue())

    def test_cli_query_strips_ansi_sequences(self):
        kb_path = os.path.join(self.temp_dir, "kb.json")
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "clusters": [{"id": "sec", "name": "Security"}],
                    "repositories": [
                        {
                            "id": 1,
                            "name": "oauth-service\x1b[31mINJECT\x1b[0m",
                            "html_url": "https://github.com/org/oauth-service",
                            "description": "OAuth2 login\x1b]0;PWN\x07 service",
                            "primary_language": "Go",
                            "cluster_name": "Security",
                            "topics": ["oauth2", "login"],
                            "tech_stack": ["Go"],
                            "stars": 10,
                        }
                    ],
                },
                f,
            )
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            query_knowledge_base("oauth2 login", kb_path=kb_path)
        self.assertNotIn("\x1b", stdout_buf.getvalue())

    # ------------------------------------------------------------------
    # 7. Markdown Sanitization & Prompt-Injection Provenance Notice
    # ------------------------------------------------------------------
    def test_markdown_sanitizes_untrusted_repo_fields(self):
        gen = KnowledgeBaseGenerator(output_dir=self.temp_dir)
        files = gen.generate_all(
            metadata={"owner": "org<script>x</script>", "input_url": "https://github.com/org"},
            clusters_data={
                "cluster_count": 1,
                "clusters": [
                    {
                        "id": "c1",
                        "name": "Domain | <img src=x>",
                        "description": "Desc ![pixel](https://evil.example/p.png)",
                        "repositories": [1],
                        "repo_count": 1,
                        "total_stars": 1,
                    }
                ],
                "repositories": [
                    {
                        "id": 1,
                        "name": "bad[repo](x)",
                        "html_url": "javascript:alert(1)",
                        "primary_language": "Python\n| injected |",
                        "stars": 1,
                        "description": "Line1\nLine2 ![img](https://evil.example/x.png) <script>alert(1)</script>",
                    }
                ],
            },
            graph_data={"nodes": [], "edges": [], "cluster_connectivity_matrix": {}},
        )
        with open(files["knowledge_base_md"], "r", encoding="utf-8") as f:
            md = f.read()

        self.assertIn("Data Provenance Notice", md)
        self.assertNotIn("<script>", md)
        self.assertIn("&lt;script&gt;", md)
        self.assertNotIn("javascript:alert(1)", md)
        # Remote image syntax neutralized with leading backslash
        self.assertIn(r"\![img](https://evil.example/x.png)", md)
        self.assertIn(r"\![pixel](https://evil.example/p.png)", md)

    # ------------------------------------------------------------------
    # 8. WCAG 2.2 AA Contrast & Structural Accessibility Verification
    # ------------------------------------------------------------------
    def test_wcag_aa_contrast_ratios_both_themes(self):
        gen = DashboardGenerator(output_dir=self.temp_dir)
        dash_path = gen.generate(
            {"owner": "demo", "input_url": "https://github.com/demo"},
            {"clusters": [], "repositories": []},
            {"nodes": [], "edges": [], "cluster_connectivity_matrix": {}},
        )
        with open(dash_path, "r", encoding="utf-8") as f:
            html_out = f.read()

        root_match = re.search(r":root\s*\{(.*?)\}", html_out, re.DOTALL)
        light_match = re.search(r'\[data-theme="light"\]\s*\{(.*?)\}', html_out, re.DOTALL)
        self.assertIsNotNone(root_match)
        self.assertIsNotNone(light_match)

        dark_vars = _extract_css_vars(root_match.group(1))
        light_vars = dict(dark_vars)
        light_vars.update(_extract_css_vars(light_match.group(1)))

        for theme_name, tv in (("dark", dark_vars), ("light", light_vars)):
            text_pairs = [
                ("--text-main", "--bg-base"),
                ("--text-main", "--bg-surface"),
                ("--text-main", "--bg-surface-elevated"),
                ("--text-main", "--border-hover"),
                ("--text-muted", "--bg-base"),
                ("--text-muted", "--bg-surface"),
                ("--text-muted", "--bg-surface-elevated"),
                ("--text-muted", "--border-hover"),
                ("--text-dim", "--bg-base"),
                ("--text-dim", "--bg-surface"),
                ("--text-dim", "--bg-surface-elevated"),
                ("--text-dim", "--border-hover"),
                ("--primary-text", "--bg-base"),
                ("--primary-text", "--bg-surface"),
                ("--primary-text", "--bg-surface-elevated"),
                ("--primary-text", "--border-hover"),
                ("--accent-text", "--bg-surface-elevated"),
                ("--accent-text", "--border-hover"),
                ("--tag-text", "--bg-surface-elevated"),
                ("--tag-tech-text", "--bg-surface-elevated"),
                ("--success-text", "--bg-surface-elevated"),
                ("--warning-text", "--bg-surface-elevated"),
                ("--danger-text", "--danger-bg"),
                ("--text-main", "--danger-bg"),
                ("--tooltip-title", "--bg-surface"),
                ("--matrix-active-text", "--matrix-active-bg"),
            ]
            for fg_k, bg_k in text_pairs:
                ratio = _contrast_ratio(tv[fg_k], tv[bg_k])
                self.assertGreaterEqual(
                    ratio,
                    4.5,
                    f"{theme_name} text contrast fail: {fg_k} ({tv[fg_k]}) on {bg_k} ({tv[bg_k]}) = {ratio:.2f}:1",
                )

            # White text on primary button
            for btn_bg in ("--primary", "--primary-hover"):
                ratio = _contrast_ratio("#ffffff", tv[btn_bg])
                self.assertGreaterEqual(
                    ratio,
                    4.5,
                    f"{theme_name} button contrast fail: #ffffff on {btn_bg} ({tv[btn_bg]}) = {ratio:.2f}:1",
                )

            # Non-text UI control borders & focus ring >= 3.0:1
            ui_pairs = [
                ("--border-control", "--bg-base"),
                ("--border-control", "--bg-surface"),
                ("--border-control", "--bg-surface-elevated"),
                ("--border-control", "--border-hover"),
                ("--focus-ring", "--bg-base"),
                ("--focus-ring", "--bg-surface"),
                ("--focus-ring", "--bg-surface-elevated"),
            ]
            for fg_k, bg_k in ui_pairs:
                ratio = _contrast_ratio(tv[fg_k], tv[bg_k])
                self.assertGreaterEqual(
                    ratio,
                    3.0,
                    f"{theme_name} UI contrast fail: {fg_k} ({tv[fg_k]}) on {bg_k} ({tv[bg_k]}) = {ratio:.2f}:1",
                )

    def test_wcag_aa_structural_and_aria_requirements(self):
        gen = DashboardGenerator(output_dir=self.temp_dir)
        dash_path = gen.generate(
            {"owner": "demo", "input_url": "https://github.com/demo"},
            {"clusters": [], "repositories": []},
            {"nodes": [], "edges": [], "cluster_connectivity_matrix": {}},
        )
        with open(dash_path, "r", encoding="utf-8") as f:
            html_out = f.read()

        # Landmarks & skip link
        self.assertIn('<a href="#main-content" class="skip-link">Skip to main content</a>', html_out)
        self.assertIn('<h1 class="topbar-title">', html_out)
        self.assertIn('<nav aria-label="Dashboard view navigation">', html_out)
        self.assertIn('<main id="main-content"', html_out)
        self.assertIn('<footer class="site-footer" role="contentinfo">', html_out)

        # Explicit text-based state identifiers & zero decorative arrow escapes
        self.assertIn("[HUB]", html_out)
        self.assertIn("[BRIDGE]", html_out)
        self.assertIn("[NO MATCH]", html_out)
        self.assertNotIn("\\u2192", html_out)
        self.assertNotIn("\\u2026", html_out)

        # Explicit label for every form control
        expected_labeled_ids = [
            "scan-target-input",
            "preset-selector",
            "graph-search",
            "graph-cluster-filter",
            "graph-edge-filter",
            "graph-label-mode",
            "graph-spacing-mode",
            "matcher-query-input",
            "repo-table-search",
            "table-cluster-filter",
            "raw-json-viewer",
        ]
        for ctrl_id in expected_labeled_ids:
            self.assertIn(f'<label for="{ctrl_id}"', html_out)

        # ARIA tabs, table captions/scopes, live regions, SVG accessible name, reduced motion, noopener
        self.assertIn('role="tablist"', html_out)
        self.assertIn('role="tab"', html_out)
        self.assertIn('role="tabpanel"', html_out)
        self.assertIn('<caption class="sr-only">', html_out)
        self.assertIn('scope="col"', html_out)
        self.assertIn('aria-live="polite"', html_out)
        self.assertIn('role="status"', html_out)
        self.assertIn('aria-labelledby="graph-svg-title graph-svg-desc"', html_out)
        self.assertIn("@media (prefers-reduced-motion: reduce)", html_out)
        self.assertIn("prefersReducedMotion()", html_out)
        self.assertIn('rel="noopener noreferrer"', html_out)
        self.assertIn(":focus-visible", html_out)
        # Ensure outline:none was removed from .scan-input
        scan_input_css = re.search(r"\.scan-input\s*\{([^}]*)\}", html_out)
        self.assertIsNotNone(scan_input_css)
        self.assertNotIn("outline: none", scan_input_css.group(1))

    # ------------------------------------------------------------------
    # 9. Strict Schema Validation, Payload Coercion & Privacy Rights
    # ------------------------------------------------------------------
    def test_config_schema_rejects_undefined_keys_and_invalid_types(self):
        with self.assertRaises(ValueError):
            validate_config_schema({"unknown_key": True})
        with self.assertRaises(ValueError):
            validate_config_schema({"scan_options": {"unexpected": 1}})
        with self.assertRaises(ValueError):
            validate_config_schema({"output": {"bad_flag": True}})
        with self.assertRaises(ValueError):
            validate_config_schema({"clustering_rules": [{"pattern": "x", "cluster_id": "y", "evil": 1}]})

        bad_cfg = os.path.join(self.temp_dir, "bad_schema.json")
        with open(bad_cfg, "w", encoding="utf-8") as f:
            json.dump({"target_url": "https://github.com/pallets", "injected": "nope"}, f)
        with self.assertRaises(ValueError):
            load_config(bad_cfg)

    def test_scanner_normalize_repo_coerces_malformed_types_and_bounds(self):
        scanner = GitHubScanner()
        malformed = {
            "id": {"unhashable": True},
            "name": "svc-" + ("x" * 500),
            "stars": "not-an-int",
            "forks": -99,
            "open_issues": True,
            "description": "D" * 9000,
            "topics": ["ok", {"bad": 1}, "tag"],
            "dependencies": [{"bad": 2}, "dep-one"],
        }
        norm = scanner._normalize_repo(malformed)
        self.assertIsInstance(norm["id"], int)
        self.assertEqual(norm["stars"], 0)
        self.assertEqual(norm["forks"], 0)
        self.assertEqual(norm["open_issues"], 0)
        self.assertLessEqual(len(norm["name"]), 256)
        self.assertLessEqual(len(norm["description"]), 4096)
        self.assertEqual(norm["topics"], ["ok", "tag"])
        self.assertEqual(norm["dependencies"], ["dep-one"])

        clustered = RepositoryClusterer().cluster_repositories([norm])
        graph = KnowledgeGraphBuilder().build_graph(clustered["repositories"], clustered["clusters"])
        self.assertEqual(graph["total_nodes"], 1)

    def test_config_auth_token_redacted_in_peek_and_errors(self):
        cfg_file = os.path.join(self.temp_dir, "local_cfg.json")
        custom_secret = "customEnterpriseToken987654321"
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump({"auth_token": custom_secret}, f)
        extracted = _peek_config_secret(cfg_file)
        self.assertEqual(extracted, custom_secret)
        scrubbed = redact_secrets(f"Error using {custom_secret}", [extracted])
        self.assertNotIn(custom_secret, scrubbed)
        self.assertIn("[REDACTED]", scrubbed)

    def test_user_data_export_and_erasure_workflows(self):
        fixture_path = os.path.join("examples", "synthetic_sample_org.json")
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            run_pipeline(fixture_path=fixture_path, output_dir=self.temp_dir)

        # 1. Portability export in JSON and CSV formats
        json_exp = export_user_data("sample-platform", output_dir=self.temp_dir, fmt="json")
        self.assertTrue(json_exp["matched_owner"])
        self.assertEqual(json_exp["record_count"], 16)
        parsed_export = json.loads(json_exp["serialized"])
        self.assertEqual(parsed_export["record_count"], 16)

        csv_exp = export_user_data("sample-platform", output_dir=self.temp_dir, fmt="csv")
        self.assertIn("sample-patient-records", csv_exp["serialized"])

        # 2. Full owner erasure purges all generated artifacts without soft-deletes
        erase_res = deleteUserData("sample-platform", output_dir=self.temp_dir)
        self.assertTrue(erase_res["purged"])
        self.assertEqual(erase_res["deleted_repositories"], 16)
        for fname in ("knowledge_base.json", "knowledge_graph.json", "KNOWLEDGE_BASE.md", "dashboard.html"):
            self.assertFalse(os.path.exists(os.path.join(self.temp_dir, fname)))

        # 3. Partial erasure in a multi-owner dataset regenerates artifacts cleanly
        multi_dir = os.path.join(self.temp_dir, "multi")
        os.makedirs(multi_dir, exist_ok=True)
        mixed_fixture = os.path.join(self.temp_dir, "mixed.json")
        with open(mixed_fixture, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {"owner": "umbrella-org", "input_url": "https://github.com/umbrella-org"},
                    "repositories": [
                        {
                            "id": 1,
                            "name": "alice-repo",
                            "full_name": "alice-handle/alice-repo",
                            "html_url": "https://github.com/alice-handle/alice-repo",
                            "description": "Alice personal repo",
                            "primary_language": "Python",
                        },
                        {
                            "id": 2,
                            "name": "core-gateway",
                            "full_name": "umbrella-org/core-gateway",
                            "html_url": "https://github.com/umbrella-org/core-gateway",
                            "description": "Core API gateway",
                            "primary_language": "Go",
                        },
                    ],
                },
                f,
            )
        with contextlib.redirect_stdout(stdout_buf):
            run_pipeline(fixture_path=mixed_fixture, output_dir=multi_dir)

        partial_res = deleteUserData("alice-handle", output_dir=multi_dir)
        self.assertTrue(partial_res["purged"])
        self.assertEqual(partial_res["deleted_repositories"], 1)
        for fname in ("knowledge_base.json", "KNOWLEDGE_BASE.md", "dashboard.html"):
            with open(os.path.join(multi_dir, fname), "r", encoding="utf-8") as fh:
                self.assertNotIn("alice-handle", fh.read())

    # ------------------------------------------------------------------
    # 10. CI Security Gate Integration Check
    # ------------------------------------------------------------------
    def test_ci_security_check_passes(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script = os.path.join(repo_root, "scripts", "ci_security_check.py")
        proc = subprocess.run(
            [sys.executable, script],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"ci_security_check.py failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
