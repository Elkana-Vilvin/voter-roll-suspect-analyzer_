from models import reasons
from utils.names import normalize

INVALID_VALUES = {"", "NAN", "NONE"}


def _add_reason(df, idx, reason):
    """Add reason safely (no duplicates)"""
    if reason not in df.at[idx, "suspect_reasons"]:
        df.at[idx, "suspect_reasons"].append(reason)


def apply_family_rules(df):
    """
    FAMILY RULES — FINAL & SAFE

    Applied ONLY at BOOTH level
    Hierarchy:
        STREET → HOUSE
    """

    # --------------------------------------------------
    # NORMALIZATION (STRICT)
    # --------------------------------------------------
    df["_name_norm"] = df["name"].apply(normalize)
    df["_father_norm"] = df["father_name"].apply(normalize)
    df["_mother_norm"] = df["mother_name"].apply(normalize)
    df["_husband_norm"] = df["husband_name"].apply(normalize)

    # --------------------------------------------------
    # STREET LEVEL
    # --------------------------------------------------
    for street, street_grp in df.groupby("street_norm"):

        # STREET missing
        if street in INVALID_VALUES:
            for idx in street_grp.index:
                _add_reason(df, idx, reasons.STREET_NAME_UNAVAILABLE)
            continue

        # --------------------------------------------------
        # HOUSE LEVEL
        # --------------------------------------------------
        for house_no, house_grp in street_grp.groupby("house_no_norm"):

            if house_no in INVALID_VALUES:
                continue

            house_indices = list(house_grp.index)
            house_size = len(house_indices)

            # ----------------------------------------------
            # SAME_NAME_IN_SAME_HOUSE
            # ----------------------------------------------
            for name_norm, g in house_grp.groupby("_name_norm"):
                if name_norm and len(g) > 1:
                    for idx in g.index:
                        _add_reason(df, idx, reasons.SAME_NAME_IN_SAME_HOUSE)

            

            # ----------------------------------------------
            # CONTEXT COLLECTION
            # ----------------------------------------------
            names = set(house_grp["_name_norm"])
            fathers = set(house_grp["_father_norm"])
            husbands = set(house_grp["_husband_norm"])

            # ----------------------------------------------
            # ADOPTED / ORPHAN LOGIC
            # ----------------------------------------------
            for idx in house_indices:
                row = df.loc[idx]

                # Only one person
                if house_size == 1:
                    _add_reason(df, idx, reasons.ORPHAN_ONLY_PERSON_IN_HOME)
                    continue

                relations = {
                    row["_father_norm"],
                    row["_mother_norm"],
                    row["_husband_norm"],
                }
                relations.discard("")

                if not relations:
                    _add_reason(df, idx, reasons.ADOPTED_NO_RELATIVE)
                    continue

                valid = False

                # Relation matches name
                if relations & names:
                    valid = True

                # Siblings (same father)
                if (
                    row["_father_norm"] and
                    list(house_grp["_father_norm"]).count(row["_father_norm"]) > 1
                ):
                    valid = True

                # Wife → husband is children’s father
                if row["_husband_norm"] and row["_husband_norm"] in fathers:
                    valid = True

                # Man → name appears as husband
                if row["_name_norm"] and row["_name_norm"] in husbands:
                    valid = True

                if not valid:
                    _add_reason(df, idx, reasons.ADOPTED_NO_RELATIVE)
