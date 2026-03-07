from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EMMA_AUTH_HEADER = {"Authorization": "Bearer demo-token-emma"}
LIAM_AUTH_HEADER = {"Authorization": "Bearer demo-token-liam"}


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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


def test_result_files_exist() -> None:
    results_dir = Path(__file__).resolve().parent.parent / "data" / "results"
    assert len(list(results_dir.glob("*.json"))) == 20


def test_login_success() -> None:
    response = client.post(
        "/login",
        json={"email": "emma.lawson@mylab.demo", "password": "demo-emma"},
    )

    assert response.status_code == 200
    assert response.json() == {"token": "demo-token-emma"}


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
    assert len(body["results"]) == 5
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
