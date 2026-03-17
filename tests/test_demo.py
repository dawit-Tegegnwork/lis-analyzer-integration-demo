from __future__ import annotations

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lis_analyzer_demo.cli import build_logger
from lis_analyzer_demo.io import load_records
from lis_analyzer_demo.processor import classify_result, transform_records


class DemoTests(unittest.TestCase):
    def test_load_records_accepts_results_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "results.json"
            source.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "sample_id": "SYN-9001",
                                "analyzer_code": "GLU_FAST",
                                "result_value": 101.2,
                                "unit": "mg/dL",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            records = load_records(source)

        self.assertEqual(records[0]["sample_id"], "SYN-9001")

    def test_transform_records_maps_and_flags_values(self) -> None:
        logger = logging.getLogger("test-transform")
        logger.handlers.clear()
        logger.addHandler(logging.NullHandler())

        payloads, errors = transform_records(
            [
                {
                    "sample_id": "SYN-1001",
                    "analyzer_code": "GLU_FAST",
                    "result_value": "132.4",
                    "unit": "mg/dL",
                    "instrument_id": "CHEM-01",
                    "captured_at": "2026-03-17T09:05:00Z",
                }
            ],
            logger,
        )

        self.assertEqual(errors, [])
        self.assertEqual(payloads[0]["lis_test_code"], "GLU")
        self.assertEqual(payloads[0]["result"]["abnormal_flag"], "high")

    def test_transform_records_logs_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "validation.log"
            logger = build_logger(log_path)
            payloads, errors = transform_records(
                [
                    {
                        "sample_id": "SYN-4001",
                        "analyzer_code": "UNKNOWN_CODE",
                        "result_value": "18",
                    },
                    {
                        "sample_id": "",
                        "analyzer_code": "GLU_FAST",
                        "result_value": "90",
                    },
                    {
                        "sample_id": "SYN-4003",
                        "analyzer_code": "CRP_SERUM",
                        "result_value": "bad",
                    },
                ],
                logger,
            )
            log_text = log_path.read_text(encoding="utf-8")

        self.assertEqual(payloads, [])
        self.assertEqual(len(errors), 3)
        self.assertIn("unknown analyzer code", log_text)
        self.assertIn("missing sample_id", log_text)
        self.assertIn("non-numeric result", log_text)

    def test_classify_result(self) -> None:
        self.assertEqual(classify_result(65, 70, 110), "low")
        self.assertEqual(classify_result(90, 70, 110), "normal")
        self.assertEqual(classify_result(140, 70, 110), "high")


if __name__ == "__main__":
    unittest.main()
