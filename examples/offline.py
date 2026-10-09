"""Deterministic HTTP fixture demo; does not generate real audio."""

import tempfile
from pathlib import Path

import httpx

from tts_api_client import TTSClient


def respond(request):
    path = request.url.path
    if path == "/v1/capabilities":
        return httpx.Response(
            200,
            json={
                "api_version": "1.0",
                "model": "fixture",
                "features": {"tts": {"supported": True}},
            },
        )
    if path == "/v1/guidance/tts":
        return httpx.Response(
            200,
            json={
                "feature": "tts",
                "model": "fixture",
                "revision": "fixture-1",
                "summary": "Plain text fixture.",
            },
        )
    if path == "/v1/speech/validate":
        return httpx.Response(200, json={"valid": True})
    if path == "/v1/speech":
        return httpx.Response(202, json={"id": "demo-job", "status": "queued"})
    if path == "/v1/jobs/demo-job":
        return httpx.Response(
            200,
            json={"id": "demo-job", "status": "succeeded", "results": [{"asset_id": "demo-audio"}]},
        )
    if path == "/v1/assets/demo-audio":
        return httpx.Response(200, content=b"fixture bytes, not playable audio")
    return httpx.Response(404)


def main():
    with tempfile.TemporaryDirectory() as directory:
        with TTSClient("https://fixture.invalid", transport=httpx.MockTransport(respond)) as client:
            print(client.capabilities().model_dump())
            print(client.guidance("tts").summary)
            request = {"text": "Hello fixture."}
            assert client.validate_speech(**request).valid
            job = client.generate_speech(**request, idempotency_key="fixture-001")
            status = job.wait()
            path = client.download_asset(status.results[0].asset_id, Path(directory) / "output.bin")
            assert path.read_bytes() == b"fixture bytes, not playable audio"
            print("Discovery → validation → job → download: OK")


if __name__ == "__main__":
    main()
