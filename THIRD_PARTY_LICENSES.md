# Third-Party Licenses & Software Bill of Materials (SBOM)

This project (`github-repo-kb-skill`) is licensed under the **Apache License, Version 2.0** (see [LICENSE](LICENSE)).

## Python Runtime Dependencies
- **None** (zero external runtime dependencies; uses the Python 3.8+ standard library exclusively).
- Optional test runner: `pytest` (MIT License; not bundled or required, standard `unittest` works out of the box).

## Vendored Client-Side Assets

| Package | Version | License | Compatibility with Apache-2.0 | Vendored Path | SHA-256 Checksum |
|---|---|---|---|---|---|
| `d3` (D3.js) | `7.9.0` | **ISC License** | Compatible (permissive) | `scripts/vendor/d3.v7.min.js` | `f2094bbf6141b359722c4fe454eb6c4b0f0e42cc10cc7af921fc158fceb86539` |
| `d3` License File | `7.9.0` | **ISC License** | Compatible | `scripts/vendor/D3_LICENSE` | `3e6849627f74ff73c257a3ae1efb574015d94fc1035c05ec3c15805165efcbc4` |

### D3.js License Notice (`d3@7.9.0`)

```text
Copyright 2010-2023 Mike Bostock

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
```
