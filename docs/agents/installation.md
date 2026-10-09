# Installation

<!-- INSTALL:start -->
Development source; no confirmed PyPI release.

```bash
uv add "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git@main"
python -m pip install "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git@main"
```
<!-- INSTALL:end -->

Python 3.10 or later. Import as `tts_api_client`; distribution name is
`tts-api-client`. Runtime dependencies are HTTPX and Pydantic only. No GPU, model
weights, audio tools, or MCP runtime are installed. No command-line entry point exists.

Use `TTSClient` for blocking code or `AsyncTTSClient` for asyncio. The deployment
root is required, such as `http://localhost:8000`, without `/v1`. A reverse-proxy
prefix is allowed. Pass `api_key` only if the server requires a Bearer token.
Keep credentials in host configuration, not source code.
