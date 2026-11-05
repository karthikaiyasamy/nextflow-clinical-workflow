#!/usr/bin/env python3
"""Telemetry cleaning and validation script.

Filters out corrupt packets, checks vital sign sanity ranges,
and formats telemetry data for downstream enrichment.
Follows PEP 8 standards.
"""

import argparse
from datetime import datetime
from pathlib import Path
import csv
import sys


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean and validate incoming clinical sensor telemetry."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to raw telemetry CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for cleaned output CSV.",
    )
    return parser.parse_args()


def is_valid_timestamp(ts_str: str) -> bool:
    """Validate ISO timestamp format."""
    try:
        datetime.fromisoformat(ts_str)
        return True
    except (ValueError, TypeError):
        return False


def clean_telemetry(input_path: Path, output_path: Path) -> int:
    """Clean raw telemetry CSV, filtering malformed records.

    Returns:
        Number of valid records retained.
    """
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    valid_count = 0
    dropped_count = 0

    with open(input_path, mode="r", encoding="utf-8") as infile, \
         open(output_path, mode="w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for line_num, row in enumerate(reader, start=2):
            ts = row.get("timestamp", "").strip()
            dev_id = row.get("device_id", "").strip()
            beacon = row.get("beacon_id", "").strip()
            hr_str = row.get("heart_rate", "").strip()
            rr_str = row.get("respiration_rate", "").strip()
            rssi_str = row.get("raw_signal_rssi", "").strip()

            # Sanity checks
            if not is_valid_timestamp(ts):
                sys.stderr.write(f"Line {line_num}: Invalid timestamp '{ts}'. Dropping.\n")
                dropped_count += 1
                continue

            try:
                hr = int(hr_str)
                rr = int(rr_str)
                rssi = int(rssi_str)
            except ValueError:
                sys.stderr.write(f"Line {line_num}: Non-integer vitals or RSSI. Dropping.\n")
                dropped_count += 1
                continue

            # Physiological and signal sanity bounds
            if not (20 <= hr <= 250) or not (5 <= rr <= 60) or not (-120 <= rssi <= 0):
                sys.stderr.write(f"Line {line_num}: Physiological values out of bounds. Dropping.\n")
                dropped_count += 1
                continue

            writer.writerow(row)
            valid_count += 1

    print(f"[{input_path.name}] Cleaning complete: {valid_count} retained, {dropped_count} dropped.")
    return valid_count


def main() -> None:
    args = parse_arguments()
    clean_telemetry(args.input, args.output)


if __name__ == "__main__":
    main()

