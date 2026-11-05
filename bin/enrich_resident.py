#!/usr/bin/env python3
"""Clinical telemetry resident registry enrichment module.

Performs database lookup against Master Resident Registry,
joins patient identifiers, and computes vital sign anomaly alerts.
Follows PEP 8 standards.
"""

import argparse
from pathlib import Path
from typing import Dict, Any
import csv
import sys


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Enrich telemetry readings with resident demographic data."
    )
    parser.add_argument(
        "--telemetry",
        type=Path,
        required=True,
        help="Path to cleaned telemetry CSV.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Path to resident master registry CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for enriched output CSV.",
    )
    return parser.parse_args()


def load_registry(registry_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load resident master database indexed by device_id."""
    registry = {}
    with open(registry_path, mode="r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            dev_id = row["device_id"].strip()
            registry[dev_id] = {
                "resident_id": row["resident_id"].strip(),
                "resident_name": row["resident_name"].strip(),
                "care_wing": row["care_wing"].strip(),
                "room_number": row["room_number"].strip(),
                "primary_caregiver": row["primary_caregiver"].strip(),
                "baseline_hr_min": int(row["baseline_hr_min"]),
                "baseline_hr_max": int(row["baseline_hr_max"]),
            }
    return registry


def evaluate_clinical_alert(
    heart_rate: int,
    motion_status: str,
    baseline_min: int,
    baseline_max: int,
) -> str:
    """Evaluate vital signs and motion to determine clinical alert status."""
    if motion_status == "FALL_DETECTED":
        return "CRITICAL_FALL_ALERT"
    if heart_rate < baseline_min:
        return "BRADYCARDIA_ALERT"
    if heart_rate > baseline_max:
        return "TACHYCARDIA_ALERT"
    return "NORMAL"


def enrich_telemetry(
    telemetry_path: Path,
    registry_path: Path,
    output_path: Path,
) -> int:
    """Join cleaned telemetry with resident registry and output enriched dataset."""
    registry = load_registry(registry_path)

    enriched_count = 0
    with open(telemetry_path, mode="r", encoding="utf-8") as in_f, \
         open(output_path, mode="w", newline="", encoding="utf-8") as out_f:

        reader = csv.DictReader(in_f)
        output_fields = [
            "timestamp",
            "device_id",
            "resident_id",
            "resident_name",
            "care_wing",
            "room_number",
            "beacon_id",
            "heart_rate",
            "respiration_rate",
            "motion_status",
            "clinical_alert",
            "primary_caregiver",
        ]

        writer = csv.DictWriter(out_f, fieldnames=output_fields)
        writer.writeheader()

        for row in reader:
            dev_id = row["device_id"].strip()
            resident = registry.get(dev_id)

            if not resident:
                sys.stderr.write(f"Warning: Unknown device_id '{dev_id}'. Skipping.\n")
                continue

            hr = int(row["heart_rate"])
            motion = row["motion_status"].strip()

            alert = evaluate_clinical_alert(
                heart_rate=hr,
                motion_status=motion,
                baseline_min=resident["baseline_hr_min"],
                baseline_max=resident["baseline_hr_max"],
            )

            writer.writerow({
                "timestamp": row["timestamp"],
                "device_id": dev_id,
                "resident_id": resident["resident_id"],
                "resident_name": resident["resident_name"],
                "care_wing": resident["care_wing"],
                "room_number": resident["room_number"],
                "beacon_id": row["beacon_id"],
                "heart_rate": hr,
                "respiration_rate": int(row["respiration_rate"]),
                "motion_status": motion,
                "clinical_alert": alert,
                "primary_caregiver": resident["primary_caregiver"],
            })
            enriched_count += 1

    print(f"[{telemetry_path.name}] Enriched {enriched_count} records with clinical registry data.")
    return enriched_count


def main() -> None:
    args = parse_arguments()
    enrich_telemetry(args.telemetry, args.registry, args.output)


if __name__ == "__main__":
    main()

