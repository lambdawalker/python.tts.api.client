"""Prepare a local release commit; remote refs change only after validation."""

import argparse
import os
import re
import subprocess
from pathlib import Path

from release import ROOT, version_check

VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")


def numbers(version):
    if not VERSION.fullmatch(version):
        raise ValueError("Version must be X.Y.Z, without v, leading zeros or prerelease suffix")
    return tuple(map(int, version.split(".")))


def choose_version(current, latest, messages, override=""):
    numbers(current)
    if latest and numbers(current) != numbers(latest):
        raise ValueError("Source version must match latest release tag before releasing")
    if override:
        value = numbers(override)
        if value < numbers(current) or (latest and value <= numbers(latest)):
            raise ValueError(
                "Manual version must be newer than the last release and not lower than source"
            )
        return override
    level = 0
    for message in messages:
        subject = message.splitlines()[0] if message else ""
        match = re.match(r"^([a-z]+)(?:\([^\n)]+\))?(!)?:\s", subject)
        if not match:
            continue
        if match[2] or re.search(r"^BREAKING[ -]CHANGE:\s", message, re.MULTILINE):
            level = max(level, 3)
        elif match[1] == "feat":
            level = max(level, 2)
        elif match[1] == "fix":
            level = max(level, 1)
    if not level:
        return None
    if not latest:
        return current  # Existing 0.1.0 is the first-release policy.
    major, minor, patch = numbers(latest)
    if level == 3 and major:
        return f"{major + 1}.0.0"
    if level >= 2:
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def update_versions(version):
    files = {
        "pyproject.toml": (r'(?m)^version = "[^"]+"$', f'version = "{version}"'),
        "src/tts_api_client/__init__.py": (
            r'(?m)^__version__ = "[^"]+".*$',
            f'__version__ = "{version}"',
        ),
        "uv.lock": ("", None),
    }
    for filename, (pattern, replacement) in files.items():
        path = ROOT / filename
        text = path.read_text()
        if filename == "uv.lock":
            text, count = re.subn(
                r'(\[\[package\]\]\nname = "tts-api-client"\nversion = ")[^"]+("\n)',
                lambda m: m[1] + version + m[2],
                text,
            )
        else:
            text, count = re.subn(pattern, replacement, text)
        if count != 1:
            raise ValueError(f"Expected exactly one version in {filename}")
        path.write_text(text)
    version_check(tag=f"v{version}")


def prepare(override=""):
    base = git("rev-parse", "HEAD")
    if git("status", "--porcelain"):
        raise ValueError("Prepare requires a clean checkout")
    versions = [t[1:] for t in git("tag", "--list", "v*").splitlines() if VERSION.fullmatch(t[1:])]
    latest = max(versions, key=numbers) if versions else None
    if latest:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", f"v{latest}", base], cwd=ROOT, check=True
        )
    revision = f"v{latest}..HEAD" if latest else "HEAD"
    messages = git("log", "--format=%B%x00", revision).split("\x00")
    messages = [m.strip() for m in messages if m.strip()]
    version = choose_version(version_check(), latest, messages, override)
    if not version:
        return {"created": "false"}
    tag = f"v{version}"
    if tag in git("tag", "--list").splitlines():
        raise ValueError("Release tag already exists")
    update_versions(version)
    changelog = ROOT / "CHANGELOG.md"
    previous = changelog.read_text() if changelog.exists() else "# Changelog\n"
    lines = "\n".join("- " + m.splitlines()[0] for m in messages)
    changelog.write_text(
        f"# Changelog\n\n## {version}\n\n{lines}\n\n"
        + previous.removeprefix("# Changelog\n").lstrip()
    )
    git("add", "pyproject.toml", "uv.lock", "src/tts_api_client/__init__.py", "CHANGELOG.md")
    git(
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit",
        "-m",
        f"chore: release {tag}",
    )
    sha = git("rev-parse", "HEAD")
    git("branch", "release-candidate", sha)
    git("bundle", "create", "release-candidate.bundle", "release-candidate")
    return {"created": "true", "tag": tag, "sha": sha, "base": base}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="")
    args = parser.parse_args()
    outputs = prepare(args.version)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")
