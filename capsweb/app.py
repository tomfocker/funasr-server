from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from capsweb import __version__
from capsweb.config import AppSettings
from capsweb.formatters import response_for_format
from capsweb.transcriber import AssetNotReadyError, FunAsrNanoTranscriber

SUPPORTED_RESPONSE_FORMATS = {"text", "json", "verbose_json", "srt"}


async def _save_upload(file: UploadFile, upload_dir: Path) -> Path:
    suffix = Path(file.filename or "upload.bin").suffix or ".bin"
    upload_dir.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(delete=False, suffix=suffix, dir=upload_dir) as handle:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
        return Path(handle.name)


def create_app(
    settings: AppSettings | None = None,
    transcriber: FunAsrNanoTranscriber | None = None,
) -> FastAPI:
    settings = settings or AppSettings.from_env()
    settings.ensure_runtime_dirs()
    transcriber = transcriber or FunAsrNanoTranscriber(settings)

    app = FastAPI(
        title="FunASR Server",
        version=__version__,
        docs_url="/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.transcriber = transcriber

    @app.get("/")
    async def index() -> dict:
        return {
            "service": "funasr-server",
            "version": __version__,
            "docs": "/docs",
            "healthz": "/healthz",
            "transcriptions": "/v1/audio/transcriptions",
            "model": transcriber.get_status().get("model"),
        }

    @app.get("/healthz")
    async def healthz() -> dict:
        payload = transcriber.get_status()
        payload["version"] = __version__
        payload["port"] = settings.port
        return payload

    async def _handle_transcription(
        file: UploadFile = File(...),
        response_format: str = Form("verbose_json"),
        temperature: float = Form(0.3),
    ):
        if response_format not in SUPPORTED_RESPONSE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported response_format: {response_format}",
            )

        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        temp_path = await _save_upload(file, settings.upload_dir)
        try:
            result = await asyncio.to_thread(transcriber.transcribe_file, temp_path, temperature)
        except AssetNotReadyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

        return response_for_format(result, response_format)

    app.post("/v1/audio/transcriptions")(_handle_transcription)
    app.post("/api/transcriptions")(_handle_transcription)

    return app


app = create_app()
