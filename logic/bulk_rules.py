from models import reasons

INVALID_VALUES = {"", "NAN", "NONE"}


def apply_bulk_rules(df):
    """
    BULK_10_PLUS applies ONLY when:
    - street is known
    - house number is known
    Grouping: STREET → HOUSE
    """

    for street, street_grp in df.groupby("street_norm"):

        # 🚫 Skip missing street
        if street in INVALID_VALUES:
            continue

        for house_no, grp in street_grp.groupby("house_no_norm"):

            # 🚫 Skip missing house number
            if house_no in INVALID_VALUES:
                continue

            if len(grp) > 10:
                for idx in grp.index:
                    df.at[idx, "suspect_reasons"].append(
                        reasons.BULK_10_PLUS
                    )
