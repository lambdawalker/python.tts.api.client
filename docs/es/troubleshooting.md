# Problemas y excepciones

| Síntoma | Significado y solución |
| --- | --- |
| Pydantic `ValidationError` | Corrige estructura o tipos locales; no valida etiquetas nativas. |
| `APIError` | Rechazo del servidor. Examina `status_code`, `code`, `field`, `retryable`, `guidance_url`, `request_id`, `detail`; lee las instrucciones sin reparar entradas automáticamente. |
| `TransportError` | Fallo de red; el envío puede haber funcionado. Conserva clave e ID. |
| `ProtocolError` | Respuesta incorrecta o incompatible; verifica el contrato común. |
| `JobFailedError` | Examina `job`, `detail`, `code`; no se reintenta automáticamente. |
| `JobCancelledError` | El servidor informa cancelación; `job` contiene el estado. |
| `JobTimeoutError` | Termina la espera, no el trabajo. También hereda `TimeoutError`. |
| 404 al descubrir | Comprueba que la URL no tenga `/v1` duplicado y que la API sea compatible. |
| Error de archivos | Crea directorios padre y revisa espacio y permisos. |
| SSE no termina | El servidor debe cerrar flujos terminales; usa sondeo con plazo. |

Las excepciones del SDK heredan `TTSError`. La configuración puede lanzar
`ValueError` y el sistema de archivos `OSError`. El paquete no registra entradas ni
credenciales; evita hacerlo en tu aplicación. Los errores de autenticación no se
ocultan con sondeo alternativo. Comprueba `ValidationResult.valid` explícitamente.
