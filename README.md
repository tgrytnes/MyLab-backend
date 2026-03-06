# MyLab Backend

FastAPI backend for the MyLab weekend demo. It serves realistic lab-result JSON for a patient-facing Flutter app.

## Endpoints

- `GET /demo-accounts`
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
  mylab-backend
```

The container serves the API on `0.0.0.0:8000` by default.

Useful environment variables:

- `MYLAB_HOST`
- `MYLAB_PORT`
- `MYLAB_DATA_DIR`

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

- Emma Lawson: `emma.lawson@mylab.demo` / `demo-emma`
- Liam Carter: `liam.carter@mylab.demo` / `demo-liam`
- Sophia Nguyen: `sophia.nguyen@mylab.demo` / `demo-sophia`
- Noah Fischer: `noah.fischer@mylab.demo` / `demo-noah`
- Ava Martinez: `ava.martinez@mylab.demo` / `demo-ava`
- Ben Weber: `ben.weber@mylab.demo` / `demo-ben`

The demo data is stored in `data/patients.json` and `data/results/*.json`.

## CI/CD

- `ci.yml` runs Ruff and pytest on pushes and pull requests.
- `publish-image.yml` builds a Docker image and publishes it to GHCR on version tags.
