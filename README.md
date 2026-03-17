# LIS Analyzer Integration Demo

Public-safe portfolio demo that simulates a small LIS-to-analyzer integration flow using synthetic laboratory data only.

[![Tests](https://github.com/dawit-Tegegnwork/lis-analyzer-integration-demo/actions/workflows/test.yml/badge.svg)](https://github.com/dawit-Tegegnwork/lis-analyzer-integration-demo/actions/workflows/test.yml)

## Overview

This repository shows the basic mechanics of a laboratory integration workflow:

- load analyzer output from CSV or JSON
- map machine codes to LIS-facing test codes
- validate identifiers, units, duplicate results, and numeric values
- flag abnormal results against simple reference thresholds
- emit normalized payloads plus validation artifacts

It is intentionally small and synthetic. The goal is to show integration thinking clearly, not to imitate a full middleware product.

## Quick Demo

Run the demo against the bundled CSV sample:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools
python -m pip install -e .

lis-analyzer-demo samples/input/analyzer_results.csv \
  --output samples/output/transformed_results.json \
  --log samples/output/validation.log \
  --errors-json samples/output/validation_errors.json \
  --summary samples/output/processing_summary.json
```

Expected result:

- `7` source records processed
- `3` normalized payloads accepted
- `4` validation errors written to log and JSON

## Demo Artifacts

- [Sample CSV input](samples/input/analyzer_results.csv)
- [Sample JSON input](samples/input/analyzer_results.json)
- [Normalized LIS-ready payloads](samples/output/transformed_results.json)
- [Validation log](samples/output/validation.log)
- [Structured validation errors](samples/output/validation_errors.json)
- [Processing summary](samples/output/processing_summary.json)

## What The Demo Covers

- CSV and JSON ingestion
- machine-code to LIS-code mapping
- reference-range flagging for low and high values
- hard rejection of unit mismatches
- structured validation for:
  - unknown analyzer codes
  - missing sample identifiers
  - missing result values
  - non-numeric results
  - duplicate sample/test combinations

## Processing Flow

1. Load analyzer rows from CSV or JSON.
2. Normalize field names into a consistent input contract.
3. Validate required identifiers and result values.
4. Map analyzer machine codes to LIS test metadata.
5. Reject invalid rows and log the reason.
6. Write accepted rows as normalized LIS-ready payloads.
7. Write a summary and structured validation report.

## Input Contract

Accepted fields:

- `sample_id` or `specimen_id`
- `analyzer_code`, `machine_code`, or `test_code`
- `result_value` or `value`
- optional `unit`
- optional `instrument_id` or `analyzer_id`
- optional `captured_at` or `timestamp`

## Example Output

Normalized payload:

```json
[
  {
    "sample_id": "SYN-1001",
    "lis_test_code": "GLU",
    "lis_test_name": "Glucose",
    "analyzer_code": "GLU_FAST",
    "instrument_id": "CHEM-01",
    "captured_at": "2026-03-17T09:05:00Z",
    "result": {
      "value": 132.4,
      "unit": "mg/dL",
      "reference_range": {
        "low": 70.0,
        "high": 110.0
      },
      "abnormal_flag": "high"
    },
    "status": "validated",
    "source": "synthetic-demo"
  }
]
```

Validation log excerpt:

```text
ERROR row=4 code=non_numeric_result message=Sample SYN-1004: non-numeric result 'bad_value' for CRP_SERUM.
ERROR row=5 code=missing_sample_id message=Missing sample_id.
ERROR row=6 code=unknown_analyzer_code message=Sample SYN-1005: unknown analyzer code 'XYZ_PANEL'.
ERROR row=7 code=unit_mismatch message=Sample SYN-1006: unit mismatch for GLU_FAST. Expected mg/dL, received mmol/L.
```

Summary report:

```json
{
  "total_records": 7,
  "validated_records": 3,
  "validation_error_count": 4,
  "accepted_rate": 0.43
}
```

## Project Layout

```text
.
├── .github/workflows/test.yml
├── LICENSE
├── pyproject.toml
├── samples
│   ├── input
│   └── output
├── src/lis_analyzer_demo
│   ├── cli.py
│   ├── io.py
│   ├── processor.py
│   └── reference.py
└── tests/test_demo.py
```

## Tests

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Why This Repo Is Public-Safe

- all sample data is synthetic
- no patient-identifiable information is included
- no vendor credentials or private endpoints are used
- mappings and thresholds are simplified for demonstration

## Scope Notes

This is a demo repository, not a production LIS integration engine. It does not include:

- HL7 or ASTM messaging
- instrument drivers
- queueing or retry infrastructure
- persistence layers
- authentication or multi-tenant concerns
