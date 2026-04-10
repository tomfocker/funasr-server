from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
import unittest
from types import SimpleNamespace
import re


class DockerImageLayoutTests(unittest.TestCase):
    def test_dockerfile_bakes_fun_asr_nano_model_into_image(self) -> None:
        dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("CW_MODEL_DIR=/app/Fun-ASR-Nano-GGUF", dockerfile)
        self.assertIn("CW_AUTO_DOWNLOAD_MODEL=0", dockerfile)
        self.assertIn("scripts/bootstrap_fun_asr_env.py", dockerfile)
        self.assertIn("CW_AUTO_DOWNLOAD_MODEL=1 python3 scripts/bootstrap_fun_asr_env.py", dockerfile)


class LongAudioTimingCompatibilityTests(unittest.TestCase):
    def test_long_audio_transcription_does_not_require_legacy_ctc_timing_fields(self) -> None:
        orchestrator_path = (
            Path(__file__).resolve().parents[1]
            / "util"
            / "fun_asr_gguf"
            / "inference"
            / "core"
            / "orchestrator.py"
        )
        source = orchestrator_path.read_text(encoding="utf-8")
        source = re.sub(r"^import numpy as np\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^from \.\..*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^from \.model_manager.*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^from \.decoder.*$", "", source, flags=re.MULTILINE)

        @dataclass
        class Timings:
            encode: float = 0.0
            ctc: float = 0.0
            prepare: float = 0.0
            inject: float = 0.0
            llm_generate: float = 0.0
            align: float = 0.0
            total: float = 0.0

        @dataclass
        class TranscriptionResult:
            text: str = ""
            segments: list[dict[str, Any]] = field(default_factory=list)
            ctc_text: str = ""
            hotwords: list[str] = field(default_factory=list)
            timings: Timings = field(default_factory=Timings)

        @dataclass
        class Statistics:
            audio_duration: float = 0.0
            n_input_tokens: int = 0
            n_prefix_tokens: int = 0
            n_audio_tokens: int = 0
            n_suffix_tokens: int = 0
            n_generated_tokens: int = 0
            tps_in: float = 0.0
            tps_out: float = 0.0

        class RecognitionStream:
            def accept_waveform(self, *_args, **_kwargs) -> None:
                return None

        class StreamDecoder:
            def __init__(self, _models) -> None:
                return None

        namespace: dict[str, Any] = {
            "__name__": "test_orchestrator_module",
            "os": __import__("os"),
            "time": __import__("time"),
            "np": None,
            "Optional": __import__("typing").Optional,
            "List": list,
            "load_audio": lambda *_args, **_kwargs: None,
            "merge_transcription_results": lambda *_args, **_kwargs: (
                "merged-text",
                [{"char": "x", "start": 0.0}],
            ),
            "generate_srt_file": lambda *_args, **_kwargs: None,
            "DisplayReporter": object,
            "TranscriptionResult": TranscriptionResult,
            "Statistics": Statistics,
            "RecognitionStream": RecognitionStream,
            "ModelManager": object,
            "StreamDecoder": StreamDecoder,
        }
        exec(source, namespace)
        TranscriptionOrchestrator = namespace["TranscriptionOrchestrator"]

        class FakeReporter:
            verbose = False
            skip_technical = False

            def print(self, *_args, **_kwargs) -> None:
                return None

            def set_segment(self, *_args, **_kwargs) -> None:
                return None

        models = SimpleNamespace(config=SimpleNamespace(sample_rate=4))
        orchestrator = TranscriptionOrchestrator(models)

        decode_calls = {"count": 0}

        def fake_decode_stream(*_args, **_kwargs):
            decode_calls["count"] += 1
            return SimpleNamespace(
                text=f"seg-{decode_calls['count']}",
                aligned=[{"char": str(decode_calls["count"]), "start": 0.1}],
                hotwords=[],
                ctc_results=[],
                timings=Timings(
                    encode=0.1,
                    ctc=0.2,
                    prepare=0.3,
                    inject=0.4,
                    llm_generate=0.5,
                    align=0.6,
                ),
            )

        orchestrator.decoder = SimpleNamespace(decode_stream=fake_decode_stream)
        result = TranscriptionResult()
        audio = [0.0] * 20  # 5s @ 4Hz => 3 segments with size=2s overlap=0.5s

        orchestrator._transcribe_long(
            audio=audio,
            result=result,
            language=None,
            context=None,
            verbose=False,
            segment_size=2.0,
            overlap=0.5,
            reporter=FakeReporter(),
            base_offset=0.0,
        )

        self.assertEqual(decode_calls["count"], 3)
        self.assertEqual(result.text, "merged-text")
        self.assertEqual(result.segments, [{"char": "x", "start": 0.0}])
        self.assertAlmostEqual(result.timings.encode, 0.3)
        self.assertAlmostEqual(result.timings.ctc, 0.6)
        self.assertAlmostEqual(result.timings.prepare, 0.9)
        self.assertAlmostEqual(result.timings.inject, 1.2)
        self.assertAlmostEqual(result.timings.llm_generate, 1.5)
        self.assertAlmostEqual(result.timings.align, 1.8)


if __name__ == "__main__":
    unittest.main()
