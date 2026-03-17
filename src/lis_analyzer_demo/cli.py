"""CLI entry point for the demo."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .io import load_records, write_payloads
from .processor import transform_records


def build_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("lis_analyzer_demo.validation")
    logger.setLevel(logging.ERROR)
    logger.handlers.clear()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    log_path = Path(args.log)
    logger = build_logger(log_path)
    records = load_records(args.input)
    payloads, errors = transform_records(records, logger)
    write_payloads(output_path, payloads)
    print(
        f"Processed {len(records)} records, produced {len(payloads)} payloads, "
        f"logged {len(errors)} validation errors."
    )
    return 0
