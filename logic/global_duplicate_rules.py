from models import reasons


def apply_global_duplicate_rules(df):
    """
    Apply booth-independent duplicate checks.
    These run on the FULL dataset before hierarchical segregation.
    """

    # -------------------------------------------------
    # 1. DUPLICATE_EPIC_ID (global)
    # -------------------------------------------------
    epic_norm = (
        df["epic_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    dup_epic_mask = epic_norm.duplicated(keep=False)

    for idx in df[dup_epic_mask].index:
        if reasons.DUPLICATE_EPIC_ID not in df.at[idx, "suspect_reasons"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.DUPLICATE_EPIC_ID
            )

    # -------------------------------------------------
    # 2. DUPLICATE_DETAILS (global)
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
    ]

    # Normalize details strictly
    norm_df = df[detail_cols].copy()
    for col in detail_cols:
        norm_df[col] = (
            norm_df[col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    detail_groups = norm_df.groupby(detail_cols)

    for _, grp in detail_groups:
        if len(grp) > 1:
            epic_ids = df.loc[grp.index, "epic_id"].astype(str).str.upper()
            if epic_ids.nunique() > 1:
                for idx in grp.index:
                    if reasons.DUPLICATE_DETAILS not in df.at[idx, "suspect_reasons"]:
                        df.at[idx, "suspect_reasons"].append(
                            reasons.DUPLICATE_DETAILS
                        )
