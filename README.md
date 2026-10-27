# Platform DevOps Hackathon

Private backup of Platform DevOps hackathon deliverables: a Python web service taken from source through CI, containers, Kubernetes manifests, and Helm deployment.

## Stack

- App: Python HTTP service (`/hello`, `/live`, `/ready`, `/central`)
- CI: GitLab CI (shared Platform component pipeline)
- Runtime: Docker + Kubernetes
- Packaging: Helm chart (`deploy/`) wrapping the platform `app-chart`
- Quality: `pytest`, `ruff`

## Layout

| Path | Purpose |
|---|---|
| `app/` | Application source |
| `tests/` | Unit tests |
| `Dockerfile` | Container image |
| `manifests/` | Kubernetes objects |
| `deploy/` | Helm chart values |
| `.gitlab-ci.yml` | CI entrypoint |
| `Makefile` | Local helpers |

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8080` | HTTP port |
| `STARTUP_DELAY_SECONDS` | `40` | Warm-up window |
| `REQUEST_THRESHOLD` | `10` | `/hello` calls before readiness fails |
| `NOT_READY_SECONDS` | `30` | Readiness failure duration |
| `GREETING` | `Hello from Platform` | `/hello` text |
| `PARTICIPANT` | `anonymous` | Participant id |
| `APP_SECRET` | empty | Demo secret; only fingerprint exposed |
| `CENTRAL_SERVICE_URL` | empty | Central check-in URL |

## Local development

```bash
make install
make test
make run STARTUP_DELAY_SECONDS=0
make docker-build && make docker-run && make smoke && make docker-stop
```

## Notes

- Image pull credentials and deploy tokens are not stored here.
- `manifests/secret.yaml` and Helm `APP_SECRET` use placeholder demo values only.
- Chart dependency archives under `deploy/charts/` are omitted on purpose.
