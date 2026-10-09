# Instalación

<!-- INSTALL:start -->
Código de desarrollo; sin publicación confirmada en PyPI.

```bash
uv add "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git@main"
python -m pip install "tts-api-client @ git+https://github.com/lambdawalker/python.tts.api.client.git@main"
```
<!-- INSTALL:end -->

Se requiere Python 3.10 o posterior. La distribución es `tts-api-client` y el módulo
importable es `tts_api_client`. Solo depende en ejecución de HTTPX y Pydantic. No
instala GPU, modelos, herramientas de audio ni MCP. No ofrece una interfaz de comandos.

Usa `TTSClient` para código bloqueante y `AsyncTTSClient` para asyncio. Configura la
raíz del servidor, por ejemplo `http://localhost:8000`, sin `/v1`. Se admite un prefijo
de proxy inverso. `api_key` envía un token Bearer cuando el servidor lo necesita.
Guarda las credenciales en la configuración de la aplicación, no en el código.
