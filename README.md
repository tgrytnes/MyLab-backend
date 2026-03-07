# MyLab Backend

FastAPI backend for the MyLab weekend demo. It serves realistic lab-result JSON for a patient-facing Flutter app.

## Endpoints

- `GET /admin`
- `GET /admin/patients/{id}/qr.png`
- `GET /demo-accounts`
- `POST /login`
- `POST /access/exchange`
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

Admin console:

```bash
open http://127.0.0.1:8000/admin
```

The admin console provides a polished web interface for uploading patient/result JSON, reviewing the live dataset immediately after upload, and generating a patient-specific QR code that opens the mobile app access flow.

Patient JSON must include:

- `id`
- `first_name`
- `last_name`
- `email`
- `birth_date` in `YYYY-MM-DD`
- `password`
- `token`
- `result_ids`

The backend generates an `access_code` automatically if the uploaded patient JSON does not contain one already.

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
- `MYLAB_MOBILE_SCHEME`
- `MYLAB_QR_SECRET`

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

## QR Access Flow

- Select a patient in `/admin`
- Open or download the generated QR image
- The QR points to `mylab://access?code=...`
- The Flutter app opens, asks for birth date, exchanges the QR access code through `POST /access/exchange`, and then loads all results linked to that patient profile

## CI/CD

- `ci.yml` runs Ruff and pytest on pushes and pull requests.
- `publish-image.yml` builds a Docker image and publishes it to GHCR on version tags.
