# Publishing and documentation implementation

Scope: apply python-package-publishing.md and standalone-library-documentation.md,
including the versioned/multilingual supplement, to this single Python distribution.
Preserve API behavior, Hatchling, uv, Python >=3.10, and caller-owned inputs.

1. Add Release Please configuration and read-only exact-source artifact validation;
   isolate OIDC upload and retain hashes. Bootstrap from the initial repository commit,
   first version 0.1.0 from existing metadata. No publication during implementation.
2. Add canonical English agent guides, reviewed Spanish translations, generated API
   declarations, offline example, and a responsive static HTML renderer. Python-Markdown
   avoids a second dependency manager for this Python-only library. No screenshots:
   there is no library UI and screenshots would not explain the HTTP contracts.
3. Keep confirmed release catalog empty until registry hashes are verified. Historical
   documentation comes from immutable git revisions, rendered as data with current tools.
   Version/language navigation stays in scope, with explicit stale-translation fallback.
4. Test custom release and documentation logic, build/install both artifacts, validate
   links and workflow syntax, review the whole change, then commit to the target repo.

Account setup remains owner work: license decision, PyPI account/project publisher,
GitHub pypi environment and Actions Pages. No account configuration is claimed.

## Verification record

- 43 tests pass on Python 3.12, including fresh git historical snapshots, translation
  fallback, archive idempotency, version checks and registry partial/conflict rejection.
- Clean uv environment site build, all local links/anchors/raw Markdown/base paths pass.
- Actionlint 1.7.12 passes. Ruff lint/format and git diff whitespace checks pass.
- Wheel/sdist strict Twine checks and isolated wheel + sdist-rebuilt installs pass.
- Offline executable demo passes. Live-model example remains unverified.
- Chromium rendered English desktop (1440px) and Spanish narrow (390px) pages inspected;
  keyboard skip links and horizontal layout checks pass. No screenshot assets needed.
- Fresh review findings addressed: missing first archive directory, publication-dependent
  historical wording, scoped AI links, and absent translation fallback.
- Owner setup and real PyPI upload remain unperformed. Remote matrix/Pages are not
  claimed by these local checks. Confirmed availability archival is a reviewed manual
  documentation commit after hash confirmation and exact-version installation.
