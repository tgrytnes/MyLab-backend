from __future__ import annotations

from copy import deepcopy
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.demo_data import load_demo_data
from app.reporting import build_report_pdf

app = FastAPI(title="MyLab Demo API", version="0.1.0")

_patients_by_id, _results_by_id = load_demo_data()
_patients_by_email = {
    patient["email"]: patient for patient in _patients_by_id.values()
}
_patients_by_token = {
    patient["token"]: patient for patient in _patients_by_id.values()
}


class LoginRequest(BaseModel):
    email: str
    password: str


class ReadRequest(BaseModel):
    is_read: bool = True


def _patient_results(patient: dict) -> list[dict]:
    result_ids = patient["result_ids"]
    patient_results = [deepcopy(_results_by_id[result_id]) for result_id in result_ids]
    patient_results.sort(key=lambda result: result["date"], reverse=True)
    return patient_results


def _current_patient(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.removeprefix("Bearer ").strip()
    patient = _patients_by_token.get(token)
    if patient is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return patient


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/demo-accounts")
def demo_accounts() -> dict[str, list[dict[str, str]]]:
    accounts = [
        {
            "id": patient["id"],
            "first_name": patient["first_name"],
            "last_name": patient["last_name"],
            "email": patient["email"],
            "password": patient["password"],
        }
        for patient in sorted(_patients_by_id.values(), key=lambda item: item["first_name"])
    ]
    return {"accounts": accounts}


@app.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    patient = _patients_by_email.get(payload.email)
    if patient is None or payload.password != patient["password"]:
        raise HTTPException(status_code=401, detail="Invalid demo credentials")

    return {"token": patient["token"]}


@app.get("/me")
def me(patient: dict = Depends(_current_patient)) -> dict[str, str]:
    return {
        "id": patient["id"],
        "first_name": patient["first_name"],
        "last_name": patient["last_name"],
    }


@app.get("/results")
def list_results(patient: dict = Depends(_current_patient)) -> dict[str, list[dict]]:
    return {"results": _patient_results(patient)}


@app.get("/results/{result_id}")
def result_detail(result_id: str, patient: dict = Depends(_current_patient)) -> dict:
    if result_id not in patient["result_ids"]:
        raise HTTPException(status_code=404, detail="Result not found")

    return deepcopy(_results_by_id[result_id])


@app.post("/results/{result_id}/read")
def mark_result_as_read(
    result_id: str,
    payload: ReadRequest,
    patient: dict = Depends(_current_patient),
) -> dict:
    if result_id not in patient["result_ids"]:
        raise HTTPException(status_code=404, detail="Result not found")

    _results_by_id[result_id]["is_new"] = not payload.is_read
    return {
        "id": result_id,
        "is_new": _results_by_id[result_id]["is_new"],
    }


@app.get("/reports/{report_name}")
def report_pdf(report_name: str, patient: dict = Depends(_current_patient)) -> Response:
    for result_id in patient["result_ids"]:
        result = _results_by_id[result_id]
        report_url = result.get("report_url")
        if report_url and report_url.endswith(report_name):
            pdf_bytes = build_report_pdf(patient, result)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'inline; filename="{report_name}"',
                },
            )

    raise HTTPException(status_code=404, detail="Report not found")
