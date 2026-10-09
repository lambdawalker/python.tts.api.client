# Public API reference

Generated declarations; explanations below define the shared contracts.

All names below are exported by `tts_api_client`. Internal modules and inherited
Pydantic validators are not SDK operations. Field `Field(...)` constraints shown
below are enforced. `default_factory` creates a fresh value for each request.
Request objects expose `payload()` (JSON-compatible dict excluding None), and
Pydantic `model_dump()` / `model_validate()`; response objects preserve extra fields.

Clients accept a deployment root, optional Bearer `api_key`, positive inactivity
`timeout=30`, injected HTTPX transport, and `trust_env=False`. `base_url` is read-only;
`clear_cache()` returns None. Sync context exit calls `close`; async exit calls
`aclose`. See [concepts](concepts.md) for lifetime, thread and cancellation rules.

| Methods | Parameters, result and effect |
| --- | --- |
| `list_models`, `capabilities`, `guidance` | Read profile lists/metadata. Optional model filters select a profile; guidance requires a feature path ID. |
| `list_voices` | Read voices, optionally filtered by model. |
| `register_voice`, `delete_voice` | Create conditioning voice or delete by ID. Registration returns Voice; deletion returns None. |
| `validate_speech` | Returns ValidationResult, does not generate. Check valid explicitly. |
| `generate_speech`, `design_voice`, `convert_voice` | POST a typed request or keyword fields (mutually exclusive); return Job/AsyncJob. Optional idempotency_key is sent unchanged. Never automatically retried. |
| `job` | Local handle with id and optional initial status; no HTTP, even on async client. |
| `get_job`, `cancel_job` | Fetch status or explicitly request cancellation; return JobStatus. |
| `wait` | Poll a job ID; return successful JobStatus or raise terminal/deadline errors. timeout permits zero, poll_interval must be positive. |
| `events` | Iterator/async iterator of Event; after is the last cursor, attempts are nonnegative, delays/intervals positive. Poll fallback is configurable. |
| `upload_asset` | Read a local path as multipart file; optional MIME overrides filename-based detection. Return Asset. |
| `download_asset` | Stream asset ID to local destination; return Path; atomically replace only on success. |
| `Job.get/wait/cancel/events` | Delegate to the owning client with stored ID; same contracts. AsyncJob awaits operations except events. |

Network errors: APIError, TransportError, ProtocolError. Wait also raises
JobFailedError, JobCancelledError, JobTimeoutError. Local request errors are
Pydantic ValidationError; filesystem errors are OSError. See [troubleshooting](troubleshooting.md).
Fields carry their literal server meaning: `text` is spoken input, `instructions`
is separate direction, `language` is server-defined, `guidance_revision` identifies
authored rules, `extensions` carries native controls, and `output` requests encoding.
References associate an uploaded asset and optional exact transcript. Design uses
`description` plus `preview_text`; conversion uses source audio plus a target voice.
Response identifiers are server-local; optional metadata may be absent. `progress`
is server-defined, not assumed to be percent. `JobStatus.terminal` is a boolean.
Event `data` may be decoded JSON or raw text. No callbacks or background workers
are registered. There are no public overload declarations beyond request-or-fields.

## TTSClient

`from tts_api_client import TTSClient`

[Source](../../src/tts_api_client/client.py)

```python
class TTSClient(ClientConfig):
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30,
        transport: httpx.BaseTransport | None = None,
        trust_env: bool = False,
    ): ...
    def close(self) -> None: ...
    def list_models(self) -> list[ModelProfile]: ...
    def capabilities(self, model: str | None = None) -> Capabilities: ...
    def guidance(self, feature: str, model: str | None = None) -> Guidance: ...
    def list_voices(self, model: str | None = None) -> list[Voice]: ...
    def register_voice(self, request: VoiceRegistration | None = None, **fields) -> Voice: ...
    def delete_voice(self, voice_id: str) -> None: ...
    def validate_speech(
        self, request: SpeechRequest | None = None, **fields
    ) -> ValidationResult: ...
    def generate_speech(
        self, request: SpeechRequest | None = None, *, idempotency_key: str | None = None, **fields
    ) -> Job: ...
    def design_voice(
        self,
        request: VoiceDesignRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> Job: ...
    def convert_voice(
        self,
        request: VoiceConversionRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> Job: ...
    def job(self, job_id: str) -> Job: ...
    def get_job(self, job_id: str) -> JobStatus: ...
    def cancel_job(self, job_id: str) -> JobStatus: ...
    def wait(self, job_id: str, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus: ...
    def upload_asset(self, path: str | Path, *, mime_type: str | None = None) -> Asset: ...
    def download_asset(self, asset_id: str, destination: str | Path) -> Path: ...
    def events(
        self,
        job_id: str,
        *,
        after: str | None = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1,
        polling_fallback: bool = True,
        poll_interval: float = 1,
    ): ...
```

## AsyncTTSClient

`from tts_api_client import AsyncTTSClient`

[Source](../../src/tts_api_client/async_client.py)

```python
class AsyncTTSClient(ClientConfig):
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30,
        transport: httpx.AsyncBaseTransport | None = None,
        trust_env: bool = False,
    ): ...
    async def aclose(self) -> None: ...
    async def list_models(self) -> list[ModelProfile]: ...
    async def capabilities(self, model: str | None = None) -> Capabilities: ...
    async def guidance(self, feature: str, model: str | None = None) -> Guidance: ...
    async def list_voices(self, model: str | None = None) -> list[Voice]: ...
    async def register_voice(self, request: VoiceRegistration | None = None, **fields) -> Voice: ...
    async def delete_voice(self, voice_id: str) -> None: ...
    async def validate_speech(
        self, request: SpeechRequest | None = None, **fields
    ) -> ValidationResult: ...
    async def generate_speech(
        self, request: SpeechRequest | None = None, *, idempotency_key: str | None = None, **fields
    ) -> AsyncJob: ...
    async def design_voice(
        self,
        request: VoiceDesignRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> AsyncJob: ...
    async def convert_voice(
        self,
        request: VoiceConversionRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> AsyncJob: ...
    def job(self, job_id: str) -> AsyncJob: ...
    async def get_job(self, job_id: str) -> JobStatus: ...
    async def cancel_job(self, job_id: str) -> JobStatus: ...
    async def wait(
        self, job_id: str, *, timeout: float = 600, poll_interval: float = 1
    ) -> JobStatus: ...
    async def upload_asset(self, path: str | Path, *, mime_type: str | None = None) -> Asset: ...
    async def download_asset(self, asset_id: str, destination: str | Path) -> Path: ...
    async def events(
        self,
        job_id: str,
        *,
        after: str | None = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1,
        polling_fallback: bool = True,
        poll_interval: float = 1,
    ): ...
```

## Job

`from tts_api_client import Job`

[Source](../../src/tts_api_client/jobs.py)

```python
class Job:
    def __init__(self, client: TTSClient, job_id: str, initial: JobStatus | None = None): ...
    def get(self) -> JobStatus: ...
    def wait(self, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus: ...
    def cancel(self) -> JobStatus: ...
    def events(self, **options): ...
```

## AsyncJob

`from tts_api_client import AsyncJob`

[Source](../../src/tts_api_client/jobs.py)

```python
class AsyncJob:
    def __init__(self, client: AsyncTTSClient, job_id: str, initial: JobStatus | None = None): ...
    async def get(self) -> JobStatus: ...
    async def wait(self, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus: ...
    async def cancel(self) -> JobStatus: ...
    def events(self, **options): ...
```

## VoiceSelector

`from tts_api_client import VoiceSelector`

[Source](../../src/tts_api_client/models.py)

```python
class VoiceSelector(Request):
    id: str | None = None
    alias: str | None = None
```

## OutputOptions

`from tts_api_client import OutputOptions`

[Source](../../src/tts_api_client/models.py)

```python
class OutputOptions(Request):
    format: str = "wav"
    sample_rate: int | None = Field(default=None, gt=0)
```

## SpeechRequest

`from tts_api_client import SpeechRequest`

[Source](../../src/tts_api_client/models.py)

```python
class SpeechRequest(Request):
    text: str = Field(min_length=1)
    model: str = "default"
    voice: VoiceSelector | None = None
    language: str | None = None
    instructions: str | None = None
    output: OutputOptions = Field(default_factory=OutputOptions)
    guidance_revision: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)
```

## Reference

`from tts_api_client import Reference`

[Source](../../src/tts_api_client/models.py)

```python
class Reference(Request):
    asset_id: str = Field(min_length=1)
    transcript: str | None = None
```

## VoiceRegistration

`from tts_api_client import VoiceRegistration`

[Source](../../src/tts_api_client/models.py)

```python
class VoiceRegistration(Request):
    references: list[Reference] = Field(min_length=1)
    model: str = "default"
    alias: str | None = None
```

## VoiceDesignRequest

`from tts_api_client import VoiceDesignRequest`

[Source](../../src/tts_api_client/models.py)

```python
class VoiceDesignRequest(Request):
    description: str = Field(min_length=1)
    preview_text: str = Field(min_length=1)
    model: str = "default"
    language: str | None = None
    output: OutputOptions = Field(default_factory=OutputOptions)
    extensions: dict[str, Any] = Field(default_factory=dict)
```

## VoiceConversionRequest

`from tts_api_client import VoiceConversionRequest`

[Source](../../src/tts_api_client/models.py)

```python
class VoiceConversionRequest(Request):
    source_asset_id: str = Field(min_length=1)
    voice: VoiceSelector
    model: str = "default"
    output: OutputOptions = Field(default_factory=OutputOptions)
    extensions: dict[str, Any] = Field(default_factory=dict)
```

## ModelProfile

`from tts_api_client import ModelProfile`

[Source](../../src/tts_api_client/models.py)

```python
class ModelProfile(Response):
    id: str
    availability: str | None = None
```

## Capabilities

`from tts_api_client import Capabilities`

[Source](../../src/tts_api_client/models.py)

```python
class Capabilities(Response):
    api_version: str
    model: str
    capabilities_revision: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    controls: dict[str, Any] = Field(default_factory=dict)
    guidance: dict[str, Any] = Field(default_factory=dict)
```

## Guidance

`from tts_api_client import Guidance`

[Source](../../src/tts_api_client/models.py)

```python
class Guidance(Response):
    feature: str
    model: str
    revision: str
    summary: str = ""
    input_rules: list[str] = Field(default_factory=list)
```

## Voice

`from tts_api_client import Voice`

[Source](../../src/tts_api_client/models.py)

```python
class Voice(Response):
    id: str
    alias: str | None = None
```

## Asset

`from tts_api_client import Asset`

[Source](../../src/tts_api_client/models.py)

```python
class Asset(Response):
    id: str
    mime_type: str | None = None
    sample_rate: int | None = None
    duration: float | None = None
```

## ValidationResult

`from tts_api_client import ValidationResult`

[Source](../../src/tts_api_client/models.py)

```python
class ValidationResult(Response):
    valid: bool
    model: str | None = None
    guidance_revision: str | None = None
```

## ErrorDetail

`from tts_api_client import ErrorDetail`

[Source](../../src/tts_api_client/models.py)

```python
class ErrorDetail(Response):
    code: str
    message: str
    field: str | None = None
    retryable: bool = False
    guidance_url: str | None = None
```

## JobResult

`from tts_api_client import JobResult`

[Source](../../src/tts_api_client/models.py)

```python
class JobResult(Response):
    asset_id: str
```

## JobStatus

`from tts_api_client import JobStatus`

[Source](../../src/tts_api_client/models.py)

```python
class JobStatus(Response):
    id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    operation: str | None = None
    model: str | None = None
    stage: str | None = None
    progress: float | None = None
    cancellation_requested: bool = False
    results: list[JobResult] = Field(default_factory=list)
    error: ErrorDetail | None = None

    @property
    def terminal(self) -> bool: ...
```

## Event

`from tts_api_client import Event`

[Source](../../src/tts_api_client/models.py)

```python
class Event(Response):
    id: str | None = None
    event: str = "message"
    data: Any = None
    source: Literal["sse", "poll"] = "sse"
```

## TTSError

`from tts_api_client import TTSError`

[Source](../../src/tts_api_client/errors.py)

```python
class TTSError(Exception):
```

## ProtocolError

`from tts_api_client import ProtocolError`

[Source](../../src/tts_api_client/errors.py)

```python
class ProtocolError(TTSError):
```

## TransportError

`from tts_api_client import TransportError`

[Source](../../src/tts_api_client/errors.py)

```python
class TransportError(TTSError):
```

## APIError

`from tts_api_client import APIError`

[Source](../../src/tts_api_client/errors.py)

```python
class APIError(TTSError):
    def __init__(self, detail: ErrorDetail, status_code: int, request_id: str | None = None): ...
```

## JobFailedError

`from tts_api_client import JobFailedError`

[Source](../../src/tts_api_client/errors.py)

```python
class JobFailedError(TTSError):
    def __init__(self, job: JobStatus): ...
```

## JobCancelledError

`from tts_api_client import JobCancelledError`

[Source](../../src/tts_api_client/errors.py)

```python
class JobCancelledError(TTSError):
    def __init__(self, job: JobStatus): ...
```

## JobTimeoutError

`from tts_api_client import JobTimeoutError`

[Source](../../src/tts_api_client/errors.py)

```python
class JobTimeoutError(TTSError, TimeoutError):
```
