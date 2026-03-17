"""CLI entry point for the demo."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .io import load_records, write_json, write_payloads
from .processor import transform_records


def build_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("lis_analyzer_demo.validation")
    logger.setLevel(logging.ERROR)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform analyzer results into LIS-ready payloads.")
    parser.add_argument("input", help="Path to a CSV or JSON analyzer result file.")
    parser.add_argument(
        "--output",
        default="output/transformed_results.json",
        help="Where to write the transformed payload JSON.",
    )
    parser.add_argument(
        "--log",
        default="output/validation.log",
        help="Where to write validation errors.",
    )
    parser.add_argument(
        "--errors-json",
        default="output/validation_errors.json",
        help="Where to write structured validation errors.",
    )
    parser.add_argument(
        "--summary",
        default="output/processing_summary.json",
        help="Where to write the processing summary report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output)
    log_path = Path(args.log)
    errors_path = Path(args.errors_json)
    summary_path = Path(args.summary)

    try:
        logger = build_logger(log_path)
        records = load_records(args.input)
        payloads, errors, summary = transform_records(records, logger)
        write_payloads(output_path, payloads)
        write_json(errors_path, errors)
        write_json(summary_path, summary)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for handler in logger.handlers:
        handler.close()

    print(
        f"Processed {summary['total_records']} records, produced {summary['validated_records']} payloads, "
        f"logged {summary['validation_error_count']} validation errors."
    )
    print(f"Payloads: {output_path}")
    print(f"Validation log: {log_path}")
    print(f"Validation errors JSON: {errors_path}")
    print(f"Summary report: {summary_path}")
    return 0
