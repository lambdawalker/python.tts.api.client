"""Intentional maintainer acceptance after reviewing both language versions."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = {}
for path in sorted((ROOT / "docs/agents").glob("*.md")):
    translation = ROOT / "docs/es" / path.name
    if translation.exists():
        records[path.stem] = {
            "canonical_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "translation_sha256": hashlib.sha256(translation.read_bytes()).hexdigest(),
        }
(ROOT / "docs/translations.json").write_text(json.dumps(records, indent=2) + "\n")
