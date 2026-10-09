"""Incremental SSE frame decoding shared by both transports."""

import json

from .errors import ProtocolError
from .models import Event


class Decoder:
    def __init__(self, last_id: str | None = None):
        self.last_id = last_id
        self._id = last_id
        self._event = "message"
        self._data: list[str] = []
        self._size = 0
        self._first = True

    def feed(self, line: str) -> Event | None:
        if self._first:
            line = line.removeprefix("\ufeff")
            self._first = False
        if line == "":
            result = None
            if self._data:
                raw = "\n".join(self._data)
                try:
                    data = json.loads(raw)
                except ValueError:
                    data = raw
                result = Event(id=self._id or None, event=self._event, data=data)
            self.last_id = self._id
            self._data = []
            self._event = "message"
            self._size = 0
            return result
        if line.startswith(":"):
            return None
        self._size += len(line)
        if self._size > 1_048_576:
            raise ProtocolError("SSE frame exceeds 1 MiB text limit")
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")
        if field == "data":
            self._data.append(value)
        elif field == "event":
            self._event = value or "message"
        elif field == "id" and "\x00" not in value:
            self._id = value
        return None


def replayed(event_id: str | None, last_id: str | None) -> bool:
    if not event_id or not last_id:
        return False
    if event_id.isdecimal() and last_id.isdecimal():
        return int(event_id) <= int(last_id)
    return event_id == last_id
