from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

DB_PATH = Path("data/embeddings.db")


class EmbeddingStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    user_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL
                )
                """
            )
            conn.commit()

    def save_embedding(self, user_id: str, embedding: np.ndarray) -> None:
        payload = embedding.astype(np.float32).tobytes()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO face_embeddings (user_id, embedding)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET embedding=excluded.embedding
                """,
                (user_id, payload),
            )
            conn.commit()

    def get_embedding(self, user_id: str) -> np.ndarray | None:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT embedding FROM face_embeddings WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return np.frombuffer(row[0], dtype=np.float32)
