import hashlib
import hmac
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PATIENT_REQUIRED_FIELDS = {
    "id",
    "first_name",
    "last_name",
    "email",
    "birth_date",
    "password",
    "token",
    "result_ids",
}

RESULT_REQUIRED_FIELDS = {
    "id",
    "patient_id",
    "title",
    "date",
    "status",
    "summary",
    "is_new",
    "explanation",
    "recommended_action",
    "report_url",
    "values",
}

VALUE_REQUIRED_FIELDS = {
    "name",
    "value",
    "unit",
    "reference_range",
    "min",
    "max",
    "status",
}


@dataclass
class UploadOutcome:
    filename: str
    kind: str
    status: str
    message: str
    preview: str
    records: int


class DemoRepository:
    def __init__(
        self,
        data_dir: Path,
        *,
        qr_secret: str = "mylab-demo-qr-secret",
        mobile_scheme: str = "mylab",
    ) -> None:
        self.data_dir = data_dir
        self.results_dir = self.data_dir / "results"
        self.qr_secret = qr_secret.encode("utf-8")
        self.mobile_scheme = mobile_scheme
        self.reload()

    def reload(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        patients = self._load_json(self.data_dir / "patients.json")
        normalized_patients = [self._validated_patient(patient) for patient in patients]
        if normalized_patients != patients:
            self._write_json(self.data_dir / "patients.json", normalized_patients)

        self.patients_by_id = {patient["id"]: patient for patient in normalized_patients}
        self.results_by_id = {}

        for result_path in sorted(self.results_dir.glob("*.json")):
            result = self._load_json(result_path)
            self.results_by_id[result["id"]] = result

        self.patients_by_email = {
            patient["email"]: patient for patient in self.patients_by_id.values()
        }
        self.patients_by_token = {
            patient["token"]: patient for patient in self.patients_by_id.values()
        }
        self.patients_by_access_code = {
            patient["access_code"]: patient for patient in self.patients_by_id.values()
        }

    def _load_json(self, path: Path) -> dict | list:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, payload: dict | list) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")

    def list_demo_accounts(self) -> list[dict[str, str]]:
        return [
            {
                "id": patient["id"],
                "first_name": patient["first_name"],
                "last_name": patient["last_name"],
                "email": patient["email"],
                "password": patient["password"],
            }
            for patient in sorted(self.patients_by_id.values(), key=lambda item: item["first_name"])
        ]

    def list_demo_access_shortcuts(self) -> list[dict[str, str]]:
        return [
            {
                "id": patient["id"],
                "first_name": patient["first_name"],
                "last_name": patient["last_name"],
                "access_code": patient["access_code"],
                "birth_date": patient["birth_date"],
            }
            for patient in sorted(self.patients_by_id.values(), key=lambda item: item["first_name"])
        ]

    def patient_by_email(self, email: str) -> dict | None:
        return self.patients_by_email.get(email)

    def patient_by_token(self, token: str) -> dict | None:
        return self.patients_by_token.get(token)

    def patient_by_access_code(self, access_code: str) -> dict | None:
        patient = self.patients_by_access_code.get(access_code)
        return deepcopy(patient) if patient is not None else None

    def patient_by_id(self, patient_id: str) -> dict | None:
        patient = self.patients_by_id.get(patient_id)
        return deepcopy(patient) if patient is not None else None

    def result_by_id(self, result_id: str) -> dict | None:
        result = self.results_by_id.get(result_id)
        return deepcopy(result) if result is not None else None

    def access_link(self, patient: dict) -> str:
        return f"{self.mobile_scheme}://access?code={patient['access_code']}"

    def patient_results(self, patient: dict) -> list[dict]:
        result_ids = patient["result_ids"]
        patient_results = [deepcopy(self.results_by_id[result_id]) for result_id in result_ids]
        patient_results.sort(key=lambda result: result["date"], reverse=True)
        return patient_results

    def result_for_patient(self, patient: dict, result_id: str) -> dict | None:
        if result_id not in patient["result_ids"]:
            return None
        result = self.results_by_id.get(result_id)
        return deepcopy(result) if result is not None else None

    def mark_result_as_read(self, patient: dict, result_id: str, is_read: bool) -> dict | None:
        if result_id not in patient["result_ids"]:
            return None

        result = self.results_by_id.get(result_id)
        if result is None:
            return None

        result["is_new"] = not is_read
        self._write_json(self.results_dir / f"{result_id}.json", result)
        return {"id": result_id, "is_new": result["is_new"]}

    def stats(self) -> dict[str, int]:
        status_counts = {
            "patients": len(self.patients_by_id),
            "results": len(self.results_by_id),
            "new_results": sum(1 for result in self.results_by_id.values() if result["is_new"]),
            "critical_results": sum(
                1 for result in self.results_by_id.values() if result["status"] == "critical"
            ),
        }
        return status_counts

    def patient_cards(self) -> list[dict]:
        cards = []
        for patient in sorted(self.patients_by_id.values(), key=lambda item: item["first_name"]):
            patient_results = self.patient_results(patient)
            cards.append(
                {
                    "id": patient["id"],
                    "name": f"{patient['first_name']} {patient['last_name']}",
                    "email": patient["email"],
                    "results": len(patient_results),
                    "new_results": sum(1 for result in patient_results if result["is_new"]),
                }
            )
        return cards

    def result_browser(self) -> list[dict]:
        items = []
        sorted_results = sorted(
            self.results_by_id.values(),
            key=lambda item: item["date"],
            reverse=True,
        )
        for result in sorted_results:
            patient = self.patients_by_id.get(result["patient_id"], {})
            patient_name = (
                f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            )
            items.append(
                {
                    "id": result["id"],
                    "title": result["title"],
                    "date": result["date"],
                    "status": result["status"],
                    "patient_name": patient_name,
                }
            )
        return items

    def preview_document(self, kind: str, identifier: str) -> tuple[str, str] | None:
        if kind == "patient":
            payload = self.patients_by_id.get(identifier)
        else:
            payload = self.results_by_id.get(identifier)

        if payload is None:
            return None

        title = payload["id"] if kind == "patient" else payload["title"]
        return title, json.dumps(payload, indent=2)

    def process_uploads(self, uploads: list[tuple[str, bytes]]) -> list[UploadOutcome]:
        outcomes: list[UploadOutcome] = []

        for filename, file_bytes in uploads:
            try:
                payload = json.loads(file_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                outcomes.append(
                    UploadOutcome(
                        filename=filename,
                        kind="invalid",
                        status="error",
                        message=f"Invalid JSON: {exc}",
                        preview=file_bytes.decode("utf-8", errors="replace"),
                        records=0,
                    )
                )
                continue

            try:
                kind, records = self._persist_payload(payload)
                preview = json.dumps(payload, indent=2)
                outcomes.append(
                    UploadOutcome(
                        filename=filename,
                        kind=kind,
                        status="success",
                        message=f"Accepted {records} {kind} record{'s' if records != 1 else ''}.",
                        preview=preview,
                        records=records,
                    )
                )
            except ValueError as exc:
                outcomes.append(
                    UploadOutcome(
                        filename=filename,
                        kind="invalid",
                        status="error",
                        message=str(exc),
                        preview=json.dumps(payload, indent=2),
                        records=0,
                    )
                )

        self.reload()
        return outcomes

    def _persist_payload(self, payload: dict | list) -> tuple[str, int]:
        if isinstance(payload, list):
            if not payload:
                raise ValueError("JSON arrays cannot be empty.")

            if all(self._is_patient_record(item) for item in payload):
                patients = [self._validated_patient(item) for item in payload]
                self._write_json(self.data_dir / "patients.json", patients)
                return "patient", len(patients)

            if all(self._is_result_record(item) for item in payload):
                results = [self._validated_result(item) for item in payload]
                for result in results:
                    self._upsert_result(result)
                return "result", len(results)

            raise ValueError("JSON array must contain only patient records or only result records.")

        if self._is_patient_record(payload):
            patient = self._validated_patient(payload)
            self._upsert_patient(patient)
            return "patient", 1

        if self._is_result_record(payload):
            result = self._validated_result(payload)
            self._upsert_result(result)
            return "result", 1

        raise ValueError("JSON must match a patient record or a result record schema.")

    def _upsert_patient(self, patient: dict) -> None:
        patients = list(self.patients_by_id.values())
        for index, existing in enumerate(patients):
            if existing["id"] == patient["id"]:
                patients[index] = patient
                break
        else:
            patients.append(patient)

        patients.sort(key=lambda item: item["first_name"])
        self._write_json(self.data_dir / "patients.json", patients)

    def _upsert_result(self, result: dict) -> None:
        patient = self.patients_by_id.get(result["patient_id"])
        if patient is None:
            raise ValueError(
                f"Unknown patient_id '{result['patient_id']}' "
                f"for result '{result['id']}'."
            )

        self._write_json(self.results_dir / f"{result['id']}.json", result)
        result_ids = list(patient["result_ids"])
        if result["id"] not in result_ids:
            result_ids.append(result["id"])
            patient["result_ids"] = sorted(result_ids, reverse=True)
            self._upsert_patient(patient)

    def _is_patient_record(self, payload: object) -> bool:
        return isinstance(payload, dict) and PATIENT_REQUIRED_FIELDS.issubset(payload.keys())

    def _is_result_record(self, payload: object) -> bool:
        return isinstance(payload, dict) and RESULT_REQUIRED_FIELDS.issubset(payload.keys())

    def _validated_patient(self, patient: dict) -> dict:
        missing = PATIENT_REQUIRED_FIELDS - patient.keys()
        if missing:
            raise ValueError(f"Patient record is missing fields: {', '.join(sorted(missing))}.")

        if not isinstance(patient["result_ids"], list):
            raise ValueError("Patient field 'result_ids' must be a list.")

        try:
            date.fromisoformat(str(patient["birth_date"]))
        except ValueError as exc:
            raise ValueError(
                "Patient field 'birth_date' must be an ISO date in YYYY-MM-DD format."
            ) from exc

        normalized = deepcopy(patient)
        access_code = str(normalized.get("access_code", "")).strip()
        if not access_code:
            normalized["access_code"] = self._generate_access_code(normalized)
        return normalized

    def _validated_result(self, result: dict) -> dict:
        missing = RESULT_REQUIRED_FIELDS - result.keys()
        if missing:
            raise ValueError(f"Result record is missing fields: {', '.join(sorted(missing))}.")

        values = result.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("Result field 'values' must be a non-empty list.")

        for value in values:
            if not isinstance(value, dict):
                raise ValueError("Every result value must be a JSON object.")
            missing_value_fields = VALUE_REQUIRED_FIELDS - value.keys()
            if missing_value_fields:
                raise ValueError(
                    "Result value is missing fields: "
                    f"{', '.join(sorted(missing_value_fields))}."
                )

        return deepcopy(result)

    def _generate_access_code(self, patient: dict) -> str:
        payload = "::".join(
            [
                patient["id"],
                patient["birth_date"],
                patient["email"],
            ]
        )
        digest = hmac.new(self.qr_secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return digest[:20]
