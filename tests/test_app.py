from io import BytesIO

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_renders() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Sightline" in response.text
    assert "Start a detection" in response.text
    assert "Open your camera" in response.text


def test_health_reports_model_state() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "model": "ready"}


def test_detects_valid_image() -> None:
    image = np.full((120, 160, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok

    response = client.post(
        "/api/detect", files={"file": ("studio.png", BytesIO(encoded.tobytes()), "image/png")}
    )
    assert response.status_code == 200
    assert response.json()["face_count"] == 0
    assert response.json()["image"] == {"width": 160, "height": 120}

def test_rejects_unsupported_content_type() -> None:
    response = client.post(
        "/api/detect", files={"file": ("notes.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 415


def test_rejects_invalid_image_data() -> None:
    response = client.post(
        "/api/detect", files={"file": ("broken.png", b"not an image", "image/png")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a valid image"
