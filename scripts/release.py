"""Release identity, artifact inspection, and registry confirmation. No upload code."""

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def version_check(root=ROOT, tag=""):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Only stable X.Y.Z versions are supported")
    runtime = re.search(
        r'__version__ = "([^"]+)"', (root / "src/tts_api_client/__init__.py").read_text()
    ).group(1)
    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = next(p["version"] for p in lock["package"] if p["name"] == project["name"])
    if runtime != version or locked != version or (tag and tag != f"v{version}"):
        raise ValueError("Project/runtime/lock/tag versions disagree")
    return version


def inspect_artifacts(dist, version):
    files = sorted(p for p in dist.iterdir() if p.name != ".gitignore")
    if len(files) != 2 or sum(p.suffix == ".whl" for p in files) != 1:
        raise ValueError("Expect exactly one wheel and one sdist")
    records = {}
    for path in files:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                metadata = archive.read(next(n for n in names if n.endswith("/METADATA")))
                expected = {
                    "tts_api_client/" + p.name for p in (ROOT / "src/tts_api_client").glob("*.py")
                }
                expected.add("tts_api_client/py.typed")
                if not expected.issubset(names):
                    raise ValueError("Wheel missing public package files")
                if any(not (n.startswith("tts_api_client/") or ".dist-info/" in n) for n in names):
                    raise ValueError("Unexpected wheel content")
        elif path.name.endswith(".tar.gz"):
            with tarfile.open(path) as archive:
                names = archive.getnames()
                metadata = archive.extractfile(
                    next(n for n in names if n.endswith("/PKG-INFO"))
                ).read()
                allowed = (
                    "src",
                    "tests",
                    "pyproject.toml",
                    "README.md",
                    "uv.lock",
                    "PKG-INFO",
                    ".gitignore",
                )
                if any(len(Path(n).parts) > 1 and Path(n).parts[1] not in allowed for n in names):
                    raise ValueError("Unexpected sdist content")
                if any(
                    m.issym()
                    or m.islnk()
                    or ".." in Path(m.name).parts
                    or Path(m.name).is_absolute()
                    for m in archive.getmembers()
                ):
                    raise ValueError("Unsafe archive member")
        else:
            raise ValueError("Unexpected distribution file")
        meta = BytesParser().parsebytes(metadata)
        if meta["Name"] != "tts-api-client" or meta["Version"] != version:
            raise ValueError("Built metadata disagrees with source")
        records[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return records


def confirm(record, attempts=6):
    """Confirm exact file hashes; missing/partial releases never become available."""
    url = f"https://pypi.org/pypi/tts-api-client/{record['version']}/json"
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                data = json.load(response)
            actual = {f["filename"]: f["digests"]["sha256"] for f in data["urls"]}
            if actual == record["files"] and not any(f["yanked"] for f in data["urls"]):
                return
            if any(n in actual and actual[n] != h for n, h in record["files"].items()):
                raise ValueError("PyPI hash conflict: stop; never replace this version")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        if attempt + 1 < attempts:
            time.sleep(10)
    raise ValueError("Registry files not fully confirmed; do not advertise availability")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inspect", "confirm"])
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    if args.command == "inspect":
        version = version_check(tag=args.tag)
        record = {
            "version": version,
            "tag": args.tag,
            "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "files": inspect_artifacts(ROOT / "dist", version),
        }
        (ROOT / "release-evidence.json").write_text(json.dumps(record, indent=2) + "\n")
    else:
        confirm(json.loads((ROOT / "release-evidence.json").read_text()))


if __name__ == "__main__":
    main()
