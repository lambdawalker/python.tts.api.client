# Concepts and ownership

The client transports model-native inputs unchanged. A person or agent reads
capabilities and feature guidance, authors input, optionally validates it, then
submits. The shared server dispatches to a model adapter; MCP belongs to that server.
Neither equal endpoints nor equal model family names imply equal feature support.

Capabilities and guidance use ETags when available and revalidate every call.
Returned objects are independent copies. There is no offline stale-cache fallback.
`clear_cache()` discards discovery metadata. The immutable base URL prevents
credentials and cached rules from leaking when switching servers: create a new client.

Use one client within a context manager; jobs retain that client and require it to
remain open. `close()` / `aclose()` release connections and discovery cache, not
server jobs. There is no thread-safety guarantee for the SDK's mutable cache; use
separate clients per thread. Async clients belong to one asyncio event loop.

Job states are `queued`, `running`, `succeeded`, `failed`, `cancelled`. Stages are
separate metadata. `wait()` returns successful status or raises on failure,
cancellation or deadline. `events()` yields notifications (including failure as
data); it does not raise `JobFailedError` merely because an event reports failure.
Call `wait()` or inspect final status to determine the outcome.

HTTP `timeout=30` is a per-operation inactivity limit. Job `timeout=600` is a polling
deadline; `poll_interval=1`. Async waits interrupt active status requests at the
deadline. Blocking waits may exceed their deadline if a response trickles bytes.
Timeouts and dropped connections do not cancel jobs. Only an explicit `cancel()`
or `cancel_job()` requests cancellation; cancellation may not be immediate.

The application owns downloaded files, reference recordings, job ID persistence,
and idempotency keys. Asset and voice IDs are deployment-local. Registration stores
conditioning references, not a trained model. Closing a client does not delete assets
or voices. `delete_voice()` is an explicit server mutation.
