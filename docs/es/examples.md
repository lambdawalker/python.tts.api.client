# Ejemplos ejecutables

## Demostración sin servidor

Desde el repositorio ejecuta `uv sync --locked --group dev` y
`uv run python examples/offline.py`. No necesita credenciales ni servidor. El fixture
HTTPX comprueba descubrimiento, validación, envío, sondeo y descarga atómica. Resultado:
`Discovery → validation → job → download: OK`. Los bytes no son audio reproducible.
[Código completo](../../examples/offline.py).

## Integración real

Configura `TTS_BASE_URL` y opcionalmente `TTS_API_KEY`; ejecuta
`uv run python examples/generate.py`. Necesita un servidor de API común con una voz.
Lee las instrucciones, introduce texto e ID de voz y obtendrás ID de trabajo y
`speech.wav`. La aplicación debe recuperar fallos de red; el plazo no cancela.
[Código completo](../../examples/generate.py). No se ha probado con un modelo real.

## Pruebas de recuperación y asyncio

`uv run pytest tests/test_streaming.py tests/test_edge_cases.py` comprueba desconexiones,
repeticiones, sondeo, plazos, transferencias y HTTP local. Son pruebas, no un servidor
para producción. Consulta [recetas](recipes.md) y [API](api.md).

No se incluyen capturas: es una biblioteca HTTP sin interfaz visual. Los ejemplos
ejecutables y resultados estructurados describen su comportamiento con más precisión.
