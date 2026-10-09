# Documentation maintenance

The site describes development source until a fully confirmed release is archived.
English and Spanish consumer guides cover the same API; maintainer runbooks remain
English and are labeled as such in Spanish navigation. There is one module, so no
artificial module selector. Every page has version/language links retaining the guide.

Authoritative ownership: Python source defines behavior; registry-verified catalog
records define availability; examples define executable snippets; docs/agents holds
English prose; docs/es holds reviewed translations. API declarations are extracted
from AST by scripts/api_docs.py. IMPORT.md is generated from confirmed catalog entries.
No runtime documentation dependencies are added. The site uses Python-Markdown and
Pygments in the existing uv development lock, with templates/CSS in sites and its
renderer in scripts/docs.py. A second Node framework would add tooling without helping
this small nonvisual library. Consumer search is currently the guide navigation and
browser find; a search index can be added if the corpus expands.

## Author and preview

```bash
uv sync --locked --group dev
uv run python scripts/api_docs.py
uv run python scripts/docs.py build
uv run python scripts/docs.py check
uv run python examples/offline.py
uv run pytest
```

Preview with `uv run python scripts/serve_docs.py`, then open
`http://localhost:8001/python.tts.api.client/en/dev/index/` or the Spanish route.
The renderer clears sites/dist on each build. HTML, raw Markdown, CSS and JavaScript
are deterministic for the same source SHA/content; generated output is not committed.
Copy buttons, heading anchors, keyboard focus, reduced-motion behavior and responsive
navigation are built in. Consumer raw Markdown is served at agents/en/dev/*.md,
with agents/index.md and llms.txt as stable entry points. Code/source links use the
scope's immutable source commit. Main source installation remains explicitly moving.

## Translation review

Edit English and Spanish pages together; preserve identifiers and code fences.
After reviewing meaning and examples, run `uv run python scripts/translation_review.py`
to record SHA256 hashes of both files. This is an intentional author command, never
a CI acceptance step. A missing or stale translation displays the canonical English
page of the SAME version with a visible Spanish notice. Changing current source never
invalidates historical translations, which use their own recorded documentation SHA.
API explanations are authored in scripts/api_docs.py; declarations are shared verbatim.

## Historical documentation

There are no seeded releases: the archive starts at the first complete confirmed
publication. scripts/archive_release.py verifies registry hashes, immutable tag/source
identity, and retained main ancestry before creating a record. It refuses conflicting
identities and never replaces older records. Each record separates source_sha from
docs_sha; rendered examples and translations come from that immutable docs revision.
A correction requires a reviewed commit retained in main, checked against the old API;
update only docs_sha and record correction reason/history, never source_sha/tag/files.
Do not point at an unmerged PR commit that squash merge may discard.

The current renderer reads historical files via git show as data. It does not run old
scripts or install historical dependencies. Missing objects fail the build. CI fetches
full history. Every build renders every catalog entry, including exact installation
and raw Markdown routes; no prior deployment/artifact is required. Failed or partial
publications never enter the catalog. Archive confirmations before changing latest
facts; semantic ordering prevents an older recovery becoming latest.

## GitHub Pages

Owner setup: Settings → Pages → Build and deployment → GitHub Actions. The supplied
docs.yml validates pull requests and deploys only canonical main. Deployment permission
is isolated in the github-pages environment job. Account settings have not been
verified. Site target: https://lambdawalker.github.io/python.tts.api.client/ .

Manual docs workflow dispatch on main is documentation-only and cannot upload to PyPI.
The workflow serializes deployments and checks main HEAD immediately before deployment,
so a delayed old build is skipped. A documentation failure does not retry package
upload. After manually archiving confirmed publication facts, a normal main push or
manual docs dispatch builds the updated catalog; no bot-trigger assumption is needed.

## Coverage and screenshots

| Public feature | Human and agent guide | Executable coverage |
| --- | --- | --- |
| Discovery / validation / speech | concepts, quickstart, api | examples/offline.py, examples/generate.py |
| asyncio / lifecycle / timeouts | quickstart, concepts, api | tests/test_edge_cases.py |
| voice references / design / conversion | recipes, api | tests/test_edge_cases.py |
| jobs / SSE / reconnect / cancellation | recipes, concepts, api | tests/test_streaming.py |
| assets / atomic download | recipes, api | examples/offline.py, tests/test_edge_cases.py |
| error types / configuration | troubleshooting, limitations, api | tests/test_client.py |
| migration / installation | migration, installation | artifact smoke checks |

Each guide is rendered in English/Spanish HTML and published as raw Markdown. Tests
are explicitly identified as fixtures, not live model demos. No library UI exists,
so screenshots/baseline tooling are omitted. Desktop/narrow rendered-site inspection
is separate from structural HTML checks; do not claim visual inspection from links alone.
