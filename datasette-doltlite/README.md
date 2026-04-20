# Datasette + Doltlite: Version-Controlled SQL with a Web UI

## TL;DR

**Yes, Datasette works with Doltlite.** With two small workarounds (a monkey-patch for memory databases and single-threaded SQL execution), Datasette provides a full web UI and JSON API for browsing and querying Doltlite's version-controlled databases — including commit history, row-level diffs, blame, and time-travel queries.

## What is Doltlite?

[Doltlite](https://github.com/dolthub/doltlite) is a SQLite fork that replaces the B-tree storage engine with a content-addressed prolly tree, enabling **Git-like version control on a SQL database**. It provides:

- `dolt_commit()` / `dolt_add()` — stage and commit changes
- `dolt_log` — commit history
- `dolt_diff_<table>` — row-level diffs between commits
- `dolt_blame_<table>` — which commit last modified each row
- `dolt_at_<table>('ref')` — point-in-time queries
- `dolt_branch()` / `dolt_merge()` — branching and merging
- `dolt_history_<table>` — full version history per row

## What is Datasette?

[Datasette](https://github.com/simonw/datasette) is a tool for exploring and publishing SQLite databases via a web UI and JSON API. It provides instant table browsing, filtering, custom SQL queries, and programmatic API access.

## How It Works

Doltlite is a **drop-in replacement** for SQLite at the C library level. Using `LD_PRELOAD`, we swap in `libdoltlite.so` so that Python's built-in `sqlite3` module (and therefore Datasette) uses the Doltlite engine transparently:

```bash
# Build doltlite from source
cd /path/to/doltlite/build && ../configure && make

# Run datasette with doltlite backend
LD_PRELOAD=/path/to/libdoltlite.so datasette serve my_database.db
```

### Workarounds Required

1. **Named memory databases:** Doltlite doesn't support `file:<name>?mode=memory&cache=shared` URIs. Datasette's internal metadata database uses this. Fix: monkey-patch `Database.connect` to redirect to a temp file.

2. **Thread safety:** Doltlite can segfault under concurrent multi-threaded access. Fix: set `--setting num_sql_threads 1` in Datasette to serialize SQL execution.

Both workarounds are implemented in the included [`launch_datasette.py`](launch_datasette.py) wrapper script.

## Features Tested

| Feature | Works? | Access Method |
|---------|--------|---------------|
| Table browsing | ✅ | Datasette UI (auto-discovered) |
| Sorting/filtering | ✅ | Datasette UI |
| JSON/CSV API | ✅ | `GET /table.json?_shape=array` |
| Commit history | ✅ | SQL: `SELECT * FROM dolt_log` |
| Row-level diffs | ✅ | SQL: `SELECT * FROM dolt_diff_employees` |
| Diff statistics | ✅ | SQL: `SELECT * FROM dolt_diff_stat('HEAD~2', 'HEAD')` |
| Blame | ✅ | SQL: `SELECT * FROM dolt_blame_employees` |
| Time-travel | ✅ | SQL: `SELECT * FROM dolt_at_employees('commit_hash')` |
| Row history | ✅ | SQL: `SELECT * FROM dolt_history_employees WHERE id=1` |
| Branches | ✅ | SQL: `SELECT * FROM dolt_branches` |
| Diff summary | ✅ | SQL: `SELECT * FROM dolt_diff_summary('HEAD~2', 'HEAD')` |

> **Note:** Doltlite's virtual tables (dolt_log, dolt_branches, etc.) don't auto-appear in Datasette's table list — they must be queried via the SQL interface. User tables are fully auto-discovered.

## Quick Start

```bash
# 1. Build doltlite
git clone https://github.com/dolthub/doltlite.git
cd doltlite/build && ../configure && make

# 2. Install datasette
pip install datasette  # or: uv add datasette

# 3. Create a database with version control
LD_PRELOAD=/path/to/libdoltlite.so python3 create_db.py

# 4. Launch datasette
LD_PRELOAD=/path/to/libdoltlite.so python3 launch_datasette.py serve \
    /path/to/database.db --port 8001 --cors
```

## Limitations

- **Single-threaded SQL:** Required to avoid segfaults in doltlite's prolly tree engine
- **LD_PRELOAD only:** No pip-installable package for doltlite yet; must build from source
- **Linux only:** `LD_PRELOAD` is a Linux mechanism (macOS uses `DYLD_INSERT_LIBRARIES`)
- **No write UI:** Datasette is read-only by default; dolt_commit() etc. need write access
- **Virtual table visibility:** Dolt virtual tables must be queried via SQL, not browsed in the UI

## Files

- `launch_datasette.py` — Datasette wrapper with doltlite workarounds
- `demo.md` — Showboat demo document with screenshots and executable examples
- `notes.md` — Detailed experiment notes
- `screenshot-*.png` — Screenshots of Datasette serving doltlite data
