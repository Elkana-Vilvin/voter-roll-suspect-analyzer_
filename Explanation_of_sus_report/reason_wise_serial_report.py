import os
from collections import defaultdict


def generate_reason_wise_serial_report(df, output_dir):
    """
    Generates a simple reason-wise serial number report.
    """

    output_path = os.path.join(
        output_dir, "reason_wise_serial_report.txt"
    )

    # Collect serial numbers per reason
    reason_map = defaultdict(list)

    for idx, row in df.iterrows():
        if not row["is_suspect"]:
            continue

        serial_no = idx + 1  # human-readable serial number

        for reason in row["suspect_reasons"]:
            reason_map[reason].append(serial_no)

    with open(output_path, "w", encoding="utf-8") as f:
        for reason in sorted(reason_map.keys()):
            serials = reason_map[reason]

            f.write(
                f"{reason} - total suspects ---- {len(serials):02d}\n"
            )
            f.write("-" * 50 + "\n")

            for s in serials:
                f.write(f"Ser No: {s}\n")

            f.write("\n")

    print(
        f"[OK] Reason-wise serial report written to {output_path}"
    )
