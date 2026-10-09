# Quickstart

Install using [installation](installation.md). First run the deterministic
[offline example](examples.md) to verify the library without a server.
For real audio, start an independently deployed shared-API server, then run:

```bash
export TTS_BASE_URL=http://localhost:8000
# Set TTS_API_KEY in your environment if required.
uv run python examples/generate.py
```

<!-- LIVE:start -->
```python
"""Run against a server implementing the unified API, after reading guidance."""

import os
from uuid import uuid4

from tts_api_client import TTSClient

with TTSClient(os.environ["TTS_BASE_URL"], api_key=os.getenv("TTS_API_KEY")) as client:
    print(client.capabilities().model_dump())
    print(client.guidance("tts").model_dump())
    print(client.list_voices())
    text = input("Model-appropriate text: ")
    voice_id = input("Voice ID from the list: ")
    request = {"text": text, "voice": {"id": voice_id}}
    if not client.validate_speech(**request).valid:
        raise ValueError("Server validation rejected the request; read guidance")
    job = client.generate_speech(**request, idempotency_key=str(uuid4()))
    print("Job:", job.id)
    result = job.wait()
    print(client.download_asset(result.results[0].asset_id, "speech.wav"))
```
<!-- LIVE:end -->

Expected behavior: capabilities, guidance and voices are printed; you enter text
and a voice ID; the job ID is printed; successful output is saved as `speech.wav`.
Read the printed guidance before entering tags or instructions. The sample blocks
until completion and does not handle all production error cases. Persist the job
ID and idempotency key before waiting when recovery across process restarts matters.
Check `ValidationResult.valid` before submitting: validation may return false
without raising. Generation can still fail after successful validation.

For asyncio:

```python
import asyncio
from tts_api_client import AsyncTTSClient


async def main():
    async with AsyncTTSClient("http://localhost:8000") as client:
        print((await client.guidance("tts")).model_dump())
        job = await client.generate_speech(text="Hello!")
        status = await job.wait(timeout=600)
        await client.download_asset(status.results[0].asset_id, "speech.wav")


asyncio.run(main())
```

This example relies on a server default voice. Select a listed ID or configured
alias if the profile requires one. Network methods are awaited; `client.job(id)`
and `job.events()` construct handles/iterators and are not awaited.
