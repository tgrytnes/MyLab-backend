from copy import deepcopy

_RESULTS = [
    {
        "id": "blood-test-2026-03-12",
        "title": "Blood Test",
        "date": "2026-03-12",
        "status": "normal",
        "summary": "All values normal",
        "is_new": False,
        "explanation": "Your complete blood count is within the expected range.",
        "recommended_action": "No action needed.",
        "report_url": "/reports/blood-test-2026-03-12.pdf",
        "values": [
            {
                "name": "Hemoglobin",
                "value": 14.1,
                "unit": "g/dL",
                "reference_range": "12.0 - 16.0",
                "min": 12.0,
                "max": 16.0,
                "status": "normal",
            },
            {
                "name": "White Blood Cells",
                "value": 6.2,
                "unit": "x10^9/L",
                "reference_range": "4.0 - 11.0",
                "min": 4.0,
                "max": 11.0,
                "status": "normal",
            },
        ],
    },
    {
        "id": "vitamin-d-2026-03-10",
        "title": "Vitamin D",
        "date": "2026-03-10",
        "status": "attention",
        "summary": "Slightly low",
        "is_new": True,
        "explanation": (
            "Your vitamin D is slightly below the usual range. "
            "This is common during darker months."
        ),
        "recommended_action": "Consider discussing a supplement with your doctor.",
        "report_url": "/reports/vitamin-d-2026-03-10.pdf",
        "values": [
            {
                "name": "Vitamin D",
                "value": 22,
                "unit": "ng/mL",
                "reference_range": "30 - 100",
                "min": 30,
                "max": 100,
                "status": "attention",
            }
        ],
    },
    {
        "id": "cholesterol-2026-03-05",
        "title": "Cholesterol",
        "date": "2026-03-05",
        "status": "normal",
        "summary": "Optimal",
        "is_new": False,
        "explanation": "Your cholesterol profile looks balanced overall.",
        "recommended_action": "Maintain your current lifestyle.",
        "report_url": "/reports/cholesterol-2026-03-05.pdf",
        "values": [
            {
                "name": "LDL",
                "value": 110,
                "unit": "mg/dL",
                "reference_range": "0 - 130",
                "min": 0,
                "max": 130,
                "status": "normal",
            },
            {
                "name": "HDL",
                "value": 65,
                "unit": "mg/dL",
                "reference_range": "40 - 90",
                "min": 40,
                "max": 90,
                "status": "normal",
            },
            {
                "name": "Triglycerides",
                "value": 120,
                "unit": "mg/dL",
                "reference_range": "0 - 150",
                "min": 0,
                "max": 150,
                "status": "normal",
            },
        ],
    },
    {
        "id": "thyroid-2026-02-28",
        "title": "Thyroid Panel",
        "date": "2026-02-28",
        "status": "normal",
        "summary": "Stable",
        "is_new": False,
        "explanation": "Your thyroid markers are within the expected range.",
        "recommended_action": "No action needed.",
        "report_url": None,
        "values": [
            {
                "name": "TSH",
                "value": 2.1,
                "unit": "mIU/L",
                "reference_range": "0.4 - 4.0",
                "min": 0.4,
                "max": 4.0,
                "status": "normal",
            }
        ],
    },
    {
        "id": "glucose-2026-02-20",
        "title": "Glucose",
        "date": "2026-02-20",
        "status": "attention",
        "summary": "Borderline elevated",
        "is_new": False,
        "explanation": "Your fasting glucose is slightly above the usual range.",
        "recommended_action": "Wait for physician review and keep an eye on diet.",
        "report_url": None,
        "values": [
            {
                "name": "Fasting Glucose",
                "value": 103,
                "unit": "mg/dL",
                "reference_range": "70 - 99",
                "min": 70,
                "max": 99,
                "status": "attention",
            }
        ],
    },
]


def get_results() -> list[dict]:
    return deepcopy(_RESULTS)
