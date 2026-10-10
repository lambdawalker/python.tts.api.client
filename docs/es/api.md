# Referencia de API pública

Declaraciones generadas; las explicaciones definen los contratos comunes.

Todos los nombres siguientes se exportan desde `tts_api_client`. Los módulos internos
y validadores heredados no son operaciones del SDK. Se aplican las restricciones
`Field(...)`; `default_factory` crea un valor nuevo por solicitud. Las solicitudes
ofrecen `payload()` (diccionario JSON sin None), además de `model_dump()` y
`model_validate()` de Pydantic. Las respuestas conservan campos adicionales.

Los clientes reciben raíz del servidor, `api_key` Bearer opcional, `timeout=30`
positivo, transporte HTTPX opcional y `trust_env=False`. `base_url` es de solo lectura;
`clear_cache()` devuelve None. Los contextos llaman a `close` o `aclose` al salir.
Consulta [conceptos](concepts.md) para propiedad, hilos y cancelación.

Sesiones anónimas: `anonymous_session=True` obtiene un token antes de la primera
operación. `session_token="..."` reutiliza un token guardado; ambas opciones son
incompatibles con `api_key`. Lee `client.session_token` para guardarlo de forma privada.
`create_session()` crea y activa una identidad nueva; `revoke_session()` la revoca.
Cerrar el cliente no revoca la sesión. Un 401 nunca provoca una sustitución automática.
Si falla la primera creación, llama explícitamente a `create_session()` para reintentar;
el servidor pudo aceptar la primera solicitud. No cambies el ciclo de vida de la sesión
mientras otras operaciones del mismo cliente están en curso.

| Métodos | Parámetros, resultado y efecto |
| --- | --- |
| `list_models`, `capabilities`, `guidance` | Consultan perfiles/metadatos. model filtra; guidance exige el ID de función. |
| `list_voices` | Lista voces, opcionalmente por modelo. |
| `register_voice`, `delete_voice` | Registra referencias y devuelve Voice, o elimina por ID y devuelve None. |
| `validate_speech` | Devuelve ValidationResult sin generar; comprueba valid. |
| `generate_speech`, `design_voice`, `convert_voice` | Envían solicitud tipada o campos, nunca ambos; devuelven Job/AsyncJob. idempotency_key se conserva. No hay reintento automático. |
| `job` | Crea un objeto local con id y estado initial opcional; no hace HTTP ni requiere await. |
| `get_job`, `cancel_job` | Consultan estado o solicitan cancelación; devuelven JobStatus. |
| `wait` | Sondea un ID y devuelve éxito o lanza error terminal/de plazo. timeout admite cero; poll_interval debe ser positivo. |
| `events` | Iterador de Event; after es el cursor, intentos no negativos y pausas positivas. Sondeo alternativo configurable. |
| `upload_asset` | Lee ruta local como archivo multipart; MIME opcional sustituye detección por nombre. Devuelve Asset. |
| `download_asset` | Descarga por ID a destino local; devuelve Path y reemplaza solo tras éxito. |
| `Job.get/wait/cancel/events` | Delegan al cliente con el ID guardado. AsyncJob espera operaciones excepto events. |

Errores de red: APIError, TransportError, ProtocolError. La espera también puede
lanzar JobFailedError, JobCancelledError, JobTimeoutError. Errores locales:
ValidationError de Pydantic y OSError. Consulta [problemas](troubleshooting.md).
`text` es entrada hablada; `instructions` son instrucciones separadas; `language`
depende del servidor; `guidance_revision` identifica las reglas; `extensions` contiene
controles nativos y `output` solicita codificación. Las referencias vinculan recurso
y transcripción opcional exacta. El diseño usa `description` y `preview_text`; la
conversión usa audio fuente y voz destino. Los IDs pertenecen al servidor; los
metadatos opcionales pueden faltar. `progress` no se supone porcentual.
`JobStatus.terminal` es booleano. Event.data puede ser JSON o texto. No se registran
callbacks ni procesos en segundo plano. No hay sobrecargas públicas adicionales.

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
        anonymous_session: bool = False,
        session_token: str | None = None,
        timeout: float = 30,
        transport: httpx.BaseTransport | None = None,
        trust_env: bool = False,
    ): ...
    def close(self) -> None: ...
    def create_session(self) -> Session: ...
    def revoke_session(self) -> None: ...
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
        anonymous_session: bool = False,
        session_token: str | None = None,
        timeout: float = 30,
        transport: httpx.AsyncBaseTransport | None = None,
        trust_env: bool = False,
    ): ...
    async def aclose(self) -> None: ...
    async def create_session(self) -> Session: ...
    async def revoke_session(self) -> None: ...
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

## Session

`from tts_api_client import Session`

[Source](../../src/tts_api_client/models.py)

```python
class Session(Response):
    session_id: str
    access_token: str = Field(min_length=1, repr=False, pattern="^[A-Za-z0-9_-]+$")
    token_type: Literal["Bearer"] = "Bearer"
    expires_at: str
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
