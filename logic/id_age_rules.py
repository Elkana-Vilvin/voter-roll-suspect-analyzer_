from models import reasons
from utils.names import normalize
from utils.epic import normalize_epic_id, is_valid_epic

import pandas as pd


def apply_id_age_rules(df):
    """
    Identity + age rules with OCR-safe EPIC handling
    """

    # --------------------------------------------------
    # EPIC NORMALIZATION (SINGLE SOURCE OF TRUTH)
    # --------------------------------------------------
    df["_epic_norm"] = df["epic_id"].apply(normalize_epic_id)

    # --------------------------------------------------
    # EPIC_ID_MISSING
    # --------------------------------------------------
    missing_mask = df["_epic_norm"].isna()

    for idx in df[missing_mask].index:
        if reasons.EPIC_ID_MISSING not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.EPIC_ID_MISSING
            )

    # --------------------------------------------------
    # INVALID_EPIC_ID
    # --------------------------------------------------
    invalid_mask = (
        ~missing_mask &
        ~df["_epic_norm"].apply(is_valid_epic)
    )

    for idx in df[invalid_mask].index:
        if reasons.INVALID_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.INVALID_EPIC_ID
            )

    # --------------------------------------------------
    # DUPLICATE_EPIC_ID (ONLY VALID EPICS)
    # --------------------------------------------------
    valid_mask = (
        ~missing_mask &
        ~invalid_mask
    )

    dup_mask = df.loc[valid_mask, "_epic_norm"].duplicated(keep=False)

    for idx in df.loc[valid_mask].index[dup_mask]:
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
    # COPY_SAME_PERSON_DIFFERENT_DOOR
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
        if grp["house_no_norm"].nunique() > 1:
            for idx in grp.index:
                if reasons.COPY_SAME_PERSON_DIFFERENT_DOOR not in df.at[idx, "suspect_reasons"]:
                    df.at[idx, "suspect_reasons"].append(
                        reasons.COPY_SAME_PERSON_DIFFERENT_DOOR
                    )
