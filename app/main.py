from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.demo_data import get_results

app = FastAPI(title="MyLab Demo API", version="0.1.0")

_results = get_results()


class LoginRequest(BaseModel):
    email: str
    password: str


class ReadRequest(BaseModel):
    is_read: bool = True


def _require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    if authorization != f"Bearer {settings.demo_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    if (
        payload.email != settings.demo_email
        or payload.password != settings.demo_password
    ):
        raise HTTPException(status_code=401, detail="Invalid demo credentials")

    return {"token": settings.demo_token}


@app.get("/me")
def me(_: None = Depends(_require_auth)) -> dict[str, str]:
    return {"id": "patient-demo", "first_name": "Thomas", "last_name": "Demo"}


@app.get("/results")
def list_results(_: None = Depends(_require_auth)) -> dict[str, list[dict]]:
    return {"results": _results}


@app.get("/results/{result_id}")
def result_detail(result_id: str, _: None = Depends(_require_auth)) -> dict:
    for result in _results:
        if result["id"] == result_id:
            return result

    raise HTTPException(status_code=404, detail="Result not found")


@app.post("/results/{result_id}/read")
def mark_result_as_read(
    result_id: str,
    payload: ReadRequest,
    _: None = Depends(_require_auth),
) -> dict:
    for result in _results:
        if result["id"] == result_id:
            result["is_new"] = not payload.is_read
            return {"id": result_id, "is_new": result["is_new"]}

    raise HTTPException(status_code=404, detail="Result not found")
