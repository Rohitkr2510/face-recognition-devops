# Sightline

Sightline is a clean, privacy-first face **detection** platform. It locates faces in images without identifying people, saving biometric profiles, or retaining uploaded files. The responsive dashboard, camera capture flow, REST API, and OpenCV inference service run together as one Python application.

## Features

- Upload, drag and drop, or capture JPEG, PNG, and WebP images.
- Draw face bounding boxes directly in the browser.
- Review session-level detection counts, latency, and recent activity.
- Run local inference with OpenCV's frontal-face Haar cascade.
- Explore a typed OpenAPI contract at `/docs`.
- Deploy with Docker Compose and validate changes through GitHub Actions.
- Process images in memory only; source images are never persisted.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000). API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Docker

```bash
docker compose up --build
```

## API

### Detect faces

```bash
curl -X POST http://localhost:8000/api/detect \
  -F "file=@portrait.jpg"
```

The response contains image dimensions, elapsed inference time, and a list of bounding boxes:

```json
{
  "id": "876d50ea-8ece-4cf5-aed1-68ed5ef5c778",
  "image": {"width": 1200, "height": 800},
  "faces": [{"x": 412, "y": 176, "width": 220, "height": 220, "confidence": 0.9}],
  "face_count": 1,
  "processing_ms": 42.7
}
```

Other endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Application and detector health |
| `GET` | `/api/activity` | Recent in-memory activity for this process |
| `GET` | `/docs` | Interactive OpenAPI documentation |

Uploads are limited to 10 MB and are discarded after inference. Recent activity contains metadata only and resets when the server restarts.

## Development

```bash
ruff check .
pytest -q
```

## Architecture

```text
Browser (Jinja UI + JavaScript canvas)
                    │ multipart image
                    ▼
          FastAPI validation layer
                    │ in-memory bytes
                    ▼
       OpenCV Haar cascade detector
                    │ bounding boxes only
                    ▼
          JSON response + canvas overlay
```

Sightline deliberately performs detection rather than recognition. It does not create embeddings, match identities, or maintain a biometric database.
