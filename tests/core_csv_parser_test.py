import io
import pytest
from core.csv_parser import parse_csv, find_cycles


def test_identity_integrity():
    csv_content = (
        "employee_id,employee_name,email,manager_id,manager_email,department\n"
        "101,Alice,alice@test.com,,,\n"  # Row 2
        "101,Alice Clone,alt@test.com,,,\n"  # Row 3 (Duplicate ID)
        "102,Bob,bob@test.com,101,,\n"  # Row 4 (Reports to invalid manager)
    )

    fake_file = io.BytesIO(csv_content.encode("utf-8"))

    result = parse_csv(fake_file)

    assert len(result["invalid_rows"]) == 2
    assert len(result["accepted_rows"]) == 1
    assert len(result["manager_relationships"]) == 0


def test_cycle_precision():
    csv_content = (
        "employee_id,employee_name,email,manager_id,manager_email,department\n"
        "1,A,a@test.com,2,,\n"  # A reports to B
        "2,B,b@test.com,3,,\n"  # B reports to C
        "3,C,c@test.com,1,,\n"  # C reports to A (Cycle!)
        "4,D,d@test.com,1,,\n"  # D reports to A (Not in cycle)
    )

    fake_file = io.BytesIO(csv_content.encode("utf-8"))

    result = parse_csv(fake_file)

    cyclic_employees = find_cycles(result["manager_relationships"])

    assert set(cyclic_employees) == {"1", "2", "3"}
    assert "4" not in cyclic_employees