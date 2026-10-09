#!/usr/bin/env bash
set -euo pipefail
rm -rf dist
uv build
uv run twine check --strict dist/*
uv run python scripts/release.py inspect --tag "${RELEASE_TAG:-}"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
uv venv "$TMP_DIR/wheel"
uv pip install --python "$TMP_DIR/wheel/bin/python" dist/*.whl
(cd "$TMP_DIR" && "$TMP_DIR/wheel/bin/python" -I -c 'from tts_api_client import TTSClient, AsyncTTSClient, SpeechRequest; print(SpeechRequest(text="hello").payload())')
uv run python -c 'import tarfile,sys; tarfile.open(sys.argv[1]).extractall(sys.argv[2], filter="data")' dist/*.tar.gz "$TMP_DIR/source"
uv build --wheel "$TMP_DIR"/source/* --out-dir "$TMP_DIR/rebuilt"
uv venv "$TMP_DIR/sdist"
uv pip install --python "$TMP_DIR/sdist/bin/python" "$TMP_DIR"/rebuilt/*.whl
(cd "$TMP_DIR" && "$TMP_DIR/sdist/bin/python" -I -c 'from tts_api_client import TTSClient, AsyncTTSClient; print("sdist import OK")')
