import argparse
import re
import pandas as pd

from Explanation_of_sus_report.evidence_report import generate_evidence_report
from Explanation_of_sus_report.reason_wise_serial_report import (
    generate_reason_wise_serial_report,
)
from io_utils.writer import write_outputs, write_excel_summary
from io_utils.loader import load_input

from logic.global_duplicate_rules import apply_global_duplicate_rules
from logic.family_rules import apply_family_rules
from logic.bulk_rules import apply_bulk_rules
from logic.id_age_rules import apply_id_age_rules
from logic.door_rules import apply_door_rules


# --------------------------------------------------
# HOUSE NUMBER NORMALIZATION (CRITICAL)
# --------------------------------------------------
def normalize_house_no(x):
    """
    Normalize house numbers so that:
    3/53 == 3 - 53 == 3–53 == 3-53
    """
    if pd.isna(x):
        return ""

    x = str(x).upper().strip()

    # Normalize all separators to "-"
    x = re.sub(r"[\/–—]", "-", x)

    # Remove spaces around dash
    x = re.sub(r"\s*-\s*", "-", x)

    # Remove all remaining spaces
    x = re.sub(r"\s+", "", x)

    # Collapse multiple dashes
    x = re.sub(r"-{2,}", "-", x)

    return x


def main():
    parser = argparse.ArgumentParser(
        description="Voter Suspect Detection Engine"
    )

    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", required=True, help="Output directory")

    # Scope control
    parser.add_argument(
        "--scope",
        choices=["assembly", "booth"],
        required=True,
        help="Analysis scope",
    )
    parser.add_argument(
        "--assembly",
        required=True,
        help="Assembly number (e.g., 116 or 116-SULUR)",
    )
    parser.add_argument(
        "--booth",
        help="Booth / Part number (required if scope=booth)",
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    df = load_input(args.input)
    print(f"[INFO] Total rows loaded: {len(df)}")

    # --------------------------------------------------
    # NORMALIZATION (CRITICAL)
    # --------------------------------------------------

    # Extract numeric assembly number (116 from "116-SULUR")
    df["assembly_no"] = (
        df["assembly"]
        .astype(str)
        .str.extract(r"(\d+)")
    )

    # part_no must be integer
    df["part_no"] = df["part_no"].astype(int)

    # ✅ FIXED house number normalization
    df["house_no_norm"] = df["house_no"].apply(normalize_house_no)

    # Street normalization
    df["street_norm"] = (
        df["street"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Initialize suspect reasons container
    df["suspect_reasons"] = [[] for _ in range(len(df))]

    # --------------------------------------------------
    # PHASE 1 — GLOBAL RULES (FULL DATASET)
    # --------------------------------------------------
    print("[INFO] Applying GLOBAL rules on full dataset")
    apply_global_duplicate_rules(df)

    # --------------------------------------------------
    # PHASE 2 — SCOPE FILTER
    # --------------------------------------------------

    # Normalize CLI assembly value
    assembly_raw = str(args.assembly).strip().upper()
    m = re.search(r"\d+", assembly_raw)
    if not m:
        raise ValueError(f"Invalid assembly value: {args.assembly}")
    assembly_cli = m.group()

    booth_cli = None
    if args.booth:
        booth_cli = int(args.booth)

    if args.scope == "assembly":
        scoped_df = df[df["assembly_no"] == assembly_cli]

    elif args.scope == "booth":
        if booth_cli is None:
            raise ValueError("--booth is required when scope is 'booth'")

        scoped_df = df[
            (df["assembly_no"] == assembly_cli) &
            (df["part_no"] == booth_cli)
        ]
    else:
        raise ValueError("Invalid scope")

    scoped_df = scoped_df.copy()
    print(f"[INFO] Rows after scope filter ({args.scope}): {len(scoped_df)}")

    if scoped_df.empty:
        print("[WARNING] Scoped dataset is EMPTY — check assembly/booth values")
        return

    # --------------------------------------------------
    # PHASE 3 — LOCAL RULES (BOOTH ONLY)
    # --------------------------------------------------
    if args.scope == "booth":
        print("[INFO] Applying BOOTH-level rules")
        apply_family_rules(scoped_df)
        apply_bulk_rules(scoped_df)
        apply_id_age_rules(scoped_df)
        apply_door_rules(scoped_df)
    else:
        print("[INFO] Assembly-level analysis: skipping local household rules")

    # --------------------------------------------------
    # FINAL FLAGS
    # --------------------------------------------------
    scoped_df["is_suspect"] = scoped_df["suspect_reasons"].apply(bool)
    print(f"[INFO] Total suspects in scope: {scoped_df['is_suspect'].sum()}")

    # --------------------------------------------------
    # OUTPUTS
    # --------------------------------------------------
    write_outputs(scoped_df, args.output)
    write_excel_summary(scoped_df, args.output)
    generate_evidence_report(scoped_df, args.output)
    generate_reason_wise_serial_report(scoped_df, args.output)

    print("[DONE] Analysis completed successfully")


if __name__ == "__main__":
    main()
