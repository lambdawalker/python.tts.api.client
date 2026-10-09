# TTS API Client

Lightweight Python client for the shared local TTS API specified in [design.ai/tts](https://github.com/lambdawalker/design.ai/tree/main/tts). Includes synchronous and asyncio clients, typed requests/responses, persistent job handles, reconnectable SSE notifications, polling, and streamed audio transfers.

**Compatibility:** this implements the proposed unified `/v1` contract. It does not directly support the legacy Fish `/v1/tts` or Chatterbox-specific API. Server adapters must implement the shared contract first. Tests use HTTP fixtures; GPU/model integration is not yet verified.

Callers own their inputs. The client never strips tags, translates instructions, changes voices, or repairs content. Read the target model's capabilities and guidance before constructing input. MCP belongs to the server; this package uses HTTP and has no model, Torch, CUDA, or MCP dependency.

## Install

Python 3.10 or newer. Install from this repository (no PyPI release is assumed):

```bash
uv add "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git"
```

Or clone and run `uv sync --group dev` for development. Import as `tts_api_client`.

## Generate speech

```python
from tts_api_client import TTSClient

with TTSClient("http://localhost:8000", api_key="your-server-token") as client:
    capabilities = client.capabilities()
    guidance = client.guidance("tts")
    voices = client.list_voices()
    print(capabilities.model_dump(), guidance.model_dump(), voices)

    # The person or agent authors model-appropriate input after reading guidance.
    request = {"text": "Hello!", "voice": {"alias": "narrator"}}
    client.validate_speech(**request)
    job = client.generate_speech(**request, idempotency_key="example-request-001")
    print(job.id)  # Persist this ID to resume from a different process.
    result = job.wait(timeout=600)
    client.download_asset(result.results[0].asset_id, "speech.wav")
```

Configure a valid `narrator` alias on the server, or select a voice ID from `list_voices()`. The base URL is the deployment root, **without `/v1`**; a reverse-proxy prefix such as `https://host/tts` is supported.

Use `instructions="..."` only when the chosen profile supports it. Model-native tags go directly into `text`. Native controls belong in `extensions={"engine_namespace": {...}}`; their names come from server guidance.

## Asyncio

```python
import asyncio
from tts_api_client import AsyncTTSClient, SpeechRequest, VoiceSelector


async def main():
    async with AsyncTTSClient("http://localhost:8000") as client:
        print((await client.guidance("tts")).model_dump())
        request = SpeechRequest(text="Hello!", voice=VoiceSelector(alias="narrator"))
        job = await client.generate_speech(request, idempotency_key="async-example-001")
        result = await job.wait(timeout=600)
        await client.download_asset(result.results[0].asset_id, "speech.wav")


asyncio.run(main())
```

All network operations have equivalent sync/async methods. `client.job(id)` simply constructs a handle, so it is not awaited. Async support uses asyncio; Trio is not currently supported.

## Progress and recovery

```python
from contextlib import closing
from tts_api_client import TTSClient

with TTSClient("http://localhost:8000") as client:
    job = client.job("previous-job-id")
    with closing(job.events()) as events:
        for event in events:
            print(event.source, event.id, event.event, event.data)
    result = job.wait(timeout=60)  # Raises if the job failed or was cancelled.
```

SSE reconnects with `Last-Event-ID`, suppresses replayed monotonic IDs, discards incomplete frames, and falls back to status polling after bounded reconnection attempts. Polling snapshots have `source="poll"`, `event="status"`, and no event ID. Events report failed/cancelled terminal states as data; `wait()` raises structured job exceptions. The event iterator normally ends when a closed/disconnected stream is followed by a terminal status lookup; servers should close streams after terminal events.

Options: `after`, `reconnect_attempts=3`, `reconnect_delay=1`, `polling_fallback=True`, `poll_interval=1`. A slow stream is bounded by the HTTP inactivity timeout. Close abandoned generators with `closing` or `contextlib.aclosing` for async generators. Neither disconnect nor client closure cancels generation. Cancellation is explicit: `job.cancel()` or `await job.cancel()`.

Generation is **never automatically retried**. After an ambiguous network failure, resubmit the identical request with the **same** idempotency key if the server supports the specified idempotency contract. A new key means new work. Existing job IDs can be reattached with `client.job(id)`.

## References, design, and conversion

```python
asset = client.upload_asset("reference.wav")
voice = client.register_voice(
    references=[{"asset_id": asset.id, "transcript": "Words actually spoken."}],
    alias="narrator",
)
job = client.generate_speech(text="New words.", voice={"id": voice.id})
```

The client must be open while using these methods. Registration stores conditioning references; it does not fine-tune a model. Optional workflows:

```python
design = client.design_voice(description="A warm, low voice", preview_text="Hello.")
conversion = client.convert_voice(source_asset_id=asset.id, voice={"id": voice.id})
```

Check capabilities first. Reference files are uploaded unchanged. No ASR, audio cleanup, or voice substitution is performed. Each server has its own asset and voice IDs.

## Errors and timeouts

```python
from tts_api_client import APIError, JobFailedError, JobTimeoutError, TransportError

try:
    result = job.wait(timeout=300)
except APIError as exc:
    print(exc.status_code, exc.code, exc.field, exc.retryable, exc.guidance_url)
except JobFailedError as exc:
    print(exc.code, exc.job.error)
except JobTimeoutError:
    print("Stopped waiting; the server job continues.")
except TransportError:
    print("Connection failed; preserve the job ID or original idempotency key.")
```

`JobCancelledError` indicates cancellation; `ProtocolError` indicates malformed/incompatible server responses. Invalid local request fields raise Pydantic `ValidationError` (a `ValueError`). Unknown native tags are not validated by the SDK.

`timeout=30` on the client bounds HTTPX connection/read/write/pool inactivity. `job.wait(timeout=600)` is a separate polling deadline. Async waits interrupt an in-flight status request at the deadline. Sync waits check the deadline between requests and cap network timeouts to remaining time; an in-flight trickling response may exceed the polling deadline. A shorter HTTP inactivity timeout can raise `TransportError` before the job wait deadline.

Downloads use a temporary file in the destination directory and atomic replacement on success. A failed transfer leaves an existing destination intact. Destination parents must exist. Async networking is nonblocking; multipart file reads and bounded local disk writes are synchronous.

## Discovery, credentials, and compatibility

Capabilities/guidance are revalidated on every call with ETags when supplied. Responses preserve additive metadata via Pydantic `model_dump()`. The base URL is read-only: create a new client to target a different server so cached discovery and credentials cannot carry over. `clear_cache()` clears discovery state.

Redirects and response-provided download URLs are never followed. Downloads use asset IDs at the configured deployment. Environment proxy/netrc settings are disabled by default; opt in with `trust_env=True` only when appropriate. API keys are sent as Bearer tokens. No key is required for servers configured without authentication.

See [contract details](docs/contracts.md), [examples](examples), and the [central specification](https://github.com/lambdawalker/design.ai/tree/main/tts).

## Develop and verify

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check dist/*
```

CI tests Python 3.10–3.13 and builds distributions. No workflow publishes to PyPI. Licensing must be chosen by the repository owner before a public package release.
