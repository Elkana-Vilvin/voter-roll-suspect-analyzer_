import os
import pandas as pd


# --------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------

def _norm(x):
    """Safe normalization for writer-level comparisons"""
    if pd.isna(x):
        return ""
    return str(x).strip().upper()


def _location_context(df):
    """
    Build location context text like:
    'in part 247 inside assembly 116'
    """
    parts = sorted(df["part_no"].dropna().astype(str).unique())
    assemblies = sorted(
        df["assembly"]
        .dropna()
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .dropna()
        .unique()
    )

    part_txt = f"part(s) {parts}" if parts else ""
    asm_txt = f"assembly {assemblies}" if assemblies else ""

    if part_txt and asm_txt:
        return f"in {part_txt} inside {asm_txt}"
    if asm_txt:
        return f"in {asm_txt}"
    return ""


def _explanation_1(row, df, reason):
    """
    WHY this particular voter was flagged
    """
    sn = int(row["serial_no"])
    house = row.get("house_no", "")
    street = row.get("street", "")
    booth = row.get("part_no", "")
    assembly = row.get("assembly", "")

    # --------------------------------------------------
    # GLOBAL RULES
    # --------------------------------------------------
    if reason == "EPIC_ID_MISSING":
       return (
        f"Serial number {sn} does not have a valid EPIC ID recorded, "
        f"which is mandatory for voter identification."
    )

    if reason == "DUPLICATE_EPIC_ID":
        matches = df[df["epic_id"] == row["epic_id"]]
        others = (
            matches["serial_no"]
            .dropna()
            .astype(int)
            .tolist()
        )
        others = [o for o in others if o != sn]

        location = _location_context(matches)

        return (
            f"Serial number {sn} shares the same EPIC ID ({row['epic_id']}) "
            f"with serial number(s) {others} {location}."
        )

    if reason == "DUPLICATE_DETAILS":
        matches = df[
            (df["serial_no"] != sn) &
            (df["name"].apply(_norm) == _norm(row["name"])) &
            (df["father_name"].apply(_norm) == _norm(row["father_name"])) &
            (df["mother_name"].apply(_norm) == _norm(row["mother_name"])) &
            (df["husband_name"].apply(_norm) == _norm(row["husband_name"])) &
            (df["other_name"].apply(_norm) == _norm(row["other_name"])) &
            (df["age"] == row["age"]) &
            (df["gender"].apply(_norm) == _norm(row["gender"])) &
            (df["house_no"].apply(_norm) == _norm(row["house_no"]))
        ]

        serials = matches["serial_no"].astype(int).tolist()
        location = _location_context(matches)

        if serials:
            return (
                f"Serial number {sn} has identical personal and family details "
                f"as serial number(s) {serials} {location}, "
                f"but appears under a different EPIC ID."
            )

        return (
            f"Serial number {sn} has identical personal and family details "
            f"as another voter {location}, but appears under a different EPIC ID."
        )

    # --------------------------------------------------
    # FAMILY / HOUSEHOLD RULES
    # --------------------------------------------------
    if reason == "ORPHAN_ONLY_PERSON_IN_HOME":
        return (
            f"Serial number {sn} is the only voter listed under house number "
            f"{house} on street '{street}' in booth {booth}."
        )

    if reason == "ADOPTED_NO_RELATIVE":
        return (
            f"Serial number {sn} does not have any valid parent or spouse "
            f"relationship with other voters in house number {house} "
            f"on street '{street}'."
        )

    if reason == "SAME_NAME_IN_SAME_HOUSE":
        return (
            f"Multiple voters in house number {house} on street '{street}' "
            f"share the same name as serial number {sn}."
        )

    if reason == "COPY_SAME_PERSON_DIFFERENT_DOOR":
        matches = df[
            (df["serial_no"] != sn) &
            (df["name"].apply(_norm) == _norm(row["name"])) &
            (df["father_name"].apply(_norm) == _norm(row["father_name"])) &
            (df["mother_name"].apply(_norm) == _norm(row["mother_name"])) &
            (df["husband_name"].apply(_norm) == _norm(row["husband_name"])) &
            (df["age"] == row["age"]) &
            (df["gender"].apply(_norm) == _norm(row["gender"])) &
            (df["house_no"] != row["house_no"])
        ]

        doors = matches["house_no"].astype(str).unique().tolist()
        serials = matches["serial_no"].astype(int).tolist()

        return (
            f"Serial number {sn} has identical personal and family details "
            f"as serial number(s) {serials}, but appears under different "
            f"house number(s): {doors}."
        )

    # --------------------------------------------------
    # BULK / ADDRESS RULES
    # --------------------------------------------------
    if reason == "BULK_10_PLUS":
        count = df[
            (df["house_no"] == row["house_no"]) &
            (df["street"] == row["street"])
        ].shape[0]

        return (
            f"House number {house} on street '{street}' contains "
            f"{count} registered voters including serial number {sn}, "
            f"which exceeds the household size threshold."
        )

    if reason == "HOUSE_NO_UNAVAILABLE":
        return f"Serial number {sn} does not have a valid house number recorded."

    if reason == "INVALID_HOUSE_NO":
        return f"House number '{house}' does not contain any numeric digits."

    if reason == "STREET_NAME_UNAVAILABLE":
        return (
            f"Street name is missing for serial number {sn}, therefore "
            f"household-level verification could not be performed."
        )

    # --------------------------------------------------
    # AGE RULES
    # --------------------------------------------------
    if reason == "UNDER_18":
        return f"Serial number {sn} has age {row['age']}, below voting age."

    if reason == "AGE_ZERO_OR_INVALID":
        return f"Serial number {sn} has invalid age value {row['age']}."

    return f"Serial number {sn} was flagged due to rule: {reason}."


# --------------------------------------------------
# CSV OUTPUTS
# --------------------------------------------------

def write_outputs(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df.to_csv(os.path.join(output_dir, "full_tagged_output.csv"), index=False)
    df[df["is_suspect"]].to_csv(
        os.path.join(output_dir, "suspects_only.csv"), index=False
    )

    print(f"[OK] CSV outputs written to {output_dir}")


# --------------------------------------------------
# EXCEL SUMMARY (FINAL)
# --------------------------------------------------

def write_excel_summary(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    out_df = df.copy()

    out_df["TOTAL_FLAGS"] = out_df["suspect_reasons"].apply(len)
    out_df["FLAG_REASONS"] = out_df["suspect_reasons"].apply(
        lambda x: ", ".join(sorted(set(x)))
    )

    out_df["EXPLANATION_1"] = ""

    for idx, row in out_df.iterrows():
        if not row["suspect_reasons"]:
            continue

        explanations = [
            _explanation_1(row, out_df, reason)
            for reason in row["suspect_reasons"]
        ]

        out_df.at[idx, "EXPLANATION_1"] = " | ".join(explanations)

    export_columns = [
        "serial_no",
        "epic_id",
        "name",
        "father_name",
        "mother_name",
        "husband_name",
        "other_name",
        "house_no",
        "street",
        "part_no",
        "assembly",
        "age",
        "gender",
        "TOTAL_FLAGS",
        "FLAG_REASONS",
        "EXPLANATION_1",
    ]

    export_columns = [c for c in export_columns if c in out_df.columns]
    out_df = out_df[export_columns]

    excel_path = os.path.join(output_dir, "suspect_summary.xlsx")
    out_df.to_excel(excel_path, index=False)

    print(f"[OK] Excel summary written to {excel_path}")
