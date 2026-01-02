from models import reasons
from utils.names import normalize
from difflib import SequenceMatcher

INVALID_VALUES = {"", "NAN", "NONE"}


def _add_reason(df, idx, reason):
    """Add reason safely (no duplicates)"""
    if reason not in df.at[idx, "suspect_reasons"]:
        df.at[idx, "suspect_reasons"].append(reason)


def _similar(a, b, threshold=0.85):
    """
    Fuzzy match for husband names (OCR-safe)
    Used ONLY inside house
    """
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


def apply_family_rules(df):
    """
    FAMILY RULES — HOUSE-CENTRIC, SAFE & AUDITABLE

    Includes:
    - SAME_NAME_IN_SAME_HOUSE
    - ORPHAN_ONLY_PERSON_IN_HOME
    - ADOPTED_NO_RELATIVE (symmetric)
    - TWO_WIVES_SAME_HUSBAND (NEW, SAFE)
    """

    # --------------------------------------------------
    # NORMALIZE NAMES
    # --------------------------------------------------
    df["_name_norm"] = df["name"].apply(normalize)
    df["_father_norm"] = df["father_name"].apply(normalize)
    df["_mother_norm"] = df["mother_name"].apply(normalize)
    df["_husband_norm"] = df["husband_name"].apply(normalize)

    # --------------------------------------------------
    # STREET → HOUSE
    # --------------------------------------------------
    for street, street_grp in df.groupby("street_norm"):

        if street in INVALID_VALUES:
            for idx in street_grp.index:
                _add_reason(df, idx, reasons.STREET_NAME_UNAVAILABLE)
            continue

        for house_no, house_grp in street_grp.groupby("house_no_norm"):

            if house_no in INVALID_VALUES:
                continue

            indices = list(house_grp.index)
            house_size = len(indices)

            # --------------------------------------------------
            # SINGLE PERSON → ORPHAN
            # --------------------------------------------------
            if house_size == 1:
                _add_reason(
                    df, indices[0], reasons.ORPHAN_ONLY_PERSON_IN_HOME
                )
                continue

            # --------------------------------------------------
            # SAME_NAME_IN_SAME_HOUSE
            # --------------------------------------------------
            for name, g in house_grp.groupby("_name_norm"):
                if name and len(g) > 1:
                    for idx in g.index:
                        _add_reason(
                            df, idx, reasons.SAME_NAME_IN_SAME_HOUSE
                        )

            # --------------------------------------------------
            # 🔥 TWO_WIVES_SAME_HUSBAND (SAFE & ISOLATED)
            # --------------------------------------------------
            wives = house_grp[
                (house_grp["gender"].astype(str).str.upper() == "F") &
                (~house_grp["_husband_norm"].isin(INVALID_VALUES))
            ]

            wife_indices = wives.index.tolist()
            husband_map = {}

            for idx in wife_indices:
                h = df.at[idx, "_husband_norm"]
                husband_map.setdefault(idx, h)

            flagged = set()

            for i in range(len(wife_indices)):
                for j in range(i + 1, len(wife_indices)):
                    idx1 = wife_indices[i]
                    idx2 = wife_indices[j]

                    h1 = husband_map[idx1]
                    h2 = husband_map[idx2]

                    if _similar(h1, h2):
                        flagged.add(idx1)
                        flagged.add(idx2)

            for idx in flagged:
                _add_reason(
                    df, idx, reasons.TWO_WIVES_SAME_HUSBAND
                )

            # --------------------------------------------------
            # FAMILY LINK CHECK (ADOPTED / VALID)
            # --------------------------------------------------
            names = set(house_grp["_name_norm"])
            fathers = set(house_grp["_father_norm"])
            husbands = set(house_grp["_husband_norm"])

            linked = set()

            for idx in indices:
                row = df.loc[idx]

                relations = {
                    row["_father_norm"],
                    row["_mother_norm"],
                    row["_husband_norm"],
                }
                relations.discard("")

                valid = False

                # Relation matches name
                if relations & names:
                    valid = True

                # Siblings (same father)
                if (
                    row["_father_norm"]
                    and list(house_grp["_father_norm"]).count(
                        row["_father_norm"]
                    ) > 1
                ):
                    valid = True

                # Wife → husband matches father
                if (
                    row["_husband_norm"]
                    and row["_husband_norm"] in fathers
                ):
                    valid = True

                # Man → name appears as husband
                if (
                    row["_name_norm"]
                    and row["_name_norm"] in husbands
                ):
                    valid = True

                if valid:
                    linked.add(idx)

            # --------------------------------------------------
            # FINAL DECISION — SYMMETRIC
            # --------------------------------------------------
            if not linked:
                for idx in indices:
                    _add_reason(
                        df, idx, reasons.ADOPTED_NO_RELATIVE
                    )
            else:
                for idx in indices:
                    if idx not in linked:
                        _add_reason(
                            df, idx, reasons.ADOPTED_NO_RELATIVE
                        )
