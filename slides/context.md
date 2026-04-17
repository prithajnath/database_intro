# Database Tutorial for the Lab

**Audience:** Complex systems researchers, PhD students. Heavy Pandas/Jupyter users with little to no database experience.
**Tone:** Informal, conversational. Use humor (Pavlo clips, Stonebraker paper).

---

## Talk Structure

### 1. Live Demo: Scaling Pain Points

Start with a Python script (`analyze.py`) that queries a CSV using pure Python — no Pandas, no NumPy. Use `generate_data.py` to create increasingly large employee datasets. Progressively uncomment code to reveal complexity.

**Escalation sequence:**

- **Memory.** Small CSV (1K rows) loads entirely into memory. Life is good. Jump to 10M+ rows — the naive `list(reader)` approach either crawls or OOMs. Switch to streaming with `csv.DictReader` line by line, but now you can't do `sum(salaries)/len(salaries)` because you never hold the full list. You need running accumulators. The code doubles in complexity for the same computation.
- **Complexity.** "Average salary by department" requires a dict of accumulators. Add "hired after 2020" and the loop body keeps growing. Every new query means rewriting loop logic. You're building a query engine by hand.
- **Lookup speed.** "What is employee #100's total comp?" requires scanning the entire file. Time it live. Then do it 1000 times — O(n) per lookup is brutal. Build a hash index (dict) — instant, but exact-match only. Then build a B+ tree — fast AND supports range queries. Print the tree structure so the audience can see the hierarchy.

**Other pain points to mention briefly (not demo'd):**

- Concurrency / shared access (two people editing the same CSV via Dropbox)
- Schema evolution / data integrity (someone puts "N/A" in the salary column)
- Composability (output of one computation → input of another, wired by hand)
- Persistence of computed state (your in-memory index dies when the script ends)
- Partial updates (changing one salary means rewriting the entire file; crash = corruption)
- Multi-entity relationships / joins (manually joining two CSVs is fragile)
- Reproducibility (imperative Pandas pipelines vs. declarative SQL)

**Scripts:**

- `generate_data.py` — generates employee CSVs at any scale
- `analyze.py` — six phases, progressively uncommented during the talk
- `btree.py` — self-contained B+ tree with insert, point search, range search, `print_tree()`

### 2. What Is a Database?

**Core definition:** A database = DBMS (the software/intelligence layer) + the data files.

- The CSV on disk is technically a database. But the moment you need performance, correctness, or concurrent access, the file alone isn't enough.
- The DBMS is the intelligence layer: query processor, storage engine, concurrency manager, recovery system. Everything you just built by hand — streaming logic, accumulators, the B+ tree, crash-safe writes — is what the DBMS does.
- The data files are surprisingly dumb. Pages, blocks, structured bytes. Without the DBMS, they're meaningless.

**Analogy:** A DBMS is to data files what the filesystem is to raw disk blocks. You'd never hand-manage disk blocks; why hand-manage data files?

**Subsystems (brief mention):** Query parser/optimizer, storage engine, buffer pool, transaction manager. Each solves one of the pain points from the demo. Emphasize the query planner — it bridges declarative queries and physical execution, choosing indexes, join orders, and scan strategies so you don't have to.

**Humor:** Plug Andy Pavlo's lecture intro and a screenshot of Stonebraker & Hellerstein's "What Goes Around Comes Around" paper (and its 2024 sequel — "they had to write it again because nobody listened").

### 3. Why the Relational Model?

The relational model is the most general and principled model for structured data. Acknowledge other models exist for specialized use cases (graph, document, time series), but the relational model has survived 50+ years because it's the most broadly applicable.

Be careful with "best" — frame as "most general" to avoid inviting challenges from people who work with non-relational data.

### 4. Why SQL?

**The case against Python for data interaction (frame carefully — the audience loves Python):**

- Python is over-specified for data queries. Writing a loop to filter rows means telling the computer *how*. You care about *what*: "all employees in engineering with salary above 100K." This is the imperative vs. declarative distinction.
- Pandas is halfway there — `df[df['dept'] == 'engineering']` is more declarative. They instinctively wanted to express *what*, not *how*. Pandas just doesn't go far enough.
- In Pandas, operation order matters (filter before join vs. join before filter). In SQL, you write the query in whatever order reads naturally and the planner reorders for efficiency.
- The optimizer does work you'd otherwise do yourself — choosing indexes, join strategies, scan methods. Same argument as the B+ tree demo: you shouldn't have to hand-optimize.

**Relational algebra (brief, intuitive):**

- Codd (1970): virtually any data question decomposes into select (filter rows), project (pick columns), join (combine tables), aggregate (summarize).
- These operations are closed over relations — tables in, tables out — so they compose freely.
- Analogy for the audience: this is the same insight that makes linear algebra powerful. A small set of operations closed over a common structure gives you a complete, composable system. You express Ax = b and let the library choose the algorithm; you express a SQL query and let the planner choose the execution.

**SQL is the punchline:** A human-readable syntax for relational algebra. `SELECT` = project, `WHERE` = select, `JOIN` = join, `GROUP BY` = aggregate. The language maps to the algebra, which maps to composable operations, which the planner compiles into an efficient plan.

**Additional arguments:**

- Readability/reproducibility — a SQL query reads like a specification. Come back 6 months later, it's still clear. A 20-line Pandas chain requires mental execution.
- Memory scales differently — databases can process datasets larger than RAM. Everyone's hit Pandas memory walls.
- Composability across data sources — DuckDB queries CSVs, parquet, and DataFrames with the same SQL.
- Lingua franca — SQL transfers across Postgres, Snowflake, BigQuery, Spark, DuckDB. 50-year compound returns.

**Honest acknowledgment:** SQL has real weaknesses for iterative exploration (no easy `df.head()` between steps). The pitch is "SQL for querying, Pandas for the rest" — expanding their toolkit, not replacing it.

### 5. OLTP vs. OLAP

Keep it simple: OLTP is optimized for INSERT/UPDATE, OLAP is optimized for SELECT. Crude but appropriate for the audience.

**One concrete example for each side:** "OLTP is your bank processing a transfer. OLAP is you asking what's the average salary by department across 10 million records."

**Why this matters for the audience:** They're doing analytical workloads. Traditional databases (Postgres) can feel like overkill. OLAP tools like DuckDB are designed for exactly what they do — scan-heavy, read-heavy, analytical queries on local data. This validates "Postgres feels like too much" while redirecting them to the right tool.

**B+ Trees vs. OLAP Indexing (transition from the B+ tree demo):**

B+ trees are an OLTP construct — designed for point lookups and small updates on row-oriented storage. OLAP databases mostly don't use them because analytical queries scan millions of rows and aggregate; a B+ tree on `employee_id` is useless for `AVG(salary)`.

OLAP systems use a different bag of tricks:

- **Columnar storage.** Store each column contiguously. `AVG(salary)` reads only the salary column, not names, departments, or dates. 10-100x speedup on wide tables.
- **Compression.** Same-type values stored together compress dramatically — run-length, dictionary, bit-packing. Less I/O > CPU cost of decompression.
- **Zone maps / min-max indexes.** Split data into chunks (DuckDB: "row groups," ~100K-1M rows), store min/max per column per chunk. `WHERE salary > 200000` skips entire chunks where `max_salary <= 200000`. A coarse-grained index that costs almost nothing to maintain.
- **Vectorized execution.** Process batches of column values through tight CPU loops exploiting SIMD and cache locality. Same idea that makes NumPy fast.
- **Bloom filters for joins.** Build a bloom filter from the small table's join keys to discard rows from the large table before the join.

**DuckDB specifics:**

- In-process (like SQLite) — `import duckdb` and you're done. No server, no setup.
- Reads parquet, CSV, and Pandas DataFrames natively with zero conversion.
- Uses ART (Adaptive Radix Tree) indexes for PKs/unique constraints, but docs explicitly recommend *against* secondary indexes for analytical queries — zone maps + columnar scanning are usually faster.

**Framing for the talk:** "I taught you B+ trees because they're the cleanest way to see the *idea* of an index — trading space for time with a precomputed lookup structure. The specific data structures vary by database, but the concept is universal."

### 6. Hands-on SQL with DuckDB

*(To be developed.)*

---

## Files

| File | Purpose |
|---|---|
| `generate_data.py` | Generate employee CSVs at any scale (1K to 50M+ rows) |
| `analyze.py` | Progressive analysis script — six phases, uncomment during talk |
| `btree.py` | B+ tree implementation with insert, search, range search, print |
