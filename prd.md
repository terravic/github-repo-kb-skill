# Product Requirements Document (PRD): GitHub Repository Knowledge Base Skill

## 1. Document Purpose and Scope

This Product Requirements Document defines the functional, architectural, security, privacy, and accessibility requirements for `github-repo-kb-skill`. It aligns with the dashboard visual and technical architecture specified in [DESIGN.md](DESIGN.md) and documents all implemented capabilities across the Python pipeline, CLI, agent skill definition, and standalone HTML dashboard.

---

## 2. Problem Statement

Engineering teams, architects, and non-technical stakeholders often work with GitHub organizations containing dozens or hundreds of repositories spanning multiple product areas, clinical or scientific domains, infrastructure stacks, and shared libraries. Manually auditing repository lists to determine domain boundaries, cross-repository dependencies, architectural hubs, or which repository satisfies a specific capability is slow and error-prone.

`github-repo-kb-skill` solves this by automating repository metadata ingestion, deterministic thematic domain clustering, directed dependency graph construction, natural-language capability search, and self-contained visual exploration without external Python runtime dependencies.

---

## 3. Target Users and Personas

| Persona | Primary Goals | Primary Interface |
|---|---|---|
| **Non-Technical Stakeholder / Product Manager** | Understand what software domains exist in an organization, locate which repository implements a capability, and inspect high-level portfolio metrics without writing code. | Agent chat prompts (`SKILL.md`) and standalone `output/dashboard.html` |
| **Software Architect / Engineering Lead** | Identify architectural hubs, cross-domain bridges, shared technology stacks, and dependency flow across thematic clusters. | `output/dashboard.html` (Knowledge Graph, Cross-Domain Flow Matrix), `output/KNOWLEDGE_BASE.md` |
| **Developer / Automation Engineer** | Run repeatable scans in CI or local workflows, query capabilities from the terminal, customize regex clustering rules, and consume machine-readable JSON outputs. | `scripts/cli.py`, `scanner_config.json`, `output/knowledge_base.json`, `output/knowledge_graph.json` |
| **Security & Governance Reviewer** | Verify offline execution, least-privilege token handling, CSP enforcement, vendored dependency integrity, and WCAG 2.2 AA conformance before deployment. | `scripts/ci_security_check.py`, `THIRD_PARTY_LICENSES.md`, `docs/legal/` |

---

## 4. System Architecture and Pipeline Overview

The system executes a four-stage deterministic pipeline orchestrated by `scripts/cli.py`:

1. **Repository Ingestion (`scripts/scanner.py`)**:
   - Parses GitHub organization URLs, user URLs, single repository URLs, or owner handles.
   - Fetches public or token-authenticated repository metadata from `https://api.github.com` over HTTPS (`TLS >= 1.2`) with strict host/IP validation and redirect filtering.
   - Supports fully offline execution using local JSON fixtures (default reference: `examples/synthetic_sample_org.json`).
   - Normalizes fields including `id`, `name`, `full_name`, `html_url`, `description`, `primary_language`, `topics`, `stars`, `forks`, `open_issues`, `updated_at`, `created_at` (retained for `knowledge_base.json` schema compatibility), `default_branch`, `license`, `is_fork`, `is_archived`, `tech_stack`, `dependencies`, and `readme_summary` with strict type coercion and length bounds.
2. **Thematic Domain Clustering (`scripts/clusterer.py`)**:
   - Classifies each repository into one of eleven built-in functional and scientific domains (`medical-healthcare`, `life-sciences-bio`, `finance-billing`, `security-identity`, `data-ai-analytics`, `developer-tooling`, `infrastructure-devops`, `core-platform`, `frontend-applications`, `utilities-libraries`, `documentation-specs`) plus fallback `general-utilities` (`General & Utilities`).
   - Applies user-defined regular expression rules from `scanner_config.json` with ReDoS-safe pattern validation before falling back to weighted keyword and language scoring.
3. **Knowledge Graph Construction (`scripts/graph_builder.py`)**:
   - Creates directed relationship edges (`depends_on`, `integrates_with`, `interfaces_with`, `routes_to`, `provisions`, `shares_tech`) from explicit dependencies, cross-references in descriptions, architectural roles, and shared technologies.
   - Calculates `in_degree`, `out_degree`, `total_degree`, normalized `centrality_score`, hub classification (`is_hub`), cross-domain bridge detection (`is_bridge`), and an inter-cluster connectivity matrix.
4. **Output Generation, Capability Querying, and Privacy Rights**:
   - `scripts/kb_generator.py`: Writes `knowledge_base.json`, `knowledge_graph.json`, and sanitized `KNOWLEDGE_BASE.md` (using `O_NOFOLLOW` symlink-safe writes) with an explicit Data Provenance Notice.
   - `scripts/dashboard_generator.py`: Generates self-contained `dashboard.html` embedding the dataset (`#kb-data`) and SHA-256 verified vendored `scripts/vendor/d3.v7.min.js`.
   - `scripts/query_engine.py`: Evaluates natural-language capability queries locally against repository metadata using tokenized synonym expansion, weighted multi-field scoring, confidence thresholds (`High`, `Moderate`, `Low`), and explicit non-match reporting listing available organization domains.
   - `scripts/security_utils.py`: Enforces strict configuration schema validation (`validate_config_schema`), symlink-safe file writing (`write_text_safe`), verified user data erasure (`deleteUserData` / `delete_user_data`), and machine-readable data portability exports (`export_user_data` in JSON and CSV).

---

## 5. Functional Requirements

### FR-1: Multi-Mode Target Ingestion
- **FR-1.1**: Support scanning public GitHub organizations, individual GitHub users, and single GitHub repositories via `--url` or `scanner_config.json`.
- **FR-1.2**: Support authenticated scanning of private organizations and restricted repositories using `GITHUB_TOKEN` (environment variable), local uncommitted configuration, or legacy `--token` CLI flag (with deprecation/exposure warning on `stderr`).
- **FR-1.3**: Support offline execution via `--fixture` or `scan_options.offline_fixture` with automatic fallback to `examples/synthetic_sample_org.json` when online demonstration scans fail due to rate limits or connectivity.
- **FR-1.4**: Support configurable repository limits (`--max-repos`), fork filtering (`--include-forks`), and archived repository filtering (`include_archived`).

### FR-2: Thematic Domain Classification
- **FR-2.1**: Classify repositories by functional subject matter and domain mission rather than grouping exclusively by programming language.
- **FR-2.2**: Allow operators to override classifications via `clustering_rules` in `scanner_config.json` while rejecting undefined schema keys and unsafe or overly complex regex patterns.
- **FR-2.3**: Produce cluster-level summary statistics (`repo_count`, `total_stars`, `top_languages`, `repositories`).

### FR-3: Architectural Knowledge Graph and Centrality Analysis
- **FR-3.1**: Generate a node-link graph compatible with D3.js, Cytoscape, Vis.js, and NetworkX (`output/knowledge_graph.json`).
- **FR-3.2**: Differentiate intra-cluster edges from cross-cluster edges (`is_cross_cluster`) and compute an inter-cluster adjacency matrix.
- **FR-3.3**: Identify architecture hubs (`is_hub`) and cross-domain bridges (`is_bridge`) using degree centrality thresholds.

### FR-4: Natural-Language Capability Search
- **FR-4.1**: Support terminal queries via `python3 scripts/cli.py --query "<capability>"` and in-browser queries in the dashboard **Repository Matcher & Chat** tab.
- **FR-4.2**: Return the best-suited repository, ranked candidate list, confidence tier, match score, and matched metadata reasons.
- **FR-4.3**: When no repository meets the minimum relevance threshold, explicitly report that no repository satisfies the requirement and enumerate the domains present in the scanned organization.

### FR-5: Standalone Interactive HTML Dashboard (`output/dashboard.html`)
- **FR-5.1**: Render all six workspace views specified in [DESIGN.md](DESIGN.md): Knowledge Graph, Repository Matcher & Chat, Cluster Explorer, Repository Catalog, Cross-Domain Flow Matrix, and Raw JSON & Config.
- **FR-5.2**: Provide interactive D3.js force simulation with zoom, pan, node dragging, cluster region hulls, semantic zoom label modes (`smart`, `all`, `hubs`), spacing profiles (`balanced`, `wide`, `compact`), live node search, cluster/relationship filters, auto-fit framing, and physics pause/resume.
- **FR-5.3**: Provide an inspection side drawer displaying repository metadata, `[HUB]` and `[BRIDGE]` badges, tech stack, topics, external GitHub link, clickable incoming consumers, and clickable outgoing dependencies.
- **FR-5.4**: Provide client-side public GitHub URL scanning (`Scan Address`), preset dataset switching, in-memory Dark/Light theme toggling, JSON file export, clipboard JSON copy, and print view support.

### FR-6: Agent Skill Integration
- **FR-6.1**: Expose clear execution workflows, CLI invocations, configuration schema, and untrusted-data handling directives in `SKILL.md` for standard agent harnesses.

### FR-7: Data Erasure and Portability (`GDPR Art. 17 & Art. 20`)
- **FR-7.1**: Provide verified permanent deletion of individual GitHub account metadata (`deleteUserData` / `python3 scripts/cli.py --erase-user <handle>`) across all generated artifacts in `output/` with zero soft-deleted remnants (either unlinking single-owner artifacts or re-generating multi-owner artifacts).
- **FR-7.2**: Provide structured machine-readable portability exports (`export_user_data` / `python3 scripts/cli.py --export-user <handle> --export-format json|csv`) in JSON and CSV formats within a documented 30-day response SLA.

---

## 6. Non-Functional Requirements

### NFR-1: Security Hardening (`scripts/security_utils.py`, `scripts/ci_security_check.py`)
- **NFR-1.1 (Zero Mandatory Third-Party Python Dependencies)**: Core runtime executes exclusively on Python 3.8+ standard library modules.
- **NFR-1.2 (Supply-Chain Pinning)**: Client-side D3.js (`7.9.0`) is vendored locally at `scripts/vendor/d3.v7.min.js` and verified against its pinned SHA-256 hash prior to embedding.
- **NFR-1.3 (SSRF and Transport Security)**: Outbound API connections enforce HTTPS (`TLS >= 1.2`), strict `api.github.com` host allowlisting, DNS/IP validation rejecting private, loopback, link-local, multicast, and reserved addresses, bounded redirect hops (`<= 3`), cross-host authorization header stripping, and response byte-size caps.
- **NFR-1.4 (Credential Protection)**: Tokens (`GITHUB_TOKEN`, config `auth_token`, or legacy `--token`) are never persisted to output artifacts and are automatically redacted from error output and logs.
- **NFR-1.5 (Filesystem Confinement & Symlink Safety)**: Path validation blocks null bytes, traversal outside configured base directories, symlink overwrites (via `O_NOFOLLOW` descriptor checks), and writes into protected OS or credential directories.
- **NFR-1.6 (Strict Schema Validation, XSS, and CSP Defense)**: Inbound configuration files reject undefined schema keys (`validate_config_schema`); normalized repository payloads coerce and bound untrusted fields; generated `dashboard.html` escapes all embedded JSON and dynamic DOM values, restricts URLs to safe `http:`/`https:` schemes, contains zero inline HTML event handlers, enforces `Referrer-Policy: no-referrer`, and locks inline script execution via exact CSP `sha256` hashes. Generated `KNOWLEDGE_BASE.md` neutralizes Markdown/HTML injection and includes a Data Provenance Notice.
- **NFR-1.7 (ReDoS Protection)**: Custom clustering regexes are bounded in length and screened for nested quantifier patterns before compilation.

### NFR-2: Privacy and Zero-Storage Compliance (`docs/legal/`)
- **NFR-2.1**: Generated `dashboard.html` sets zero cookies, performs zero `localStorage`/`sessionStorage`/`IndexedDB` operations, and makes zero outbound network requests on page load.
- **NFR-2.2**: All included sample datasets (`examples/synthetic_sample_org.json`) and test fixtures contain synthetic, non-PHI, non-PII data.
- **NFR-2.3**: Legal and governance templates (`PRIVACY_POLICY.md`, `TERMS_OF_USE.md`, `REFUND_POLICY.md`, `COOKIE_AND_STORAGE_POLICY.md`, `ROPA_AND_GOVERNANCE.md`, `ACCESSIBILITY_STATEMENT.md`), security audit documentation (`SECURITY_AUDIT.md`), and software attribution (`THIRD_PARTY_LICENSES.md`) are maintained for operator review prior to public deployment.

### NFR-3: Accessibility Conformance (WCAG 2.2 Level AA)
- **NFR-3.1**: Full keyboard operability across all views, including skip link, ARIA tablist arrow navigation, semantic buttons, and focusable SVG graph nodes (`Enter`/`Space`).
- **NFR-3.2**: Verified contrast ratios (`>= 4.5:1` for text across default, elevated, and hover states; `>= 3.0:1` for interactive borders and `:focus-visible` outlines) in both Dark and Light themes, paired with explicit text tags (`[HUB]`, `[BRIDGE]`, `[HIGH]`, `[MODERATE]`, `[NO MATCH]`).
- **NFR-3.3**: Semantic landmarks (`<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`), single-`<h1>` heading hierarchy without skipped levels, explicit form control labels, table captions and headers with `aria-sort`, `aria-live="polite"` status regions, and screen-reader external link notices.
- **NFR-3.4**: Respects `prefers-reduced-motion`, enforces `>= 24x24` CSS pixel target sizing, and reflows cleanly down to `320px` CSS viewport width with zero horizontal page scrolling.

### NFR-4: Performance and Portability
- **NFR-4.1**: Offline end-to-end execution against the 16-repository synthetic dataset completes in under 2 seconds on standard hardware.
- **NFR-4.2**: All generated files, console progress logs, and documentation use relative paths from the project root directory and operate identically across Linux, macOS, and Windows environments.

---

## 7. Deliverables and File Artifacts

| Artifact Path | Format | Purpose |
|---|---|---|
| `output/dashboard.html` | Standalone HTML5 | Self-contained interactive architecture dashboard |
| `output/knowledge_base.json` | JSON | Complete normalized metadata, clusters, graph, and matrices |
| `output/knowledge_graph.json` | JSON | Node-link architectural graph specification |
| `output/KNOWLEDGE_BASE.md` | Markdown | Structured technical knowledge base report |
| `examples/sample_output/*` | HTML/JSON/MD | Pre-generated reference artifacts from synthetic fixture |
| `SECURITY_AUDIT.md` | Markdown | Security, privacy, sanitization, and accessibility audit register |

---

## 8. Acceptance Criteria and Verification Gates

Release readiness requires all verification gates to pass with zero errors:

1. **Unit and Integration Test Suite**:
   - `python3 -m unittest discover -s tests -v` passes all 52 tests covering scanner URL validation, strict schema and payload bounds validation, metadata normalization, thematic clustering, graph centrality, query matching, Markdown/JSON generation, dashboard rendering, end-to-end pipeline execution, user data erasure/portability, security hardening, and WCAG 2.2 AA accessibility invariants (including hover contrast and semantic landmarks).
2. **Offline Security and Supply-Chain Gate**:
   - `python3 scripts/ci_security_check.py` exits with status `0`, verifying vendored D3.js SHA-256 integrity, zero exposed secrets, required compliance files, semantic HTML landmarks, CSP script hash matching, `Referrer-Policy`, zero inline handlers, and strict host allowlisting across both `output/dashboard.html` and `examples/sample_output/dashboard.html`.
3. **Browser Runtime and Reflow Verification**:
   - Standalone `output/dashboard.html` loads cleanly with zero console or CSP violations, zero external network requests on load, functional theme/tab/matcher/XSS-sanitization behavior, and zero horizontal overflow at `320px` viewport width.
