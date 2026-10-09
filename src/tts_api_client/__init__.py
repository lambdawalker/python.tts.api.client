"""Client for the design.ai shared TTS v1 API."""

from .async_client import AsyncTTSClient
from .client import TTSClient
from .errors import (
    APIError,
    JobCancelledError,
    JobFailedError,
    JobTimeoutError,
    ProtocolError,
    TransportError,
    TTSError,
)
from .jobs import AsyncJob, Job
from .models import (
    Asset,
    Capabilities,
    ErrorDetail,
    Event,
    Guidance,
    JobResult,
    JobStatus,
    ModelProfile,
    OutputOptions,
    Reference,
    SpeechRequest,
    ValidationResult,
    Voice,
    VoiceConversionRequest,
    VoiceDesignRequest,
    VoiceRegistration,
    VoiceSelector,
)

__version__ = "0.1.0"  # x-release-please-version
__all__ = [
    "TTSClient",
    "AsyncTTSClient",
    "Job",
    "AsyncJob",
    "TTSError",
    "APIError",
    "TransportError",
    "ProtocolError",
    "JobFailedError",
    "JobCancelledError",
    "JobTimeoutError",
    "SpeechRequest",
    "VoiceSelector",
    "OutputOptions",
    "Reference",
    "VoiceRegistration",
    "VoiceDesignRequest",
    "VoiceConversionRequest",
    "ModelProfile",
    "Capabilities",
    "Guidance",
    "Voice",
    "Asset",
    "ValidationResult",
    "ErrorDetail",
    "JobResult",
    "JobStatus",
    "Event",
]
