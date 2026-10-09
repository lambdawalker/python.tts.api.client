# Compatibilidad y limitaciones

Se implementa el contrato propuesto `/v1`. Fish `/v1/tts` y las APIs particulares de
Chatterbox requieren adaptadores. Las pruebas usan fixtures y un servidor HTTP local;
no se ha verificado integración con modelos o GPU reales.

Se declara Python >=3.10; CI cubre 3.10–3.13. Es Python puro, con soporte de plataforma
condicionado por HTTPX, Pydantic y Python. Async usa asyncio, no Trio. Las lecturas
multipart y escrituras locales limitadas siguen siendo síncronas en el cliente async.

No hay reproducción incremental, decodificación PCM, ASR, ejecución de modelos, MCP,
reescritura de entradas ni reintentos automáticos. SSE informa progreso, no garantiza
audio incremental. No existe un método público para consultar OpenAPI.

Las solicitudes son estrictas y rechazan campos desconocidos. Las respuestas conservan
campos adicionales. Se admite la versión mayor 1 de la API; los controles nativos son
responsabilidad del servidor. Los IDs en rutas admiten letras, dígitos, guion bajo,
punto y guion; deben empezar por letra, dígito o guion bajo. Los IDs de modelo en
JSON o parámetros de consulta no tienen esa restricción.

Se deshabilitan redirecciones y no se siguen URLs de respuesta. `trust_env=False`
evita configuración ambiental de proxy/netrc salvo activación explícita. No hay
parámetro específico de TLS. El cliente posee y cierra el transporte HTTPX inyectado.

El propietario aún no ha elegido licencia; consulta instalación para verificar disponibilidad en PyPI.
Consulta [migración](migration.md) antes de depender de esta API en producción.
