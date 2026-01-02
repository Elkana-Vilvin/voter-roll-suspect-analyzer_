import re
import pandas as pd

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

EPIC_PATTERN = re.compile(r"^[A-Z]{3}\d{7}$")
INVALID_VALUES = {"", "NAN", "NONE", None}


# --------------------------------------------------
# NORMALIZE EPIC ID (OCR SAFE)
# --------------------------------------------------
def normalize_epic_id(raw):
    """
    Normalize EPIC ID with OCR-safe rules.

    Rules:
    - Ignore empty / NAN / NONE
    - Final EPIC must be exactly 10 chars
    - First 3 letters
    - Next 7 digits
    - OCR fix: O -> 0 in numeric part
    - If length == 11 and contains 'O' in numeric part,
      remove ONE 'O' then re-evaluate
    """

    if raw is None or pd.isna(raw):
        return None

    epic = str(raw).strip().upper()

    if epic in INVALID_VALUES:
        return None

    # Must have at least 10 chars to even attempt
    if len(epic) < 10:
        return epic

    prefix = epic[:3]
    rest = epic[3:]

    # Prefix must be alphabetic
    if not prefix.isalpha():
        return epic

    # --------------------------------------------------
    # CASE 1: length == 11 → remove ONE 'O' from numeric part
    # --------------------------------------------------
    if len(prefix + rest) == 11:
        if "O" in rest:
            rest = rest.replace("O", "", 1)

    # --------------------------------------------------
    # OCR FIX: Replace remaining O → 0 in numeric part
    # --------------------------------------------------
    rest = rest.replace("O", "0")

    # After fixes, numeric part must be exactly 7 digits
    if len(rest) != 7 or not rest.isdigit():
        return prefix + rest

    return prefix + rest


# --------------------------------------------------
# VALIDATE EPIC ID
# --------------------------------------------------
def is_valid_epic(epic):
    """
    Validate final EPIC format.
    Must be exactly:
    - 3 letters
    - 7 digits
    """

    if epic is None or pd.isna(epic):
        return False

    epic = str(epic).strip().upper()

    if epic in INVALID_VALUES:
        return False

    return bool(EPIC_PATTERN.fullmatch(epic))
