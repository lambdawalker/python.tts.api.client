"""Blocking HTTP client. No operation rewrites text or retries submissions."""

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
from .errors import JobTimeoutError, TransportError
from .jobs import Job
from .models import (
    Asset,
    Capabilities,
    Guidance,
    JobStatus,
    ModelProfile,
    SpeechRequest,
    ValidationResult,
    Voice,
    VoiceConversionRequest,
    VoiceDesignRequest,
    VoiceRegistration,
)


class TTSClient(ClientConfig):
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30,
        transport: httpx.BaseTransport | None = None,
        trust_env: bool = False,
    ):
        super().__init__(base_url, timeout, api_key)
        self._http = httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=trust_env,
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        self._http.close()
        self.clear_cache()

    def _response(self, method: str, path: str, **options) -> httpx.Response:
        try:
            return self._http.request(method, path, **options)
        except httpx.TransportError as exc:
            raise TransportError("HTTP transport failed; a submitted job may still exist") from exc

    def _json(self, method: str, path: str, **options) -> Any:
        return decode(self._response(method, path, **options))

    def _discovery(self, path: str, model: str | None):
        key = (path, model)
        r = self._response(
            "GET", path, params={"model": model} if model else {}, headers=self._cache_headers(key)
        )
        return self._discovery_response(r, key)

    def list_models(self) -> list[ModelProfile]:
        return collection(ModelProfile, self._json("GET", "v1/models"), "models")

    def capabilities(self, model: str | None = None) -> Capabilities:
        return parse(Capabilities, self._discovery("v1/capabilities", model))

    def guidance(self, feature: str, model: str | None = None) -> Guidance:
        return parse(Guidance, self._discovery(f"v1/guidance/{segment(feature)}", model))

    def list_voices(self, model: str | None = None) -> list[Voice]:
        data = self._json("GET", "v1/voices", params={"model": model} if model else {})
        return collection(Voice, data, "voices")

    def register_voice(self, request: VoiceRegistration | None = None, **fields) -> Voice:
        return parse(
            Voice,
            self._json(
                "POST", "v1/voices", json=request_payload(VoiceRegistration, request, fields)
            ),
        )

    def delete_voice(self, voice_id: str) -> None:
        check_response(self._response("DELETE", f"v1/voices/{segment(voice_id)}"))

    def validate_speech(self, request: SpeechRequest | None = None, **fields) -> ValidationResult:
        return parse(
            ValidationResult,
            self._json(
                "POST", "v1/speech/validate", json=request_payload(SpeechRequest, request, fields)
            ),
        )

    def _submit(self, path: str, payload: dict, key: str | None) -> Job:
        status = parse(
            JobStatus, self._json("POST", path, json=payload, headers=self._idempotency(key))
        )
        return Job(self, segment(status.id), status)

    def generate_speech(
        self, request: SpeechRequest | None = None, *, idempotency_key: str | None = None, **fields
    ) -> Job:
        return self._submit(
            "v1/speech", request_payload(SpeechRequest, request, fields), idempotency_key
        )

    def design_voice(
        self,
        request: VoiceDesignRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> Job:
        return self._submit(
            "v1/voice-designs",
            request_payload(VoiceDesignRequest, request, fields),
            idempotency_key,
        )

    def convert_voice(
        self,
        request: VoiceConversionRequest | None = None,
        *,
        idempotency_key: str | None = None,
        **fields,
    ) -> Job:
        return self._submit(
            "v1/voice-conversions",
            request_payload(VoiceConversionRequest, request, fields),
            idempotency_key,
        )

    def job(self, job_id: str) -> Job:
        return Job(self, segment(job_id))

    def get_job(self, job_id: str) -> JobStatus:
        return parse(JobStatus, self._json("GET", f"v1/jobs/{segment(job_id)}"))

    def cancel_job(self, job_id: str) -> JobStatus:
        return parse(JobStatus, self._json("POST", f"v1/jobs/{segment(job_id)}/cancel"))

    def wait(self, job_id: str, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus:
        positive(timeout, "timeout", allow_zero=True)
        positive(poll_interval, "poll_interval")
        path = f"v1/jobs/{segment(job_id)}"
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise JobTimeoutError(f"Timed out waiting for {job_id}; job not cancelled")
            try:
                status = parse(
                    JobStatus, self._json("GET", path, timeout=min(self._timeout, remaining))
                )
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
            time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))

    def upload_asset(self, path: str | Path, *, mime_type: str | None = None) -> Asset:
        source = Path(path)
        content_type = (
            mime_type or mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        )
        with source.open("rb") as f:
            return parse(
                Asset,
                self._json("POST", "v1/assets", files={"file": (source.name, f, content_type)}),
            )

    def download_asset(self, asset_id: str, destination: str | Path) -> Path:
        path = f"v1/assets/{segment(asset_id)}"
        target = Path(destination)
        temp = None
        try:
            with self._http.stream("GET", path) as r:
                if not r.is_success:
                    r.read()
                    check_response(r)
                with tempfile.NamedTemporaryFile(
                    dir=target.parent, prefix=".tts-", delete=False
                ) as f:
                    temp = Path(f.name)
                    for chunk in r.iter_bytes():
                        f.write(chunk)
                os.replace(temp, target)
            return target
        except httpx.TransportError as exc:
            raise TransportError("Asset download interrupted; destination unchanged") from exc
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)

    def events(
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
        cursor = after
        last_emitted = after
        failure = None
        for attempt in range(reconnect_attempts + 1):
            headers = {"Accept": "text/event-stream"}
            if cursor:
                headers["Last-Event-ID"] = cursor
            decoder = Decoder(cursor)
            try:
                with self._http.stream("GET", f"v1/jobs/{job_id}/events", headers=headers) as r:
                    if not r.is_success:
                        r.read()
                        check_response(r)
                    if (
                        r.headers.get("Content-Type", "").split(";")[0].strip()
                        != "text/event-stream"
                    ):
                        raise ProtocolError("Expected text/event-stream")
                    r.encoding = "utf-8"
                    for line in r.iter_lines():
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
                status = self.get_job(job_id)
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
                time.sleep(reconnect_delay)
        if not polling_fallback:
            raise failure or TransportError("Event stream unavailable")
        while True:
            status = self.get_job(job_id)
            yield Event(event="status", source="poll", data=status.model_dump(mode="json"))
            if status.terminal:
                return
            time.sleep(poll_interval)
