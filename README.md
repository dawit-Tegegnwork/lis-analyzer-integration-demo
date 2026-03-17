# LIS Analyzer Integration Demo

Public-safe portfolio demo that simulates a simple LIS to analyzer integration workflow using synthetic data only.

## What it does

- Reads analyzer result files in CSV or JSON
- Maps analyzer machine codes to LIS test codes and names
- Flags low and high values using basic reference thresholds
- Logs validation errors for unknown codes, missing identifiers, and invalid numbers
- Produces normalized JSON payloads ready for an LIS ingestion layer
- Includes sample inputs, sample outputs, and automated tests

## Project layout

```text
.
├── pyproject.toml
├── samples
│   ├── input
│   │   ├── analyzer_results.csv
│   │   └── analyzer_results.json
│   └── output
│       ├── transformed_results.json
│       └── validation.log
├── src
│   └── lis_analyzer_demo
│       ├── cli.py
│       ├── io.py
│       ├── processor.py
│       └── reference.py
└── tests
    └── test_demo.py
```

## Quick start

Run the demo against the CSV sample:

```bash
cd ~/career-engine/lis-analyzer-integration-demo
PYTHONPATH=src python -m lis_analyzer_demo samples/input/analyzer_results.csv \
  --output samples/output/transformed_results.json \
  --log samples/output/validation.log
```

Run the tests:

```bash
cd ~/career-engine/lis-analyzer-integration-demo
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Sample input

CSV:

```csv
sample_id,analyzer_code,result_value,unit,instrument_id,captured_at
SYN-1001,GLU_FAST,132.4,mg/dL,CHEM-01,2026-03-17T09:05:00Z
SYN-1002,HGB_WB,11.2,g/dL,HEM-02,2026-03-17T09:07:00Z
```

JSON:

```json
[
  {
    "sample_id": "SYN-2001",
    "analyzer_code": "GLU_FAST",
    "result_value": 98.1,
    "unit": "mg/dL"
  }
]
```

## Sample output

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

Validation errors are written to `samples/output/validation.log`:

```text
ERROR Sample SYN-1004: non-numeric result 'bad_value' for CRP_SERUM.
ERROR Row 5: missing sample_id.
ERROR Sample SYN-1005: unknown analyzer code 'XYZ_PANEL'.
```

## Public-safe notes

- All files use synthetic sample IDs and non-sensitive results
- No confidential or patient data is included
- Thresholds and test mappings are simplified for demo purposes
