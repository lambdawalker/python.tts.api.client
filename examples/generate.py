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
