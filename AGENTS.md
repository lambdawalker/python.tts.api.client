# Agent guidance

This repository implements only the Python HTTP client. Architecture authority: https://github.com/lambdawalker/design.ai/tree/main/tts.

- Preserve text, tags, instructions, and transcripts exactly. Never add automatic input adaptation.
- Keep sync and asyncio public methods equivalent. Share model/validation/parser behavior in common modules.
- MCP belongs to the server. No GPU/framework/model dependency belongs here.
- Do not retry submissions automatically or cancel jobs when clients close/time out.
- Never follow untrusted response URLs or HTTP redirects with caller credentials.
- Request fields are strict; responses retain additive fields. Model-native extension constraints belong to the server.
- Test real observable HTTP behavior and network recovery with fixtures. No live TTS server is assumed.
- Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and `uv build` before delivery.
- Keep README and docs/contracts.md accurate about draft wire assumptions and limitations.
- PyPI publishing and a license require owner decisions; do not imply this package is released.
