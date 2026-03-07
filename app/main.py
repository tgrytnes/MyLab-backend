from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.qr_codes import build_qr_png
from app.reporting import build_report_pdf
from app.repository import DemoRepository, UploadOutcome

app = FastAPI(title="MyLab Demo API", version="0.1.0")

app_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(app_dir / "templates"))
app.mount("/admin/static", StaticFiles(directory=str(app_dir / "static")), name="admin_static")

repository = DemoRepository(
    Path(settings.data_dir),
    qr_secret=settings.qr_secret,
    mobile_scheme=settings.mobile_scheme,
)


class LoginRequest(BaseModel):
    email: str
    password: str


class ReadRequest(BaseModel):
    is_read: bool = True


class AccessExchangeRequest(BaseModel):
    code: str
    birth_date: str


def _session_payload(patient: dict) -> dict[str, object]:
    return {
        "token": patient["token"],
        "patient": {
            "id": patient["id"],
            "first_name": patient["first_name"],
            "last_name": patient["last_name"],
        },
    }


def _current_patient(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.removeprefix("Bearer ").strip()
    patient = repository.patient_by_token(token)
    if patient is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return patient


def _admin_context(
    request: Request,
    *,
    upload_results: list[UploadOutcome] | None = None,
    preview_kind: str | None = None,
    preview_id: str | None = None,
) -> dict:
    patient_cards = repository.patient_cards()
    result_browser = repository.result_browser()

    preview = None
    chosen_kind = preview_kind
    chosen_id = preview_id
    selected_patient = None
    selected_result = None
    selected_patient_results: list[dict] = []
    selected_patient_access_link = None

    if chosen_kind and chosen_id:
        preview = repository.preview_document(chosen_kind, chosen_id)
    elif result_browser:
        chosen_kind = "result"
        chosen_id = result_browser[0]["id"]
        preview = repository.preview_document(chosen_kind, chosen_id)
    elif patient_cards:
        chosen_kind = "patient"
        chosen_id = patient_cards[0]["id"]
        preview = repository.preview_document(chosen_kind, chosen_id)

    if chosen_kind == "patient" and chosen_id:
        selected_patient = repository.patient_by_id(chosen_id)
    elif chosen_kind == "result" and chosen_id:
        selected_result = repository.result_by_id(chosen_id)
        if selected_result is not None:
            selected_patient = repository.patient_by_id(selected_result["patient_id"])

    if selected_patient is not None:
        selected_patient_results = repository.patient_results(selected_patient)
        selected_patient_access_link = repository.access_link(selected_patient)

    return {
        "request": request,
        "stats": repository.stats(),
        "patient_cards": patient_cards,
        "result_browser": result_browser,
        "selected_patient": selected_patient,
        "selected_result": selected_result,
        "selected_patient_results": selected_patient_results,
        "selected_patient_access_link": selected_patient_access_link,
        "preview_kind": chosen_kind,
        "preview_id": chosen_id,
        "preview": preview,
        "upload_results": upload_results or [],
    }


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
def admin_console(
    request: Request,
    kind: str | None = None,
    identifier: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_console.html",
        _admin_context(request, preview_kind=kind, preview_id=identifier),
    )


@app.post("/admin/upload", response_class=HTMLResponse)
async def admin_upload(
    request: Request,
    files: list[UploadFile] = File(...),
) -> HTMLResponse:
    uploads = []
    for file in files:
        filename = file.filename or "upload.json"
        payload = await file.read()
        uploads.append((filename, payload))

    upload_results = repository.process_uploads(uploads)
    return templates.TemplateResponse(
        request,
        "admin_console.html",
        _admin_context(request, upload_results=upload_results),
    )


@app.post("/admin/save-document", response_class=HTMLResponse)
async def admin_save_document(
    request: Request,
    kind: str = Form(...),
    identifier: str = Form(...),
    document_text: str = Form(...),
) -> HTMLResponse:
    try:
        saved_kind, saved_identifier, payload = repository.save_document(
            kind,
            identifier,
            document_text,
        )
        save_results = [
            UploadOutcome(
                filename=f"{saved_identifier}.json",
                kind=saved_kind,
                status="success",
                message=f"Saved {saved_kind} '{saved_identifier}' successfully.",
                preview=json.dumps(payload, indent=2),
                records=1,
            )
        ]
        preview_kind = saved_kind
        preview_id = saved_identifier
    except ValueError as exc:
        save_results = [
            UploadOutcome(
                filename=f"{identifier}.json",
                kind=kind,
                status="error",
                message=str(exc),
                preview=document_text,
                records=0,
            )
        ]
        preview_kind = kind
        preview_id = identifier

    return templates.TemplateResponse(
        request,
        "admin_console.html",
        _admin_context(
            request,
            upload_results=save_results,
            preview_kind=preview_kind,
            preview_id=preview_id,
        ),
    )


@app.get("/admin/patients/{patient_id}/qr.png")
def admin_patient_qr(patient_id: str) -> Response:
    patient = repository.patient_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return Response(
        content=build_qr_png(repository.access_link(patient)),
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{patient_id}-access.png"',
        },
    )


@app.get("/demo-accounts")
def demo_accounts() -> dict[str, list[dict[str, str]]]:
    return {"accounts": repository.list_demo_accounts()}


@app.get("/demo-access-shortcuts")
def demo_access_shortcuts() -> dict[str, list[dict[str, str]]]:
    return {"shortcuts": repository.list_demo_access_shortcuts()}


@app.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    patient = repository.patient_by_email(payload.email)
    if patient is None or payload.password != patient["password"]:
        raise HTTPException(status_code=401, detail="Invalid demo credentials")

    return {"token": patient["token"]}


@app.post("/access/exchange")
def access_exchange(payload: AccessExchangeRequest) -> dict[str, object]:
    patient = repository.patient_by_access_code(payload.code)
    if patient is None or patient["birth_date"] != payload.birth_date:
        raise HTTPException(status_code=401, detail="Birth date did not match this access code")

    return _session_payload(patient)


@app.get("/me")
def me(patient: dict = Depends(_current_patient)) -> dict[str, str]:
    return {
        "id": patient["id"],
        "first_name": patient["first_name"],
        "last_name": patient["last_name"],
    }


@app.get("/results")
def list_results(patient: dict = Depends(_current_patient)) -> dict[str, list[dict]]:
    return {"results": repository.patient_results(patient)}


@app.get("/results/{result_id}")
def result_detail(result_id: str, patient: dict = Depends(_current_patient)) -> dict:
    result = repository.result_for_patient(patient, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")

    return result


@app.get("/events")
def list_events(
    since: str | None = Query(default=None),
    patient: dict = Depends(_current_patient),
) -> dict[str, list[dict]]:
    since_dt = None
    if since is not None:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid 'since' timestamp") from exc

    return {"events": repository.patient_events(patient, since_dt)}


@app.post("/results/{result_id}/read")
def mark_result_as_read(
    result_id: str,
    payload: ReadRequest,
    patient: dict = Depends(_current_patient),
) -> dict:
    result = repository.mark_result_as_read(patient, result_id, payload.is_read)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")

    return result


@app.get("/reports/{report_name}")
def report_pdf(report_name: str, patient: dict = Depends(_current_patient)) -> Response:
    for result_id in patient["result_ids"]:
        result = repository.result_for_patient(patient, result_id)
        if result is None:
            continue
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
