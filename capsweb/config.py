from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REQUIRED_MODEL_FILENAMES = (
    "Fun-ASR-Nano-Encoder-Adaptor.int4.onnx",
    "Fun-ASR-Nano-CTC.int4.onnx",
    "Fun-ASR-Nano-Decoder.q5_k.gguf",
    "tokens.txt",
)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def required_model_files(model_dir: Path) -> tuple[Path, ...]:
    return tuple(model_dir / filename for filename in REQUIRED_MODEL_FILENAMES)


def has_valid_model_assets(model_dir: Path) -> bool:
    return all(path.is_file() and path.stat().st_size > 0 for path in required_model_files(model_dir))


def resolve_default_model_dir(repo_root: Path, data_dir: Path) -> Path:
    candidate_dirs = (
        repo_root / "models" / "Fun-ASR-Nano" / "Fun-ASR-Nano-GGUF",
        repo_root / "Fun-ASR-Nano-GGUF",
        data_dir / "models" / "Fun-ASR-Nano" / "Fun-ASR-Nano-GGUF",
    )

    for candidate_dir in candidate_dirs:
        if has_valid_model_assets(candidate_dir):
            return candidate_dir

    return data_dir / "models" / "Fun-ASR-Nano" / "Fun-ASR-Nano-GGUF"


@dataclass(frozen=True)
class AppSettings:
    host: str
    port: int
    repo_root: Path
    data_dir: Path
    upload_dir: Path
    model_dir: Path
    hotwords_path: Path
    auto_download_model: bool
    n_predict: int
    n_threads: int | None
    dml_enable: bool
    vulkan_enable: bool
    vulkan_force_fp32: bool

    @classmethod
    def from_env(cls) -> "AppSettings":
        repo_root = Path(__file__).resolve().parent.parent
        data_dir = Path(os.getenv("CW_DATA_DIR", repo_root / ".data"))
        default_model_dir = resolve_default_model_dir(repo_root=repo_root, data_dir=data_dir)
        thread_value = os.getenv("CW_N_THREADS")

        return cls(
            host=os.getenv("CW_HOST", "0.0.0.0"),
            port=int(os.getenv("CW_PORT", "8000")),
            repo_root=repo_root,
            data_dir=data_dir,
            upload_dir=Path(os.getenv("CW_UPLOAD_DIR", data_dir / "uploads")),
            model_dir=Path(os.getenv("CW_MODEL_DIR", default_model_dir)),
            hotwords_path=Path(os.getenv("CW_HOTWORDS_PATH", repo_root / "hot-server.txt")),
            auto_download_model=_bool_env("CW_AUTO_DOWNLOAD_MODEL", True),
            n_predict=int(os.getenv("CW_N_PREDICT", "512")),
            n_threads=int(thread_value) if thread_value else None,
            dml_enable=_bool_env("CW_DML_ENABLE", False),
            vulkan_enable=_bool_env("CW_VULKAN_ENABLE", False),
            vulkan_force_fp32=_bool_env("CW_VULKAN_FORCE_FP32", False),
        )

    def ensure_runtime_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
