"""Shared, transport-independent contract and URL handling."""

import copy
import math
import re
from typing import Any, TypeVar

import httpx
from pydantic import ValidationError

from .errors import APIError, JobCancelledError, JobFailedError, ProtocolError
from .models import ErrorDetail, JobStatus, Request, Response

R = TypeVar("R", bound=Response)
Q = TypeVar("Q", bound=Request)


def segment(value: str) -> str:
    # Opaque server identifiers, not paths/URLs. Encode nothing that could change routing.
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", value):
        raise ValueError(
            "Identifier must contain only letters, digits, underscores, dots or hyphens"
        )
    return value


def request_payload(cls: type[Q], request: Q | None, fields: dict[str, Any]) -> dict[str, Any]:
    if request is not None:
        if fields:
            raise ValueError("Supply a request object OR keyword fields, not both")
        if not isinstance(request, cls):
            raise TypeError(f"Expected {cls.__name__}")
        return request.payload()
    return cls.model_validate(fields).payload()


def parse(cls: type[R], data: Any) -> R:
    try:
        return cls.model_validate(data)
    except ValidationError as exc:
        raise ProtocolError(f"Invalid {cls.__name__} response") from exc


def collection(cls: type[R], data: Any, name: str) -> list[R]:
    if isinstance(data, dict):
        data = data.get(name, data.get("data"))
    if not isinstance(data, list):
        raise ProtocolError(f"Expected a {name} array")
    return [parse(cls, item) for item in data]


def decode(response: httpx.Response) -> Any:
    check_response(response)
    try:
        data = response.json()
    except ValueError as exc:
        raise ProtocolError("Expected a JSON response") from exc
    if isinstance(data, dict) and "api_version" in data:
        version = str(data["api_version"])
        if not re.fullmatch(r"1(?:\.\d+)*", version):
            raise ProtocolError(f"Unsupported API version: {version}")
    return data


def check_response(response: httpx.Response) -> None:
    if 200 <= response.status_code < 300:
        return
    try:
        detail = ErrorDetail.model_validate(response.json()["error"])
    except (ValueError, TypeError, KeyError):
        detail = ErrorDetail(
            code="http_error",
            message=f"HTTP {response.status_code}",
            retryable=response.status_code in {429, 502, 503, 504},
        )
    raise APIError(detail, response.status_code, response.headers.get("X-Request-ID"))


def completed(job: JobStatus) -> JobStatus | None:
    if job.status == "failed":
        raise JobFailedError(job)
    if job.status == "cancelled":
        raise JobCancelledError(job)
    return job if job.status == "succeeded" else None


def positive(value: float, name: str, allow_zero: bool = False) -> None:
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}")


class ClientConfig:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        api_key: str | None,
        anonymous_session: bool = False,
        session_token: str | None = None,
    ):
        if api_key is not None and (anonymous_session or session_token is not None):
            raise ValueError("api_key cannot be combined with anonymous sessions")
        if session_token is not None and not re.fullmatch(r"[A-Za-z0-9_-]+", session_token):
            raise ValueError("session_token must be a nonempty opaque token")
        self._api_key = api_key
        self._session_mode = anonymous_session or session_token is not None
        self._session_token = session_token
        self._session_attempted = session_token is not None
        url = httpx.URL(base_url)
        if url.scheme not in {"http", "https"} or not url.host:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if url.username or url.password or url.query or url.fragment:
            raise ValueError("base_url cannot contain credentials, query or fragment")
        if url.path.rstrip("/").endswith("/v1"):
            raise ValueError("base_url is the deployment root, without /v1")
        positive(timeout, "timeout")
        self._base_url = str(url).rstrip("/") + "/"
        self._timeout = timeout
        self._headers = {"User-Agent": "tts-api-client/0.1.0"}
        credential = session_token if session_token is not None else api_key
        if credential is not None:
            self._headers["Authorization"] = f"Bearer {credential}"
        self._cache: dict[tuple[str, str | None], tuple[str, Any]] = {}

    @property
    def session_token(self) -> str | None:
        """Save privately to resume this identity; close does not revoke it."""
        return self._session_token

    def _activate_session(self, session):
        self._session_mode = True
        self._http.headers["Authorization"] = f"Bearer {session.access_token}"
        self.clear_cache()
        # Publish readiness only after credentials are installed for concurrent callers.
        self._session_token = session.access_token
        return session

    @property
    def base_url(self) -> str:
        return self._base_url

    def clear_cache(self) -> None:
        self._cache.clear()

    def _cache_headers(self, key):
        entry = self._cache.get(key)
        return {"If-None-Match": entry[0]} if entry else {}

    def _discovery_response(self, response, key):
        if response.status_code == 304:
            if key not in self._cache:
                raise ProtocolError("Received 304 without a cached discovery document")
            return copy.deepcopy(self._cache[key][1])
        data = decode(response)
        etag = response.headers.get("ETag")
        if etag:
            self._cache[key] = (etag, copy.deepcopy(data))
        else:
            self._cache.pop(key, None)
        return data

    @staticmethod
    def _idempotency(key: str | None):
        if key is None:
            return {}
        if not key or any(ord(ch) < 33 or ord(ch) > 126 for ch in key):
            raise ValueError("idempotency_key must be nonempty printable ASCII without spaces")
        return {"Idempotency-Key": key}
