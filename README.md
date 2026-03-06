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

## Docker

Build the image:

```bash
docker build -t mylab-backend .
```

Run it on a server:

```bash
docker run -d \
  --name mylab-backend \
  -p 8000:8000 \
  -e MYLAB_DEMO_EMAIL=demo@mylab.app \
  -e MYLAB_DEMO_PASSWORD=demo123 \
  -e MYLAB_DEMO_TOKEN=demo-token \
  mylab-backend
```

The container serves the API on `0.0.0.0:8000` by default.

Useful environment variables:

- `MYLAB_HOST`
- `MYLAB_PORT`
- `MYLAB_DEMO_EMAIL`
- `MYLAB_DEMO_PASSWORD`
- `MYLAB_DEMO_TOKEN`

If you want to run the published image from GitHub Container Registry instead of building locally:

```bash
docker run -d \
  --name mylab-backend \
  -p 8000:8000 \
  ghcr.io/tgrytnes/mylab-backend:backend-v0.1.0
```

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
