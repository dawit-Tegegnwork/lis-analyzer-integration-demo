"""Input and output helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def load_records(path: str | Path) -> list[dict]:
    input_path = Path(path)
    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        with input_path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    if suffix == ".json":
        with input_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return payload["results"]
        raise ValueError("JSON input must be a list or an object with a 'results' list.")

    raise ValueError(f"Unsupported input format: {input_path.suffix}")


def write_payloads(path: str | Path, payloads: list[dict]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payloads, handle, indent=2)
        handle.write("\n")
