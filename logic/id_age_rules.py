from models import reasons
from utils.names import normalize
import re
import pandas as pd


def apply_id_age_rules(df):
    """
    Booth-level + Global identity & age rules
    """

    # --------------------------------------------------
    # NORMALIZE EPIC ID ONCE
    # --------------------------------------------------
    epic_raw = df["epic_id"]

    epic_norm = (
        epic_raw
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------
    # EPIC_ID_MISSING (GLOBAL + LOCAL)
    # --------------------------------------------------
    missing_mask = (
        epic_raw.isna() |
        epic_norm.isin(["", "NAN", "NONE"])
    )

    for idx in df[missing_mask].index:
        if reasons.EPIC_ID_MISSING not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.EPIC_ID_MISSING
            )

    # --------------------------------------------------
    # INVALID_EPIC_ID (FORMAT CHECK — ONLY IF PRESENT)
    # Format: AAA1234567
    # --------------------------------------------------
    epic_pattern = re.compile(r"^[A-Z]{3}\d{7}$")

    valid_mask = ~missing_mask

    for idx in df[valid_mask].index:
        epic = epic_norm.loc[idx]

        if not epic_pattern.fullmatch(epic):
            if reasons.INVALID_EPIC_ID not in df.at[idx, "suspect_reasons"]:
                df.at[idx, "suspect_reasons"].append(
                    reasons.INVALID_EPIC_ID
                )

    # --------------------------------------------------
    # DUPLICATE_EPIC_ID (VALID EPIC ONLY)
    # --------------------------------------------------
    valid_epics = epic_norm[valid_mask]

    dup_mask = valid_epics.duplicated(keep=False)

    for idx in valid_epics[dup_mask].index:
        if reasons.DUPLICATE_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.DUPLICATE_EPIC_ID
            )

    # --------------------------------------------------
    # AGE RULES
    # --------------------------------------------------
    for idx, row in df.iterrows():
        try:
            age = int(row["age"])
        except Exception:
            age = -1

        if age <= 0:
            if reasons.AGE_ZERO_OR_INVALID not in df.at[idx, "suspect_reasons"]:
                df.at[idx, "suspect_reasons"].append(
                    reasons.AGE_ZERO_OR_INVALID
                )
        elif age < 18:
            if reasons.UNDER_18 not in df.at[idx, "suspect_reasons"]:
                df.at[idx, "suspect_reasons"].append(
                    reasons.UNDER_18
                )

    # --------------------------------------------------
    # COPY_SAME_PERSON_DIFFERENT_DOOR (STRICT MATCH)
    # --------------------------------------------------
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
        if grp["house_no"].nunique() > 1:
            for idx in grp.index:
                if reasons.COPY_SAME_PERSON_DIFFERENT_DOOR not in df.at[idx, "suspect_reasons"]:
                    df.at[idx, "suspect_reasons"].append(
                        reasons.COPY_SAME_PERSON_DIFFERENT_DOOR
                    )
