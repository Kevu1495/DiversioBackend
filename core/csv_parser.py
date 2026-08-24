import logging
import pandas as pd
logger = logging.getLogger(__name__)




REQUIRED_HEADERS = {
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
}


def parse_csv(csv_file):
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.fillna("")

    if set(df.columns) != REQUIRED_HEADERS:
        logger.warning(f"Invalid CSV headers. Expected: {REQUIRED_HEADERS}")
        raise ValueError(f"Invalid CSV headers. Expected: {REQUIRED_HEADERS}")

    df['employee_id'] = df['employee_id'].astype(str).str.strip()
    df['employee_name'] = df['employee_name'].astype(str).str.strip()
    df['email'] = df['email'].astype(str).str.strip().str.lower()
    df['manager_id'] = df['manager_id'].astype(str).str.strip()
    df['manager_email'] = df['manager_email'].astype(str).str.strip().str.lower()
    df['department'] = df['department'].astype(str).str.strip()
    df['row_number'] = df.index + 2

    duplicate_id_mask = df.duplicated(subset=['employee_id'], keep=False)
    duplicate_email_mask = df.duplicated(subset=['email'], keep=False)

    is_valid_mask = (
            df['employee_id'].str.strip().ne('') &
            df['email'].str.strip().ne('') &
            ~duplicate_id_mask &
            ~duplicate_email_mask
    )

    df_accepted = df[is_valid_mask]
    df_invalid = df[~is_valid_mask]

    accepted_rows = df_accepted.to_dict('records')
    invalid_rows = []

# this is to add error messages to the invalid rows
    for _, row in df_invalid.iterrows():
        errors = []
        if pd.isna(row['employee_id']): errors.append("employee_id is required")
        if pd.isna(row['email']): errors.append("email is required")
        if duplicate_id_mask.loc[_]: errors.append("duplicate employee_id")
        if duplicate_email_mask.loc[_]: errors.append("duplicate email")

        invalid_rows.append({
            "row_number": int(row["row_number"]),
            "employee_id": row["employee_id"],
            "errors": errors,
        })
    logger.info(f"CSV parsing completed. Total rows: {len(df)}, Accepted: {len(accepted_rows)}, Invalid: {len(invalid_rows)}")
    root_employees, manager_relationships, manager_report_counts, manager_errors = resolve_relationships(accepted_rows)

    cyclic_employees = find_cycles(manager_relationships)

    # 9. Final Response
    return {
        "total_rows": len(df),
        "accepted_rows": accepted_rows,
        "invalid_rows": invalid_rows,
        "root_employees": root_employees,
        "manager_relationships": manager_relationships,
        "manager_report_counts": manager_report_counts,
        "manager_errors": manager_errors,
        "cyclic_employees": cyclic_employees,
    }

def resolve_relationships(accepted_rows):
    """
    Takes a list of clean employee dictionaries and resolves
    their reporting lines and counts.
    """
    employees_by_id = {row["employee_id"]: row for row in accepted_rows}
    employees_by_email = {row["email"]: row for row in accepted_rows}

    root_employees = []
    manager_relationships = []
    manager_errors = []

    for row in accepted_rows:
        manager_id = row["manager_id"]
        manager_email = row["manager_email"]

        # Case 1: No manager
        if not manager_id and not manager_email:
            root_employees.append(row)
            continue

        # Case 2: manager_id only
        if manager_id and not manager_email:
            manager = employees_by_id.get(manager_id)
            if manager is None:
                manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "manager_id not found"})
                continue
            if manager["employee_id"] == row["employee_id"]:
                manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "employee cannot manage themselves"})
                continue
            manager_relationships.append({"employee": row, "manager": manager})
            continue

        # Case 3: manager_email only
        if not manager_id and manager_email:
            manager = employees_by_email.get(manager_email)
            if manager is None:
                manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "manager_email not found"})
                continue
            if manager["employee_id"] == row["employee_id"]:
                manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "employee cannot manage themselves"})
                continue
            manager_relationships.append({"employee": row, "manager": manager})
            continue

        # Case 4: Both provided (Safety Check)
        manager_by_id = employees_by_id.get(manager_id)
        manager_by_email = employees_by_email.get(manager_email)

        if manager_by_id is None:
            manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "manager_id not found"})
            continue
        if manager_by_email is None:
            manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "manager_email not found"})
            continue
        if manager_by_id["employee_id"] != manager_by_email["employee_id"]:
            manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "manager_id and manager_email refer to different employees"})
            continue
        if manager_by_id["employee_id"] == row["employee_id"]:
            manager_errors.append({"row_number": row["row_number"], "employee_id": row["employee_id"], "error": "employee cannot manage themselves"})
            continue

        manager_relationships.append({"employee": row, "manager": manager_by_id})

    # Direct-report counts
    manager_report_counts = {}
    for rel in manager_relationships:
        m_id = rel["manager"]["employee_id"]
        manager_report_counts[m_id] = manager_report_counts.get(m_id, 0) + 1

    return root_employees, manager_relationships, manager_report_counts, manager_errors


# ---------------------------------------------------------
# HELPER: CYCLE DETECTION
# ---------------------------------------------------------
def find_cycles(manager_relationships):
    manager_map = {r["employee"]["employee_id"]: r["manager"]["employee_id"] for r in manager_relationships}

    cyclic_employees = set()
    visited_globally = set()  # To ensure O(N) efficiency

    for emp_id in manager_map:
        if emp_id in visited_globally:
            continue

        # This list tracks the current chain we are walking
        current_path = []
        path_set = set()  # For O(1) lookups within the current chain

        curr = emp_id
        while curr in manager_map:
            if curr in path_set:
                # CYCLE DETECTED!
                # Find where the cycle starts in our current path and add those members
                cycle_start_idx = current_path.index(curr)
                for i in range(cycle_start_idx, len(current_path)):
                    cyclic_employees.add(current_path[i])
                break

            if curr in visited_globally:
                # We hit a chain we already fully explored; no new cycle here
                break

            # Add to our current "walk"
            current_path.append(curr)
            path_set.add(curr)

            # Move to the next link in the "list"
            curr = manager_map[curr]

        # Mark everything we walked through as visited so we never walk it again
        for person in current_path:
            visited_globally.add(person)

    return sorted(list(cyclic_employees))
