from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TranscriptionOutput:
    text: str
    segments: list[dict[str, Any]]
    subtitle_segments: list[dict[str, Any]]
    srt: str
    model: str
    timings: dict[str, Any] = field(default_factory=dict)

    def to_verbose_json(self) -> dict[str, Any]:
        return asdict(self)
