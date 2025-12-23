import pandas as pd

# --------------------------------------------------
# REQUIRED COLUMNS (PHASE 4 SCHEMA)
# --------------------------------------------------
REQUIRED_COLUMNS = {
    "serial_no",
    "epic_id",
    "name",
    "father_name",
    "mother_name",
    "husband_name",
    "other_name",
    "age",
    "gender",
    "house_no",
    "street",
    "part_no",
    "assembly",
}

def load_input(path: str) -> pd.DataFrame:
    """
    Load voter data from CSV or Excel and validate schema.
    """

    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Validate required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # -----------------------------
    # Normalize core fields
    # -----------------------------
    df["epic_id"] = df["epic_id"].astype(str).str.strip().str.upper()
    df["name"] = df["name"].astype(str).str.strip()
    df["father_name"] = df["father_name"].astype(str).str.strip()
    df["mother_name"] = df["mother_name"].astype(str).str.strip()
    df["husband_name"] = df["husband_name"].astype(str).str.strip()
    df["other_name"] = df["other_name"].astype(str).str.strip()

    # Age → numeric
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)

    # Gender
    df["gender"] = df["gender"].astype(str).str.upper().str.strip()

    # House / street
    df["house_no"] = df["house_no"].astype(str).str.strip()
    df["street"] = df["street"].astype(str).str.strip()

    # Hierarchy
    # Normalize assembly and extract numeric assembly_no only
    df["assembly"] = df["assembly"].astype(str).str.strip()

    df["assembly_no"] = (
       df["assembly"]
       .str.split("-", n=1)
       .str[0]
       .str.strip()
)

    df["part_no"] = df["part_no"].astype(str).str.strip()

    return df
