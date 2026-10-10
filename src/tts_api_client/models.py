"""Strict caller inputs and forward-compatible server responses."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    def payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class VoiceSelector(Request):
    id: str | None = None
    alias: str | None = None

    @model_validator(mode="after")
    def exactly_one(self):
        if (self.id is None) == (self.alias is None):
            raise ValueError("Supply exactly one voice id or alias")
        if self.id == "" or self.alias == "":
            raise ValueError("Voice id or alias must not be empty")
        return self


class OutputOptions(Request):
    format: str = "wav"
    sample_rate: int | None = Field(default=None, gt=0)


class SpeechRequest(Request):
    text: str = Field(min_length=1)
    model: str = "default"
    voice: VoiceSelector | None = None
    language: str | None = None
    instructions: str | None = None
    output: OutputOptions = Field(default_factory=OutputOptions)
    guidance_revision: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class Reference(Request):
    asset_id: str = Field(min_length=1)
    transcript: str | None = None


class VoiceRegistration(Request):
    references: list[Reference] = Field(min_length=1)
    model: str = "default"
    alias: str | None = None


class VoiceDesignRequest(Request):
    description: str = Field(min_length=1)
    preview_text: str = Field(min_length=1)
    model: str = "default"
    language: str | None = None
    output: OutputOptions = Field(default_factory=OutputOptions)
    extensions: dict[str, Any] = Field(default_factory=dict)


class VoiceConversionRequest(Request):
    source_asset_id: str = Field(min_length=1)
    voice: VoiceSelector
    model: str = "default"
    output: OutputOptions = Field(default_factory=OutputOptions)
    extensions: dict[str, Any] = Field(default_factory=dict)


class Response(BaseModel):
    model_config = ConfigDict(extra="allow")


class ModelProfile(Response):
    id: str
    availability: str | None = None


class Capabilities(Response):
    api_version: str
    model: str
    capabilities_revision: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    controls: dict[str, Any] = Field(default_factory=dict)
    guidance: dict[str, Any] = Field(default_factory=dict)


class Guidance(Response):
    feature: str
    model: str
    revision: str
    summary: str = ""
    input_rules: list[str] = Field(default_factory=list)


class Voice(Response):
    id: str
    alias: str | None = None


class Asset(Response):
    id: str
    mime_type: str | None = None
    sample_rate: int | None = None
    duration: float | None = None


class ValidationResult(Response):
    valid: bool
    model: str | None = None
    guidance_revision: str | None = None


class ErrorDetail(Response):
    code: str
    message: str
    field: str | None = None
    retryable: bool = False
    guidance_url: str | None = None


class JobResult(Response):
    asset_id: str


class JobStatus(Response):
    id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    operation: str | None = None
    model: str | None = None
    stage: str | None = None
    progress: float | None = None
    cancellation_requested: bool = False
    results: list[JobResult] = Field(default_factory=list)
    error: ErrorDetail | None = None

    @property
    def terminal(self) -> bool:
        return self.status in {"succeeded", "failed", "cancelled"}


class Event(Response):
    id: str | None = None
    event: str = "message"
    data: Any = None
    source: Literal["sse", "poll"] = "sse"


class Session(Response):
    session_id: str
    access_token: str = Field(min_length=1, repr=False, pattern=r"^[A-Za-z0-9_-]+$")
    token_type: Literal["Bearer"] = "Bearer"
    expires_at: str
