# Notes: Database Options for Research Portfolio Management

## 2026-03-04 — Initial investigation

### Setup
- Ubuntu 24.04 environment
- Installed dolt v1.50.1 from GitHub releases tarball
- PostgreSQL 16 available (needed `pg_ctlcluster 16 main start`)
- MongoDB 8.0 available via apt (needed `sudo mongod --dbpath ... --fork`)
- `uv` installed for Python environment management

### Databases tried
- **PostgreSQL**: psycopg2-binary client, portfolio_db with portfolio_user
- **MongoDB**: pymongo client, portfolio_demo database
- **Dolt**: CLI-only (no Python SDK needed), dolt repo at /tmp/portfolio_dolt_repo

### Issues encountered and resolved

#### Dolt: global config required
Running `dolt init` fails without a global user.email/user.name config.
Fixed by calling `dolt config --global --add user.email ...` before init.

#### Dolt: reserved keyword `lead`
`lead` is a reserved SQL keyword in Dolt (window function). Must backtick-quote it:
```sql
CREATE TABLE streams (..., `lead` VARCHAR(120))
```
This is a minor rough edge vs standard MySQL/Postgres compatibility.

#### Dolt: ANSI escape codes in output
`dolt log --oneline` emits ANSI colour codes (e.g. `\x1b[33m` for the hash colour).
When extracting the commit hash with Python `str.split()[0]`, the escape code
is prepended to the hash string, making it invalid for `AS OF` queries.
Fixed by applying `re.sub(r'\x1b\[[0-9;]*m', '', text)` to all dolt output.

#### Dolt: AS OF query hash format
The `AS OF '<hash>'` syntax requires the full 32-char commit hash from `dolt log`.
Branch names (`AS OF 'feature/add-streams'`) also work.
The special `AS OF 'HEAD~3'` ref only works for refs that exist on the current branch.
`AS OF` is used to query a point-in-time projection of the table schema+data.

### Key findings

#### PostgreSQL
- ALTER TABLE is blocking in Postgres (can lock tables). For large tables,
  `pg_repack` or `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL` (instant in PG 11+) is needed.
- Adding a new hierarchy level = new table + FK + data migration.
- No built-in history — must manage migration scripts manually (Flyway, Alembic).

#### MongoDB
- Schema-free is both a strength and a weakness. A `_schema_version` field is essential
  to manage coexisting document shapes during incremental migrations.
- Restructuring (e.g. moving projects into streams) requires application-level migration
  code (no SET/ALTER semantics), but can be done document-by-document without downtime.
- Array filters (`array_filters` in `update_one`) needed for nested array updates.
- No foreign-key enforcement — referential integrity is the app's responsibility.

#### Dolt
- `dolt diff branch1 branch2` shows exact schema (DDL) and data changes — like `git diff`
  for your database. This is extremely useful for reviewing migrations before merge.
- Time-travel (`AS OF`) lets you query the portfolio as it was at any past commit —
  critical for research reproducibility (what projects were active in Q1 2023?).
- Merge conflicts can occur on data (if two branches change the same row) — Dolt
  has a conflict resolution UI/API, similar to git mergetool.
- Performance: Dolt is ~2x slower than MySQL on benchmarks but faster than ever (v1.x).

### Conclusion
Dolt is the most compelling choice for a research portfolio database with frequent
schema changes. The git-like workflow turns schema evolution from a risky manual
process into a safe, reviewable, and reversible operation.
