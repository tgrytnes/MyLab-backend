from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from app.config import settings


def _load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_demo_data() -> tuple[dict[str, dict], dict[str, dict]]:
    data_dir = Path(settings.data_dir)
    patients = {
        patient["id"]: patient for patient in _load_json(data_dir / "patients.json")
    }
    results = {}

    for result_path in sorted((data_dir / "results").glob("*.json")):
        result = _load_json(result_path)
        results[result["id"]] = result

    return deepcopy(patients), deepcopy(results)
