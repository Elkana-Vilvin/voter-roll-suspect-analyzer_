from models import reasons
from utils.names import normalize

INVALID_VALUES = {"", "NAN", "NONE"}


def _add_reason(df, idx, reason):
    """Add reason safely (no duplicates)"""
    if reason not in df.at[idx, "suspect_reasons"]:
        df.at[idx, "suspect_reasons"].append(reason)


def apply_family_rules(df):
    """
    FAMILY RULES — HOUSE-CENTRIC, SYMMETRIC & CORRECT

    Core rule:
    - If a house has >1 people AND
    - NO valid family linkage exists between ANY pair
      → ALL people in that house are ADOPTED_NO_RELATIVE

    Valid family linkage means AT LEAST ONE of:
    1. Relation (father/mother/husband) matches someone's NAME
    2. Siblings: same father AND father exists as a PERSON in the house
    3. Wife → husband matches children's father
    4. Man → his name appears as someone's husband
    """

    # --------------------------------------------------
    # NORMALIZE NAME FIELDS
    # --------------------------------------------------
    df["_name_norm"] = df["name"].apply(normalize)
    df["_father_norm"] = df["father_name"].apply(normalize)
    df["_mother_norm"] = df["mother_name"].apply(normalize)
    df["_husband_norm"] = df["husband_name"].apply(normalize)

    # --------------------------------------------------
    # STREET → HOUSE
    # --------------------------------------------------
    for street, street_grp in df.groupby("street_norm"):

        # Street missing
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
            # HOUSE CONTEXT
            # --------------------------------------------------
            names = set(house_grp["_name_norm"])
            fathers = set(house_grp["_father_norm"])
            mothers = set(house_grp["_mother_norm"])
            husbands = set(house_grp["_husband_norm"])

            linked = set()  # indices that have ≥1 valid family link

            # --------------------------------------------------
            # PER-PERSON FAMILY CHECK
            # --------------------------------------------------
            for idx in indices:
                row = df.loc[idx]

                relations = {
                    row["_father_norm"],
                    row["_mother_norm"],
                    row["_husband_norm"],
                }
                relations.discard("")

                valid = False

                # 1️⃣ Relation matches someone's NAME
                if relations & names:
                    valid = True

                # 2️⃣ Siblings:
                # SAME father AND father exists as a PERSON in house
                if (
                    row["_father_norm"]
                    and row["_father_norm"] in names
                    and list(house_grp["_father_norm"]).count(
                        row["_father_norm"]
                    ) > 1
                ):
                    valid = True

                # 3️⃣ Wife → husband is children's father
                if (
                    row["_husband_norm"]
                    and row["_husband_norm"] in fathers
                ):
                    valid = True

                # 4️⃣ Man → his name appears as husband
                if (
                    row["_name_norm"]
                    and row["_name_norm"] in husbands
                ):
                    valid = True

                if valid:
                    linked.add(idx)

            # --------------------------------------------------
            # FINAL DECISION
            # --------------------------------------------------

            # NO LINKS AT ALL → FLAG EVERYONE
            if not linked:
                for idx in indices:
                    _add_reason(
                        df, idx, reasons.ADOPTED_NO_RELATIVE
                    )
                continue

            # SOME LINKS EXIST → FLAG ONLY UNLINKED
            for idx in indices:
                if idx not in linked:
                    _add_reason(
                        df, idx, reasons.ADOPTED_NO_RELATIVE
                    )
