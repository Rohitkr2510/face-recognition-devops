from __future__ import annotations

import logging
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.responses import Response

from app.logging_config import configure_logging
from app.services.embedder import SimpleFaceEmbedder
from app.services.storage import EmbeddingStore

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Face Recognition Service", version="1.0.0")
embedder = SimpleFaceEmbedder()
store = EmbeddingStore()

match_requests_total = Counter(
    "face_match_requests_total", "Total number of face match requests"
)
match_failures_total = Counter(
    "face_match_failures_total", "Total number of failed face match requests"
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/faces/enroll")
async def enroll_face(
    user_id: Annotated[str, Form(...)], image: Annotated[UploadFile, File(...)]
) -> dict[str, str]:
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image")

    embedding = embedder.embed(image_bytes)
    store.save_embedding(user_id, embedding)
    logger.info("enrolled user_id=%s", user_id)
    return {"message": "Enrollment successful", "user_id": user_id}


@app.post("/api/v1/faces/match")
async def match_face(
    user_id: Annotated[str, Form(...)],
    image: Annotated[UploadFile, File(...)],
    threshold: Annotated[float, Form(...)] = 0.85,
) -> dict[str, float | bool | str]:
    match_requests_total.inc()

    stored_embedding = store.get_embedding(user_id)
    if stored_embedding is None:
        match_failures_total.inc()
        raise HTTPException(status_code=404, detail="User not found")

    image_bytes = await image.read()
    if not image_bytes:
        match_failures_total.inc()
        raise HTTPException(status_code=400, detail="Empty image")

    current_embedding = embedder.embed(image_bytes)
    score = embedder.cosine_similarity(stored_embedding, current_embedding)
    matched = score >= threshold

    if not matched:
        match_failures_total.inc()

    logger.info("match evaluated user_id=%s score=%.4f matched=%s", user_id, score, matched)

    return {
        "user_id": user_id,
        "match": matched,
        "confidence": round(score, 4),
        "threshold": threshold,
    }
