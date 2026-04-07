from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from capsweb.config import AppSettings, has_valid_model_assets, required_model_files
from capsweb.contracts import TranscriptionOutput
from capsweb.formatters import build_subtitle_segments, normalize_segments, render_srt


class AssetNotReadyError(RuntimeError):
    pass


class FunAsrNanoTranscriber:
    name = "fun_asr_nano"

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._engine = None
        self._lock = Lock()

    def _required_model_files(self) -> list[Path]:
        return list(required_model_files(self.settings.model_dir))

    def _assets_ready(self) -> bool:
        return has_valid_model_assets(self.settings.model_dir)

    def get_status(self) -> dict[str, Any]:
        assets_ready = self._assets_ready()
        return {
            "status": "ok",
            "model": self.name,
            "ready": assets_ready,
            "assets_ready": assets_ready,
            "engine_loaded": self._engine is not None,
            "model_dir": str(self.settings.model_dir),
        }

    def ensure_ready(self) -> None:
        if self._engine is not None:
            return

        if not self._assets_ready():
            raise AssetNotReadyError(
                "Fun-ASR-Nano model assets are missing. Run the bootstrap script or enable auto download."
            )

        with self._lock:
            if self._engine is not None:
                return

            from util.fun_asr_gguf import create_asr_engine

            self._engine = create_asr_engine(
                encoder_onnx_path=str(self.settings.model_dir / "Fun-ASR-Nano-Encoder-Adaptor.int4.onnx"),
                ctc_onnx_path=str(self.settings.model_dir / "Fun-ASR-Nano-CTC.int4.onnx"),
                decoder_gguf_path=str(self.settings.model_dir / "Fun-ASR-Nano-Decoder.q5_k.gguf"),
                tokens_path=str(self.settings.model_dir / "tokens.txt"),
                hotwords_path=str(self.settings.hotwords_path),
                enable_ctc=True,
                n_predict=self.settings.n_predict,
                n_threads=self.settings.n_threads,
                similar_threshold=0.6,
                max_hotwords=20,
                dml_enable=self.settings.dml_enable,
                pad_to=30,
                vulkan_enable=self.settings.vulkan_enable,
                vulkan_force_fp32=self.settings.vulkan_force_fp32,
                verbose=False,
            )

    def transcribe_file(self, file_path: Path, temperature: float) -> TranscriptionOutput:
        self.ensure_ready()

        with self._lock:
            result = self._engine.transcribe(
                audio_path=str(file_path),
                verbose=False,
                srt=False,
                temperature=temperature,
            )

        segments = normalize_segments(getattr(result, "segments", []))
        subtitle_segments = build_subtitle_segments(segments)
        srt_text = render_srt(subtitle_segments)
        timings = self._timings_to_dict(getattr(result, "timings", {}))
        return TranscriptionOutput(
            text=getattr(result, "text", ""),
            segments=segments,
            subtitle_segments=subtitle_segments,
            srt=srt_text,
            model=self.name,
            timings=timings,
        )

    @staticmethod
    def _timings_to_dict(timings: Any) -> dict[str, Any]:
        if is_dataclass(timings):
            return asdict(timings)
        if isinstance(timings, dict):
            return dict(timings)
        return {}
