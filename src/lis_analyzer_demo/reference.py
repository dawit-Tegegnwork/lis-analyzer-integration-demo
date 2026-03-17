"""Reference mappings for the demo integration."""

from __future__ import annotations

TEST_CATALOG = {
    "GLU_FAST": {
        "lis_test_code": "GLU",
        "lis_test_name": "Glucose",
        "unit": "mg/dL",
        "range": {"low": 70.0, "high": 110.0},
    },
    "HGB_WB": {
        "lis_test_code": "HGB",
        "lis_test_name": "Hemoglobin",
        "unit": "g/dL",
        "range": {"low": 12.0, "high": 17.5},
    },
    "WBC_DIFF": {
        "lis_test_code": "WBC",
        "lis_test_name": "White Blood Cell Count",
        "unit": "x10^3/uL",
        "range": {"low": 4.0, "high": 11.0},
    },
    "CRP_SERUM": {
        "lis_test_code": "CRP",
        "lis_test_name": "C-Reactive Protein",
        "unit": "mg/L",
        "range": {"low": 0.0, "high": 5.0},
    },
}
