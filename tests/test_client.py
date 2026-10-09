import asyncio
import json

import httpx
import pytest


def api():
    import tts_api_client

    assert hasattr(tts_api_client, "TTSClient"), "client not implemented"
    return tts_api_client


def job(status="queued", **extra):
    return {"id": "j1", "status": status, "operation": "tts", "model": "test", **extra}


@pytest.mark.parametrize("asynchronous", [False, True])
def test_submit_preserves_native_input_and_returns_job(asynchronous):
    sdk = api()
    text = "  [unknown native cue] ¡Hola!\n<|speaker:1|>  "

    def handler(request):
        assert request.url.path == "/v1/speech"
        assert request.headers["Idempotency-Key"] == "stable-key"
        assert request.headers["Authorization"] == "Bearer secret"
        data = json.loads(request.content)
        assert data["text"] == text
        assert data["instructions"] == "  cálido\n"
        return httpx.Response(202, json=job())

    transport = httpx.MockTransport(handler)

    async def run():
        async with sdk.AsyncTTSClient("http://tts", api_key="secret", transport=transport) as c:
            result = await c.generate_speech(
                text=text, instructions="  cálido\n", idempotency_key="stable-key"
            )
            assert result.id == "j1"

    if asynchronous:
        asyncio.run(run())
    else:
        with sdk.TTSClient("http://tts", api_key="secret", transport=transport) as c:
            assert (
                c.generate_speech(
                    text=text, instructions="  cálido\n", idempotency_key="stable-key"
                ).id
                == "j1"
            )


def test_error_fields_and_no_submission_retry():
    sdk = api()
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            422,
            json={
                "error": {
                    "code": "unsupported_parameter",
                    "message": "No instructions",
                    "field": "instructions",
                    "retryable": False,
                    "guidance_url": "/v1/guidance/tts",
                }
            },
        )

    with sdk.TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(sdk.APIError) as info:
            c.generate_speech(text="hello", instructions="warm")
    assert info.value.code == "unsupported_parameter"
    assert info.value.field == "instructions"
    assert info.value.status_code == 422
    assert not info.value.retryable
    assert len(seen) == 1


def test_transport_failure_does_not_retry():
    sdk = api()
    seen = []

    def handler(request):
        seen.append(request)
        raise httpx.ReadError("connection lost", request=request)

    with sdk.TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(sdk.TransportError):
            c.generate_speech(text="hello", idempotency_key="same")
    assert len(seen) == 1


def test_discovery_revalidates_cache_and_preserves_extra():
    sdk = api()
    seen = []

    def handler(request):
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(
                200,
                headers={"ETag": '"r1"'},
                json={"api_version": "1.0", "model": "m1", "features": {}, "future_field": 42},
            )
        assert request.headers["If-None-Match"] == '"r1"'
        return httpx.Response(304)

    with sdk.TTSClient("http://tts/prefix", transport=httpx.MockTransport(handler)) as c:
        first = c.capabilities()
        first.features["poison"] = True
        second = c.capabilities()
        assert second.model == "m1"
        assert second.future_field == 42
        assert "poison" not in second.features
        assert seen[0].url.path == "/prefix/v1/capabilities"
        with pytest.raises(AttributeError):
            c.base_url = "http://elsewhere"


def test_invalid_requests_and_server_version():
    sdk = api()
    with pytest.raises(ValueError):
        sdk.SpeechRequest(text="hello", typo="x")
    with pytest.raises(ValueError):
        sdk.VoiceSelector(id="a", alias="b")
    with sdk.TTSClient(
        "http://tts",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"api_version": "2.0", "model": "m"})
        ),
    ) as c:
        with pytest.raises(sdk.ProtocolError):
            c.capabilities()


@pytest.mark.parametrize("bad", ["..", "../x", "x/y", "https://evil", "x?secret", "%2e%2e"])
def test_invalid_identifiers_never_make_requests(bad):
    sdk = api()

    def handler(request):
        pytest.fail("unexpected request")

    with sdk.TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(ValueError):
            c.get_job(bad)


def test_wait_terminal_failure_timeout_and_no_implicit_cancel():
    sdk = api()
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json=job(
                "failed",
                error={"code": "server_restarted", "message": "interrupted", "retryable": False},
            ),
        )

    with sdk.TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(sdk.JobFailedError) as info:
            c.job("j1").wait(timeout=1, poll_interval=0.01)
        assert info.value.code == "server_restarted"
        with pytest.raises(sdk.JobTimeoutError):
            c.job("j1").wait(timeout=0)
    assert all(r.method == "GET" for r in calls)


def test_download_is_atomic_and_does_not_follow_redirect(tmp_path):
    sdk = api()
    target = tmp_path / "audio.wav"
    target.write_bytes(b"old")
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://evil/audio"})

    with sdk.TTSClient("http://tts", api_key="secret", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(sdk.APIError):
            c.download_asset("a1", target)
    assert target.read_bytes() == b"old"
    assert len(calls) == 1
    assert list(tmp_path.iterdir()) == [target]


def test_endpoints_and_upload(tmp_path):
    sdk = api()
    source = tmp_path / "reference.wav"
    source.write_bytes(b"RIFF-test")
    calls = []

    def handler(r):
        calls.append((r.method, r.url.path))
        path = r.url.path
        if path == "/v1/models":
            return httpx.Response(200, json={"models": [{"id": "m1"}]})
        if path == "/v1/guidance/tts":
            return httpx.Response(
                200, json={"feature": "tts", "model": "m1", "revision": "1", "summary": "native"}
            )
        if path == "/v1/assets":
            assert b'filename="reference.wav"' in r.content
            assert b"RIFF-test" in r.content
            return httpx.Response(201, json={"id": "a1"})
        if path == "/v1/assets/a1":
            return httpx.Response(200, content=b"audio")
        if path == "/v1/voices" and r.method == "GET":
            return httpx.Response(200, json=[{"id": "v1"}])
        if path == "/v1/voices" and r.method == "POST":
            assert json.loads(r.content)["references"][0]["transcript"] == " exact "
            return httpx.Response(201, json={"id": "v1"})
        if r.method == "DELETE":
            return httpx.Response(204)
        if path == "/v1/speech/validate":
            return httpx.Response(200, json={"valid": True, "model": "m1"})
        if path in ("/v1/voice-designs", "/v1/voice-conversions"):
            return httpx.Response(202, json=job())
        if path == "/v1/jobs/j1/cancel":
            return httpx.Response(200, json=job("cancelled"))
        pytest.fail(path)

    with sdk.TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        assert c.list_models()[0].id == "m1"
        assert c.guidance("tts").revision == "1"
        assert c.upload_asset(source).id == "a1"
        assert c.download_asset("a1", tmp_path / "out.wav").read_bytes() == b"audio"
        assert c.list_voices()[0].id == "v1"
        assert c.register_voice(references=[{"asset_id": "a1", "transcript": " exact "}]).id == "v1"
        c.delete_voice("v1")
        assert c.validate_speech(text="hello").valid
        assert c.design_voice(description="warm", preview_text="hi").id == "j1"
        assert c.convert_voice(source_asset_id="a1", voice={"id": "v1"}).id == "j1"
        assert c.cancel_job("j1").status == "cancelled"
    assert len(calls) == 11
