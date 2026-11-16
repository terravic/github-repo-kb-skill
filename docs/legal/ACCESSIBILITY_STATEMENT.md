> **DRAFT - REQUIRES LEGAL REVIEW**
> Replace bracketed placeholders (`[LEGAL ENTITY NAME]`, `[JURISDICTION]`, `[CONTACT EMAIL]`, `[EFFECTIVE DATE]`) and perform assistive-technology verification with screen readers before publishing.

# Accessibility Statement

**Effective Date:** `[EFFECTIVE DATE]`
**Organization:** `[LEGAL ENTITY NAME]`
**Jurisdiction:** `[JURISDICTION]`
**Accessibility Contact:** `[CONTACT EMAIL]`

---

## 1. Conformance Target
`[LEGAL ENTITY NAME]` is committed to making the interactive Repository Architecture Dashboard (`dashboard.html`) accessible in accordance with **WCAG 2.2 Level AA** (Web Content Accessibility Guidelines 2.2, AA).

## 2. Implemented Accessibility Measures
- **Keyboard Accessibility**:
  - Skip-to-main-content link as the first focusable control.
  - Full ARIA tablist navigation (`ArrowLeft`, `ArrowRight`, `Home`, `End`, `Tab`) across all six dashboard views.
  - Semantic `<button type="button">` elements for all interactive actions (cluster expansion, repository inspection, table sorting, matrix filtering, graph sidebar links).
  - Keyboard-focusable SVG graph nodes (`tabindex="0"`, `role="button"`, `Enter` / `Space` to inspect in the side drawer).
  - High-contrast `:focus-visible` outlines across all controls in both Dark and Light themes.
- **Color Contrast & Non-Color Cues**:
  - Text contrast ratios verified >= `4.5:1` and interactive UI borders/focus rings >= `3.0:1` across both Dark and Light themes.
  - Cluster badges pair geometric color indicators (`aria-hidden="true"`) with high-contrast text labels so color never carries meaning alone.
- **Screen Reader & Semantic Structure**:
  - Single semantic `<h1>`, logical `<h2>`/`<h3>` heading hierarchy, landmark regions (`<header>`, `<main>`, `<aside>`, `<footer>`), explicit `<label for="...">` associations for all inputs/selects/textareas, table `<caption>` and `scope` attributes, `aria-sort` state, `aria-live="polite"` status announcements, and `(opens in new tab)` screen-reader context on external links.
- **Motion, Reflow & Target Size**:
  - Respects `@media (prefers-reduced-motion: reduce)` in CSS and D3 zoom animations.
  - Responsive layout reflows cleanly down to `320px` CSS viewport width without page-level horizontal scrolling.
  - Interactive buttons and controls meet or exceed `24x24` CSS pixel minimum target sizing.

## 3. Known Limitations & Alternative Formats
- **Force-Directed Graph Spatial Dragging**: Dragging graph nodes to arbitrary `(x, y)` coordinates is pointer-based. All architectural relationships, dependencies, cluster memberships, and search capabilities are fully accessible via keyboard through the **Repository Matcher & Chat**, **Cluster Explorer**, **Repository Catalog**, and **Cross-Domain Flow** tabs, as well as the standalone Markdown report (`KNOWLEDGE_BASE.md`).

## 4. Feedback & Contact
If you encounter an accessibility barrier, please contact `[CONTACT EMAIL]` with a description of the issue and the browser/assistive technology used.
