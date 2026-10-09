# Troubleshooting and errors

| Symptom | Meaning and action |
| --- | --- |
| Pydantic `ValidationError` | Invalid local structure/types; fix the request. Unknown native tags are not checked locally. |
| `APIError` | Server rejected the operation. Inspect `status_code`, `code`, `field`, `retryable`, `guidance_url`, `request_id`, `detail`. Read guidance; do not silently repair input. |
| `TransportError` | Network failure. Submission may have succeeded; retain the key/job ID. |
| `ProtocolError` | Malformed or incompatible response. Verify the server implements the shared API. |
| `JobFailedError` | Inspect `job`, `detail`, `code`; no automatic retry. |
| `JobCancelledError` | Server reports cancellation; original status is `job`. |
| `JobTimeoutError` | Waiting stopped; job continues. Also a `TimeoutError`. Reattach later. |
| 404 on discovery | Base URL may include an extra `/v1`, or server is a legacy API. |
| Download filesystem error | Create destination parents and verify disk permissions/space. |
| SSE never ends | Server must close terminal streams. Use status polling for a bounded wait. |

SDK errors inherit `TTSError`. Local configuration/path errors can raise `ValueError`;
file operations can raise `OSError`. The package does not log request content or keys.
Do not log credentials or sensitive reference text in application error reporting.
Auth errors are surfaced, not hidden by progress fallback. `ValidationResult.valid`
may be false without an exception; inspect it explicitly before submission.
