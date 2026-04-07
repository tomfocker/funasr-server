from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi.responses import JSONResponse, PlainTextResponse, Response

from capsweb.contracts import TranscriptionOutput

SENTENCE_PUNCTUATION = set("，。！？；,.!?;")
PAUSE_THRESHOLD = 0.4
LONG_PAUSE_THRESHOLD = 1.0
MIN_CHARS_TO_BREAK = 5
MAX_SUBTITLE_CHARS = 30


def _format_ts(seconds: float) -> str:
    total_millis = max(0, round(seconds * 1000))
    hours, rem = divmod(total_millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def render_srt(segments: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, segment in enumerate(segments, start=1):
        start = _format_ts(float(segment["start"]))
        end = _format_ts(float(segment["end"]))
        text = str(segment["text"])
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def normalize_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not segments:
        return []

    normalized: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        start = float(segment["start"])
        if "end" in segment:
            end = float(segment["end"])
        else:
            next_start = (
                float(segments[index + 1]["start"])
                if index + 1 < len(segments)
                else start + 0.5
            )
            end = max(start + 0.1, next_start)

        normalized.append(
            {
                "id": int(segment.get("id", index)),
                "start": start,
                "end": end,
                "text": str(segment.get("text", segment.get("char", ""))),
            }
        )
    return normalized


def build_subtitle_segments(
    segments: list[dict[str, Any]],
    max_chars_per_line: int = MAX_SUBTITLE_CHARS,
) -> list[dict[str, Any]]:
    normalized = normalize_segments(segments)
    if not normalized:
        return []

    subtitle_segments: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_start = float(normalized[0]["start"])

    for index, segment in enumerate(normalized):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue

        current_parts.append(text)
        current_text = "".join(current_parts)
        is_last = index == len(normalized) - 1
        is_punctuation = text in SENTENCE_PUNCTUATION
        too_long = len(current_text) >= max_chars_per_line

        has_pause = False
        if not is_last:
            next_start = float(normalized[index + 1]["start"])
            pause_duration = next_start - float(segment["start"])
            if (
                len(current_text) >= MIN_CHARS_TO_BREAK and pause_duration > PAUSE_THRESHOLD
            ) or pause_duration > LONG_PAUSE_THRESHOLD:
                has_pause = True

        if not (is_punctuation or is_last or too_long or has_pause):
            continue

        if is_last:
            end_time = float(segment["start"]) + 0.5
        else:
            next_start = float(normalized[index + 1]["start"])
            end_time = min(float(segment["start"]) + 0.5, (float(segment["start"]) + next_start) / 2)

        subtitle_text = current_text.rstrip("".join(SENTENCE_PUNCTUATION) + " ").strip()
        if subtitle_text:
            subtitle_segments.append(
                {
                    "id": len(subtitle_segments),
                    "start": current_start,
                    "end": end_time,
                    "text": subtitle_text,
                }
            )

        if not is_last:
            current_parts = []
            current_start = float(normalized[index + 1]["start"])

    return subtitle_segments


def response_for_format(result: TranscriptionOutput, response_format: str) -> Response:
    if response_format == "text":
        return PlainTextResponse(result.text)
    if response_format == "json":
        return JSONResponse({"text": result.text})
    if response_format == "verbose_json":
        if hasattr(result, "to_verbose_json"):
            return JSONResponse(result.to_verbose_json())
        if is_dataclass(result):
            return JSONResponse(asdict(result))
        return JSONResponse(dict(result))
    if response_format == "srt":
        return PlainTextResponse(result.srt)
    raise ValueError(f"Unsupported response_format: {response_format}")
