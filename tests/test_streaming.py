import asyncio

import httpx
import pytest

from tts_api_client import AsyncTTSClient, TransportError, TTSClient


class BrokenSync(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial"
        raise httpx.ReadError("disconnect")


class BrokenAsync(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b"partial"
        raise httpx.ReadError("disconnect")


@pytest.mark.parametrize("async_mode", [False, True])
def test_interrupted_download_preserves_destination(tmp_path, async_mode):
    dest = tmp_path / "existing.wav"
    dest.write_bytes(b"original")

    def handler(r):
        return httpx.Response(200, stream=BrokenAsync() if async_mode else BrokenSync())

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            with pytest.raises(TransportError):
                await c.download_asset("a1", dest)

    if async_mode:
        asyncio.run(run())
    else:
        with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            with pytest.raises(TransportError):
                c.download_asset("a1", dest)
    assert dest.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [dest]


@pytest.mark.parametrize("async_mode", [False, True])
def test_sse_reconnects_deduplicates_and_discards_incomplete_frame(async_mode):
    stream_calls = []
    status_calls = []

    def handler(r):
        if r.url.path.endswith("/events"):
            stream_calls.append(r)
            if len(stream_calls) == 1:
                assert "Last-Event-ID" not in r.headers
                content = (
                    "\ufeff: heartbeat\n\nid: 1\nevent: progress\n"
                    'data: {"stage":\ndata: "generating"}\n\nid: 2\ndata: unfinished'
                )
            else:
                assert r.headers["Last-Event-ID"] == "1"
                content = (
                    "id: 1\ndata: duplicate\n\nid: 2\nevent: completed\n"
                    'data: {"status":"succeeded"}\n\n'
                )
            return httpx.Response(
                200, headers={"Content-Type": "text/event-stream"}, content=content.encode()
            )
        status_calls.append(r)
        return httpx.Response(
            200, json={"id": "j1", "status": "succeeded" if len(stream_calls) == 2 else "running"}
        )

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            assert hasattr(c, "events"), "SSE not implemented"
            return [e async for e in c.events("j1", reconnect_delay=0, poll_interval=0.001)]

    if async_mode:
        events = asyncio.run(run())
    else:
        with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            assert hasattr(c, "events"), "SSE not implemented"
            events = list(c.events("j1", reconnect_delay=0, poll_interval=0.001))
    native = [e for e in events if e.source == "sse"]
    assert [e.id for e in native] == ["1", "2"]
    assert native[0].data == {"stage": "generating"}
    assert len(stream_calls) == 2


@pytest.mark.parametrize("async_mode", [False, True])
def test_expired_sse_history_falls_back_to_polling(async_mode):
    statuses = iter(["running", "succeeded"])

    def handler(r):
        if r.url.path.endswith("/events"):
            return httpx.Response(
                409, json={"error": {"code": "event_history_expired", "message": "expired"}}
            )
        return httpx.Response(200, json={"id": "j1", "status": next(statuses)})

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            assert hasattr(c, "events"), "SSE not implemented"
            return [e async for e in c.job("j1").events(poll_interval=0.001)]

    if async_mode:
        events = asyncio.run(run())
    else:
        with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            assert hasattr(c, "events"), "SSE not implemented"
            events = list(c.job("j1").events(poll_interval=0.001))
    assert [e.data["status"] for e in events] == ["running", "succeeded"]
    assert all(e.source == "poll" and e.id is None for e in events)


def test_sse_authentication_error_is_not_hidden():
    from tts_api_client import APIError

    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(
            401, json={"error": {"code": "authentication_required", "message": "no"}}
        )

    with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        assert hasattr(c, "events"), "SSE not implemented"
        with pytest.raises(APIError) as err:
            list(c.events("j1"))
        assert err.value.code == "authentication_required"
    assert len(calls) == 1


def test_async_operation_parity(tmp_path):
    seen = []
    path = tmp_path / "input.wav"
    path.write_bytes(b"RIFF")

    def handler(r):
        seen.append(r.url.path)
        if r.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "m"}]})
        if r.url.path == "/v1/capabilities":
            return httpx.Response(200, json={"api_version": "1.0", "model": "m"})
        if r.url.path == "/v1/guidance/tts":
            return httpx.Response(200, json={"feature": "tts", "model": "m", "revision": "1"})
        if r.url.path == "/v1/voices":
            return httpx.Response(200, json=[{"id": "v"}] if r.method == "GET" else {"id": "v"})
        if r.method == "DELETE":
            return httpx.Response(204)
        if r.url.path == "/v1/assets":
            return httpx.Response(201, json={"id": "a"})
        if r.url.path == "/v1/assets/a":
            return httpx.Response(200, content=b"audio")
        if r.url.path == "/v1/speech/validate":
            return httpx.Response(200, json={"valid": True})
        if r.url.path == "/v1/jobs/j1/cancel":
            return httpx.Response(200, json={"id": "j1", "status": "cancelled"})
        return httpx.Response(
            200, json={"id": "j1", "status": "succeeded", "results": [{"asset_id": "a"}]}
        )

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            assert (await c.list_models())[0].id == "m"
            assert (await c.capabilities()).model == "m"
            assert (await c.guidance("tts")).revision == "1"
            assert (await c.list_voices())[0].id == "v"
            assert (await c.register_voice(references=[{"asset_id": "a"}])).id == "v"
            await c.delete_voice("v")
            assert (await c.upload_asset(path)).id == "a"
            assert (await c.download_asset("a", tmp_path / "out.wav")).read_bytes() == b"audio"
            assert (await c.validate_speech(text="hello")).valid
            handle = await c.generate_speech(text="[laugh] Hello")
            assert (await handle.wait()).results[0].asset_id == "a"
            assert (await handle.get()).status == "succeeded"
            assert (await handle.cancel()).status == "cancelled"
            assert (await c.design_voice(description="warm", preview_text="hello")).id == "j1"
            assert (await c.convert_voice(source_asset_id="a", voice={"id": "v"})).id == "j1"

    asyncio.run(run())
    assert len(seen) == 15


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("outage", ["connection", "service_unavailable"])
def test_sse_reconnect_survives_outage_during_status_probe(async_mode, outage):
    requests = []

    def handler(r):
        requests.append(r.url.path)
        if len(requests) <= 2:
            if outage == "connection":
                raise httpx.ConnectError("brief outage", request=r)
            return httpx.Response(
                503,
                json={
                    "error": {
                        "code": "model_unavailable",
                        "message": "brief outage",
                        "retryable": True,
                    }
                },
            )
        if r.url.path.endswith("/events"):
            return httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                content=b'id: 1\ndata: {"status":"succeeded"}\n\n',
            )
        return httpx.Response(200, json={"id": "j1", "status": "succeeded"})

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            return [e async for e in c.events("j1", reconnect_delay=0)]

    if async_mode:
        events = asyncio.run(run())
    else:
        with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            events = list(c.events("j1", reconnect_delay=0))
    assert requests[:3] == ["/v1/jobs/j1/events", "/v1/jobs/j1", "/v1/jobs/j1/events"]
    assert events[-1].data["status"] == "succeeded"
