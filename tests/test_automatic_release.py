"""Version policy and metadata update invariants."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "prepare_release", ROOT / "scripts/prepare_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


@pytest.mark.parametrize(
    "latest,messages,expected",
    [
        (None, ["feat: initial"], "0.1.0"),
        ("0.1.0", ["fix: bug"], "0.1.1"),
        ("0.1.0", ["feat: operation"], "0.2.0"),
        ("0.1.0", ["feat!: incompatible"], "0.2.0"),
        ("1.2.3", ["fix: change\n\nBREAKING CHANGE: removed"], "2.0.0"),
        ("1.2.3", ["docs: explain", "chore: release v1.2.3"], None),
    ],
)
def test_policy(latest, messages, expected):
    assert release.choose_version(latest or "0.1.0", latest, messages) == expected


@pytest.mark.parametrize("value", ["v0.2.0", "0.1.0", "0.0.9", "1.0.0rc1", "01.2.3", "x\n1.0.0"])
def test_reject_invalid_manual_version(value):
    with pytest.raises(ValueError):
        release.choose_version("0.1.0", "0.1.0", [], value)


def test_manual_override_and_initial():
    assert release.choose_version("0.1.0", "0.1.0", [], "0.5.0") == "0.5.0"
    assert release.choose_version("0.1.0", None, [], "0.1.0") == "0.1.0"


def test_updates_only_project_lock_entry(tmp_path, monkeypatch):
    import shutil

    for filename in ["pyproject.toml", "uv.lock", "src/tts_api_client/__init__.py"]:
        target = tmp_path / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / filename, target)
    current = release.version_check()
    before = (tmp_path / "uv.lock").read_text()
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "version_check", lambda **kwargs: None)
    release.update_versions("0.9.0")
    expected = before.replace(
        f'name = "tts-api-client"\nversion = "{current}"',
        'name = "tts-api-client"\nversion = "0.9.0"',
    )
    assert (tmp_path / "uv.lock").read_text() == expected
    assert '__version__ = "0.9.0"' in (tmp_path / "src/tts_api_client/__init__.py").read_text()


def test_prepares_version_commit_and_reusable_bundle(tmp_path, monkeypatch):
    import shutil
    import subprocess

    for filename in ["pyproject.toml", "uv.lock", "src/tts_api_client/__init__.py"]:
        target = tmp_path / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / filename, target)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.org")
    git("add", ".")
    git("commit", "-qm", "feat: initial")
    current = release.version_check()
    git("tag", f"v{current}")
    (tmp_path / "README.md").write_text("new feature")
    git("add", ".")
    git("commit", "-qm", "feat: next operation")
    base = git("rev-parse", "HEAD")
    original_check = release.version_check
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(
        release, "version_check", lambda tag="": original_check(root=tmp_path, tag=tag)
    )
    result = release.prepare()
    expected = release.choose_version(current, current, ["feat: next operation"])
    assert result == {
        "created": "true",
        "tag": f"v{expected}",
        "sha": git("rev-parse", "HEAD"),
        "base": base,
    }
    assert git("rev-parse", "HEAD^") == base
    assert release.version_check() == expected
    bundle = tmp_path / "release-candidate.bundle"
    clone = tmp_path / "recovered"
    subprocess.run(
        ["git", "clone", "-q", "--branch", "release-candidate", str(bundle), str(clone)], check=True
    )
    recovered = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone, text=True).strip()
    assert recovered == result["sha"]
    assert f"v{expected}" not in git("tag", "--list").splitlines()
