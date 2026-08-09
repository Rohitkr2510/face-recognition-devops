"""OpenCV-backed face detection service."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache

import cv2
import numpy as np


class InvalidImageError(ValueError):
    """Raised when uploaded bytes cannot be decoded as an image."""


@dataclass(frozen=True)
class Face:
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass(frozen=True)
class DetectionResult:
    image_width: int
    image_height: int
    faces: tuple[Face, ...]
    processing_ms: float

    def as_dict(self) -> dict[str, object]:
        return {
            "image": {"width": self.image_width, "height": self.image_height},
            "faces": [asdict(face) for face in self.faces],
            "face_count": len(self.faces),
            "processing_ms": self.processing_ms,
        }


@lru_cache(maxsize=1)
def get_classifier() -> cv2.CascadeClassifier:
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    classifier = cv2.CascadeClassifier(path)
    if classifier.empty():
        raise RuntimeError("OpenCV face detection model could not be loaded")
    return classifier


def detect_faces(data: bytes) -> DetectionResult:
    """Decode image bytes and return frontal-face bounding boxes."""
    from time import perf_counter

    started = perf_counter()
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise InvalidImageError("The uploaded file is not a valid image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    boxes = get_classifier().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    elapsed = round((perf_counter() - started) * 1000, 1)
    faces = tuple(
        Face(int(x), int(y), int(width), int(height), 0.9)
        for x, y, width, height in boxes
    )
    height, width = image.shape[:2]
    return DetectionResult(width, height, faces, elapsed)

