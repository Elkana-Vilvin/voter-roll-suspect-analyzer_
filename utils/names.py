import re
import pandas as pd

def normalize(name):
    """
    Strong, OCR-safe name normalization
    Used ONLY for family linking (not duplicates)
    """
    if pd.isna(name):
        return ""

    name = str(name).upper().strip()

    if name in {"", "NAN", "NONE"}:
        return ""

    # Remove OCR junk
    name = re.sub(r"[~=\-_.]", " ", name)

    # Remove non-letters (keep spaces)
    name = re.sub(r"[^A-Z\s]", "", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)

    return name.strip()
