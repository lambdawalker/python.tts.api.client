# Compatibility and limitations

This implements a proposed shared `/v1` contract. Legacy Fish `/v1/tts` and
Chatterbox-specific APIs are not compatible without adapters. Tests use HTTP fixtures
and a local HTTP server; no live model/GPU compatibility has been verified.

Python >=3.10 is declared; CI targets 3.10–3.13. The package is pure Python; platform
support depends on HTTPX/Pydantic and the host Python runtime. Async support requires
asyncio, not Trio. Multipart file reads and bounded download writes are synchronous
local disk operations even in the async client.

No streaming playback API, PCM decoding, ASR, model execution, MCP, automatic input
rewriting, or automatic generation retry is provided. SSE is progress notification,
not a guarantee of incremental audio. No public OpenAPI retrieval method exists.

Requests forbid unknown fields and use strict types. Responses preserve additive
metadata. Recognized API major version is 1; native feature schemas remain server-owned.
Identifiers embedded in paths are restricted to letters, digits, underscore, period
and hyphen, starting with a letter, digit or underscore. Model IDs in JSON/query
fields are not subject to that path restriction.

Redirects are disabled; server-provided URLs are never followed. `trust_env=False`
is the default; opt in deliberately for environment proxy/netrc behavior. There is
no custom TLS configuration parameter. An injected HTTPX transport is primarily
for tests and advanced host integrations; the client owns and closes it.

No license has been selected by the owner at the time this guide was authored. Check installation for publication availability.
See [migration](migration.md) before relying on this development API in production.
