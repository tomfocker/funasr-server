from __future__ import annotations

from pathlib import Path


def resolve_shared_library_path(lib_dir: str | Path, library_name: str) -> Path:
    base_dir = Path(lib_dir)
    direct_path = base_dir / library_name
    if direct_path.is_file():
        return direct_path

    candidates = sorted(
        (path for path in base_dir.glob(f"{library_name}*") if path.is_file()),
        key=lambda path: (len(path.name), path.name),
    )
    if candidates:
        return candidates[0]

    raise FileNotFoundError(f"Unable to locate shared library {library_name} under {base_dir}")
