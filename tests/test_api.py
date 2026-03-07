import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.repository import DemoRepository

client = TestClient(app)

EMMA_AUTH_HEADER = {"Authorization": "Bearer demo-token-emma"}
LIAM_AUTH_HEADER = {"Authorization": "Bearer demo-token-liam"}


@pytest.fixture(autouse=True)
def isolated_repository(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> DemoRepository:
    source_data_dir = Path(__file__).resolve().parent.parent / "data"
    temp_data_dir = tmp_path / "data"
    shutil.copytree(source_data_dir, temp_data_dir)
    repository = DemoRepository(temp_data_dir)
    monkeypatch.setattr(main_module, "repository", repository)
    return repository


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_console_renders() -> None:
    response = client.get("/admin")

    assert response.status_code == 200
    assert "MyLab Admin Console" in response.text
    assert "Upload JSON" in response.text
    assert "Mobile Access QR" in response.text


def test_demo_accounts() -> None:
    response = client.get("/demo-accounts")

    body = response.json()
    assert response.status_code == 200
    assert len(body["accounts"]) == 6
    assert {account["first_name"] for account in body["accounts"]} == {
        "Ava",
        "Ben",
        "Emma",
        "Liam",
        "Noah",
        "Sophia",
    }


def test_demo_access_shortcuts() -> None:
    response = client.get("/demo-access-shortcuts")

    body = response.json()
    assert response.status_code == 200
    assert len(body["shortcuts"]) == 6
    assert all(shortcut["access_code"] for shortcut in body["shortcuts"])
    assert all(shortcut["birth_date"] for shortcut in body["shortcuts"])


def test_result_files_exist() -> None:
    results_dir = Path(__file__).resolve().parent.parent / "data" / "results"
    assert len(list(results_dir.glob("*.json"))) == 24


def test_login_success() -> None:
    response = client.post(
        "/login",
        json={"email": "emma.lawson@mylab.demo", "password": "demo-emma"},
    )

    assert response.status_code == 200
    assert response.json() == {"token": "demo-token-emma"}


def test_access_exchange_success(isolated_repository: DemoRepository) -> None:
    emma = isolated_repository.patient_by_id("patient-emma-lawson")
    assert emma is not None

    response = client.post(
        "/access/exchange",
        json={"code": emma["access_code"], "birth_date": emma["birth_date"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "token": "demo-token-emma",
        "patient": {
            "id": "patient-emma-lawson",
            "first_name": "Emma",
            "last_name": "Lawson",
        },
    }


def test_access_exchange_rejects_wrong_birth_date(isolated_repository: DemoRepository) -> None:
    emma = isolated_repository.patient_by_id("patient-emma-lawson")
    assert emma is not None

    response = client.post(
        "/access/exchange",
        json={"code": emma["access_code"], "birth_date": "2000-01-01"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Birth date did not match this access code"


def test_login_failure() -> None:
    response = client.post(
        "/login",
        json={"email": "emma.lawson@mylab.demo", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid demo credentials"


def test_results_require_auth() -> None:
    response = client.get("/results")

    assert response.status_code == 401


def test_me_returns_current_patient() -> None:
    response = client.get("/me", headers=EMMA_AUTH_HEADER)

    assert response.status_code == 200
    assert response.json() == {
        "id": "patient-emma-lawson",
        "first_name": "Emma",
        "last_name": "Lawson",
    }


def test_results_list_is_patient_specific() -> None:
    response = client.get("/results", headers=EMMA_AUTH_HEADER)

    body = response.json()
    assert response.status_code == 200
    assert len(body["results"]) == 7
    assert any(result["is_new"] for result in body["results"])
    assert all(result["patient_id"] == "patient-emma-lawson" for result in body["results"])


def test_result_detail_is_patient_scoped() -> None:
    response = client.get(
        "/results/emma-vitamin-d-2026-03-01",
        headers=EMMA_AUTH_HEADER,
    )

    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "Vitamin D"
    assert body["values"][0]["status"] == "attention"


def test_other_patient_result_is_hidden() -> None:
    response = client.get(
        "/results/emma-vitamin-d-2026-03-01",
        headers=LIAM_AUTH_HEADER,
    )

    assert response.status_code == 404


def test_mark_result_as_read() -> None:
    response = client.post(
        "/results/emma-vitamin-d-2026-03-01/read",
        headers=EMMA_AUTH_HEADER,
        json={"is_read": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "emma-vitamin-d-2026-03-01",
        "is_new": False,
    }


def test_report_pdf_is_available_for_own_result() -> None:
    response = client.get(
        "/reports/emma-vitamin-d-2026-03-01.pdf",
        headers=EMMA_AUTH_HEADER,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_report_pdf_is_not_available_for_other_patient() -> None:
    response = client.get(
        "/reports/emma-vitamin-d-2026-03-01.pdf",
        headers=LIAM_AUTH_HEADER,
    )

    assert response.status_code == 404


def test_admin_patient_qr_is_available(isolated_repository: DemoRepository) -> None:
    emma = isolated_repository.patient_by_id("patient-emma-lawson")
    assert emma is not None

    response = client.get(f"/admin/patients/{emma['id']}/qr.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_admin_upload_result_json(isolated_repository: DemoRepository) -> None:
    payload = {
        "id": "emma-magnesium-2026-03-07",
        "patient_id": "patient-emma-lawson",
        "title": "Magnesium",
        "date": "2026-03-07",
        "status": "normal",
        "summary": "Magnesium is in range",
        "is_new": True,
        "explanation": "Your magnesium is within the expected range.",
        "recommended_action": "No action needed.",
        "report_url": None,
        "values": [
            {
                "name": "Magnesium",
                "value": 1.9,
                "unit": "mg/dL",
                "reference_range": "1.7 - 2.2",
                "min": 1.7,
                "max": 2.2,
                "status": "normal",
            }
        ],
    }

    response = client.post(
        "/admin/upload",
        files={
            "files": (
                "emma-magnesium.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 200
    assert "Accepted 1 result record" in response.text
    assert "emma-magnesium-2026-03-07" in response.text
    assert (isolated_repository.results_dir / "emma-magnesium-2026-03-07.json").exists()


def test_admin_upload_invalid_json_shows_error(isolated_repository: DemoRepository) -> None:
    response = client.post(
        "/admin/upload",
        files={
            "files": (
                "broken.json",
                b"{ this is not valid json",
                "application/json",
            )
        },
    )

    assert response.status_code == 200
    assert "Invalid JSON" in response.text


def test_uploaded_patient_gets_access_code(isolated_repository: DemoRepository) -> None:
    payload = {
        "id": "patient-isla-ross",
        "first_name": "Isla",
        "last_name": "Ross",
        "email": "isla.ross@mylab.demo",
        "birth_date": "1990-06-17",
        "password": "demo-isla",
        "token": "demo-token-isla",
        "result_ids": [],
    }

    response = client.post(
        "/admin/upload",
        files={
            "files": (
                "isla-ross.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    saved_patient = isolated_repository.patient_by_id("patient-isla-ross")
    assert response.status_code == 200
    assert saved_patient is not None
    assert saved_patient["birth_date"] == "1990-06-17"
    assert saved_patient["access_code"]
