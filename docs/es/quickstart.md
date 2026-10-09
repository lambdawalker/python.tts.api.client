# Inicio rápido

Sigue [instalación](installation.md). Prueba primero el [ejemplo sin servidor](examples.md).
Para producir audio real, inicia un servidor de la API común y configura el entorno:

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

El programa muestra capacidades, instrucciones y voces; pide texto e identificador
de voz; muestra el identificador del trabajo y guarda `speech.wav`. Lee las
instrucciones antes de escribir etiquetas. El ejemplo bloquea hasta terminar.
En producción conserva la clave de idempotencia y el identificador para recuperarte
tras reiniciar. Comprueba `ValidationResult.valid`: puede ser falso sin excepción.
La generación puede fallar aunque la validación haya sido correcta.

Con asyncio:

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

Este ejemplo requiere una voz predeterminada en el servidor; selecciona un ID o alias
si el perfil lo exige. Espera las operaciones de red con `await`, pero no
`client.job(id)` ni `job.events()`, que crean objetos o iteradores localmente.
