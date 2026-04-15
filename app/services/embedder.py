from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image


class SimpleFaceEmbedder:
    """Lightweight deterministic image embedder.

    Note: this is not production-grade face recognition,
    but provides a working baseline pipeline.
    """

    def __init__(self, size: tuple[int, int] = (64, 64)) -> None:
        self.size = size

    def embed(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(BytesIO(image_bytes)).convert("L").resize(self.size)
        array = np.asarray(image, dtype=np.float32).flatten()
        normalized = array / 255.0
        return normalized

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denominator = np.linalg.norm(a) * np.linalg.norm(b)
        if denominator == 0:
            return 0.0
        return float(np.dot(a, b) / denominator)
