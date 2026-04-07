from __future__ import annotations

import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from capsweb.config import AppSettings, has_valid_model_assets, required_model_files


MODEL_URL = (
    "https://github.com/HaujetZhao/CapsWriter-Offline/releases/download/models/"
    "Fun-ASR-Nano-GGUF.zip"
)
def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"[bootstrap] downloading {url}")
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def extract_zip(zip_path: Path, destination_dir: Path) -> None:
    print(f"[bootstrap] extracting {zip_path.name} -> {destination_dir}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination_dir)


def main() -> int:
    settings = AppSettings.from_env()
    settings.ensure_runtime_dirs()

    if has_valid_model_assets(settings.model_dir):
        print(f"[bootstrap] model already present at {settings.model_dir}")
        return 0

    if not settings.auto_download_model:
        print("[bootstrap] model assets missing and CW_AUTO_DOWNLOAD_MODEL is disabled")
        return 0

    cache_dir = settings.data_dir / "cache"
    archive_path = cache_dir / "Fun-ASR-Nano-GGUF.zip"
    download_file(MODEL_URL, archive_path)
    extract_zip(archive_path, settings.model_dir.parent)

    if not has_valid_model_assets(settings.model_dir):
        missing_or_invalid = ", ".join(str(path) for path in required_model_files(settings.model_dir))
        print(
            "[bootstrap] model download completed but required files are still missing or invalid "
            f"under {settings.model_dir}: {missing_or_invalid}",
            file=sys.stderr,
        )
        return 1

    print(f"[bootstrap] model ready at {settings.model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
