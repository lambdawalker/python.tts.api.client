import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from tts_api_client import (
    AsyncTTSClient,
    JobCancelledError,
    JobTimeoutError,
    ProtocolError,
    TTSClient,
)


def test_wait_timeout_classification():
    def handler(r):
        time.sleep(0.015)
        raise httpx.ReadTimeout("waiting", request=r)

    with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(JobTimeoutError):
            c.job("j1").wait(timeout=0.01)


def test_async_wait_deadline_interrupts_slow_response():
    async def handler(r):
        await asyncio.sleep(1)
        return httpx.Response(200, json={"id": "j1", "status": "running"})

    async def run():
        async with AsyncTTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
            start = time.monotonic()
            with pytest.raises(JobTimeoutError):
                await c.job("j1").wait(timeout=0.01)
            assert time.monotonic() - start < 0.5

    asyncio.run(run())


def test_malformed_success_is_protocol_error():
    with TTSClient(
        "http://tts", transport=httpx.MockTransport(lambda r: httpx.Response(200, text="oops"))
    ) as c:
        with pytest.raises(ProtocolError):
            c.list_models()


def test_cancelled_wait_raises_without_cancel_post():
    seen = []

    def handler(r):
        seen.append(r.method)
        return httpx.Response(200, json={"id": "j1", "status": "cancelled"})

    with TTSClient("http://tts", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(JobCancelledError):
            c.job("j1").wait()
    assert seen == ["GET"]


@pytest.mark.parametrize("async_mode", [False, True])
def test_real_http_roundtrip(tmp_path, async_mode):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data, code=200):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path == "/v1/assets":
                assert b"RIFF-test" in body
                self.reply({"id": "a1"}, 201)
            else:
                received.append(json.loads(body))
                self.reply({"id": "j1", "status": "queued"}, 202)

        def do_GET(self):
            if self.path == "/v1/assets/a1":
                self.send_response(200)
                self.send_header("Content-Length", "5")
                self.end_headers()
                self.wfile.write(b"audio")
            else:
                self.reply({"id": "j1", "status": "succeeded", "results": [{"asset_id": "a1"}]})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    source = tmp_path / "ref.wav"
    source.write_bytes(b"RIFF-test")
    url = f"http://127.0.0.1:{server.server_port}"

    async def run():
        async with AsyncTTSClient(url) as c:
            assert (await c.upload_asset(source)).id == "a1"
            job = await c.generate_speech(text=" [native] ¡Hola! ")
            status = await job.wait()
            await c.download_asset(status.results[0].asset_id, tmp_path / "out.wav")

    try:
        if async_mode:
            asyncio.run(run())
        else:
            with TTSClient(url) as c:
                assert c.upload_asset(source).id == "a1"
                status = c.generate_speech(text=" [native] ¡Hola! ").wait()
                c.download_asset(status.results[0].asset_id, tmp_path / "out.wav")
        assert received[0]["text"] == " [native] ¡Hola! "
        assert (tmp_path / "out.wav").read_bytes() == b"audio"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
