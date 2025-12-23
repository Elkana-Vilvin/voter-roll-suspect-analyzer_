import argparse
import re

from Explanation_of_sus_report.evidence_report import generate_evidence_report
from Explanation_of_sus_report.reason_wise_serial_report import (
    generate_reason_wise_serial_report,
)
from io_utils.writer import write_outputs, write_excel_summary
from logic.global_duplicate_rules import apply_global_duplicate_rules
from io_utils.loader import load_input
from logic.family_rules import apply_family_rules
from logic.bulk_rules import apply_bulk_rules
from logic.id_age_rules import apply_id_age_rules
from logic.door_rules import apply_door_rules


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    # Scope control
    parser.add_argument("--scope", choices=["assembly", "booth"], required=True)
    parser.add_argument("--assembly", required=True)
    parser.add_argument("--booth")

    args = parser.parse_args()

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    df = load_input(args.input)
    print(f"[INFO] Total rows loaded: {len(df)}")

    # --------------------------------------------------
    # NORMALIZATION (CRITICAL)
    # --------------------------------------------------

    # Extract numeric assembly number from values like "116-SULUR"
    df["assembly_no"] = (
        df["assembly"]
        .astype(str)
        .str.extract(r"(\d+)")
    )

    # part_no MUST stay int
    df["part_no"] = df["part_no"].astype(int)

    # Normalize house & street
    df["house_no_norm"] = (
        df["house_no"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["street_norm"] = (
        df["street"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Init suspect reasons
    df["suspect_reasons"] = [[] for _ in range(len(df))]

    # --------------------------------------------------
    # PHASE 1 — GLOBAL RULES (FULL DATASET)
    # --------------------------------------------------
    print("[INFO] Applying GLOBAL rules on full dataset")
    apply_global_duplicate_rules(df)

    # --------------------------------------------------
    # PHASE 2 — SCOPE FILTER
    # --------------------------------------------------

    # Normalize CLI assembly (accepts 116 or 116-SULUR)
    assembly_raw = str(args.assembly).strip().upper()
    m = re.search(r"\d+", assembly_raw)
    if not m:
        raise ValueError(f"Invalid assembly value: {args.assembly}")
    assembly_cli = m.group()  # "116"

    booth_cli = None
    if args.booth:
        booth_cli = int(args.booth)

    if args.scope == "assembly":
        scoped_df = df[df["assembly_no"] == assembly_cli]

    elif args.scope == "booth":
        if booth_cli is None:
            raise ValueError("--booth is required for booth scope")

        scoped_df = df[
            (df["assembly_no"] == assembly_cli) &
            (df["part_no"] == booth_cli)
        ]
    else:
        raise ValueError("Invalid scope")

    scoped_df = scoped_df.copy()

    print(f"[INFO] Rows after scope filter ({args.scope}): {len(scoped_df)}")

    if scoped_df.empty:
        print("[WARNING] Scoped dataset is EMPTY — check CLI values")
        return

    # --------------------------------------------------
    # PHASE 3 — LOCAL RULES (ONLY FOR BOOTH)
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


if __name__ == "__main__":
    main()
