"""Record confirmed registry facts for a retained release; never upload or commit."""

import json
import subprocess
import sys
from pathlib import Path

from release import ROOT, confirm


def archive(evidence):
    confirm(evidence)
    version = evidence["version"]
    import re

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Only stable versions are supported")
    if evidence["tag"] != f"v{version}":
        raise ValueError("Tag/version mismatch")
    source = subprocess.check_output(
        ["git", "rev-parse", f"refs/tags/v{version}^{{commit}}"], cwd=ROOT, text=True
    ).strip()
    if source != evidence["source_sha"]:
        raise ValueError("Tag no longer matches evidence")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", source, "origin/main"], cwd=ROOT, check=True
    )
    record = {**evidence, "module": "tts-api-client", "destination": "pypi", "docs_sha": source}
    target = ROOT / f"docs/releases/history/{version}.json"
    if target.exists():
        old = json.loads(target.read_text())
        if any(old[k] != record[k] for k in evidence):
            raise ValueError("Conflicting immutable release identity")
        return  # preserve reviewed documentation corrections on retry
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + "\n")
    print("Archived confirmed release; review and commit:", target)


if __name__ == "__main__":
    archive(json.loads(Path(sys.argv[1]).read_text()))
