# Conceptos y propiedad de recursos

La aplicación consulta capacidades e instrucciones, redacta entradas nativas del
modelo, las valida opcionalmente y envía la solicitud. El servidor común elige el
adaptador. MCP pertenece al servidor. Compartir endpoints o familia de modelos no
implica que todos los perfiles ofrezcan las mismas funciones.

Las capacidades y las instrucciones se revalidan en cada consulta con ETag cuando
existe. Los objetos devueltos son copias independientes; no se usan datos obsoletos
sin conexión. `clear_cache()` borra estos metadatos. La URL base es inmutable: crea
otro cliente para cambiar de servidor sin reutilizar credenciales o reglas.

Usa un contexto para cerrar las conexiones. Los trabajos conservan el cliente y lo
necesitan abierto. `close()` / `aclose()` liberan conexiones y caché, no cancelan
trabajos. No se garantiza acceso concurrente a la caché desde varios hilos: usa un
cliente por hilo. Un cliente asíncrono pertenece a un solo bucle de asyncio.

Estados: `queued`, `running`, `succeeded`, `failed`, `cancelled`. La etapa se indica
por separado. `wait()` devuelve éxito o lanza una excepción por fallo, cancelación
o plazo agotado. `events()` informa fallos como datos; no lanza `JobFailedError`
solo por recibir un evento de fallo. Consulta el estado final o llama a `wait()`.

`timeout=30` limita la inactividad HTTP. `wait(timeout=600, poll_interval=1)` define
un plazo de sondeo distinto. La espera asíncrona interrumpe una consulta activa al
vencer el plazo; la bloqueante puede superarlo si siguen llegando bytes lentamente.
Solo `cancel()` o `cancel_job()` solicita cancelación, que puede no ser inmediata.

La aplicación conserva grabaciones, archivos descargados, claves e identificadores.
Los IDs de voces y recursos solo sirven en su servidor. Registrar una voz guarda
referencias de condicionamiento, no entrena un modelo. Cerrar el cliente no elimina
recursos; `delete_voice()` sí solicita una modificación explícita al servidor.
