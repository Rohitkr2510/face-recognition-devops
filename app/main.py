"""FastAPI application entry point."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.detector import InvalidImageError, detect_faces, get_classifier

BASE_DIR = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(
    title="Sightline API",
    description="Privacy-first face detection without identity recognition.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
activity: deque[dict[str, object]] = deque(maxlen=12)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"recent_activity": list(activity)},
    )


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    try:
        get_classifier()
        model = "ready"
    except RuntimeError:
        model = "unavailable"
    return {"status": "healthy" if model == "ready" else "degraded", "model": model}


@app.get("/api/activity", tags=["detections"])
async def get_activity() -> dict[str, object]:
    return {"items": list(activity), "total": len(activity)}


@app.post("/api/detect", tags=["detections"])
async def detect(
    file: Annotated[UploadFile, File(description="JPEG, PNG, or WebP image")],
) -> dict[str, object]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be smaller than 10 MB")
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty")

    try:
        result = detect_faces(data)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    event = {
        "id": str(uuid4()),
        "filename": file.filename or "camera-capture.jpg",
        "faces": len(result.faces),
        "processing_ms": result.processing_ms,
        "created_at": datetime.now(UTC).isoformat(),
    }
    activity.appendleft(event)
    return {"id": event["id"], **result.as_dict()}
