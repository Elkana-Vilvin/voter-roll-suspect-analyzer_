import os
from collections import defaultdict


def generate_evidence_report(df, output_dir):
    path = os.path.join(output_dir, "evidence_report.txt")

    total_voters = len(df)
    suspects = df[df["is_suspect"]]

    reason_map = defaultdict(list)
    for idx, row in suspects.iterrows():
        for reason in row["suspect_reasons"]:
            reason_map[reason].append(idx)

    with open(path, "w", encoding="utf-8") as f:
        f.write("EVIDENCE-BACKED SUSPECT REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total voters: {total_voters}\n")
        f.write(f"Total suspects: {len(suspects)}\n\n")

        for reason, indices in sorted(reason_map.items()):
            f.write(f"Reason: {reason}\n")
            f.write(f"Total flagged: {len(indices)}\n")
            f.write("-" * 52 + "\n")

            for idx in indices:
                row = df.loc[idx]

                f.write(f"EPIC: {row['epic_id']}\n")
                f.write(f"Serial No: {row['serial_no']}\n")
                f.write(f"Name: {row['name']}\n")
                f.write(f"House: {row['house_no']}\n")
                f.write("Reasons:\n")
                for r in row["suspect_reasons"]:
                    f.write(f" - {r}\n")

                f.write("\nExplanation:\n")
                write_explanation(f, row, reason)
                f.write("-" * 52 + "\n")

    print(f"[OK] Evidence report written to {path}")


def write_explanation(f, row, reason):
    age = row["age"]

    if reason == "AGE_ZERO_OR_INVALID":
        f.write(f"  Age value = {age}\n")
        f.write("  Rule: age <= 0 is invalid\n")
        f.write("  Conclusion: AGE_ZERO_OR_INVALID triggered\n")

    elif reason == "UNDER_18":
        f.write(f"  Age = {age}\n")
        f.write("  Rule: age < 18\n")
        f.write("  Conclusion: UNDER_18 triggered\n")

    


    elif reason == "HOUSE_NO_UNAVAILABLE":
        f.write(f"  House number value = '{row['house_no']}'\n")
        f.write("  Rule: house number is missing or unavailable\n")
        f.write("  Interpretation: data not provided or unreadable\n")
        f.write("  Conclusion: HOUSE_NO_UNAVAILABLE triggered\n")

    elif reason == "INVALID_HOUSE_NO":
        f.write(f"  House number value = '{row['house_no']}'\n")
        f.write("  Rule: house number must contain at least one digit (0–9)\n")
        f.write("  Observation: value contains only alphabetic characters\n")
        f.write("  Conclusion: INVALID_HOUSE_NO triggered\n")
 

   

    elif reason == "DUPLICATE_EPIC_ID":
        f.write(f"  EPIC ID '{row['epic_id']}' appears more than once in this booth\n")
        f.write("  Conclusion: DUPLICATE_EPIC_ID triggered\n")

    elif reason == "SAME_NAME_IN_SAME_HOUSE":
        f.write("  Self-row consistency check:\n")
        f.write(f"   - name = '{row['name']}'\n")
        f.write(f"   - father_name = '{row['father_name']}'\n")
        f.write(f"   - mother_name = '{row['mother_name']}'\n")
        f.write(f"   - husband_name = '{row['husband_name']}'\n")
        f.write("  Rule: voter name must not equal their own parent/spouse name\n")
        f.write("  Conclusion: SAME_NAME_IN_SAME_HOUSE triggered\n")

    elif reason == "BULK_10_PLUS":
        f.write("  House contains more than 10 registered voters\n")
        f.write("  Conclusion: BULK_10_PLUS triggered\n")

    # ---------------- NEW FAMILY RULES ----------------

    elif reason == "ORPHAN_ONLY_PERSON_IN_HOME":
        f.write("  Observation:\n")
        f.write("   - Only one voter is registered under this house number\n")
        f.write("  Interpretation:\n")
        f.write("   - This may represent a single-person household or incomplete data\n")
        f.write("  Conclusion:\n")
        f.write("   - ORPHAN_ONLY_PERSON_IN_HOME flagged for manual verification\n")

    elif reason == "ADOPTED_NO_RELATIVE":
       f.write("  Observation:\n")
       f.write("   - Multiple voters exist in the same street and house\n")
       f.write("   - The voter has declared parent/spouse information OR none\n")
       f.write("   - No declared relation could be resolved within the same house\n\n")

       f.write("  Checked logic:\n")
       f.write("   - Direct name match with father/mother/husband\n")
       f.write("   - Reverse linkage (child ↔ parent)\n")
       f.write("   - Husband acting as father of another voter\n\n")

       f.write("  Conclusion:\n")
       f.write("   - No valid family linkage found inside the house\n")
       f.write("   - ADOPTED_NO_RELATIVE flagged for manual verification\n")

    # --------------------------------------------------

    else:
        f.write("  Rule triggered based on deterministic business logic\n")
        f.write(f"  Conclusion: {reason} triggered\n")
