# Client contract and server integration expectations

Baseline: [design.ai/tts at 0678d14](https://github.com/lambdawalker/design.ai/tree/0678d14f47f42d9de1ec8dd379cd810f35b32e73/tts).

## Methods

| Method | HTTP route | Return |
| --- | --- | --- |
| list_models() | GET /v1/models | list[ModelProfile] |
| capabilities(model=None) | GET /v1/capabilities | Capabilities |
| guidance(feature, model=None) | GET /v1/guidance/{feature} | Guidance |
| list_voices(model=None) | GET /v1/voices | list[Voice] |
| register_voice(request=None, **fields) | POST /v1/voices | Voice |
| delete_voice(id) | DELETE /v1/voices/{id} | None |
| upload_asset(path, mime_type=None) | POST /v1/assets | Asset |
| download_asset(id, destination) | GET /v1/assets/{id} | Path |
| validate_speech(request=None, **fields) | POST /v1/speech/validate | ValidationResult |
| generate_speech(request=None, idempotency_key=None, **fields) | POST /v1/speech | Job / AsyncJob |
| design_voice(request=None, idempotency_key=None, **fields) | POST /v1/voice-designs | Job / AsyncJob |
| convert_voice(request=None, idempotency_key=None, **fields) | POST /v1/voice-conversions | Job / AsyncJob |
| get_job(id) | GET /v1/jobs/{id} | JobStatus |
| cancel_job(id) | POST /v1/jobs/{id}/cancel | JobStatus |
| events(id, ...) | GET /v1/jobs/{id}/events | Iterator / AsyncIterator[Event] |
| wait(id, timeout=600, poll_interval=1) | Poll GET /v1/jobs/{id} | JobStatus |
| job(id) | No request | Job / AsyncJob |

Callers pass either a typed request object or keyword fields, never both. Request models forbid unknown fields and use strict types. `None` fields are omitted. Defaults are model=`default`, output.format=`wav`, extensions={}. Voices require exactly one nonempty id/alias. Text, instructions, and transcripts are not stripped or normalized.

## Draft contract choices

The central design is prose, not a finalized OpenAPI schema. The SDK makes the following explicit interoperability choices:

- Collections accept bare arrays, `{models: [...]}` / `{voices: [...]}`, or `{data: [...]}`. Items require `id`. Pagination is not defined and is not implemented.
- Capability responses require string `api_version` and `model`. Only major version 1 is accepted when `api_version` is returned. Call `capabilities()` when connecting; the SDK does not perform a hidden discovery request before every operation.
- Guidance requires `feature`, `model`, and string `revision`. Arbitrary added fields survive as response metadata.
- Multipart uploads use field `file`; response requires `id`. Paths are local caller paths only, never server paths.
- Output options accept `format` and positive integer `sample_rate`; server capabilities decide whether values are supported.
- Jobs require `id` and status in queued/running/succeeded/failed/cancelled. Each result requires `asset_id`. `error` uses code/message plus optional field, retryable, and guidance_url.
- Server IDs used in URL paths must match `[A-Za-z0-9_][A-Za-z0-9_.-]*`. Native model selection in JSON/query fields is unrestricted, allowing Hugging Face model names with slashes.
- SSE data may be JSON or text. Numeric event IDs are treated as monotonic, with replay IDs at or below the delivered cursor suppressed. Opaque IDs support immediate duplicate suppression. Incomplete frames at disconnect are not dispatched. Server-provided `retry` hints are ignored in favor of the configured reconnect delay.
- Servers should close streams after terminal events; the SDK confirms termination via a status lookup after EOF/disconnect. Poll fallback applies to unavailable endpoints (404/405/501), expired event history, malformed content type, or exhausted network reconnection. Authentication errors remain visible.
- Polling snapshots are client-generated notifications, not replayable server events. They have no SSE cursor.
- ETag revalidation is scoped to one immutable client base URL and the requested model selector. Servers must change ETags when a `default` selector resolves differently. Without an ETag the SDK refetches every time. No offline stale-cache fallback occurs.

## Boundaries

No generation retry, automatic cancellation, tag stripping, instruction repair, ASR, embedding conversion, MCP hosting, duplex audio, legacy endpoint translation, or model installation. No cross-host result URL downloads. Asset/job/voice state belongs to the server.

## Validation evidence

The suite covers synchronous/asynchronous operations, HTTP errors and malformed responses, input preservation, discovery revalidation, job outcomes, retry safety, SSE reconnection/replay/fallback, multipart uploads, atomic interrupted downloads, and real loopback HTTP round trips. Tests do not prove GPU inference or live compatibility with a deployed unified server.
