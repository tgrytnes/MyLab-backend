from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

AUTH_HEADER = {"Authorization": "Bearer demo-token"}


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success() -> None:
    response = client.post(
        "/login",
        json={"email": "demo@mylab.app", "password": "demo123"},
    )

    assert response.status_code == 200
    assert response.json() == {"token": "demo-token"}


def test_login_failure() -> None:
    response = client.post(
        "/login",
        json={"email": "demo@mylab.app", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid demo credentials"


def test_results_require_auth() -> None:
    response = client.get("/results")

    assert response.status_code == 401


def test_results_list() -> None:
    response = client.get("/results", headers=AUTH_HEADER)

    body = response.json()
    assert response.status_code == 200
    assert len(body["results"]) >= 5
    assert any(result["is_new"] for result in body["results"])


def test_result_detail() -> None:
    response = client.get("/results/vitamin-d-2026-03-10", headers=AUTH_HEADER)

    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "Vitamin D"
    assert body["values"][0]["status"] == "attention"


def test_mark_result_as_read() -> None:
    response = client.post(
        "/results/vitamin-d-2026-03-10/read",
        headers=AUTH_HEADER,
        json={"is_read": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "vitamin-d-2026-03-10",
        "is_new": False,
    }
