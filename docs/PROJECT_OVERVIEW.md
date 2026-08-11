# Sightline project overview

## 1. Purpose

Sightline is a privacy-focused web application and HTTP API that detects frontal faces in an uploaded image. It returns face locations as rectangular coordinates; it does not identify a person, compare identities, create embeddings, or retain uploaded images.

The repository currently represents a small, stateless, single-service application suitable for local development, demonstrations, CI validation, and container-based deployment experiments.

## 2. Functional scope

### Included

- Upload JPEG, PNG, or WebP images through a browser.
- Capture a still image through the browser camera API.
- Validate media type, file size, and image decodability.
- Detect frontal faces with OpenCV's Haar cascade classifier.
- Return image dimensions, face count, processing time, and bounding boxes.
- Draw the returned bounding boxes in an HTML canvas.
- Expose OpenAPI documentation through FastAPI.
- Report application/model health.
- Run locally with Python or in a Docker container.
- Validate changes with Ruff, pytest, and a Docker build in GitHub Actions.

### Not included

- Face recognition or identity matching.
- User accounts, authentication, authorization, or sessions.
- A database, object storage, queues, caches, or persistent image history.
- Metrics, distributed tracing, centralized logging, alerts, or dashboards.
- TLS termination, a reverse proxy, autoscaling, or a production deployment manifest.
- A container registry push or automated deployment stage.

## 3. Technology stack

| Area | Technology | Responsibility |
|---|---|---|
| Runtime | Python 3.14+ | Runs the application and detection code |
| Web framework | FastAPI | Routing, request validation, HTTP responses, and OpenAPI |
| Application server | Uvicorn | ASGI server listening on port 8000 |
| Templates | Jinja2 | Renders the main HTML page |
| Browser code | HTML, CSS, JavaScript | Upload/camera UI, API calls, and canvas overlays |
| Computer vision | OpenCV headless | Image decoding, preprocessing, and face detection |
| Numerical arrays | NumPy | Converts uploaded bytes into an OpenCV-compatible buffer |
| Tests | pytest, FastAPI TestClient, HTTPX | Endpoint and validation tests |
| Linting | Ruff | Style, import, upgrade, bug-risk, and error checks |
| Packaging | `pyproject.toml` and pip | Metadata and dependency installation |
| Containerization | Docker | Reproducible application image |
| Local orchestration | Docker Compose | Container startup, port mapping, restart, and health check |
| CI | GitHub Actions | Lint, test, and container build validation |

## 4. Repository map

```text
.
├── .github/workflows/ci.yml       # CI test and container-build jobs
├── app/
│   ├── detector.py                # OpenCV detection domain logic
│   ├── main.py                    # FastAPI app, routes, and validation
│   ├── static/
│   │   ├── app.js                 # Browser state, camera, upload, and drawing
│   │   └── styles.css             # Responsive user-interface styling
│   └── templates/index.html       # Server-rendered page structure
├── docs/                           # Project and operational documentation
├── tests/test_app.py              # API and UI smoke tests
├── .dockerignore                  # Excludes development files from build context
├── .gitignore                     # Excludes local/generated files from Git
├── Dockerfile                     # Production-style runtime image definition
├── docker-compose.yml             # Local container service definition
├── pyproject.toml                 # Package, dependencies, pytest, and Ruff config
└── README.md                      # Entry point and quick start
```

## 5. Application interfaces

| Method | Path | Input | Success result | Failure examples |
|---|---|---|---|---|
| `GET` | `/` | None | HTML application | Template/static-file configuration error |
| `GET` | `/health` | None | `200` JSON with app and model state | Currently returns degraded JSON if classifier loading fails |
| `POST` | `/api/detect` | Multipart field named `file` | `200` detection JSON | `400` empty/invalid image, `413` over 10 MiB, `415` unsupported media type |
| `GET` | `/docs` | None | Swagger UI | Framework-generated |
| `GET` | `/openapi.json` | None | OpenAPI schema | Framework-generated |
| `GET` | `/static/*` | Static path | CSS or JavaScript | `404` when absent |

### Detection request

```bash
curl -X POST http://localhost:8000/api/detect \
  -F "file=@portrait.jpg"
```

### Detection response

```json
{
  "image": {"width": 1200, "height": 800},
  "faces": [
    {"x": 412, "y": 176, "width": 220, "height": 220, "confidence": 0.9}
  ],
  "face_count": 1,
  "processing_ms": 42.7
}
```

Coordinate `(x, y)` is the upper-left corner of a detected box. Width and height are in pixels relative to the original decoded image. The browser scales these values to the displayed image dimensions.

> Important: the current `confidence` value is always `0.9`. OpenCV's `detectMultiScale` call does not produce this value in the current implementation, so it must not be interpreted as a calibrated probability.

## 6. Validation rules

The API applies these checks in order:

1. `Content-Type` must be `image/jpeg`, `image/png`, or `image/webp`.
2. The server reads at most 10 MiB plus one byte.
3. More than 10 MiB returns HTTP `413`.
4. An empty body returns HTTP `400`.
5. OpenCV must successfully decode the bytes; otherwise HTTP `400` is returned.
6. Valid bytes are converted to grayscale, histogram-equalized, and scanned.

Content type alone is not trusted as proof of a valid image; OpenCV decoding provides the second validation layer.

## 7. Configuration

The application currently has no environment-variable configuration. Important values are defined in source or deployment files:

| Setting | Current value | Location |
|---|---:|---|
| Maximum upload | 10 MiB | `app/main.py` |
| Allowed media types | JPEG, PNG, WebP | `app/main.py` |
| Runtime port | 8000 | `Dockerfile`, `docker-compose.yml` |
| Cascade scale factor | 1.1 | `app/detector.py` |
| Minimum neighbors | 5 | `app/detector.py` |
| Minimum face size | 40 × 40 px | `app/detector.py` |
| Container restart | `unless-stopped` | `docker-compose.yml` |
| Health interval | 30 seconds | `docker-compose.yml` |

For a production service, values such as upload limits, logging level, workers, and allowed origins should become validated configuration.

## 8. Privacy and data lifecycle

Uploaded data is read into process memory, decoded into an in-memory NumPy/OpenCV array, analyzed, and then becomes eligible for garbage collection after the request completes. The application does not intentionally write source images to disk or a database.

The browser creates a temporary object URL for local preview and revokes the previous URL when another image is processed. Camera tracks are stopped when the camera dialog closes.

This design reduces retention but does not, by itself, constitute a complete privacy or compliance guarantee. Infrastructure access logs, reverse proxies, crash dumps, browser behavior, and hosting-platform telemetry must also be reviewed in a real deployment.

## 9. Current limitations

- Haar cascades can miss rotated, partially hidden, small, poorly lit, or non-frontal faces and can produce false positives.
- Detection is synchronous and CPU-bound inside the application process.
- Multiple simultaneous large requests can increase memory and response time.
- There is no explicit request timeout, concurrency limit, or rate limit.
- Health reports classifier availability but does not test an end-to-end detection.
- The UI relies on Google Fonts, so font loading makes an external network request.
- Camera access generally requires a secure context (`HTTPS`) except on localhost.
- The CI pipeline validates a build but does not scan, sign, publish, or deploy the image.
- Dependencies use bounded ranges rather than a lock file, reducing exact reproducibility.

