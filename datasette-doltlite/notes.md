# Datasette + Doltlite Experiment Notes

## What we're testing
Can [Datasette](https://github.com/simonw/datasette) (v0.65.2) serve a [Doltlite](https://github.com/dolthub/doltlite) (v0.8.0) database?

## Key findings

### 1. Doltlite is a C-level SQLite replacement
- Not a Python library — it's a fork of SQLite that replaces the B-tree storage engine with a prolly tree
- Uses the same `sqlite3.h` header and API as regular SQLite
- Python can use it via `LD_PRELOAD=libdoltlite.so` — zero code changes needed in Python's sqlite3 module

### 2. Building doltlite
- Standard autotools build: `cd build && ../configure && make`
- Produces `libdoltlite.so` (shared) and `libdoltlite.a` (static)
- Also produces the `doltlite` CLI (replacement for `sqlite3`)
- Build requires: gcc, make, zlib-dev, tcl

### 3. Doltlite file format
- Doltlite databases use a different on-disk format (prolly tree chunk store)
- Regular SQLite **cannot** read doltlite files ("file is not a database")
- `LD_PRELOAD` is required for any tool to read doltlite databases

### 4. Workaround #1: Named memory databases
- **Problem:** Datasette uses `file:<name>?mode=memory&cache=shared` for its internal metadata database
- Doltlite doesn't support this URI format — returns "unable to open database file"
- **Fix:** Monkey-patch `Database.connect` to redirect memory databases to a temp file
- Simple 15-line patch in `launch_datasette.py`

### 5. Workaround #2: Thread safety
- **Problem:** Doltlite segfaults (SIGSEGV, exit code 139) under concurrent multi-threaded access
- This happens when datasette's default thread pool processes parallel requests (e.g., browser loading page + CSS + JS)
- **Fix:** Set `--setting num_sql_threads 1` to serialize all database access
- This means slightly slower response times but complete stability

### 6. What works through Datasette
- ✅ Standard table browsing (employees, departments)
- ✅ Sorting, filtering, pagination
- ✅ JSON API (`/table.json?_shape=array`)
- ✅ CSV export
- ✅ Custom SQL queries
- ✅ `dolt_log` — commit history
- ✅ `dolt_diff_<table>` — row-level diffs with to_/from_ columns
- ✅ `dolt_diff_stat(from, to)` — aggregate change counts
- ✅ `dolt_diff_summary(from, to)` — high-level table change classification
- ✅ `dolt_blame_<table>` — which commit last modified each row
- ✅ `dolt_at_<table>('commit')` — point-in-time queries (time travel!)
- ✅ `dolt_history_<table>` — all versions of a row across commits
- ✅ `dolt_branches` — list branches
- ✅ `dolt_tags` — list tags

### 7. Virtual tables not auto-discovered
- Dolt's virtual tables (`dolt_log`, `dolt_branches`, etc.) don't appear in Datasette's table list
- They're only accessible via the custom SQL query interface
- This is expected — SQLite virtual tables aren't in `sqlite_master` by default
- User tables (employees, departments) are fully auto-discovered

### 8. Performance note
- With `num_sql_threads=1`, datasette is single-threaded for SQL execution
- This is fine for exploration/demo use but not ideal for production
- The doltlite thread safety issue might be fixed in future versions

## Tools used
- `uv` for Python environment management
- `datasette` v0.65.2
- `doltlite` v0.8.0 (built from source)
- `rodney` for browser automation and screenshots
- `showboat` for demo document
