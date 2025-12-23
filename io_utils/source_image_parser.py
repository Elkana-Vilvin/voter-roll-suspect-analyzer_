import re

STATE_CODE_MAP = {
    "S01": "Andhra Pradesh",
    "S02": "Arunachal Pradesh",
    "S03": "Assam",
    "S04": "Bihar",
    "S05": "Goa",
    "S06": "Gujarat",
    "S07": "Haryana",
    "S08": "Himachal Pradesh",
    "S09": "Jammu & Kashmir",
    "S10": "Karnataka",
    "S11": "Kerala",
    "S12": "Madhya Pradesh",
    "S13": "Maharashtra",
    "S14": "Manipur",
    "S15": "Meghalaya",
    "S16": "Mizoram",
    "S17": "Nagaland",
    "S18": "Odisha",
    "S19": "Punjab",
    "S20": "Rajasthan",
    "S21": "Sikkim",
    "S22": "Tamil Nadu",
    "S23": "Tripura",
    "S24": "Uttar Pradesh",
    "S25": "West Bengal",
    "S26": "Chhattisgarh",
    "S27": "Jharkhand",
    "S28": "Uttarakhand",
    "S29": "Telangana",
    "U01": "Andaman & Nicobar Islands",
    "U02": "Chandigarh",
    "U03": "Dadra & Nagar Haveli and Daman & Diu",
    "U04": "Delhi (NCT)",
    "U05": "Lakshadweep",
    "U06": "Puducherry",
    "U07": "Ladakh",
}


def parse_source_image(source_image: str):
    """
    Extract state_code, state_name, assembly_no, booth_no from source_image.
    """

    if not source_image or str(source_image).lower() in ["nan", "none"]:
        return None, None, None, None

    source_image = str(source_image)

    # State code (S22, U04 etc.)
    state_match = re.search(r"(S\d{2}|U\d{2})", source_image)
    state_code = state_match.group(1) if state_match else None
    state_name = STATE_CODE_MAP.get(state_code)

    # Assembly number (e.g., -116-)
    assembly_match = re.search(r"-(\d{1,3})-FinalRoll", source_image)
    assembly_no = assembly_match.group(1) if assembly_match else None

    # Booth / Part number (ENG-246-WI)
    booth_match = re.search(r"ENG-(\d+)-WI", source_image)
    booth_no = booth_match.group(1) if booth_match else None

    return state_code, state_name, assembly_no, booth_no
