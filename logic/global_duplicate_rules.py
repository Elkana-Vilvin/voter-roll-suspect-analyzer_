from models import reasons
import pandas as pd

from utils.epic import normalize_epic_id, is_valid_epic


def apply_global_duplicate_rules(df):
    """
    GLOBAL RULES (ASSEMBLY-WIDE):
    - EPIC_ID_MISSING
    - INVALID_EPIC_ID
    - DUPLICATE_EPIC_ID
    - DUPLICATE_DETAILS
    """

    # -------------------------------------------------
    # EPIC NORMALIZATION (OCR SAFE — SINGLE SOURCE)
    # -------------------------------------------------
    df["_epic_norm"] = df["epic_id"].apply(normalize_epic_id)

    # -------------------------------------------------
    # 1. EPIC_ID_MISSING
    # -------------------------------------------------
    missing_mask = df["_epic_norm"].isna()

    for idx in df[missing_mask].index:
        if reasons.EPIC_ID_MISSING not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.EPIC_ID_MISSING
            )

    # -------------------------------------------------
    # 2. INVALID_EPIC_ID
    # -------------------------------------------------
    invalid_mask = (
        ~missing_mask &
        ~df["_epic_norm"].apply(is_valid_epic)
    )

    for idx in df[invalid_mask].index:
        if reasons.INVALID_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.INVALID_EPIC_ID
            )

    # -------------------------------------------------
    # 3. DUPLICATE_EPIC_ID (ONLY VALID EPICS)
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 4. DUPLICATE_DETAILS (GLOBAL — EPIC IGNORED)
    # -------------------------------------------------
    detail_cols = [
        "name",
        "father_name",
        "mother_name",
        "husband_name",
        "other_name",
        "age",
        "gender",
        "house_no",
        "street",
    ]

    norm_df = df[detail_cols].copy()

    for col in detail_cols:
        norm_df[col] = (
            norm_df[col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    groups = norm_df.groupby(detail_cols, dropna=False)

    for _, grp in groups:
        if len(grp) > 1:
            for idx in grp.index:
                if reasons.DUPLICATE_DETAILS not in df.at[idx, "suspect_reasons"]:
                    df.at[idx, "suspect_reasons"].append(
                        reasons.DUPLICATE_DETAILS
                    )
