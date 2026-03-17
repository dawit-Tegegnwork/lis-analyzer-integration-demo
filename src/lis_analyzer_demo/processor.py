"""Transform analyzer records into LIS-ready payloads."""

from __future__ import annotations

import logging
from typing import Iterable

from .reference import TEST_CATALOG


def classify_result(value: float, low: float, high: float) -> str:
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "normal"


def _normalized_value(record: dict, *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None:
            text = str(value).strip()
            if text:
                return text
    return ""


def transform_records(records: Iterable[dict], logger: logging.Logger) -> tuple[list[dict], list[str]]:
    transformed: list[dict] = []
    errors: list[str] = []

    for index, record in enumerate(records, start=1):
        sample_id = _normalized_value(record, "sample_id", "specimen_id")
        analyzer_code = _normalized_value(record, "analyzer_code", "machine_code", "test_code")
        instrument_id = _normalized_value(record, "instrument_id", "analyzer_id") or "UNKNOWN-INSTRUMENT"
        captured_at = _normalized_value(record, "captured_at", "timestamp") or "UNKNOWN-TIMESTAMP"
        raw_value = _normalized_value(record, "result_value", "value")
        input_unit = _normalized_value(record, "unit")

        if not sample_id:
            message = f"Row {index}: missing sample_id."
            logger.error(message)
            errors.append(message)
            continue

        mapping = TEST_CATALOG.get(analyzer_code)
        if mapping is None:
            message = f"Sample {sample_id}: unknown analyzer code '{analyzer_code}'."
            logger.error(message)
            errors.append(message)
            continue

        try:
            numeric_value = float(raw_value)
        except ValueError:
            message = f"Sample {sample_id}: non-numeric result '{raw_value}' for {analyzer_code}."
            logger.error(message)
            errors.append(message)
            continue

        low = mapping["range"]["low"]
        high = mapping["range"]["high"]
        abnormal_flag = classify_result(numeric_value, low, high)

        transformed.append(
            {
                "sample_id": sample_id,
                "lis_test_code": mapping["lis_test_code"],
                "lis_test_name": mapping["lis_test_name"],
                "analyzer_code": analyzer_code,
                "instrument_id": instrument_id,
                "captured_at": captured_at,
                "result": {
                    "value": numeric_value,
                    "unit": input_unit or mapping["unit"],
                    "reference_range": {"low": low, "high": high},
                    "abnormal_flag": abnormal_flag,
                },
                "status": "validated",
                "source": "synthetic-demo",
            }
        )

    return transformed, errors
