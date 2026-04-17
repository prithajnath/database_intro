"""
Analyze employee CSV data using pure Python.

This script is structured as a progression for a live database tutorial.
Start with Phase 1 enabled only, then progressively uncomment later phases
as you scale up the CSV size to demonstrate pain points.

Phases:
    1. Naive in-memory analysis       (small CSV, life is good)
    2. Streaming analysis              (file too big for memory)
    3. Multi-pass aggregations         (per-department stats)
    4. Naive point lookups             (O(n) scan per query)
    5. Hash index for point lookups    (O(1) but memory-hungry)
    6. B+ tree index for range queries (the payoff)

Usage:
    python analyze.py employees_small.csv
    python analyze.py employees_large.csv
"""

import csv
import sys
import time
from contextlib import contextmanager
import pandas as pd


@contextmanager
def timer(label):
    """Context manager to time a block and print the result."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"  [{label}] {elapsed:.4f}s")


# =============================================================================
# PHASE 1: Naive in-memory analysis
# -----------------------------------------------------------------------------
# This is the "life is good" version. Load the whole file into memory,
# compute stats with simple list comprehensions. Works great for small data.
# =============================================================================


def phase1_in_memory(path):
    print("\n=== PHASE 1: In-memory analysis ===")

    with timer("load entire file"):
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    print(f"  loaded {len(rows):,} rows")

    with timer("average salary"):
        salaries = [int(r["salary"]) for r in rows]
        avg = sum(salaries) / len(salaries)
    print(f"  average salary: ${avg:,.2f}")

    with timer("max salary"):
        max_sal = max(int(r["salary"]) for r in rows)
    print(f"  max salary: ${max_sal:,}")


# =============================================================================
# PHASE 2: Streaming analysis
# -----------------------------------------------------------------------------
# File no longer fits in memory (or is too slow to load). Switch to streaming.
# Note how we now need RUNNING ACCUMULATORS because we can't hold all values.
# The code is already getting more complex for the SAME computation.
# =============================================================================

# def phase2_streaming(path):
#     print("\n=== PHASE 2: Streaming analysis ===")
#
#     with timer("streaming average + max"):
#         total = 0
#         count = 0
#         max_sal = 0
#         with open(path) as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 sal = int(row["salary"])
#                 total += sal
#                 count += 1
#                 if sal > max_sal:
#                     max_sal = sal
#         avg = total / count
#
#     print(f"  rows processed: {count:,}")
#     print(f"  average salary: ${avg:,.2f}")
#     print(f"  max salary: ${max_sal:,}")
#     print("  NOTE: we now maintain running accumulators manually.")


# =============================================================================
# PHASE 3: Multi-pass / grouped aggregations
# -----------------------------------------------------------------------------
# "Average salary BY DEPARTMENT" - now we need a dict of accumulators.
# Add another condition ("hired after 2020") and the loop body keeps growing.
# You're writing a query engine by hand.
# =============================================================================

# def phase3_grouped(path):
#     print("\n=== PHASE 3: Grouped aggregation (avg salary by department) ===")
#
#     with timer("group by department"):
#         dept_totals = {}
#         dept_counts = {}
#         with open(path) as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 dept = row["department"]
#                 sal = int(row["salary"])
#                 dept_totals[dept] = dept_totals.get(dept, 0) + sal
#                 dept_counts[dept] = dept_counts.get(dept, 0) + 1
#
#     print("  department averages:")
#     for dept in sorted(dept_totals):
#         avg = dept_totals[dept] / dept_counts[dept]
#         print(f"    {dept:15s} ${avg:>12,.2f}  (n={dept_counts[dept]:,})")
#
#     # Now add a filter: only employees hired after 2020
#     print("\n  Now: avg salary by dept, hired after 2020")
#     with timer("group by department, filtered"):
#         dept_totals = {}
#         dept_counts = {}
#         with open(path) as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 if row["hire_date"] < "2020-01-01":
#                     continue
#                 dept = row["department"]
#                 sal = int(row["salary"])
#                 dept_totals[dept] = dept_totals.get(dept, 0) + sal
#                 dept_counts[dept] = dept_counts.get(dept, 0) + 1
#
#     print("  department averages (post-2020 hires):")
#     for dept in sorted(dept_totals):
#         avg = dept_totals[dept] / dept_counts[dept]
#         print(f"    {dept:15s} ${avg:>12,.2f}  (n={dept_counts[dept]:,})")
#     print("  NOTE: every new query = new loop. You're building a query engine.")


# =============================================================================
# PHASE 4: Naive point lookups - O(n) scan per query
# -----------------------------------------------------------------------------
# "What is employee #100's total compensation?" Scan the whole file.
# Do this for 1000 different employees and watch it crawl.
# This motivates the index.
# =============================================================================


def phase4_naive_lookup(path, lookup_ids):
    print("\n=== PHASE 4: Naive point lookups (linear scan per query) ===")

    def find_employee(emp_id):
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["employee_id"]) == emp_id:
                    return row
        return None

    with timer(f"look up {len(lookup_ids)} employees (full scan each)"):
        rows = []
        for emp_id in lookup_ids:
            emp = find_employee(emp_id)
            if emp:
                # print(
                #     f"  last lookup: employee #{lookup_ids[-1]} = {emp['first_name']} {emp['last_name']}"
                # )
                rows.append(emp)
        print(pd.DataFrame(rows))
    print("  NOTE: each lookup scans the ENTIRE file. O(n) per query.")


# =============================================================================
# PHASE 5: Hash index - O(1) lookups but no range queries
# -----------------------------------------------------------------------------
# Build a dict mapping employee_id -> row. Now lookups are instant.
# But what if we want "all employees with salary between 80K and 120K"?
# A hash index can't do that.
# =============================================================================

# def phase5_hash_index(path, lookup_ids):
#     print("\n=== PHASE 5: Hash index ===")
#
#     with timer("build hash index"):
#         index = {}
#         with open(path) as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 index[int(row["employee_id"])] = row
#     print(f"  indexed {len(index):,} employees")
#
#     with timer(f"look up {len(lookup_ids)} employees (hash)"):
#         for emp_id in lookup_ids:
#             emp = index[emp_id]
#     print(f"  last lookup: employee #{lookup_ids[-1]} = {emp['first_name']} {emp['last_name']}")
#     print("  FAST! But this only works for exact-match queries on employee_id.")
#     print("  What about 'salary BETWEEN 80000 AND 120000'? Hash can't help.")


# =============================================================================
# PHASE 6: B+ tree index - the payoff
# -----------------------------------------------------------------------------
# This is the closer. Build a B+ tree on salary, show point lookups AND
# range queries working fast. Then reveal: this is what CREATE INDEX does.
# (B+ tree implementation will be a separate file - see btree.py)
# =============================================================================


def phase6_btree_index(path):
    print("\n=== PHASE 6: B+ tree index on salary ===")
    from btree import BPlusTree  # separate module

    with timer("build B+ tree on salary"):
        tree = BPlusTree(order=32)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                tree.insert(int(row["salary"]), int(row["employee_id"]))

    with timer("range query: salary between 80000 and 82000"):
        results = tree.range_search(80000, 82000)
    print(f"  found {len(results):,} employees in range")
    print("  NOTE: leaves are linked, so range scan is sequential after finding start.")


# =============================================================================
# Main: wire up the phases
# =============================================================================


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <csv_file>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"Analyzing: {path}")

    # --- Enable phases progressively as you scale up the data ---
    # phase1_in_memory(path)

    # phase2_streaming(path)

    # phase3_grouped(path)

    lookup_ids = [
        100,
        5000,
        50_000,
        500_000,
        999_999,
        35_237_463,
    ]  # adjust to data size
    phase4_naive_lookup(path, lookup_ids)

    # phase5_hash_index(path, lookup_ids)

    phase6_btree_index(path)


if __name__ == "__main__":
    main()
