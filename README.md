# TTS API Client

Typed synchronous and asyncio Python clients for the shared local TTS HTTP API.
Discover model capabilities and guidance, generate speech, manage voices, track
persistent jobs, reconnect progress streams, and transfer audio assets.

**Development source:** this targets the proposed shared `/v1` contract. Model
servers still need adapters; legacy Fish/Chatterbox endpoints are not directly
compatible. No live GPU/model integration or PyPI release is claimed.

```bash
uv add "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git@main"
```

Python >=3.10; import `tts_api_client`. Only HTTPX and Pydantic are runtime dependencies.
[Installation facts](IMPORT.md) track confirmed releases when available.

```python
from tts_api_client import TTSClient

with TTSClient("http://localhost:8000") as client:
    print(client.guidance("tts").model_dump())
    job = client.generate_speech(text="Hello!")  # Requires a server default voice.
    print("Save this job ID:", job.id)
    status = job.wait()
    client.download_asset(status.results[0].asset_id, "speech.wav")
```

Callers own model-native input: **no tag stripping, rewriting, or automatic generation
retry**. Client closure and timeouts do not cancel server jobs. MCP belongs to the server.

- [Human documentation — English / Español](https://lambdawalker.github.io/python.tts.api.client/) (deployment requires owner Pages setup)
- [Agent entry point](AI_INTEGRATION_GUIDE.md) and [consumer guides](docs/agents/index.md)
- [Runnable demonstrations](docs/agents/examples.md), including [offline fixture](examples/offline.py)
- [Wire contract](docs/contracts.md) and [system specification](https://github.com/lambdawalker/design.ai/tree/main/tts)
- [Publishing setup and recovery](docs/publishing.md)
- [Documentation authoring and preview](docs/documentation.md)

```bash
uv sync --locked --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
bash scripts/check_artifacts.sh
uv run python scripts/docs.py build
```

Main-branch changes now release automatically from Conventional Commits. The manual
**Release and publish** action accepts an optional exact `version` (X.Y.Z).

The owner must select a license and configure PyPI Trusted Publishing before release.

## Anonymous sessions

For a server launched with `--anonymous-sessions`:

```python
with TTSClient("http://spark:8000", anonymous_session=True) as client:
    models = client.list_models()  # Creates one session automatically.
    token = client.session_token  # Save privately if you need to reconnect later.

with TTSClient("http://spark:8000", session_token=token) as client:
    models = client.list_models()  # Reuses the same identity.
```

`AsyncTTSClient` offers the same options and async `create_session()` / `revoke_session()`.
Closing a client leaves its session alive. Expired/revoked credentials return 401;
the client never silently creates a replacement. New sessions cannot access old jobs.
The server controls expiration (24 hours by default). `api_key` remains available for
configured-token deployments; existing token-free servers need neither option.
