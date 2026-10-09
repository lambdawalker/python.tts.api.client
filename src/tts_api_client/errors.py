"""Errors preserve domain information without logging requests or credentials."""

from .models import ErrorDetail, JobStatus


class TTSError(Exception):
    """Base SDK error."""


class ProtocolError(TTSError):
    """The response violates the supported API contract."""


class TransportError(TTSError):
    """A network operation failed. Submission outcome may be unknown."""


class APIError(TTSError):
    def __init__(self, detail: ErrorDetail, status_code: int, request_id: str | None = None):
        self.detail = detail
        self.status_code = status_code
        self.request_id = request_id
        self.code = detail.code
        self.field = detail.field
        self.retryable = detail.retryable
        self.guidance_url = detail.guidance_url
        super().__init__(f"{detail.code}: {detail.message}")


class JobFailedError(TTSError):
    def __init__(self, job: JobStatus):
        self.job = job
        self.detail = job.error
        self.code = job.error.code if job.error else "job_failed"
        super().__init__(f"Job {job.id} failed: {self.code}")


class JobCancelledError(TTSError):
    def __init__(self, job: JobStatus):
        self.job = job
        super().__init__(f"Job {job.id} was cancelled")


class JobTimeoutError(TTSError, TimeoutError):
    """Waiting ended; the job was not cancelled."""
