# Webapp — CV Site Analytics

Flask backend для аналитики посещений CV-сайта.

## Stack
- Python 3.11 (Flask 3.0.0)
- psycopg2-binary (PostgreSQL driver)
- Kubernetes (K3S) Deployment
- Docker (non-root user)

## API Endpoints
- `POST /api/visit` — record a visit (IP + User-Agent)
- `GET /api/stats` — JSON statistics
- `GET /stats` — HTML page with stats
- `GET /health` — health check (used by K8S probes)

## Structure
- `src/` — application source
  - `app.py` — Flask application
  - `requirements.txt` — Python dependencies
  - `Dockerfile` — container image (Python 3.11-slim, non-root user)
- `k8s/` — Kubernetes manifests
  - `01-secret.yaml` — DB credentials (gitignored)
  - `01-secret.example.yaml` — template
  - `02-configmap.yaml` — DB host/port/name
  - `03-deployment.yaml` — Deployment with probes
  - `04-service.yaml` — ClusterIP Service

## Deploy

Build image:
\`\`\`bash
docker build -t webapp:latest src/
docker save webapp:latest -o /tmp/webapp.tar
sudo k3s ctr images import /tmp/webapp.tar
\`\`\`

Apply manifests:
\`\`\`bash
cp k8s/01-secret.example.yaml k8s/01-secret.yaml
# Edit k8s/01-secret.yaml with real credentials
kubectl apply -f k8s/
\`\`\`

## Dependencies
- PostgreSQL must be running (see `../postgres/`)
- Table `visits` must exist in `myappdb`
