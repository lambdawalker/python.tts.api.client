"""Generate public declarations from source AST without importing historical code."""

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reference():
    init = ast.parse((ROOT / "src/tts_api_client/__init__.py").read_text())
    exports = next(
        ast.literal_eval(n.value)
        for n in init.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)
    )
    sections = []
    for file in ["client.py", "async_client.py", "jobs.py", "models.py", "errors.py"]:
        tree = ast.parse((ROOT / "src/tts_api_client" / file).read_text())
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef) or cls.name not in exports:
                continue
            rows = [
                f"## {cls.name}",
                "",
                f"`from tts_api_client import {cls.name}`",
                "",
                f"[Source](../../src/tts_api_client/{file})",
                "",
                "```python",
                "class " + cls.name + "(" + ", ".join(ast.unparse(b) for b in cls.bases) + "):",
            ]
            for node in cls.body:
                if isinstance(node, ast.AnnAssign):
                    rows.append("    " + ast.unparse(node))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    not node.name.startswith("_") or node.name == "__init__"
                ):
                    if any("model_validator" in ast.unparse(d) for d in node.decorator_list):
                        continue
                    if any(ast.unparse(d) == "property" for d in node.decorator_list):
                        rows.append("    @property")
                    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                    result = " -> " + ast.unparse(node.returns) if node.returns else ""
                    rows.append(f"    {prefix} {node.name}({ast.unparse(node.args)}){result}: ...")
            rows.extend(["```", ""])
            sections.append("\n".join(rows))
    return "\n".join(sections)


def main():
    headings = {
        "agents": "# Public API reference\n\nGenerated declarations; explanations below define the shared contracts.\n",
        "es": "# Referencia de API pública\n\nDeclaraciones generadas; las explicaciones definen los contratos comunes.\n",
    }
    en = """
All names below are exported by `tts_api_client`. Internal modules and inherited
Pydantic validators are not SDK operations. Field `Field(...)` constraints shown
below are enforced. `default_factory` creates a fresh value for each request.
Request objects expose `payload()` (JSON-compatible dict excluding None), and
Pydantic `model_dump()` / `model_validate()`; response objects preserve extra fields.

Clients accept a deployment root, optional Bearer `api_key`, positive inactivity
`timeout=30`, injected HTTPX transport, and `trust_env=False`. `base_url` is read-only;
`clear_cache()` returns None. Sync context exit calls `close`; async exit calls
`aclose`. See [concepts](concepts.md) for lifetime, thread and cancellation rules.

Anonymous sessions: `anonymous_session=True` lazily obtains a token before the first
operation. `session_token="..."` resumes a saved token; both are incompatible with
`api_key`. Read `client.session_token` to save it privately. `create_session()` creates
and activates a fresh identity; `revoke_session()` revokes it. Closing does not revoke.
401 never triggers automatic replacement. After a failed first creation, explicitly call
`create_session()` to retry; the server may have accepted the first request. Lifecycle
changes must not run concurrently with other operations on the same client.

| Methods | Parameters, result and effect |
| --- | --- |
| `list_models`, `capabilities`, `guidance` | Read profile lists/metadata. Optional model filters select a profile; guidance requires a feature path ID. |
| `list_voices` | Read voices, optionally filtered by model. |
| `register_voice`, `delete_voice` | Create conditioning voice or delete by ID. Registration returns Voice; deletion returns None. |
| `validate_speech` | Returns ValidationResult, does not generate. Check valid explicitly. |
| `generate_speech`, `design_voice`, `convert_voice` | POST a typed request or keyword fields (mutually exclusive); return Job/AsyncJob. Optional idempotency_key is sent unchanged. Never automatically retried. |
| `job` | Local handle with id and optional initial status; no HTTP, even on async client. |
| `get_job`, `cancel_job` | Fetch status or explicitly request cancellation; return JobStatus. |
| `wait` | Poll a job ID; return successful JobStatus or raise terminal/deadline errors. timeout permits zero, poll_interval must be positive. |
| `events` | Iterator/async iterator of Event; after is the last cursor, attempts are nonnegative, delays/intervals positive. Poll fallback is configurable. |
| `upload_asset` | Read a local path as multipart file; optional MIME overrides filename-based detection. Return Asset. |
| `download_asset` | Stream asset ID to local destination; return Path; atomically replace only on success. |
| `Job.get/wait/cancel/events` | Delegate to the owning client with stored ID; same contracts. AsyncJob awaits operations except events. |

Network errors: APIError, TransportError, ProtocolError. Wait also raises
JobFailedError, JobCancelledError, JobTimeoutError. Local request errors are
Pydantic ValidationError; filesystem errors are OSError. See [troubleshooting](troubleshooting.md).
Fields carry their literal server meaning: `text` is spoken input, `instructions`
is separate direction, `language` is server-defined, `guidance_revision` identifies
authored rules, `extensions` carries native controls, and `output` requests encoding.
References associate an uploaded asset and optional exact transcript. Design uses
`description` plus `preview_text`; conversion uses source audio plus a target voice.
Response identifiers are server-local; optional metadata may be absent. `progress`
is server-defined, not assumed to be percent. `JobStatus.terminal` is a boolean.
Event `data` may be decoded JSON or raw text. No callbacks or background workers
are registered. There are no public overload declarations beyond request-or-fields.
"""
    es = """
Todos los nombres siguientes se exportan desde `tts_api_client`. Los módulos internos
y validadores heredados no son operaciones del SDK. Se aplican las restricciones
`Field(...)`; `default_factory` crea un valor nuevo por solicitud. Las solicitudes
ofrecen `payload()` (diccionario JSON sin None), además de `model_dump()` y
`model_validate()` de Pydantic. Las respuestas conservan campos adicionales.

Los clientes reciben raíz del servidor, `api_key` Bearer opcional, `timeout=30`
positivo, transporte HTTPX opcional y `trust_env=False`. `base_url` es de solo lectura;
`clear_cache()` devuelve None. Los contextos llaman a `close` o `aclose` al salir.
Consulta [conceptos](concepts.md) para propiedad, hilos y cancelación.

Sesiones anónimas: `anonymous_session=True` obtiene un token antes de la primera
operación. `session_token="..."` reutiliza un token guardado; ambas opciones son
incompatibles con `api_key`. Lee `client.session_token` para guardarlo de forma privada.
`create_session()` crea y activa una identidad nueva; `revoke_session()` la revoca.
Cerrar el cliente no revoca la sesión. Un 401 nunca provoca una sustitución automática.
Si falla la primera creación, llama explícitamente a `create_session()` para reintentar;
el servidor pudo aceptar la primera solicitud. No cambies el ciclo de vida de la sesión
mientras otras operaciones del mismo cliente están en curso.

| Métodos | Parámetros, resultado y efecto |
| --- | --- |
| `list_models`, `capabilities`, `guidance` | Consultan perfiles/metadatos. model filtra; guidance exige el ID de función. |
| `list_voices` | Lista voces, opcionalmente por modelo. |
| `register_voice`, `delete_voice` | Registra referencias y devuelve Voice, o elimina por ID y devuelve None. |
| `validate_speech` | Devuelve ValidationResult sin generar; comprueba valid. |
| `generate_speech`, `design_voice`, `convert_voice` | Envían solicitud tipada o campos, nunca ambos; devuelven Job/AsyncJob. idempotency_key se conserva. No hay reintento automático. |
| `job` | Crea un objeto local con id y estado initial opcional; no hace HTTP ni requiere await. |
| `get_job`, `cancel_job` | Consultan estado o solicitan cancelación; devuelven JobStatus. |
| `wait` | Sondea un ID y devuelve éxito o lanza error terminal/de plazo. timeout admite cero; poll_interval debe ser positivo. |
| `events` | Iterador de Event; after es el cursor, intentos no negativos y pausas positivas. Sondeo alternativo configurable. |
| `upload_asset` | Lee ruta local como archivo multipart; MIME opcional sustituye detección por nombre. Devuelve Asset. |
| `download_asset` | Descarga por ID a destino local; devuelve Path y reemplaza solo tras éxito. |
| `Job.get/wait/cancel/events` | Delegan al cliente con el ID guardado. AsyncJob espera operaciones excepto events. |

Errores de red: APIError, TransportError, ProtocolError. La espera también puede
lanzar JobFailedError, JobCancelledError, JobTimeoutError. Errores locales:
ValidationError de Pydantic y OSError. Consulta [problemas](troubleshooting.md).
`text` es entrada hablada; `instructions` son instrucciones separadas; `language`
depende del servidor; `guidance_revision` identifica las reglas; `extensions` contiene
controles nativos y `output` solicita codificación. Las referencias vinculan recurso
y transcripción opcional exacta. El diseño usa `description` y `preview_text`; la
conversión usa audio fuente y voz destino. Los IDs pertenecen al servidor; los
metadatos opcionales pueden faltar. `progress` no se supone porcentual.
`JobStatus.terminal` es booleano. Event.data puede ser JSON o texto. No se registran
callbacks ni procesos en segundo plano. No hay sobrecargas públicas adicionales.
"""
    for lang, intro in headings.items():
        (ROOT / f"docs/{lang}/api.md").write_text(
            intro + (en if lang == "agents" else es) + "\n" + reference()
        )

    subprocess.run(["ruff", "format", "docs/agents/api.md", "docs/es/api.md"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
