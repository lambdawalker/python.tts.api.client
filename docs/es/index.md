# TTS API Client

Consulta instalación para el ámbito de versión y disponibilidad. La biblioteca
conecta Python con servidores que implementan la API TTS común
`/v1`. No ejecuta modelos ni ofrece MCP; los servidores necesitan sus adaptadores.

Empieza por [instalación](installation.md) y [inicio rápido](quickstart.md).

| Tarea | API | Guía |
| --- | --- | --- |
| Consultar modelos y reglas | `list_models`, `capabilities`, `guidance` | [Conceptos](concepts.md) |
| Generar voz | `validate_speech`, `generate_speech` | [Inicio rápido](quickstart.md) |
| Referencias, diseño y conversión | `upload_asset`, `register_voice`, `design_voice`, `convert_voice` | [Recetas](recipes.md) |
| Reanudar, observar y cancelar | `job`, `events`, `wait`, `cancel` | [Recetas](recipes.md) |
| Consultar declaraciones exactas | Exportaciones y campos | [API](api.md) |
| Resolver errores | Excepciones estructuradas | [Problemas](troubleshooting.md) |
| Evaluar compatibilidad | Requisitos y restricciones | [Limitaciones](limitations.md) |
| Actualizar | Política de versiones | [Migración](migration.md) |
| Ejecutar demostraciones | Ejemplos locales y reales | [Ejemplos](examples.md) |

Reglas esenciales: conservar las entradas, leer las instrucciones del modelo antes
de escribirlas, no reintentar generaciones automáticamente ni cancelar implícitamente.
Los identificadores pertenecen a un servidor. La aplicación conserva claves de
idempotencia, identificadores de trabajos y archivos; el cliente posee sus conexiones.
