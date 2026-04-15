# Face Recognition Service with DevOps + MLOps

Production-focused starter project for a **Face Recognition API** with:

- FastAPI service for image enrollment and matching
- SQLite embedding storage
- Docker image for local/prod use
- CI/CD with GitHub Actions (test, build, push, deploy)
- Terraform for AWS EC2 + security group
- Monitoring with Prometheus metrics + alert rules
- Optional Kubernetes manifests for next-level deployment

## 1) Core AI Service

### API endpoints
- `POST /api/v1/faces/enroll` → enroll reference face
- `POST /api/v1/faces/match` → compare image with enrolled user
- `GET /health` → liveness check
- `GET /metrics` → Prometheus metrics

### How matching works
This repo ships with a lightweight baseline embedder (`SimpleFaceEmbedder`) that:
- decodes an image,
- normalizes/resizes to fixed dimensions,
- creates a deterministic vector embedding,
- compares with cosine similarity.

> Swap this class with FaceNet/ArcFace for production-grade biometric accuracy.

## 2) Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs: http://localhost:8000/docs

## 3) Run tests

```bash
pytest -q
```

## 4) Docker

```bash
docker build -t face-recognition-service:local .
docker run -p 8000:8000 face-recognition-service:local
```

## 5) CI/CD (GitHub Actions)
Pipeline file: `.github/workflows/ci-cd.yml`

Stages:
1. Lint + unit tests
2. Build Docker image
3. Push to Docker Hub (main branch)
4. Deploy to EC2 via SSH (main branch)

Required GitHub secrets:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`

## 6) Infrastructure (Terraform)
Terraform folder: `infra/terraform`

Creates:
- VPC + subnet references (default VPC data lookup)
- Security group (SSH + app port)
- EC2 instance

Usage:

```bash
cd infra/terraform
terraform init
terraform apply -var="public_key_path=~/.ssh/id_rsa.pub"
```

## 7) Monitoring + Alerts
- App exposes Prometheus metrics at `/metrics`
- `monitoring/prometheus-alerts.yml` includes sample high-failure-rate alert
- Structured app logging configured in `app/logging_config.py`

## 8) Kubernetes upgrade path
Manifests under `k8s/`:
- Deployment
- Service
- HPA

Apply:

```bash
kubectl apply -f k8s/
```

---

## Suggested next improvements
- Replace baseline embedder with ArcFace/FaceNet
- Add object storage (S3) for image retention
- Add PostgreSQL + pgvector for large-scale vector search
- Add model registry + drift detection for full MLOps
