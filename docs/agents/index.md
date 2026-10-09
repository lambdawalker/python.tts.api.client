# TTS API Client

For installation and version scope, follow the installation guide. This Python library
connects to a server implementing the proposed shared TTS `/v1` API. It does not run
models, provide MCP, or adapt legacy model APIs. Server adapters are required.

Start with [installation](installation.md), then [quickstart](quickstart.md).

| Task | API | Guide |
| --- | --- | --- |
| Discover profiles and input rules | `list_models`, `capabilities`, `guidance` | [Concepts](concepts.md) |
| Generate speech | `validate_speech`, `generate_speech` | [Quickstart](quickstart.md) |
| Clone/register, design, convert | `upload_asset`, `register_voice`, `design_voice`, `convert_voice` | [Recipes](recipes.md) |
| Reconnect, wait, cancel, download | `job`, `events`, `wait`, `cancel`, `download_asset` | [Recipes](recipes.md) |
| Inspect exact declarations | Public exports and model fields | [API](api.md) |
| Diagnose failures | Structured errors | [Troubleshooting](troubleshooting.md) |
| Evaluate support | Requirements and caveats | [Limitations](limitations.md) |
| Upgrade | Version policy | [Migration](migration.md) |
| Run demonstrations | Offline and live examples | [Examples](examples.md) |

Critical invariants: preserve inputs exactly; discover guidance before authoring;
never retry generation automatically; never cancel implicitly; IDs belong to one
server. A client owns its HTTP pool and must be closed. The application owns job IDs,
idempotency keys, reference consent, and downloaded files.
