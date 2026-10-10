import asyncio
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from tts_api_client import APIError, AsyncTTSClient, ProtocolError, TransportError, TTSClient


def payload(token="session-token"):
    return {
        "session_id": "session_one",
        "access_token": token,
        "token_type": "Bearer",
        "expires_at": "2026-10-11T00:00:00+00:00",
    }


@pytest.mark.parametrize("asynchronous", [False, True])
def test_lazy_session_reuse_revoke_and_explicit_restart(asynchronous):
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/v1/sessions":
            return httpx.Response(201, json=payload())
        assert request.headers["Authorization"] == "Bearer session-token"
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"models": []})

    transport = httpx.MockTransport(handler)

    async def run():
        async with AsyncTTSClient(
            "http://tts", anonymous_session=True, transport=transport
        ) as client:
            await asyncio.gather(*(client.list_models() for _ in range(5)))
            assert client.session_token == "session-token"
            assert calls.count(("POST", "/v1/sessions")) == 1
            await client.revoke_session()
            with pytest.raises(ProtocolError):
                await client.list_models()
            assert "session-token" not in repr(await client.create_session())

    if asynchronous:
        asyncio.run(run())
    else:
        with TTSClient("http://tts", anonymous_session=True, transport=transport) as client:
            with ThreadPoolExecutor(max_workers=5) as pool:
                list(pool.map(lambda _: client.list_models(), range(5)))
            assert client.session_token == "session-token"
            assert calls.count(("POST", "/v1/sessions")) == 1
            client.revoke_session()
            with pytest.raises(ProtocolError):
                client.list_models()
            assert "session-token" not in repr(client.create_session())
    assert calls.count(("POST", "/v1/sessions")) == 2
    assert calls.count(("DELETE", "/v1/sessions/current")) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_resume_expired_token_does_not_create_new_identity(asynchronous):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        assert request.headers["Authorization"] == "Bearer saved-token"
        return httpx.Response(
            401, json={"error": {"code": "authentication_required", "message": "expired"}}
        )

    transport = httpx.MockTransport(handler)

    async def run():
        async with AsyncTTSClient(
            "http://tts", session_token="saved-token", transport=transport
        ) as client:
            with pytest.raises(APIError):
                await client.list_models()
            assert client.session_token == "saved-token"

    if asynchronous:
        asyncio.run(run())
    else:
        with TTSClient("http://tts", session_token="saved-token", transport=transport) as client:
            with pytest.raises(APIError):
                client.list_models()
            assert client.session_token == "saved-token"
    assert calls == ["/v1/models"]


@pytest.mark.parametrize("asynchronous", [False, True])
def test_ambiguous_creation_not_automatically_retried(asynchronous):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        raise httpx.ReadError("lost response")

    transport = httpx.MockTransport(handler)

    async def run():
        async with AsyncTTSClient(
            "http://tts", anonymous_session=True, transport=transport
        ) as client:
            with pytest.raises(TransportError):
                await client.list_models()
            with pytest.raises(ProtocolError):
                await client.list_models()

    if asynchronous:
        asyncio.run(run())
    else:
        with TTSClient("http://tts", anonymous_session=True, transport=transport) as client:
            with pytest.raises(TransportError):
                client.list_models()
            with pytest.raises(ProtocolError):
                client.list_models()
    assert calls == ["/v1/sessions"]


@pytest.mark.parametrize("asynchronous", [False, True])
def test_streaming_download_bootstraps_session(asynchronous, tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/v1/sessions":
            return httpx.Response(201, json=payload())
        assert request.headers["Authorization"] == "Bearer session-token"
        return httpx.Response(200, content=b"audio")

    transport = httpx.MockTransport(handler)

    async def run():
        async with AsyncTTSClient(
            "http://tts", anonymous_session=True, transport=transport
        ) as client:
            await client.download_asset("a1", tmp_path / "audio.wav")

    if asynchronous:
        asyncio.run(run())
    else:
        with TTSClient("http://tts", anonymous_session=True, transport=transport) as client:
            client.download_asset("a1", tmp_path / "audio.wav")
    assert calls == ["/v1/sessions", "/v1/assets/a1"]
    assert (tmp_path / "audio.wav").read_bytes() == b"audio"


@pytest.mark.parametrize("cls", [TTSClient, AsyncTTSClient])
def test_conflicting_credentials_rejected(cls):
    with pytest.raises(ValueError):
        cls("http://tts", api_key="a", anonymous_session=True)
    with pytest.raises(ValueError):
        cls("http://tts", api_key="a", session_token="b")
    with pytest.raises(ValueError):
        cls("http://tts", session_token="")


def test_concurrent_operation_waits_until_auth_header_is_installed(monkeypatch):
    import threading

    installing, release, sent = threading.Event(), threading.Event(), threading.Event()
    original = httpx.Headers.__setitem__

    def pause(headers, key, value):
        if key == "Authorization" and value == "Bearer session-token":
            installing.set()
            assert release.wait(3)
        return original(headers, key, value)

    monkeypatch.setattr(httpx.Headers, "__setitem__", pause)

    def handler(request):
        if request.url.path == "/v1/sessions":
            return httpx.Response(201, json=payload())
        sent.set()
        assert request.headers.get("Authorization") == "Bearer session-token"
        return httpx.Response(200, json={"models": []})

    with TTSClient(
        "http://tts", anonymous_session=True, transport=httpx.MockTransport(handler)
    ) as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(client.list_models)
            try:
                assert installing.wait(2)
                second = pool.submit(client.list_models)
                assert not sent.wait(0.1)
            finally:
                release.set()
            assert first.result() == second.result() == []
