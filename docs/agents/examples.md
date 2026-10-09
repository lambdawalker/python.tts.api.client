# Runnable examples

## Offline contract demonstration

Run `uv sync --locked --group dev`, then `uv run python examples/offline.py` from a
source checkout. No credentials or server needed. The deterministic HTTPX fixture
exercises discovery, validation, submission, polling and atomic download. Expected:
`Discovery → validation → job → download: OK`. Output bytes are a fixture, not audio.
[Full source](../../examples/offline.py).

## Live speech integration

Set `TTS_BASE_URL` and optionally `TTS_API_KEY`, then run
`uv run python examples/generate.py`. Requires a shared-API server with a listed voice.
Read guidance, enter native text and a voice ID. Expected: job ID and `speech.wav`.
Network errors require application recovery; timeouts leave the server job running.
[Full source](../../examples/generate.py). This example has not been tested with a live model.

## Recovery and async fixtures

`uv run pytest tests/test_streaming.py tests/test_edge_cases.py` exercises disconnects,
replay, polling fallback, timeouts, upload/download, asyncio and real loopback HTTP.
These are tests, not a production server implementation. See [recipes](recipes.md)
for integration snippets and [API](api.md) for exact declarations.

Screenshots are intentionally omitted: this is a nonvisual HTTP library. Executable
examples and structured output communicate its behavior more accurately.
