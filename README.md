# MyLab Backend

FastAPI backend for the MyLab weekend demo. It serves realistic lab-result JSON for a patient-facing Flutter app.

## Endpoints

- `POST /login`
- `GET /me`
- `GET /results`
- `GET /results/{id}`
- `POST /results/{id}/read`
- `GET /health`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API will start on `http://127.0.0.1:8000`.

## Test And Lint

```bash
python3 -m pytest
python3 -m ruff check .
```

## Demo Credentials

- Email: `demo@mylab.app`
- Password: `demo123`

## CI/CD

- `ci.yml` runs Ruff and pytest on pushes and pull requests.
- `publish-image.yml` builds a Docker image and publishes it to GHCR on version tags.
