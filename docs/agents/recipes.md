# Task recipes

These snippets run inside an open `with TTSClient(...) as client:` block.
Read feature guidance and confirm capability support before optional operations.

## References and voices

```python
asset = client.upload_asset("reference.wav")
voice = client.register_voice(
    references=[{"asset_id": asset.id, "transcript": "Actual spoken words."}],
    alias="narrator",
)
job = client.generate_speech(text="Hello!", voice={"id": voice.id})
```

Reference bytes and transcripts are unchanged. The host supplies an appropriate
recording and transcript; there is no ASR, resampling, denoising or voice fallback.
`list_voices(model=...)` lists available voices; `delete_voice(voice.id)` removes one.
A selector supplies exactly one nonempty `id` or `alias`.

## Voice design and conversion

```python
design = client.design_voice(description="Warm, low voice", preview_text="Hello!")
conversion = client.convert_voice(source_asset_id=asset.id, voice={"id": voice.id})
```

Both return jobs. Their result asset IDs are retrieved with `wait()` and downloaded
using `download_asset`. A design result does not automatically register a reusable
voice; follow the server's guidance for subsequent registration.

## Native controls

```python
job = client.generate_speech(
    text="Hello!",
    model="default",
    instructions="Speak calmly",
    output={"format": "wav", "sample_rate": 24000},
)
```

This is illustrative: instructions, formats and rates must be supported by the
profile. Put native tags directly in text, and documented namespaced controls in
`extensions`. The SDK validates structure, not native semantics. It never removes tags.
Use either a typed request object or keyword fields, never both.

## Reconnect and observe

```python
from contextlib import closing

job = client.job("saved-job-id")
with closing(job.events(after="saved-event-id")) as events:
    for event in events:
        print(event.source, event.id, event.event, event.data)
status = job.wait(timeout=60)
```

SSE resumes using `Last-Event-ID`, suppresses monotonic numeric replays and immediate
opaque duplicates, and discards incomplete frames. Defaults: `reconnect_attempts=3`,
`reconnect_delay=1`, `polling_fallback=True`, `poll_interval=1`. Fallback snapshots
have `source="poll"`, `event="status"`, `id=None`. Servers should close terminal
streams. Close abandoned generators; use `contextlib.aclosing` for async iterators.
The SSE iterator has no total deadline, only HTTP inactivity limits.

## Submission recovery

Save a unique idempotency key for each intended generation. After an ambiguous
transport error, the application may resubmit the identical request with the same
key, if the server implements idempotency. A new key requests new work. The SDK
never retries a submission automatically; a `retryable` field is information only.

## Atomic downloads

```python
client.download_asset(status.results[0].asset_id, "speech.wav")
```

Parent directories must exist. Success atomically replaces the destination; failure
removes the temporary file and preserves any existing destination. Download URLs
from responses are ignored. All downloads use the configured server and asset ID.
