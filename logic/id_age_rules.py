from models import reasons
from utils.names import normalize
import re


def apply_id_age_rules(df):
    """
    Booth-level + Global identity & age rules
    """

    # --------------------------------------------------
    # INVALID_EPIC_ID (GLOBAL + LOCAL)
    # Format: 3 letters + 7 digits (AAA1234567)
    # --------------------------------------------------
    epic_pattern = re.compile(r"^[A-Z]{3}\d{7}$")

    for idx, row in df.iterrows():
        epic = str(row["epic_id"]).strip().upper()
        if not epic_pattern.match(epic):
            df.at[idx, "suspect_reasons"].append(
                reasons.INVALID_EPIC_ID
            )

    # --------------------------------------------------
    # DUPLICATE_EPIC_ID (same file only)
    # --------------------------------------------------
    epic_counts = (
        df["epic_id"]
        .astype(str)
        .str.strip()
        .value_counts()
    )

    duplicate_epics = epic_counts[epic_counts > 1].index.tolist()

    for idx, row in df.iterrows():
        if str(row["epic_id"]).strip() in duplicate_epics:
            df.at[idx, "suspect_reasons"].append(
                reasons.DUPLICATE_EPIC_ID
            )

    # --------------------------------------------------
    # AGE RULES
    # --------------------------------------------------
    for idx, row in df.iterrows():
        age = int(row["age"])

        if age <= 0:
            df.at[idx, "suspect_reasons"].append(
                reasons.AGE_ZERO_OR_INVALID
            )
        elif age < 18:
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
                df.at[idx, "suspect_reasons"].append(
                    reasons.COPY_SAME_PERSON_DIFFERENT_DOOR
                )
