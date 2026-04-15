from __future__ import annotations

from io import BytesIO

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _image_bytes(seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 255, size=(64, 64), dtype=np.uint8)
    image = Image.fromarray(pixels, mode="L")
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_enroll_and_match_success() -> None:
    img = _image_bytes(42)

    enroll_response = client.post(
        "/api/v1/faces/enroll",
        data={"user_id": "alice"},
        files={"image": ("face.png", img, "image/png")},
    )
    assert enroll_response.status_code == 200

    match_response = client.post(
        "/api/v1/faces/match",
        data={"user_id": "alice", "threshold": 0.8},
        files={"image": ("face.png", img, "image/png")},
    )
    body = match_response.json()
    assert match_response.status_code == 200
    assert body["match"] is True


def test_match_missing_user() -> None:
    img = _image_bytes(7)
    response = client.post(
        "/api/v1/faces/match",
        data={"user_id": "missing", "threshold": 0.8},
        files={"image": ("face.png", img, "image/png")},
    )
    assert response.status_code == 404
