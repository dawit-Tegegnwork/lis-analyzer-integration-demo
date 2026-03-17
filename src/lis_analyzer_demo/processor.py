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


def _append_error(
    *,
    errors: list[dict],
    logger: logging.Logger,
    row_number: int,
    sample_id: str,
    analyzer_code: str,
    error_code: str,
    message: str,
) -> None:
    error = {
        "row_number": row_number,
        "sample_id": sample_id or None,
        "analyzer_code": analyzer_code or None,
        "error_code": error_code,
        "message": message,
    }
    errors.append(error)
    logger.error("row=%s code=%s message=%s", row_number, error_code, message)


def transform_records(records: Iterable[dict], logger: logging.Logger) -> tuple[list[dict], list[dict], dict]:
    transformed: list[dict] = []
    errors: list[dict] = []
    seen_result_keys: set[tuple[str, str]] = set()
    total_records = 0

    for index, record in enumerate(records, start=1):
        total_records += 1
        sample_id = _normalized_value(record, "sample_id", "specimen_id")
        analyzer_code = _normalized_value(record, "analyzer_code", "machine_code", "test_code")
        instrument_id = _normalized_value(record, "instrument_id", "analyzer_id") or "UNKNOWN-INSTRUMENT"
        captured_at = _normalized_value(record, "captured_at", "timestamp") or "UNKNOWN-TIMESTAMP"
        raw_value = _normalized_value(record, "result_value", "value")
        input_unit = _normalized_value(record, "unit")

        if not sample_id:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="missing_sample_id",
                message="Missing sample_id.",
            )
            continue

        if not analyzer_code:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="missing_analyzer_code",
                message=f"Sample {sample_id}: missing analyzer code.",
            )
            continue

        if not raw_value:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="missing_result_value",
                message=f"Sample {sample_id}: missing result value for {analyzer_code}.",
            )
            continue

        mapping = TEST_CATALOG.get(analyzer_code)
        if mapping is None:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="unknown_analyzer_code",
                message=f"Sample {sample_id}: unknown analyzer code '{analyzer_code}'.",
            )
            continue

        try:
            numeric_value = float(raw_value)
        except ValueError:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="non_numeric_result",
                message=f"Sample {sample_id}: non-numeric result '{raw_value}' for {analyzer_code}.",
            )
            continue

        expected_unit = mapping["unit"]
        if input_unit and input_unit != expected_unit:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="unit_mismatch",
                message=(
                    f"Sample {sample_id}: unit mismatch for {analyzer_code}. "
                    f"Expected {expected_unit}, received {input_unit}."
                ),
            )
            continue

        low = mapping["range"]["low"]
        high = mapping["range"]["high"]
        abnormal_flag = classify_result(numeric_value, low, high)
        lis_test_code = mapping["lis_test_code"]
        unique_result_key = (sample_id, lis_test_code)

        if unique_result_key in seen_result_keys:
            _append_error(
                errors=errors,
                logger=logger,
                row_number=index,
                sample_id=sample_id,
                analyzer_code=analyzer_code,
                error_code="duplicate_result",
                message=f"Sample {sample_id}: duplicate result for LIS test {lis_test_code}.",
            )
            continue

        seen_result_keys.add(unique_result_key)

        transformed.append(
            {
                "sample_id": sample_id,
                "lis_test_code": lis_test_code,
                "lis_test_name": mapping["lis_test_name"],
                "analyzer_code": analyzer_code,
                "instrument_id": instrument_id,
                "captured_at": captured_at,
                "result": {
                    "value": numeric_value,
                    "unit": input_unit or expected_unit,
                    "reference_range": {"low": low, "high": high},
                    "abnormal_flag": abnormal_flag,
                },
                "status": "validated",
                "source": "synthetic-demo",
            }
        )

    summary = {
        "total_records": total_records,
        "validated_records": len(transformed),
        "validation_error_count": len(errors),
        "accepted_rate": round(len(transformed) / total_records, 2) if total_records else 0.0,
    }

    return transformed, errors, summary
