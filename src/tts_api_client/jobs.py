"""Handles keep job identity, never imply cancellation on close."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import JobStatus

if TYPE_CHECKING:
    from .async_client import AsyncTTSClient
    from .client import TTSClient


class Job:
    def __init__(self, client: TTSClient, job_id: str, initial: JobStatus | None = None):
        self._client = client
        self.id = job_id
        self.initial = initial

    def get(self) -> JobStatus:
        return self._client.get_job(self.id)

    def wait(self, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus:
        return self._client.wait(self.id, timeout=timeout, poll_interval=poll_interval)

    def cancel(self) -> JobStatus:
        return self._client.cancel_job(self.id)

    def events(self, **options):
        return self._client.events(self.id, **options)


class AsyncJob:
    def __init__(self, client: AsyncTTSClient, job_id: str, initial: JobStatus | None = None):
        self._client = client
        self.id = job_id
        self.initial = initial

    async def get(self) -> JobStatus:
        return await self._client.get_job(self.id)

    async def wait(self, *, timeout: float = 600, poll_interval: float = 1) -> JobStatus:
        return await self._client.wait(self.id, timeout=timeout, poll_interval=poll_interval)

    async def cancel(self) -> JobStatus:
        return await self._client.cancel_job(self.id)

    def events(self, **options):
        return self._client.events(self.id, **options)
