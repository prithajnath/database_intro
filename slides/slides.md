---
theme: seriph
background: /bg.jpg
title: Intro to Databases
info: |
  ## Intro to Databases
  For complex systems researchers who live in Jupyter and are curious what all the SQL fuss is about.
class: text-center
drawings:
  persist: false
transition: slide-left
comark: true
duration: 35min
fonts:
  sans: "Space Mono"
  mono: "Space Mono"
  provider: google
---

# Intro to Databases

Prithaj Nath

<div @click="$slidev.nav.next" class="mt-12 py-1" hover:bg="white op-10">
  Press Space to begin <carbon:arrow-right />
</div>

---

# Index

<div class="grid grid-cols-1 gap-2 text-left max-w-lg mx-auto mt-6">
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">01</span><span class="text-2xl tracking-widest">MOTIVATION</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">02</span><span class="text-2xl tracking-widest">DEFINITION</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">03</span><span class="text-2xl tracking-widest">RELATIONAL MODEL</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">04</span><span class="text-2xl tracking-widest">SQL</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">05</span><span class="text-2xl tracking-widest">OLAP vs OLTP</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">06</span><span class="text-2xl tracking-widest">PATTERNS</span></div>
  <div class="flex items-baseline gap-4"><span class="text-xs opacity-50">07</span><span class="text-2xl tracking-widest">RESOURCES</span></div>
</div>

---

# 01 — Motivation

Your CSV is fine. Until it isn't.

---

# Start Small: 1K Rows

```python
import csv

with open("employees_small.csv") as f:
    rows = list(csv.DictReader(f))          # load everything into memory

avg = sum(float(r["salary"]) for r in rows) / len(rows)
print(f"Avg salary: {avg:.2f}")
```

Life is good. Fast, readable. Ship it.

<v-click>

**Now try 10 million rows.**

```python
rows = list(csv.DictReader(f))   # OOM, or 45 seconds of swapping
```

`list(reader)` reads the entire file into RAM. At 10M rows × ~200 bytes, that's ~2 GB before you've done anything.

</v-click>

---

# Streaming Fixes Memory — But Breaks Everything Else

```python
total, count = 0.0, 0
with open("employees_large.csv") as f:
    for row in csv.DictReader(f):            # stream line by line
        total += float(row["salary"])
        count += 1
avg = total / count
```

<v-click>

OK, memory fixed. Now add "average salary **by department**."

```python
dept_totals, dept_counts = {}, {}
for row in csv.DictReader(f):
    d = row["department"]
    dept_totals[d] = dept_totals.get(d, 0) + float(row["salary"])
    dept_counts[d] = dept_counts.get(d, 0) + 1

avgs = {d: dept_totals[d] / dept_counts[d] for d in dept_totals}
```

You just wrote a GROUP BY by hand. Every new query rewrites this loop.
**You're building a query engine. Badly.**

</v-click>

---

# Lookup Speed: The O(n) Problem

"What is employee #100's total comp?"

```python
# Scan the entire file for every lookup
for row in csv.DictReader(f):
    if row["id"] == "100":
        print(row)
        break
```

<v-click>

Do that 1,000 times: **O(n × 1000)**. Time it live — it hurts.

</v-click>

<v-click>

**Fix with a hash index:**

```python
index = {row["id"]: row for row in csv.DictReader(f)}  # O(n) once
index["100"]                                            # O(1) forever
```

Fast, but exact-match only. No range queries. Index dies when the script ends.

</v-click>

<v-click>

**Fix with a B+ tree** → O(log n) lookups AND range queries. But now you've written 200 lines of data structure code just to query a CSV.

</v-click>

---

# Other Pain Points (No Time to Demo, But Very Real)

<div grid="~ cols-2 gap-6" class="mt-2">
<div>

- **Concurrency** — two lab members editing the same CSV via Dropbox. The last write wins. Maybe.
- **Schema integrity** — someone puts `"N/A"` in the salary column. Your `float()` call explodes at row 4,817,332.
- **Partial updates** — changing one salary means rewriting the entire file. Crash halfway = corruption.

</div>
<div v-click>

- **Multi-entity joins** — manually joining `employees.csv` and `departments.csv` is fragile and slow.
- **Reproducibility** — an imperative Pandas pipeline is hard to re-read 6 months later.
- **Persistence** — your B+ tree index is gone when the script exits.
- **Composability** — wiring computation outputs to inputs by hand every time.

</div>
</div>

<v-click>

> Everything you just built by hand — streaming, accumulators, B+ tree, crash safety — is what the DBMS does. Automatically. Correctly.

</v-click>

---

# 02 — Definition

What a DBMS actually is

---

# The CSV Is Already a Database

Technically. A database is just an organized collection of structured data stored electronically.

<v-click>

But the moment you need **performance**, **correctness**, or **concurrent access** — the file alone isn't enough.

</v-click>

<v-click>

**The DBMS is the intelligence layer:**

| What you built by hand         | What the DBMS calls it       |
| ------------------------------ | ---------------------------- |
| `for row in csv.DictReader(f)` | Storage engine + buffer pool |
| `dept_totals` accumulator dict | Query executor (GROUP BY)    |
| B+ tree index                  | Index manager                |
| "don't crash mid-write" logic  | Transaction manager + WAL    |
| "only one writer at a time"    | Concurrency control          |

</v-click>

---

# Inside the DBMS

Most of your time as a data practitioner is spent here — talking to the **Query Optimizer**.

<div class="flex gap-8 items-start mt-2">
<div class="flex-shrink-0 text-center" style="width:190px; font-size:0.7em; line-height:1.3">
  <div class="text-slate-400 mb-1">SQL Query</div>
  <div class="text-blue-400 text-lg leading-none">↓</div>
  <div class="border border-slate-500 rounded mt-1 pb-2 px-1">
    <div class="text-slate-400 border-b border-slate-600 py-1 mb-2">DBMS</div>
    <div class="border border-slate-600 rounded py-1 text-slate-300 bg-slate-800">Query Rewrite</div>
    <div class="text-blue-400 text-xs italic leading-tight">↓ rel. algebra</div>
    <div class="border-2 border-blue-500 rounded py-1 font-bold bg-blue-950" style="color:#93c5fd">Query Optimizer ★</div>
    <div class="text-blue-400 text-xs italic leading-tight">↓ query plan</div>
    <div class="border border-slate-600 rounded py-1 text-slate-300 bg-slate-800">Query Executor</div>
    <div class="text-blue-400 text-lg leading-none">↓</div>
    <div class="border border-slate-600 rounded py-1 text-slate-300 bg-slate-800">Memory Buffer</div>
    <div class="text-blue-400 text-lg leading-none">↕</div>
    <div class="border border-slate-600 rounded py-1 text-slate-300 bg-slate-800">Index</div>
  </div>
  <div class="text-blue-400 text-lg leading-none">↕</div>
  <div class="border border-slate-500 rounded py-1 text-slate-300 mt-0">Disk</div>
</div>
<div class="space-y-2 pt-2" style="font-size:0.68em; line-height:1.5">

**Query Rewrite** — parses SQL into a relational algebra tree.

**Query Optimizer ★** — explores equivalent plans, picks the cheapest. Chooses indexes, join order, scan strategy. You don't.

`WHERE a = 1 AND b = 2` → optimizer decides index on `a`, index on `b`, or full scan.

**Query Executor** — runs the plan; pulls data through operators (scan → filter → aggregate).

**Memory Buffer + Index** — caches hot pages; indexes narrow how much disk is read.

<v-click>

> The optimizer is why SQL is worth learning. Same query, 1000x difference in performance depending on the plan it picks.

</v-click>

</div>
</div>

---

# ACID — The Four Guarantees

| Property        | What it means                   | Without it                 |
| --------------- | ------------------------------- | -------------------------- |
| **Atomicity**   | All-or-nothing                  | Half-written bank transfer |
| **Consistency** | Valid state → valid state       | `"N/A"` in salary column   |
| **Isolation**   | Concurrent txns don't interfere | Dropbox edit collision     |
| **Durability**  | Committed data survives crashes | Index gone on restart      |

<v-click>

> **Analogy:** A DBMS is to data files what a filesystem is to raw disk blocks. You'd never hand-manage disk blocks. Why hand-manage data files?

</v-click>

---

# 03 — Relational Model

Tables, keys, and 50 years of not being replaced

---

# Edgar Codd, 1970

The relational model has survived 50+ years. Not because it's perfect, but because it's the most **broadly applicable** model for structured data.

Graph DBs, document stores, time-series DBs — they're all great for specific use cases. But most data in the world fits naturally in tables.

<v-click>

**The core idea:** represent all data as **relations** (tables). Rows are observations. Columns are attributes.

| id  | name  | dept_id | salary |
| --- | ----- | ------- | ------ |
| 1   | Alice | 10      | 120000 |
| 2   | Bob   | 10      | 110000 |
| 3   | Carol | 20      | 150000 |

**Relational algebra** — 4 operations that compose to answer virtually any question: **select** (filter rows), **project** (pick columns), **join** (combine tables), **aggregate** (summarize).

</v-click>

---
layout: image-right
image: /wgaca.png
---

# The Relational Model Keeps Winning

<div style="font-size:0.78em; line-height:1.6">

Stonebraker & Pavlo, 2024 — _"What Goes Around Comes Around… And Around…"_

The original 2005 paper reviewed 40 years of attempts to replace the relational model. The 2024 sequel covers the next 20: MapReduce, key-value stores, document DBs, column families, vector DBs, graph DBs.

<v-click>

The conclusion each time: **SQL absorbed the best ideas and survived.** Every "NoSQL will kill SQL" wave ended with the new system either adding SQL support or fading out.

</v-click>

<v-click>

> _"The RM continues to be the dominant data model and SQL has been extended to capture the good ideas from others."_

They had to write the paper twice because nobody listened the first time.

</v-click>

</div>

---

# SQL is Relational Algebra in Disguise

<div class="flex gap-10 items-start mt-3" style="font-size:0.75em">
<div class="flex-shrink-0" style="width:200px">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-3">The SQL</div>
<pre class="text-xs leading-relaxed bg-slate-900 rounded p-3 border border-slate-700" style="font-size:0.72em">SELECT e.name, d.name
FROM   employees e
JOIN   departments d
  ON   e.dept_id = d.id
WHERE  e.salary > 100000</pre>
<div v-click="5" class="mt-3 text-xs text-slate-400 leading-relaxed">SQL → logical plan: a direct translation of each clause to an algebra operator.</div>
<div v-click="6" class="mt-2 text-orange-300 font-bold leading-snug" style="font-size:0.65em">Predicate pushdown: σ only touches <em>employees</em>, so it moves below ⋈. Join cost is O(n log m) — shrinking n from 10M → 50K is a 200× win. Payoff scales with table size.</div>
<div v-click="7" class="mt-2 text-slate-400 leading-snug">The SQL didn't change. The optimizer rewrote the tree. This is why you declare <em>what</em>, not <em>how</em>.</div>
</div>
<div class="flex-1">
<div class="flex items-center gap-3 mb-2">
  <div v-show="$clicks < 6" class="text-xs text-slate-400 uppercase tracking-widest">Logical Plan</div>
  <div v-show="$clicks >= 6" class="text-xs text-orange-400 uppercase tracking-widest">Physical Plan — after pushdown</div>
</div>
<div class="relative font-mono" style="font-size:0.72em; line-height:1.6">
<div v-show="$clicks < 6">
<div v-click="1" class="flex flex-col items-center">
  <div class="border border-slate-500 rounded px-3 py-1 bg-slate-800 text-slate-200 w-fit">
    <span class="text-yellow-300">π</span><span class="text-slate-400 text-xs"> (project)</span>&nbsp;&nbsp;e.name, d.name
  </div>
  <div class="text-slate-600 text-lg leading-none">│</div>
</div>
<div v-click="2" class="flex flex-col items-center">
  <div class="border border-slate-500 rounded px-3 py-1 bg-slate-800 text-slate-200 w-fit">
    <span class="text-red-300">σ</span><span class="text-slate-400 text-xs"> (select)</span>&nbsp;&nbsp;salary &gt; 100000
  </div>
  <div class="text-slate-600 text-lg leading-none">│</div>
</div>
<div v-click="3" class="flex flex-col items-center">
  <div class="border border-slate-500 rounded px-3 py-1 bg-slate-800 text-slate-200 w-fit">
    <span class="text-green-300">⋈</span><span class="text-slate-400 text-xs"> (join)</span>&nbsp;&nbsp;e.dept_id = d.id
  </div>
  <div class="flex gap-8 mt-1">
    <div class="text-slate-600 text-lg leading-none ml-6">╱</div>
    <div class="text-slate-600 text-lg leading-none mr-6">╲</div>
  </div>
</div>
<div v-click="4" class="flex gap-12 justify-center">
  <div class="border border-slate-600 rounded px-3 py-1 bg-slate-900 text-slate-300">
    <span class="text-blue-300">R</span> employees
  </div>
  <div class="border border-slate-600 rounded px-3 py-1 bg-slate-900 text-slate-300">
    <span class="text-blue-300">R</span> departments
  </div>
</div>
</div>
<div v-show="$clicks >= 6">
<div class="flex flex-col items-center">
  <div class="border border-slate-500 rounded px-3 py-1 bg-slate-800 text-slate-200 w-fit">
    <span class="text-yellow-300">π</span><span class="text-slate-400 text-xs"> (project)</span>&nbsp;&nbsp;e.name, d.name
  </div>
  <div class="text-slate-600 text-lg leading-none">│</div>
  <div class="border border-slate-500 rounded px-3 py-1 bg-slate-800 text-slate-200 w-fit">
    <span class="text-green-300">⋈</span><span class="text-slate-400 text-xs"> (join)</span>&nbsp;&nbsp;e.dept_id = d.id
  </div>
  <div class="flex gap-8 mt-1">
    <div class="text-slate-600 text-lg leading-none ml-4">╱</div>
    <div class="text-slate-600 text-lg leading-none mr-4">╲</div>
  </div>
  <div class="flex gap-8 justify-center">
    <div class="flex flex-col items-center">
      <div class="border-2 border-orange-500 rounded px-3 py-1 bg-slate-800 text-orange-200 w-fit">
        <span class="text-red-300">σ</span><span class="text-slate-400 text-xs"> salary &gt; 100k</span>
      </div>
      <div class="text-slate-600 text-lg leading-none">│</div>
      <div class="border border-slate-600 rounded px-3 py-1 bg-slate-900 text-slate-300">
        <span class="text-blue-300">R</span> employees
      </div>
    </div>
    <div class="flex flex-col items-center" style="margin-top:2.4em">
      <div class="border border-slate-600 rounded px-3 py-1 bg-slate-900 text-slate-300">
        <span class="text-blue-300">R</span> departments
      </div>
    </div>
  </div>
</div>
</div>
</div>
<div v-click="2" class="mt-4 text-xs space-y-1">
  <div><span class="text-yellow-300 font-bold">π</span> &nbsp;Project — <span class="text-slate-400">pick columns</span> &nbsp;→&nbsp; <code>SELECT col1, col2</code></div>
  <div><span class="text-red-300 font-bold">σ</span> &nbsp;Select &nbsp;— <span class="text-slate-400">filter rows &nbsp;</span> &nbsp;→&nbsp; <code>WHERE ...</code></div>
  <div><span class="text-green-300 font-bold">⋈</span> &nbsp;Join &nbsp;&nbsp;&nbsp;— <span class="text-slate-400">combine tables</span> →&nbsp; <code>JOIN ... ON ...</code></div>
  <div><span class="text-blue-300 font-bold">R</span> &nbsp;&nbsp;Relation — <span class="text-slate-400">base table &nbsp;&nbsp;</span> &nbsp;→&nbsp; <code>FROM table</code></div>
</div>
</div>
</div>

---

# 04 — SQL

Declarative queries for people who think in DataFrames

---

# Imperative vs. Declarative

**Imperative (Python):** tell the computer _how_

```python
result = []
for row in employees:
    if row['dept'] == 'Engineering' and row['salary'] > 100000:
        result.append(row)
result.sort(key=lambda r: r['salary'], reverse=True)
```

<v-click>

**Declarative (SQL):** tell the computer _what_

```sql
SELECT *
FROM   employees
WHERE  department = 'Engineering'
  AND  salary > 100000
ORDER  BY salary DESC;
```

You express the question. The **query planner** decides _how_ to answer it — which indexes to use, what join order, whether to scan or seek.

</v-click>

---

# Pandas Is Halfway There

```python
df[df['dept'] == 'Engineering']   # declarative-ish
```

You instinctively wanted to express _what_, not _how_. Pandas just doesn't go far enough.

<v-click>

**The problem with Pandas for data queries:**

- Operation order matters: `filter → join` vs `join → filter` changes performance, and you have to think about it.
- Hits memory walls on large datasets — everyone in this room has seen a `MemoryError`.
- Pipelines are hard to read 6 months later.

</v-click>

<v-click>

**In SQL:** write the query in whatever order reads naturally. The planner reorders for efficiency. Same argument as the B+ tree — you shouldn't have to hand-optimize.

> The pitch is **"SQL for querying, Pandas for the rest"** — expanding your toolkit, not replacing it.

</v-click>

---

# SQL Maps to Relational Algebra

| SQL clause           | Relational algebra | What it does   |
| -------------------- | ------------------ | -------------- |
| `WHERE`              | Select (σ)         | Filter rows    |
| `SELECT col1, col2`  | Project (π)        | Pick columns   |
| `JOIN`               | Join (⋈)           | Combine tables |
| `GROUP BY` + `AVG()` | Aggregate          | Summarize      |

<v-click>

```sql
SELECT   department, AVG(salary) AS avg_salary
FROM     employees
WHERE    hire_date > '2020-01-01'
GROUP BY department
ORDER BY avg_salary DESC;
```

This reads like a specification. Come back 6 months later — still clear. A 20-line Pandas chain requires mental execution.

</v-click>

---

# SQL Scales Beyond RAM

**Pandas:** everything in memory. At 10M rows, you've seen the wall.

**SQL / DuckDB:** processes datasets larger than RAM — streaming, predicate pushdown, columnar scans.

<v-click>

```python
import duckdb

# Reads a 10GB parquet file without loading it into memory
result = duckdb.sql("""
    SELECT   department, AVG(salary)
    FROM     'employees_large.parquet'
    WHERE    hire_date > '2020-01-01'
    GROUP BY department
""").df()  # returns a Pandas DataFrame when you're done
```

Same Python workflow. No server. No setup. DuckDB is in-process like SQLite.

</v-click>

<v-click>

SQL is also the **lingua franca** — Postgres, Snowflake, BigQuery, Spark, DuckDB. 50-year compound returns on one skill.

</v-click>

---

# 05 — OLAP vs OLTP

Two very different workloads. You're doing one of them.

---

# The Simple Version

**OLTP** = (Online Transcation Processing) optimized for INSERT / UPDATE

**OLAP** = (Online Analytical Processing) optimized for SELECT (over millions of rows)

<v-click>

**OLTP example:**

> Your bank processing a wire transfer — one row updated, sub-millisecond, highly concurrent.

**OLAP example:**

> "What's the average salary by department across 10 million employees, filtered by hire date?"

</v-click>

<v-click>

**For this audience:** you're doing analytical workloads. Traditional databases (Postgres) can handle it, but they're not optimized for it. OLAP tools like **DuckDB** are designed for exactly what you do — scan-heavy, read-heavy, analytical queries on local data.

> "Postgres feels like overkill for a CSV" is valid. But the answer isn't raw Python — it's a better tool.

</v-click>

---

# The Landscape

<div class="mt-4 grid grid-cols-2 gap-6">
<div>
<div class="text-slate-400 text-xs uppercase tracking-widest mb-3">OLTP — Transactional</div>
<div class="flex gap-6 items-center mb-4">
<div class="text-center">
<img :src="'/postgres.svg'" class="h-12 mx-auto mb-1" />
<div class="text-xs text-slate-400">PostgreSQL</div>
</div>
<div class="text-center">
<img :src="'/mysql.jpg'" class="h-12 mx-auto mb-1 rounded" />
<div class="text-xs text-slate-400">MySQL</div>
</div>
</div>
<div class="text-xs text-white-500 leading-relaxed">General-purpose. Strong consistency, row storage, B+ tree indexes. Reach for these when you have concurrent writes, foreign keys, and transactional workloads.</div>
</div>
<div>
<div class="text-slate-400 text-xs uppercase tracking-widest mb-3">OLAP — Analytical</div>
<div class="flex gap-6 items-center mb-4">
<div class="text-center">
<img :src="'/duckdb.webp'" class="h-12 mx-auto mb-1" />
<div class="text-xs text-slate-400">DuckDB</div>
</div>
<div class="text-center">
<img :src="'/snowflake.png'" class="h-12 mx-auto mb-1" />
<div class="text-xs text-slate-400">Snowflake</div>
</div>
<div class="text-center">
<img :src="'/bigquery.svg'" class="h-12 mx-auto mb-1" />
<div class="text-xs text-slate-400">BigQuery</div>
</div>
</div>
<div class="text-xs text-white-500 leading-relaxed">Columnar storage, vectorized execution, built for aggregations. DuckDB runs in-process. Snowflake and BigQuery are managed cloud warehouses — same SQL, petabyte scale.</div>
</div>
</div>

---

# Why Row Storage Hurts for OLAP

Traditional (OLTP) databases store data **row by row** on disk:

```
[id=1, Alice, Engineering, 120000, 2019-03-01]
[id=2, Bob,   Engineering, 110000, 2021-07-15]
[id=3, Carol, Marketing,   150000, 2018-11-30]
...
```

<v-click>

Query: `SELECT AVG(salary) FROM employees`

To compute this, the DB reads **every column of every row** off disk — even though you only need the salary column.

At 10M rows × 200 bytes/row = **2 GB read** to sum one column.

</v-click>

---

# Columnar Storage: The OLAP Superpower

OLAP databases store data **column by column**:

```
salaries:  [120000, 110000, 150000, 95000, ...]
names:     [Alice, Bob, Carol, Dave, ...]
depts:     [Engineering, Engineering, Marketing, Marketing, ...]
```

<v-click>

`SELECT AVG(salary)` reads **only the salary column** — ~8 bytes/row instead of 200.

**10–100x speedup on wide tables.** And that's before compression.

</v-click>

<v-click>

**Compression bonus:** same-type values stored together compress dramatically.

- Salary column: run-length, delta, or bit-packing encoding.
- Department column: dictionary encoding (store "Engineering" once, use 1-byte codes).

Less I/O >> CPU cost of decompression.

</v-click>

---

# Zone Maps: Free Indexes

OLAP systems split data into chunks (~100K–1M rows per "row group"). For each chunk, they store **min and max per column**.

```
Row group 1: salary ∈ [50000, 120000]
Row group 2: salary ∈ [130000, 210000]
Row group 3: salary ∈ [45000, 115000]
```

<v-click>

Query: `WHERE salary > 200000`

Row groups 1 and 3 are **entirely skipped** — max salary ≤ 120K and 115K respectively. Only row group 2 is read.

This is a coarse-grained index that costs almost nothing to maintain, requires zero configuration, and works automatically.

</v-click>

<v-click>

This is why DuckDB's docs say "don't add secondary indexes for analytical queries" — zone maps + columnar scanning are usually faster than B+ tree lookups for OLAP patterns.

</v-click>

---

# Vectorized Execution

Traditional query engines process one row at a time through a pipeline of operators.

OLAP engines process **batches of column values** (vectors) through tight CPU loops:

```
AVG(salary):
  chunk = salary_column[0:1024]    # load 1024 values into CPU cache
  sum  += SIMD_add(chunk)          # add 8 floats at once with AVX2
  ...
```

<v-click>

Same idea that makes NumPy fast:

```python
# Slow: Python loop
total = sum(row["salary"] for row in rows)

# Fast: vectorized
total = np.sum(salary_array)       # SIMD, cache-local, compiled
```

DuckDB uses the same trick at the query engine level — automatically, for every query.

</v-click>

---

# OLTP vs OLAP — Side by Side

|                    | OLTP                    | OLAP                               |
| ------------------ | ----------------------- | ---------------------------------- |
| **Query type**     | Point lookups / updates | Aggregations over millions of rows |
| **Storage layout** | Row-oriented            | Column-oriented                    |
| **Index type**     | B+ tree                 | Zone maps + columnar scan          |
| **Execution**      | Row-at-a-time           | Vectorized batches                 |
| **Schema**         | Normalized (3NF)        | Denormalized / star schema         |
| **Examples**       | Postgres, MySQL         | DuckDB, BigQuery, Snowflake        |
| **Your workload**  | ❌                      | ✅                                 |

---

# DuckDB: OLAP in Your Notebook

```python
import duckdb

# Query a Parquet file
duckdb.sql("SELECT AVG(salary) FROM 'employees.parquet'")

# Query a Pandas DataFrame directly — zero copy
import pandas as pd
df = pd.read_csv("employees_small.csv")
duckdb.sql("SELECT department, AVG(salary) FROM df GROUP BY department")

# Chain back to Pandas
result = duckdb.sql("SELECT * FROM df WHERE salary > 100000").df()
```

<v-click>

- **In-process** — no server, no Docker, `pip install duckdb`
- **Reads parquet, CSV, and DataFrames natively** — no conversion
- **Uses ART indexes** for PK/unique constraints, but relies on zone maps + columnar scan for everything else
- **SQL is the query layer** — same syntax you'd use on Snowflake or BigQuery

</v-click>

---

# 06 — Patterns

5 SQL patterns every researcher needs

---

# Pattern 1 — GROUP BY

The SQL equivalent of `df.groupby().agg()`. One declarative step for bucketing + math.

<div class="flex gap-8 mt-4">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Pandas</div>

```python
df.groupby('department').agg(
    headcount=('id', 'count'),
    avg_salary=('salary', 'mean')
)
```

</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">SQL</div>

```sql
SELECT   department,
         COUNT(*)       AS headcount,
         AVG(salary)    AS avg_salary
FROM     employees
GROUP BY department;
```

</div>
</div>

<v-click>

**Golden rule:** every column in `SELECT` that isn't inside an aggregate function (`AVG`, `SUM`, `COUNT`, `MAX`, `MIN`) **must** appear in `GROUP BY`. The DB will error if you forget — this is a feature, not a bug.

</v-click>

<v-click>

```sql
-- Add a filter on the aggregated result with HAVING (not WHERE — that runs before aggregation)
SELECT   department, AVG(salary) AS avg_salary
FROM     employees
GROUP BY department
HAVING   AVG(salary) > 100000;
```

</v-click>

---

# Pattern 2 — CTEs

Long queries nest into unreadable subquery soup. CTEs let you write SQL top-to-bottom, like a Python script.

<div class="flex gap-8 mt-3">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Pandas — intermediate vars</div>

```python
df_senior = df[df['salary'] > 100_000]
df_dept   = df_senior.groupby('dept_id') \
                     .agg(n=('id','count'))
df_final  = df_dept[df_dept['n'] > 2]
```

</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">SQL — CTEs</div>

```sql
WITH senior AS (
  SELECT * FROM employees
  WHERE  salary > 100000
),
dept_counts AS (
  SELECT   dept_id, COUNT(*) AS n
  FROM     senior
  GROUP BY dept_id
)
SELECT d.name, dc.n
FROM   dept_counts dc
JOIN   departments d ON dc.dept_id = d.id
WHERE  dc.n > 2;
```

</div>
</div>

<v-click>

Each `WITH` block is a named, reusable result — testable in isolation. Exactly like assigning an intermediate DataFrame to a variable, except the DB can optimise across all steps at once.

</v-click>

---

# Pattern 3 — CASE WHEN

The SQL equivalent of `np.where()` / `pd.cut()`. Conditional logic and on-the-fly binning, inline.

<div class="flex gap-8 mt-3">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Salary bands</div>

```sql
SELECT name,
  CASE
    WHEN salary < 80000  THEN 'Junior'
    WHEN salary < 130000 THEN 'Mid'
    ELSE                      'Senior'
  END AS band
FROM employees;
```

</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Conditional aggregation (pivot)</div>

```sql
SELECT
  department,
  SUM(CASE WHEN salary > 100000
           THEN 1 ELSE 0 END) AS senior_count,
  SUM(CASE WHEN salary <= 100000
           THEN 1 ELSE 0 END) AS junior_count
FROM employees
GROUP BY department;
```

</div>
</div>

<v-click>

The right column is a **pivot without a pivot table** — `CASE WHEN` inside an aggregate creates custom summary columns for any condition. Equivalent to `df.pivot_table()` but composable with any other SQL clause.

</v-click>

---

# Pattern 4 — JOINs

Research data is never in one table. `LEFT JOIN` is your safest default.

<div class="flex gap-8 mt-3">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">INNER JOIN — only matched rows</div>

```sql
SELECT e.name, d.name AS dept
FROM   employees e
JOIN   departments d
  ON   e.dept_id = d.id;
-- drops employees with no dept
```

</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">LEFT JOIN — keep all left rows</div>

```sql
SELECT e.name, d.name AS dept
FROM   employees e
LEFT JOIN departments d
  ON   e.dept_id = d.id;
-- dept = NULL for unmatched rows
```

</div>
</div>

<v-click>

**Watch out — fan-out.** If `departments` has duplicate `id` values (it shouldn't, but messy data happens), every matching employee row gets multiplied. Row count explodes silently. Always `COUNT(*)` before and after a join when working with unfamiliar data.

```sql
-- Sanity check: does dept_id uniquely identify a department?
SELECT dept_id, COUNT(*) FROM departments GROUP BY dept_id HAVING COUNT(*) > 1;
```

</v-click>

---

# Pattern 5 — Window Functions

Aggregates per group **without** collapsing rows. The analytical powerhouse.

<div class="flex gap-8 mt-2">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Rank within group</div>

```sql
SELECT name, department, salary,
  RANK() OVER (
    PARTITION BY department
    ORDER BY salary DESC
  ) AS dept_rank
FROM employees;
```

<div class="text-xs text-slate-500 mt-1">≈ df.groupby('dept')['salary'].rank()</div>
</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Delta between rows (LAG)</div>

```sql
SELECT name, salary, hire_date,
  salary - LAG(salary) OVER (
    PARTITION BY department
    ORDER BY hire_date
  ) AS salary_delta
FROM employees;
```

<div class="text-xs text-slate-500 mt-1">≈ df.groupby('dept')['salary'].diff()</div>
</div>
</div>

<v-click>

`OVER()` is the keyword that opens the window. `PARTITION BY` = `groupby`. `ORDER BY` = sequence. No subquery needed, rows stay intact. Also works for running totals (`SUM(...) OVER`), rolling averages, percentile ranks — all in one pass.

</v-click>

---

# Pattern 5 (cont.) — Rolling Average

"3-month rolling average salary, per department." A one-liner in SQL. A lookup-every-time in Pandas.

<div class="flex gap-6 mt-3">
<div class="flex-1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">Pandas</div>

```python
df.sort_values('hire_date', inplace=True)

df['rolling_avg'] = (
  df.groupby('department')['salary']
    .transform(lambda x:
        x.rolling(3, min_periods=1).mean()
    )
)
```

<div class="text-xs text-slate-500 mt-2">groupby + transform + rolling + lambda.<br>Most people google this every time.</div>
</div>
<div class="flex-1" v-click="1">
<div class="text-xs text-slate-400 uppercase tracking-widest mb-2">SQL</div>

```sql
SELECT
  name,
  department,
  hire_date,
  AVG(salary) OVER (
    PARTITION BY department
    ORDER BY hire_date
    ROWS BETWEEN 2 PRECEDING
             AND CURRENT ROW
  ) AS rolling_avg_salary
FROM employees;
```

<div class="text-xs text-slate-500 mt-2">Reads like a spec. Single pass.<br>No intermediate objects.</div>
</div>
</div>

<v-click>

**`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`** — a physical window of 3 rows. There's also `RANGE BETWEEN`, which operates on value ranges (e.g. all rows within 30 days) rather than row counts — useful for irregular time series where gaps matter.

</v-click>

---

# 07 — Resources

Where to go from here

---

# Learning Resources

<div grid="~ cols-2 gap-8" class="mt-4">
<div>

**Books**

- _Designing Data-Intensive Applications_ — Kleppmann  
  (the bible; read this first)
- _Database Internals_ — Petrov  
  (storage engines, B-trees deep dive)
- _DuckDB: Up and Running_ — emerging, check O'Reilly

**Papers**

- Codd (1970) — "A Relational Model of Data"
- Stonebraker & Hellerstein — _"What Goes Around Comes Around"_ (and the 2024 sequel — they had to write it again because nobody listened)

</div>
<div v-click>

**Interactive**

- [duckdb.org/docs](https://duckdb.org/docs) — excellent, start here
- [pgexercises.com](https://pgexercises.com) — SQL practice
- [use-the-index-luke.com](https://use-the-index-luke.com) — index deep dive
- [Leetcode] (https://leetcode.com) - SQL practice
- [explain.depesz.com/] (https://explain.depesz.com/) — Interactive query plans

**Videos**

- CMU 15-445 Database Systems — Andy Pavlo (free on YouTube). Genuinely entertaining. Watch lecture 1 just for the intro.

**Tools**

- **DuckDB** — start here for analytical work
- **SQLite** — when you need persistence, zero config
- **DBeaver** / **TablePlus** — GUI clients

</div>
</div>

---

<Youtube id="otE2WvX3XdQ" width="800" height="450" :params="{ start: 0, end: 51 }" />

---

# That's a Wrap

<div class="mt-6 space-y-1 opacity-60 text-sm">

01 Motivation — why your CSV breaks at 10M rows

02 Definition — DBMS as the intelligence layer, ACID

03 Relational Model — tables, keys, Codd's 4 operations

04 SQL — declarative queries, "SQL for querying, Pandas for the rest"

05 OLAP vs OLTP — columnar storage, zone maps, vectorized execution, DuckDB

06 Patterns — star schema, soft deletes, window functions

07 Resources — Kleppmann, Pavlo, Stonebraker

</div>

<div class="mt-10 text-sm opacity-40">Questions?</div>
