# Development and testing guide

## 1. Prerequisites

- Git
- Python 3.14 or newer
- pip
- Optional: Docker Engine and Docker Compose v2
- A modern browser; camera capture requires camera permission and normally HTTPS outside localhost

## 2. Clone and enter the project

```bash
git clone https://github.com/Rohitkr2510/face-recognition-devops.git
cd face-recognition-devops
```

## 3. Python environment

Always use a project virtual environment. It isolates Sightline dependencies from system Python and other projects.

### Windows PowerShell

```powershell
py -V:3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Windows Git Bash

Create the environment with the Windows Python launcher from PowerShell first, or run an explicit Python 3.14 executable. Activate it in Git Bash with:

```bash
source .venv/Scripts/activate
python --version
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Do not run `.venv/Scripts/Activate.ps1` in Git Bash; that file contains PowerShell syntax.

### Linux or macOS

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## 4. Start locally

```bash
uvicorn app.main:app --reload
```

Useful URLs:

- Application: <http://localhost:8000>
- Health: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

`--reload` is for development. It monitors source files and restarts the server when they change; do not use it as a production setting.

## 5. Run quality checks

```bash
ruff check .
pytest -q
```

To see individual test names:

```bash
pytest -v
```

To run one test:

```bash
pytest tests/test_app.py::test_detects_valid_image -v
```

## 6. Existing test coverage

| Test | Verifies |
|---|---|
| `test_dashboard_renders` | `/` returns HTML containing key interface text |
| `test_health_reports_model_state` | Classifier loads and `/health` reports ready |
| `test_detects_valid_image` | A generated valid PNG returns dimensions and zero faces |
| `test_rejects_unsupported_content_type` | Text input returns `415` |
| `test_rejects_invalid_image_data` | Fake PNG bytes return `400` |

The test image is created in memory, so tests do not need a fixture image or write uploads to disk.

## 7. Recommended additional tests

The current suite is a useful baseline but does not cover every branch. Add tests for:

- Empty upload returns `400`.
- An upload over 10 MiB returns `413`.
- JPEG and WebP success paths.
- A known face fixture returns at least one correctly bounded face.
- Classifier loading failure produces degraded health.
- Response schema types and coordinate bounds.
- Static assets return successfully.
- Browser behavior with an end-to-end tool such as Playwright.
- Container health check after `docker compose up`.
- Basic load/concurrency behavior and memory limits.

Avoid using real personal photos as committed fixtures unless consent and licensing are clear. A synthetic or appropriately licensed fixture is safer.

## 8. Ruff configuration

Ruff targets Python 3.14 and enables:

| Rule family | Purpose |
|---|---|
| `E` | pycodestyle errors |
| `F` | Pyflakes correctness checks |
| `I` | Import ordering |
| `UP` | Modern Python syntax upgrades |
| `B` | Common bug-risk patterns |

The configured maximum line length is 100 characters.

## 9. Manual API checks

### Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"healthy","model":"ready"}
```

### Valid image

```bash
curl -X POST http://localhost:8000/api/detect \
  -F "file=@portrait.jpg"
```

### Unsupported media type

```bash
curl -i -X POST http://localhost:8000/api/detect \
  -F "file=@notes.txt;type=text/plain"
```

Expected status: `415 Unsupported Media Type`.

## 10. Docker development

```bash
docker compose up --build
```

Inspect state and logs:

```bash
docker compose ps
docker compose logs -f sightline
```

Stop the service:

```bash
docker compose down
```

Compose does not mount the source directory, so application changes require rebuilding the image.

## 11. Common problems

### `python` shows an old version on Windows

Create the environment explicitly:

```powershell
py -V:3.14 -m venv .venv
```

Then activate it. The active virtual environment should make `python --version` report Python 3.14.x.

### PowerShell blocks activation

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Run this only if permitted by your organization's security policy.

### Git Bash reports an error for `Activate.ps1`

Use the Bash activation script:

```bash
source .venv/Scripts/activate
```

### OpenCV package installation fails

Confirm Python is 3.14 and pip is current:

```bash
python --version
python -m pip install --upgrade pip
```

Then recreate `.venv` rather than mixing packages from another Python version.

### Camera does not open

- Allow camera access in the browser.
- Test on `localhost` or serve through HTTPS.
- Confirm another application is not exclusively using the camera.
- Upload a file to verify that the backend works independently of camera access.

### Container is unhealthy

```bash
docker compose ps
docker compose logs sightline
docker inspect --format '{{json .State.Health}}' face-recognition-devops-sightline-1
```

Container names can differ by Compose project name; use `docker compose ps` to find the actual name.

