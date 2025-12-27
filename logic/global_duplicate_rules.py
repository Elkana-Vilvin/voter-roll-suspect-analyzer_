from models import reasons
import pandas as pd


def apply_global_duplicate_rules(df):
    """
    Apply booth-independent duplicate checks.
    """

    # -------------------------------------------------
    # NORMALIZE EPIC ID
    # -------------------------------------------------
    epic_raw = df["epic_id"]

    epic_norm = (
        epic_raw
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # -------------------------------------------------
    # 0. EPIC_ID_MISSING (GLOBAL)
    # -------------------------------------------------
    missing_mask = (
        epic_raw.isna() |
        epic_norm.isin(["", "NAN", "NONE"])
    )

    for idx in df[missing_mask].index:
        if reasons.EPIC_ID_MISSING not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.EPIC_ID_MISSING
            )

    # -------------------------------------------------
    # 1. DUPLICATE_EPIC_ID (GLOBAL, VALID ONLY)
    # -------------------------------------------------
    valid_mask = ~missing_mask
    valid_epic = epic_norm[valid_mask]

    dup_mask = valid_epic.duplicated(keep=False)

    for idx in valid_epic[dup_mask].index:
        if reasons.DUPLICATE_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.DUPLICATE_EPIC_ID
            )

    # -------------------------------------------------
    # 2. DUPLICATE_DETAILS (GLOBAL)
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
            epics = (
                df.loc[grp.index, "epic_id"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # ignore missing EPIC IDs
            valid_epics = epics[~epics.isin(["", "NAN", "NONE"])]

            if valid_epics.nunique() > 1:
                for idx in grp.index:
                    if reasons.DUPLICATE_DETAILS not in df.at[idx, "suspect_reasons"]:
                        df.at[idx, "suspect_reasons"].append(
                            reasons.DUPLICATE_DETAILS
                        )
