# Publishing runbook

Distribution: `tts-api-client`. Import: `tts_api_client`. Package root:
`src/tts_api_client`. One pure-Python wheel and one sdist; no CLI. Hatchling and uv
remain the build/dependency tools. Runtime dependencies remain HTTPX and Pydantic.

## Owner setup before the first release

PyPI returned HTTP 404 for the proposed name on 2026-10-09. This is not a name
reservation or proof of ownership. No GitHub releases/tags existed at inspection.
The initial source version is 0.1.0. With no prior release tags, the first automatic
release uses that existing version; a manual override may choose a higher version.

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
runs on `main` even while checking out a release SHA, so allow `main`. Only the
finalize job needs contents:write to fast-forward the release commit and create the
tag/release. No PR creation/approval or issues permission is needed. The upload job
alone has OIDC. No long-lived PyPI token is required. Account settings have NOT been
configured by this change. Branch rules must allow the workflow to write version
commits to main; if your policy requires PRs, this direct-release mode will stop.

## Automatic releases and manual versions

Push or merge to main → calculate next version → prepare local version/changelog
commit → validate that exact candidate on Python 3.10–3.13 → atomically fast-forward
main and add the immutable tag → GitHub release → PyPI upload → confirmation.
No release pull request, automatic PR approval, or PR merge is involved.

`fix:` increments patch; `feat:` increments minor. A Conventional Commit with `!`
or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer increments major after 1.0 and
minor before 1.0. Multiple commits use the highest required bump. Other commit types
alone do not release unless marked breaking. The first eligible release uses the
existing source version. The script updates pyproject, runtime version, the project's
uv.lock entry and CHANGELOG together; unrelated dependencies are unchanged.

To choose the number: Actions → Release and publish → Run workflow → select main →
enter `version`, for example `0.3.0`. Leave it blank to calculate from commits. This
is a production release action, not a dry run. The input accepts stable X.Y.Z without
v, leading zeros or prerelease suffixes. It must exceed the latest release and must
not lower the source version. A manual version can release documentation-only changes.
A reused tag is rejected; this field is not a recovery/overwrite mechanism.

| Event | Behavior |
| --- | --- |
| Pull request | ci.yml tests/builds; docs.yml validates; no release or upload. |
| Push to main | Automatic commit-based release when eligible changes exist. |
| Manual dispatch on main | Automatic calculation or explicit version; may publish. |
| Release event | Not subscribed; recover using the original run. |
| Fork or non-main dispatch | Release preparation skipped; no publication. |

Preparation has read-only permissions. The candidate is retained as a git bundle
and every matrix job checks out its exact SHA. All checks must pass before remote
refs change or upload starts. Finalization verifies the expected parent and rejects
an advanced main branch; start a fresh run against current main if another commit
arrived. It never force-pushes. A repeat finalization accepts only the exact same
existing tag/source identity. Branch/tag creation is atomic.

GITHUB_TOKEN-created version commits do not normally trigger push workflows, so
all publication jobs are connected in the same run. Documentation separately rebuilds
on successful completion of Release and publish, checking out current main and
checking its SHA again before deployment. A site failure cannot republish a package.
Release reconciliation is serialized and actual upload retains the shared
`pypi-tts-api-client` lock with cancellation disabled.

Any old Release Please PR/branch can be closed/deleted by the owner; it is no longer
used. Do not merge an old release PR after switching to this workflow.

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

A GitHub release is not proof of a PyPI publication. Candidate validation happens
before tag creation. For finalization/upload failures, retain the candidate bundle,
artifacts and source identity and rerun failed jobs in the ORIGINAL workflow run.
A new automatic run may find no eligible commits and skip release preparation.
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
mismatch: inspect candidate pyproject, runtime version and uv.lock. A protected-main
rejection requires an owner decision on direct-release write permissions. Duplicate filenames: use reconciliation above, not
skip-existing. No TestPyPI workflow is configured because staging was not requested.

Sources: [PyPA publisher](https://github.com/pypa/gh-action-pypi-publish),
[packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/),
[workflow event rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
