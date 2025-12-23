import re
from models import reasons


def apply_door_rules(df):
    """
    Door number rules:
    - HOUSE_NO_UNAVAILABLE → empty / nan / none
    - INVALID_HOUSE_NO → contains NO digits at all
      (A ❌, BX ❌, 12 ✔, A1 ✔, 12B ✔, B14/2 ✔)
    """

    for idx, row in df.iterrows():
        house_no = str(row["house_no"]).strip()

        # Case 1: house number unavailable
        if house_no.lower() in ["", "nan", "none"]:
            df.at[idx, "suspect_reasons"].append(
                reasons.HOUSE_NO_UNAVAILABLE
            )
            continue

        # Case 2: invalid house number (NO digit anywhere)
        if not re.search(r"\d", house_no):
            df.at[idx, "suspect_reasons"].append(
                reasons.INVALID_HOUSE_NO
            )
