from models import reasons
from utils.names import normalize
import re
import pandas as pd


def apply_id_age_rules(df):
    """
    Identity + age rules with OCR-safe EPIC handling
    """

    epic_raw = df["epic_id"]

    epic_norm = (
        epic_raw
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # -----------------------------
    # EPIC_ID_MISSING
    # -----------------------------
    missing_mask = (
        epic_raw.isna() |
        epic_norm.isin(["", "NAN", "NONE"])
    )

    for idx in df[missing_mask].index:
        if reasons.EPIC_ID_MISSING not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(reasons.EPIC_ID_MISSING)

    # -----------------------------
    # OCR FIX: O → 0 at 4th position
    # -----------------------------
    def fix_ocr(epic):
        if len(epic) == 10 and epic[3] == "O":
            return epic[:3] + "0" + epic[4:]
        return epic

    epic_fixed = epic_norm.apply(fix_ocr)

    # -----------------------------
    # INVALID_EPIC_ID
    # -----------------------------
    pattern = re.compile(r"^[A-Z]{3}\d{7}$")

    for idx in df[~missing_mask].index:
        epic = epic_fixed.loc[idx]
        if not pattern.fullmatch(epic):
            if reasons.INVALID_EPIC_ID not in df.at[idx, "suspect_reasons"]:
                df.at[idx, "suspect_reasons"].append(reasons.INVALID_EPIC_ID)

    # -----------------------------
    # DUPLICATE_EPIC_ID (VALID ONLY)
    # -----------------------------
    valid_epics = epic_fixed[~missing_mask]
    dup_mask = valid_epics.duplicated(keep=False)

    for idx in valid_epics[dup_mask].index:
        if reasons.DUPLICATE_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(reasons.DUPLICATE_EPIC_ID)

    # -----------------------------
    # AGE RULES
    # -----------------------------
    for idx, row in df.iterrows():
        try:
            age = int(row["age"])
        except Exception:
            age = -1

        if age <= 0:
            df.at[idx, "suspect_reasons"].append(reasons.AGE_ZERO_OR_INVALID)
        elif age < 18:
            df.at[idx, "suspect_reasons"].append(reasons.UNDER_18)

    # -----------------------------
    # COPY_SAME_PERSON_DIFFERENT_DOOR
    # -----------------------------
    df["_name_norm"] = df["name"].apply(normalize)
    df["_father_norm"] = df["father_name"].apply(normalize)
    df["_mother_norm"] = df["mother_name"].apply(normalize)
    df["_husband_norm"] = df["husband_name"].apply(normalize)
    df["_other_norm"] = df["other_name"].apply(normalize)

    identity_cols = [
        "_name_norm",
        "_father_norm",
        "_mother_norm",
        "_husband_norm",
        "_other_norm",
        "age",
        "gender",
    ]

    for _, grp in df.groupby(identity_cols, dropna=False):
        if grp["house_no_norm"].nunique() > 1:
            for idx in grp.index:
                if reasons.COPY_SAME_PERSON_DIFFERENT_DOOR not in df.at[idx, "suspect_reasons"]:
                    df.at[idx, "suspect_reasons"].append(
                        reasons.COPY_SAME_PERSON_DIFFERENT_DOOR
                    )
