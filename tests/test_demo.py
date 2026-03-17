from __future__ import annotations

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lis_analyzer_demo.cli import build_logger, main
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

        payloads, errors, summary = transform_records(
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
        self.assertEqual(summary["validated_records"], 1)

    def test_transform_records_logs_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "validation.log"
            logger = build_logger(log_path)
            payloads, errors, summary = transform_records(
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
                    {
                        "sample_id": "SYN-4004",
                        "analyzer_code": "GLU_FAST",
                        "result_value": "99",
                        "unit": "mmol/L",
                    },
                    {
                        "sample_id": "SYN-4005",
                        "analyzer_code": "",
                        "result_value": "18",
                    },
                    {
                        "sample_id": "SYN-4006",
                        "analyzer_code": "GLU_FAST",
                        "result_value": "",
                    },
                    {
                        "sample_id": "SYN-4007",
                        "analyzer_code": "GLU_FAST",
                        "result_value": "93",
                    },
                    {
                        "sample_id": "SYN-4007",
                        "analyzer_code": "GLU_FAST",
                        "result_value": "95",
                    },
                ],
                logger,
            )
            log_text = log_path.read_text(encoding="utf-8")

        self.assertEqual(len(payloads), 1)
        self.assertEqual(len(errors), 7)
        self.assertEqual(summary["validation_error_count"], 7)
        self.assertEqual(errors[0]["error_code"], "unknown_analyzer_code")
        self.assertIn("unknown analyzer code", log_text)
        self.assertIn("Missing sample_id", log_text)
        self.assertIn("non-numeric result", log_text)
        self.assertIn("unit mismatch", log_text)
        self.assertIn("missing analyzer code", log_text)
        self.assertIn("missing result value", log_text)
        self.assertIn("duplicate result", log_text)

    def test_classify_result(self) -> None:
        self.assertEqual(classify_result(65, 70, 110), "low")
        self.assertEqual(classify_result(90, 70, 110), "normal")
        self.assertEqual(classify_result(140, 70, 110), "high")

    def test_cli_writes_all_expected_outputs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / "payloads.json"
            log_path = temp_dir_path / "validation.log"
            errors_path = temp_dir_path / "validation_errors.json"
            summary_path = temp_dir_path / "summary.json"

            exit_code = main(
                [
                    str(repo_root / "samples" / "input" / "analyzer_results.csv"),
                    "--output",
                    str(output_path),
                    "--log",
                    str(log_path),
                    "--errors-json",
                    str(errors_path),
                    "--summary",
                    str(summary_path),
                ]
            )

            payloads = json.loads(output_path.read_text(encoding="utf-8"))
            errors = json.loads(errors_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payloads), 3)
        self.assertEqual(len(errors), 4)
        self.assertEqual(summary["total_records"], 7)
        self.assertEqual(summary["validated_records"], 3)

    def test_cli_returns_non_zero_for_unsupported_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_input = Path(temp_dir) / "bad.txt"
            bad_input.write_text("not supported", encoding="utf-8")

            exit_code = main([str(bad_input)])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
