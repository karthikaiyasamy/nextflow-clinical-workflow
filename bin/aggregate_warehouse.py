#!/usr/bin/env python3
"""Clinical data warehouse aggregation and reporting module.

Aggregates multiple enriched batch streams into a unified warehouse table
and generates an executive clinical alert summary for nursing supervisors.
Follows PEP 8 standards.
"""

import argparse
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any
import csv
import sys


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate enriched telemetry batches into warehouse repository."
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        required=True,
        help="List of enriched batch CSV files.",
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        required=True,
        help="Path for combined warehouse CSV table.",
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        required=True,
        help="Path for Markdown clinical alert summary report.",
    )
    return parser.parse_args()


def aggregate_batches(
    input_files: List[Path],
    output_table_path: Path,
    output_summary_path: Path,
) -> None:
    """Aggregate enriched files and generate markdown clinical dashboard."""
    all_records: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []
    wing_counts: Dict[str, int] = defaultdict(int)

    fieldnames = [
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

    for file_path in input_files:
        if not file_path.exists():
            continue
        with open(file_path, mode="r", encoding="utf-8") as in_f:
            reader = csv.DictReader(in_f)
            for row in reader:
                all_records.append(row)
                wing_counts[row["care_wing"]] += 1
                if row["clinical_alert"] != "NORMAL":
                    alerts.append(row)

    # 1. Write Consolidated Warehouse CSV
    with open(output_table_path, mode="w", newline="", encoding="utf-8") as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    # 2. Write Markdown Clinical Alert Report
    with open(output_summary_path, mode="w", encoding="utf-8") as out_md:
        out_md.write("# 🏥 Clinical Telemetry & Emergency Alert Summary\n\n")
        out_md.write(f"**Total Processed Telemetry Records:** {len(all_records)}  \n")
        out_md.write(f"**Total Critical Alerts Detected:** {len(alerts)}  \n\n")

        out_md.write("### 🏢 Telemetry Volume by Care Wing\n\n")
        out_md.write("| Care Facility Wing | Total Records Processed |\n")
        out_md.write("| :--- | :--- |\n")
        for wing, count in sorted(wing_counts.items()):
            out_md.write(f"| {wing} | {count} |\n")
        out_md.write("\n")

        out_md.write("### 🚨 Active Clinical Alerts Requiring Nurse Intervention\n\n")
        if alerts:
            out_md.write(
                "| Timestamp | Resident Name | Room | Alert Type | HR | Motion | Caregiver |\n"
            )
            out_md.write(
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            )
            for a in alerts:
                out_md.write(
                    f"| {a['timestamp']} | **{a['resident_name']}** | {a['room_number']} | "
                    f"`{a['clinical_alert']}` | {a['heart_rate']} bpm | {a['motion_status']} | {a['primary_caregiver']} |\n"
                )
        else:
            out_md.write("*(No clinical anomalies detected across batches)*\n")

    print(
        f"Warehousing complete: {len(all_records)} total rows consolidated. "
        f"{len(alerts)} clinical alerts reported in {output_summary_path.name}."
    )


def main() -> None:
    args = parse_arguments()
    aggregate_batches(args.inputs, args.output_table, args.output_summary)


if __name__ == "__main__":
    main()

