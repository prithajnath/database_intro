"""
Generate a synthetic employee dataset for the database tutorial demo.

Usage:
    python generate_data.py --rows 1000 --out employees_small.csv
    python generate_data.py --rows 1000000 --out employees_medium.csv
    python generate_data.py --rows 50000000 --out employees_large.csv

The schema is intentionally simple but rich enough to motivate
filtering, grouping, joining, and range queries.
"""

import argparse
import csv
import random
from datetime import date, timedelta

DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Finance", "HR",
    "Operations", "Research", "Legal", "Support", "Product",
]

LOCATIONS = [
    "Boston", "New York", "San Francisco", "Austin", "Seattle",
    "Chicago", "Denver", "Atlanta", "Remote", "Burlington",
]

FIRST_NAMES = [
    "Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley",
    "Jamie", "Avery", "Quinn", "Parker", "Rowan", "Sage", "Blake",
    "Drew", "Hayden", "Reese", "Skyler", "Emerson", "Finley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
    "Jackson", "Martin",
]

# Department salary baselines - creates realistic structure for aggregations
DEPT_SALARY_BASE = {
    "Engineering": 110_000,
    "Sales": 85_000,
    "Marketing": 75_000,
    "Finance": 95_000,
    "HR": 70_000,
    "Operations": 72_000,
    "Research": 105_000,
    "Legal": 120_000,
    "Support": 60_000,
    "Product": 100_000,
}


def random_date(start_year=2010, end_year=2024):
    """Return a random hire date within the given range."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_row(employee_id):
    """Generate a single employee record with realistic structure."""
    dept = random.choice(DEPARTMENTS)
    base_salary = DEPT_SALARY_BASE[dept]
    # Salary varies +/- 40% around department baseline
    salary = int(base_salary * random.uniform(0.6, 1.4))
    # Bonus is roughly 5-25% of salary
    bonus = int(salary * random.uniform(0.05, 0.25))

    return {
        "employee_id": employee_id,
        "first_name": random.choice(FIRST_NAMES),
        "last_name": random.choice(LAST_NAMES),
        "department": dept,
        "location": random.choice(LOCATIONS),
        "hire_date": random_date().isoformat(),
        "salary": salary,
        "bonus": bonus,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate employee CSV for demo")
    parser.add_argument("--rows", type=int, required=True, help="Number of rows")
    parser.add_argument("--out", type=str, required=True, help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)

    fieldnames = [
        "employee_id", "first_name", "last_name", "department",
        "location", "hire_date", "salary", "bonus",
    ]

    print(f"Generating {args.rows:,} rows -> {args.out}")
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(1, args.rows + 1):
            writer.writerow(generate_row(i))
            # Progress indicator for large files
            if i % 1_000_000 == 0:
                print(f"  wrote {i:,} rows...")

    print(f"Done: {args.out}")


if __name__ == "__main__":
    main()
