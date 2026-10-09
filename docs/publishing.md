# Publishing runbook

Distribution: `tts-api-client`. Import: `tts_api_client`. Package root:
`src/tts_api_client`. One pure-Python wheel and one sdist; no CLI. Hatchling and uv
remain the build/dependency tools. Runtime dependencies remain HTTPX and Pydantic.

## Owner setup before the first release

PyPI returned HTTP 404 for the proposed name on 2026-10-09. This is not a name
reservation or proof of ownership. No GitHub releases/tags existed at inspection.
The source version is 0.1.0, which is the configured first-release target. The empty
manifest means no prior release, not a fictional 0.0.0 publication. Bootstrap SHA
`a67b05279f42c4687f862fee7c9efbb293a17c9c` is this repository's initial commit.

Choose the package license before publication; none has been invented here. Confirm
rights to the proposed PyPI name. Create a PyPI account with verified email and 2FA.
For a new project, configure a pending publisher in account Publishing settings;
for an existing project you own, add a publisher in that project's Publishing settings.
A pending publisher does not reserve the name. See the official
[PyPI setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and [existing project guide](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

| Trusted Publisher field | Exact value |
| --- | --- |
| PyPI project | `tts-api-client` |
| GitHub owner | `lambdawalker` |
| Repository | `python.tts.api.client` |
| Workflow filename | `publish.yml` |
| GitHub environment | `pypi` |

Create GitHub environment `pypi` and choose reviewers/ref restrictions. This workflow
runs on `main` even while checking out a tagged SHA, so allow `main`. Enable Actions
permission to create pull requests. Release management has contents/issues/PR write;
validation is read-only; only upload has OIDC. No long-lived PyPI token is required.
These account/environment settings have NOT been configured or verified by this change.

## Everyday release flow

Conventional Commits → Release Please PR → maintainer review/merge → GitHub release
→ exact-source validation across Python 3.10–3.13 → retained artifacts → PyPI upload
→ registry hash confirmation and clean exact-version install.

`fix:` increments patch; `feat:` increments minor. With the explicit pre-1.0 policy,
breaking changes increment minor instead of major. After 1.0, breaking changes
increment major. Prereleases are not supported by this workflow: versions/tags must
be stable `X.Y.Z` / `vX.Y.Z`. No automatic merge is enabled. The Python strategy updates
pyproject; extra-file updaters keep runtime version and the local uv.lock entry aligned.
The lock updater targets only this project's entry, leaving dependency versions intact.

| Event | Behavior |
| --- | --- |
| Pull request | ci.yml tests, docs checks and artifact validation; no OIDC or publication. |
| Push to main | publish.yml reconciles releases, validates the returned release PR candidate or exact release SHA, uploads only when release_created is true. |
| Manual dispatch on main | Same reconciliation, MAY publish a newly created release; not a dry run. |
| Published release event | Not subscribed; prevents duplicate paths. Recover with original run. |
| Fork | CI only; canonical repository checks prevent release management/upload. |

GITHUB_TOKEN-created PRs do not normally start a separate PR workflow. The release
workflow explicitly checks out the returned PR branch and tests it with read-only
permissions. These checks belong to the workflow's triggering commit, not necessarily
the PR head, and may not satisfy branch protection. If required PR checks are absent,
use an owner-managed GitHub App integration that triggers normal PR checks, or a
maintainer-triggered PR update; do not bypass required checks or assume base-commit
checks prove the candidate. Verify the candidate SHA in checkout logs before merging.

Release-created tag and SHA outputs feed dependent jobs directly. Tags are resolved
to commits and compared with checkout HEAD; main ancestry is verified. A failed
matrix cell blocks upload. Publication is serialized as `pypi-tts-api-client`, with
cancellation disabled. Workflow reconciliation is also serialized.

## Local validation / safe rehearsal

```bash
uv sync --locked --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python scripts/docs.py build
uv run python scripts/docs.py check
uv run python examples/offline.py
bash scripts/check_artifacts.sh
```

This does not upload. `RELEASE_TAG=v0.1.0 bash scripts/check_artifacts.sh` additionally
checks the chosen tag text against metadata (the workflow separately resolves the
actual git tag). Artifacts are inspected for expected modules/metadata and unintended
files; wheel and sdist-rebuilt wheel are installed outside the checkout. Evidence
records source SHA, version, filenames and SHA256 hashes. Retain `release-evidence`
and `tts-api-client-distributions` workflow artifacts durably before they expire.
Action versions follow the existing major-tag policy; no unverified SHA pins were invented.

## Recovery and confirmation

A GitHub release is not proof of a PyPI publication. If validation fails after tag
creation, keep the tag/source identity and rerun failed jobs in the ORIGINAL workflow
run. Starting a new reconciliation may return release_created=false and skip upload.
Do not move tags, change code under an existing version, or delete/reuse public files.

If upload may have partially succeeded, STOP before rerunning the upload job. Download
the original distributions and evidence; query
`https://pypi.org/pypi/tts-api-client/VERSION/json` and compare every filename and SHA256.
If all match, rerun only confirmation. If any hash conflicts, stop and investigate;
changed code needs a new version. If only some files exist, a maintainer must review
an explicit recovery workflow that uploads only the verified missing original files
under the SAME `pypi-tts-api-client` lock and publisher identity. There is intentionally
no blanket skip-existing or automatic partial-upload route. Do not rerun an uploader
with already-existing files. If artifacts expired, compare rebuilt hashes with durable
evidence; do not assume byte identity. Without original matching bytes/evidence, stop.

Confirmation retries registry metadata up to six times with ten-second pauses and
requires exact file/hash agreement and no yanked files. Propagation or install failure
is reported as failure, not publication success. Once confirmed, download evidence
and archive the release facts in a reviewed documentation-only commit:

```bash
uv run python scripts/archive_release.py release-evidence.json
uv run python scripts/docs.py build
```

Archive only after successful exact-version install from the confirmation job. Review
and commit the new `docs/releases/history/VERSION.json` and generated `IMPORT.md`.
This manual durable bookkeeping step is deliberate: registry confirmation does not
silently mutate the branch. It does not republish the package. All old records survive;
latest coordinates use semantic version ordering. Never update availability from a
proposed version. The docs workflow is independently retryable.

Publisher mismatch: compare owner/repository/workflow/environment exactly. Version
mismatch: review the release PR's pyproject, runtime version and uv.lock. Missing PR
checks: see bot behavior above. Duplicate filenames: use reconciliation above, not
skip-existing. No TestPyPI workflow is configured because staging was not requested.

Sources: [Release Please](https://github.com/googleapis/release-please-action),
[configuration](https://github.com/googleapis/release-please/blob/main/docs/customizing.md),
[PyPA publisher](https://github.com/pypa/gh-action-pypi-publish),
[packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/),
[workflow event rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
