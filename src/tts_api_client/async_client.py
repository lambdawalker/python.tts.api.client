"""Asynchronous HTTP client. No operation rewrites text or retries submissions."""

import asyncio
import mimetypes
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from ._common import (
    ClientConfig,
    check_response,
    collection,
    completed,
    decode,
    parse,
    positive,
    request_payload,
    segment,
)
from .errors import JobTimeoutError, ProtocolError, TransportError
from .jobs import AsyncJob
from .models import (
    Asset,
    Capabilities,
    Guidance,
    JobStatus,
    ModelProfile,
    Session,
    SpeechRequest,
    ValidationResult,
    Voice,
    VoiceConversionRequest,
    VoiceDesignRequest,
    VoiceRegistration,
)


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
    ):
        super().__init__(base_url, timeout, api_key, anonymous_session, session_token)
        self._session_lock = asyncio.Lock()
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=trust_env,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self.clear_cache()

    async def _create_session_unlocked(self) -> Session:
        if self._api_key is not None:
            raise ValueError("Cannot create an anonymous session with api_key configured")
        self._session_mode = True
        self._session_attempted = True
        session = parse(Session, decode(await self._send_response("POST", "v1/sessions")))
        return self._activate_session(session)

    async def create_session(self) -> Session:
        """Explicitly create a fresh identity. Does not revoke the previous session."""
        async with self._session_lock:
            return await self._create_session_unlocked()

    async def _ensure_session(self):
        if not self._session_mode or self._session_token is not None:
            return
        async with self._session_lock:
            if self._session_token is not None:
                return
            if self._session_attempted:
                raise ProtocolError("No active session; call create_session() explicitly")
            await self._create_session_unlocked()

    async def revoke_session(self) -> None:
        """Revoke this credential. Further operations require an explicit new session."""
        async with self._session_lock:
            if self._session_token is None:
                raise ValueError("No session token is configured")
            check_response(await self._send_response("DELETE", "v1/sessions/current"))
            self._session_token = None
            self._session_attempted = True
            self._http.headers.pop("Authorization", None)
            self.clear_cache()

    async def _response(self, method: str, path: str, **options) -> httpx.Response:
        await self._ensure_session()
        return await self._send_response(method, path, **options)

    async def _send_response(self, method: str, path: str, **options) -> httpx.Response:
        try:
            return await self._http.request(method, path, **options)
        except httpx.TransportError as exc:
            raise TransportError("HTTP transport failed; a submitted job may still exist") from exc

    async def _json(self, method: str, path: str, **options) -> Any:
        return decode(await self._response(method, path, **options))

    async def _discovery(self, path: str, model: str | None):
        key = (path, model)
        r = await self._response(
            "GET", path, params={"model": model} if model else {}, headers=self._cache_headers(key)
        )
        return self._discovery_response(r, key)

    async def list_models(self) -> list[ModelProfile]:
        return collection(ModelProfile, await self._json("GET", "v1/models"), "models")

    async def capabilities(self, model: str | None = None) -> Capabilities:
        return parse(Capabilities, await self._discovery("v1/capabilities", model))

    async def guidance(self, feature: str, model: str | None = None) -> Guidance:
        return parse(Guidance, await self._discovery(f"v1/guidance/{segment(feature)}", model))

    async def list_voices(self, model: str | None = None) -> list[Voice]:
        data = await self._json("GET", "v1/voices", params={"model": model} if model else {})
        return collection(Voice, data, "voices")

    async def register_voice(self, request: VoiceRegistration | None = None, **fields) -> Voice:
        return parse(
            Voice,
            await self._json(
                "POST", "v1/voices", json=request_payload(VoiceRegistration, request, fields)
            ),
        )

    async def delete_voice(self, voice_id: str) -> None:
        check_response(await self._response("DELETE", f"v1/voices/{segment(voice_id)}"))

    async def validate_speech(
        self, request: SpeechRequest | None = None, **fields
    ) -> ValidationResult:
        return parse(
            ValidationResult,
            await self._json(
                "POST", "v1/speech/validate", json=request_payload(SpeechRequest, request, fields)
            ),
        )

    async def _submit(self, path: str, payload: dict, key: str | None) -> AsyncJob:
        status = parse(
            JobStatus, await self._json("POST", path, json=payload, headers=self._idempotency(key))
        )
        return AsyncJob(self, segment(status.id), status)

    async def generate_speech(
        self, request: SpeechRequest | None = None, *, idempotency_key: str | None = None, **fields
    ) -> AsyncJob:
        return await self._submit(
            "v1/speech", request_payload(SpeechRequest, request, fields), idempotency_key
        )

    async def design_voice(
        self,
        request: VoiceDesignRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> AsyncJob:
        return await self._submit(
            "v1/voice-designs",
            request_payload(VoiceDesignRequest, request, fields),
            idempotency_key,
        )

    async def convert_voice(
        self,
        request: VoiceConversionRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> AsyncJob:
        return await self._submit(
            "v1/voice-conversions",
            request_payload(VoiceConversionRequest, request, fields),
            idempotency_key,
        )

    def job(self, job_id: str) -> AsyncJob:
        return AsyncJob(self, segment(job_id))

    async def get_job(self, job_id: str) -> JobStatus:
        return parse(JobStatus, await self._json("GET", f"v1/jobs/{segment(job_id)}"))

    async def cancel_job(self, job_id: str) -> JobStatus:
        return parse(JobStatus, await self._json("POST", f"v1/jobs/{segment(job_id)}/cancel"))

    async def wait(
        self, job_id: str, *, timeout: float = 600, poll_interval: float = 1
    ) -> JobStatus:
        positive(timeout, "timeout", allow_zero=True)
        positive(poll_interval, "poll_interval")
        path = f"v1/jobs/{segment(job_id)}"
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise JobTimeoutError(f"Timed out waiting for {job_id}; job not cancelled")
            try:
                data = await asyncio.wait_for(
                    self._json("GET", path, timeout=min(self._timeout, remaining)), remaining
                )
                status = parse(JobStatus, data)
            except asyncio.TimeoutError as exc:
                raise JobTimeoutError(f"Timed out waiting for {job_id}; job not cancelled") from exc
            except TransportError as exc:
                if time.monotonic() >= deadline:
                    raise JobTimeoutError(
                        f"Timed out waiting for {job_id}; job not cancelled"
                    ) from exc
                raise
            if time.monotonic() >= deadline:
                raise JobTimeoutError(f"Timed out waiting for {job_id}; job not cancelled")
            if completed(status):
                return status
            await asyncio.sleep(min(poll_interval, max(0, deadline - time.monotonic())))

    async def upload_asset(self, path: str | Path, *, mime_type: str | None = None) -> Asset:
        source = Path(path)
        content_type = (
            mime_type or mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        )
        with source.open("rb") as f:
            return parse(
                Asset,
                await self._json(
                    "POST", "v1/assets", files={"file": (source.name, f, content_type)}
                ),
            )

    async def download_asset(self, asset_id: str, destination: str | Path) -> Path:
        await self._ensure_session()
        path = f"v1/assets/{segment(asset_id)}"
        target = Path(destination)
        temp = None
        try:
            async with self._http.stream("GET", path) as r:
                if not r.is_success:
                    await r.aread()
                    check_response(r)
                with tempfile.NamedTemporaryFile(
                    dir=target.parent, prefix=".tts-", delete=False
                ) as f:
                    temp = Path(f.name)
                    async for chunk in r.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
                os.replace(temp, target)
            return target
        except httpx.TransportError as exc:
            raise TransportError("Asset download interrupted; destination unchanged") from exc
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)

    async def events(
        self,
        job_id: str,
        *,
        after: str | None = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1,
        polling_fallback: bool = True,
        poll_interval: float = 1,
    ):
        """Yield SSE events, then polling snapshots if the stream is unavailable.

        Close the iterator when abandoning it. This never cancels generation.
        Event data is arbitrary JSON or text; poll snapshots use event='status'.
        """
        from ._sse import Decoder, replayed
        from .errors import APIError, ProtocolError
        from .models import Event

        job_id = segment(job_id)
        positive(reconnect_delay, "reconnect_delay", allow_zero=True)
        positive(poll_interval, "poll_interval")
        if not isinstance(reconnect_attempts, int) or reconnect_attempts < 0:
            raise ValueError("reconnect_attempts must be a nonnegative integer")
        await self._ensure_session()
        cursor = after
        last_emitted = after
        failure = None
        for attempt in range(reconnect_attempts + 1):
            headers = {"Accept": "text/event-stream"}
            if cursor:
                headers["Last-Event-ID"] = cursor
            decoder = Decoder(cursor)
            try:
                async with self._http.stream(
                    "GET", f"v1/jobs/{job_id}/events", headers=headers
                ) as r:
                    if not r.is_success:
                        await r.aread()
                        check_response(r)
                    if (
                        r.headers.get("Content-Type", "").split(";")[0].strip()
                        != "text/event-stream"
                    ):
                        raise ProtocolError("Expected text/event-stream")
                    r.encoding = "utf-8"
                    async for line in r.aiter_lines():
                        event = decoder.feed(line)
                        if line == "":
                            cursor = decoder.last_id
                        if event is not None and not replayed(event.id, last_emitted):
                            last_emitted = event.id
                            yield event
                failure = TransportError("Event stream ended before a terminal job was observed")
            except APIError as exc:
                if exc.status_code in {404, 405, 501} or exc.code == "event_history_expired":
                    failure = exc
                    break
                if not exc.retryable or exc.status_code in {401, 403}:
                    raise
                failure = exc
            except ProtocolError as exc:
                failure = exc
                break
            except httpx.TransportError as exc:
                failure = TransportError("Event stream disconnected")
                failure.__cause__ = exc
            status = None
            try:
                status = await self.get_job(job_id)
            except TransportError as exc:
                failure = exc
            except APIError as exc:
                if not exc.retryable or exc.status_code in {401, 403}:
                    raise
                failure = exc
            if status is not None and status.terminal:
                yield Event(event="status", source="poll", data=status.model_dump(mode="json"))
                return
            if attempt < reconnect_attempts:
                await asyncio.sleep(reconnect_delay)
        if not polling_fallback:
            raise failure or TransportError("Event stream unavailable")
        while True:
            status = await self.get_job(job_id)
            yield Event(event="status", source="poll", data=status.model_dump(mode="json"))
            if status.terminal:
                return
            await asyncio.sleep(poll_interval)
