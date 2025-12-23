from collections import defaultdict

SAMPLE_LIMIT = 5


def build_reason_index(df):
    """
    Build mapping:
    reason -> list of row indices
    """
    reason_map = defaultdict(list)
    for idx, row in df.iterrows():
        for r in row["suspect_reasons"]:
            reason_map[r].append(idx)
    return reason_map


def explanation_1(row, df, reason):
    """
    WHY this person was flagged
    """
    sn = row["serial_no"]
    house = row.get("house_no", "")
    street = row.get("street", "")
    booth = row.get("part_no", "")
    assembly = row.get("assembly", "")

    if reason == "DUPLICATE_EPIC_ID":
        matches = df[df["epic_id"] == row["epic_id"]]
        others = matches[matches["serial_no"] != sn]["serial_no"].tolist()
        return (
            f"Serial number {sn} shares the same EPIC ID ({row['epic_id']}) "
            f"with serial number(s) {others} in the same assembly."
        )

    if reason == "DUPLICATE_DETAILS":
        matches = df[
            (df["name"] == row["name"]) &
            (df["age"] == row["age"]) &
            (df["gender"] == row["gender"]) &
            (df["house_no"] == row["house_no"])
        ]
        others = matches[matches["serial_no"] != sn]["serial_no"].tolist()
        return (
            f"Serial number {sn} has identical personal details as "
            f"serial number(s) {others}, despite having a different EPIC ID."
        )

    if reason == "ORPHAN_ONLY_PERSON_IN_HOME":
        return (
            f"Serial number {sn} is the only voter listed under house number "
            f"{house} on street '{street}' in booth {booth}."
        )

    if reason == "ADOPTED_NO_RELATIVE":
        return (
            f"In house number {house} on street '{street}', serial number {sn} "
            f"has no matching father, mother, or husband name among other residents "
            f"of the same house."
        )

    if reason == "BULK_10_PLUS":
        return (
            f"House number {house} on street '{street}' contains more than 10 voters, "
            f"which exceeds the allowed household threshold."
        )

    if reason == "HOUSE_NO_UNAVAILABLE":
        return (
            f"Serial number {sn} has no valid house number recorded."
        )

    if reason == "INVALID_HOUSE_NO":
        return (
            f"House number '{house}' for serial number {sn} contains no numeric digits "
            f"and is considered invalid."
        )

    if reason == "STREET_NAME_UNAVAILABLE":
        return (
            f"Serial number {sn} has no street name recorded, preventing household-level verification."
        )

    return f"Serial number {sn} was flagged due to rule: {reason}."


def explanation_2(row, df, reason, reason_index):
    """
    CONTEXT: how widespread this issue is
    """
    sn = row["serial_no"]
    booth = row.get("part_no", "")
    assembly = row.get("assembly", "")

    affected = reason_index.get(reason, [])
    count = len(affected)

    sample = [
        df.loc[i, "serial_no"]
        for i in affected
        if df.loc[i, "serial_no"] != sn
    ][:SAMPLE_LIMIT]

    if booth:
        return (
            f"In booth {booth}, {count} voters are flagged under {reason}. "
            f"Sample serial numbers include: {sample}."
        )

    return (
        f"In assembly {assembly}, {count} voters are flagged under {reason}. "
        f"Sample serial numbers include: {sample}."
    )
