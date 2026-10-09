"""Publishing and documentation invariants; no external registry writes."""

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_versions_and_tag_policy():
    release = module("release")
    version = release.version_check()
    assert release.version_check(tag=f"v{version}") == version
    for tag in [version, "v9999.0.0", f"v{version}rc1", "../v0.1.0"]:
        with pytest.raises(ValueError):
            release.version_check(tag=tag)


def test_raw_link_transform_preserves_code_and_fragment():
    docs = module("docs")
    text = "[Guide](concepts.md#ownership)\n[Web](https://example.org/x)\n```\n[x](api.md)\n```"
    result = docs.transform_links(text, "0.1.0", "es", "a" * 40, True)
    assert "/agents/es/0.1.0/concepts.md#ownership" in result
    assert "[Web](https://example.org/x)" in result
    assert "```\n[x](api.md)\n```" in result


def test_all_exports_in_reference_and_translations_preserve_code():
    import tts_api_client

    api = (ROOT / "docs/agents/api.md").read_text()
    for name in tts_api_client.__all__:
        assert f"## {name}" in api
    for en in (ROOT / "docs/agents").glob("*.md"):
        es = ROOT / "docs/es" / en.name
        assert es.exists()
        assert re.findall(r"```[\s\S]*?```", en.read_text()) == re.findall(
            r"```[\s\S]*?```", es.read_text()
        )


def test_stale_translation_uses_same_revision(monkeypatch):
    docs = module("docs")
    seen = []

    def read(path, ref=None):
        seen.append(ref)
        return "{}" if path.endswith("translations.json") else "# Historical canonical"

    monkeypatch.setattr(docs, "read", read)
    assert docs.localized("api", "es", "a" * 40) == ("# Historical canonical", True)
    assert seen == ["a" * 40, "a" * 40]


def test_missing_snapshot_fails():
    docs = module("docs")
    with pytest.raises(Exception):
        docs.read("docs/agents/index.md", "0" * 40)


def test_catalog_semantic_order_and_installation_scope(tmp_path, monkeypatch):
    docs = module("docs")
    monkeypatch.setattr(docs, "ROOT", tmp_path)
    folder = tmp_path / "docs/releases/history"
    folder.mkdir(parents=True)
    for version in ["0.9.0", "0.10.0"]:
        (folder / f"{version}.json").write_text(
            json.dumps(
                {
                    "module": "tts-api-client",
                    "destination": "pypi",
                    "version": version,
                    "source_sha": "a" * 40,
                    "docs_sha": "b" * 40,
                    "tag": f"v{version}",
                    "files": {"wheel.whl": "c" * 64},
                }
            )
        )
    assert [r["version"] for r in docs.catalog()] == ["0.9.0", "0.10.0"]
    assert "tts-api-client==0.9.0" in docs.installation(docs.catalog()[0])
    assert "tts-api-client==0.10.0" in docs.import_document()


def test_registry_partial_or_conflicting_files_never_confirm(monkeypatch):
    release = module("release")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(
                {"urls": [{"filename": "wheel.whl", "yanked": False, "digests": {"sha256": "a"}}]}
            ).encode()

    monkeypatch.setattr(release.urllib.request, "urlopen", lambda *a, **k: Response())
    release.confirm({"version": "0.1.0", "files": {"wheel.whl": "a"}}, attempts=1)
    with pytest.raises(ValueError, match="fully confirmed"):
        release.confirm({"version": "0.1.0", "files": {"wheel.whl": "a", "sdist": "b"}}, attempts=1)
    with pytest.raises(ValueError, match="hash conflict"):
        release.confirm({"version": "0.1.0", "files": {"wheel.whl": "wrong"}}, attempts=1)


def test_archive_preserves_old_records_and_corrections(tmp_path, monkeypatch):
    archive = module("archive_release")
    monkeypatch.setattr(archive, "ROOT", tmp_path)
    monkeypatch.setattr(archive, "confirm", lambda record: None)
    monkeypatch.setattr(archive.subprocess, "check_output", lambda *a, **k: "a" * 40)
    monkeypatch.setattr(archive.subprocess, "run", lambda *a, **k: None)
    folder = tmp_path / "docs/releases/history"
    evidence = {
        "version": "0.1.0",
        "tag": "v0.1.0",
        "source_sha": "a" * 40,
        "files": {"wheel.whl": "b"},
    }
    archive.archive(evidence)
    record = folder / "0.1.0.json"
    data = json.loads(record.read_text())
    data["docs_sha"] = "c" * 40
    record.write_text(json.dumps(data))
    archive.archive(evidence)
    assert json.loads(record.read_text())["docs_sha"] == "c" * 40
    archive.archive({**evidence, "version": "0.2.0", "tag": "v0.2.0"})
    assert record.exists()
    with pytest.raises(ValueError, match="Conflicting"):
        archive.archive({**evidence, "files": {"wheel.whl": "different"}})


def test_missing_translation_file_falls_back(monkeypatch):
    docs = module("docs")
    original = docs.read

    def read(path, ref=None):
        if path.startswith("docs/es/"):
            raise FileNotFoundError(path)
        return original(path, ref)

    monkeypatch.setattr(docs, "read", read)
    text, fallback = docs.localized("concepts", "es")
    assert fallback
    assert text.startswith("# Concepts")


def test_complete_historical_build_is_pinned_and_cleans_stale_files(tmp_path, monkeypatch):
    import shutil
    import subprocess

    docs = module("docs")
    for folder in ["docs", "sites", "examples"]:
        shutil.copytree(
            ROOT / folder, tmp_path / folder, ignore=shutil.ignore_patterns("dist", "__pycache__")
        )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.org",
            "commit",
            "-qm",
            "snapshot",
        ],
        cwd=tmp_path,
        check=True,
    )
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    history = tmp_path / "docs/releases/history"
    history.mkdir(parents=True, exist_ok=True)
    (history / "0.1.0.json").write_text(
        json.dumps(
            {
                "module": "tts-api-client",
                "destination": "pypi",
                "version": "0.1.0",
                "source_sha": sha,
                "docs_sha": sha,
                "tag": "v0.1.0",
                "files": {"fixture": "hash"},
            }
        )
    )
    canonical = tmp_path / "docs/agents/concepts.md"
    canonical.write_text(canonical.read_text() + "\nCurrent-only-sentinel\n")
    out = tmp_path / "sites/dist"
    out.mkdir()
    (out / "stale.html").write_text("must disappear")
    monkeypatch.setattr(docs, "ROOT", tmp_path)
    monkeypatch.setattr(docs, "OUT", out)
    docs.build()
    historical = (out / "es/0.1.0/concepts/index.html").read_text()
    current = (out / "es/dev/concepts/index.html").read_text()
    assert "Current-only-sentinel" not in historical
    assert "Current-only-sentinel" in current
    assert "Traducción ausente o desactualizada" in current
    assert "Traducción ausente o desactualizada" not in historical
    assert "/agents/es/0.1.0/index.md" in historical
    assert not (out / "stale.html").exists()
    assert "tts-api-client==0.1.0" in (out / "agents/en/0.1.0/installation.md").read_text()
