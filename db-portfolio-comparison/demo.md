# Database Options for Research Portfolio Management: Dolt vs PostgreSQL vs MongoDB

*2026-03-04T10:06:08Z by Showboat 0.6.1*
<!-- showboat-id: 6d28cf41-f6b1-4653-8be9-a5e364908be5 -->


## Context

A research organisation manages a multi-level portfolio: **Programs** → **Streams** → **Projects**.

The structure evolves frequently — new hierarchy levels are added, new fields introduced,
and relationships between entities change. Three databases are evaluated for their ability
to handle this kind of _schema evolution_ gracefully:

| Database   | Type             | Key feature                        |
|------------|------------------|------------------------------------|
| PostgreSQL | Relational       | ACID, mature, ALTER TABLE          |
| MongoDB    | Document store   | Schemaless, flexible JSON docs     |
| Dolt       | Relational + VCS | Git-like branching for schema+data |

All three demos use the same portfolio mock data and perform three schema migrations:

- **V1** baseline: Programs → Projects (flat)
- **V2**: Add Streams as a middle layer between Programs and Projects
- **V3**: Add `priority` (int) and `tags` (array) columns to projects

## PostgreSQL Demo

PostgreSQL uses **ALTER TABLE** migrations to evolve the schema. Changes are permanent and
require careful coordination in production (locks, downtime windows, rollback scripts).
Each migration here is applied as a set of DDL statements.

The schema starts flat (programs → projects) then grows a streams layer and new columns.

```bash
cd /home/runner/work/experiments/experiments/db-portfolio-comparison && PATH="$HOME/.local/bin:$PATH" uv run python postgres_demo.py
```

```output

[PostgreSQL] V1: programs → projects
  ✓ create tables
  ✓ insert mock data

  === V1 data ===
    program=Climate Science | project=Arctic Ice Modelling | status=active
    program=Climate Science | project=Carbon Flux Analysis | status=active
    program=Genomics Initiative | project=CRISPR Toolkit Dev | status=planning
    program=Genomics Initiative | project=Protein Folding Study | status=active

[PostgreSQL] V2 migration: add streams layer
  ✓ apply V2 migration

  === V2 data (with streams) ===
    program=Climate Science | stream=Modelling & Simulation | project=Arctic Ice Modelling | status=active
    program=Climate Science | stream=Modelling & Simulation | project=Carbon Flux Analysis | status=active
    program=Genomics Initiative | stream=Computational Bio | project=CRISPR Toolkit Dev | status=planning
    program=Genomics Initiative | stream=Computational Bio | project=Protein Folding Study | status=active

[PostgreSQL] V3 migration: add priority + tags columns
  ✓ apply V3 migration

  === V3 data (with priority + tags) ===
    program=Climate Science | stream=Modelling & Simulation | project=Arctic Ice Modelling | status=active | priority=1 | tags=['ice', 'modelling']
    program=Climate Science | stream=Modelling & Simulation | project=Carbon Flux Analysis | status=active | priority=2 | tags=['carbon', 'climate']
    program=Genomics Initiative | stream=Computational Bio | project=CRISPR Toolkit Dev | status=planning | priority=3
    program=Genomics Initiative | stream=Computational Bio | project=Protein Folding Study | status=active | priority=1 | tags=['proteins', 'computational']

[PostgreSQL] Demo complete.
```

## MongoDB Demo

MongoDB stores each **Program** as a document with nested sub-documents (first projects,
then streams). Schema changes are applied document-by-document without any global DDL.
A `_schema_version` field allows the application to handle both old and new formats simultaneously.

Key observations:
- V1→V2 requires restructuring nested arrays (projects moved into streams sub-documents)
- V3 adds fields only to selected documents — others remain valid without the new fields
- The `CRISPR Toolkit Dev` project deliberately shows a document with no tags/priority

```bash
cd /home/runner/work/experiments/experiments/db-portfolio-comparison && PATH="$HOME/.local/bin:$PATH" uv run python mongodb_demo.py
```

```output

[MongoDB] V1: programs with embedded projects
  ✓ inserted V1 documents

  === V1 data ===
    program=Climate Science (schema_v=1)
      project=Arctic Ice Modelling | status=active | priority=- | tags=[]
      project=Carbon Flux Analysis | status=active | priority=- | tags=[]
    program=Genomics Initiative (schema_v=1)
      project=Protein Folding Study | status=active | priority=- | tags=[]
      project=CRISPR Toolkit Dev | status=planning | priority=- | tags=[]

[MongoDB] V2 migration: introduce 'streams' layer inside programs
  ✓ applied V2 migration (streams added, projects moved in)

  === V2 data (with streams) ===
    program=Climate Science (schema_v=2)
      stream=Modelling & Simulation | project=Arctic Ice Modelling | status=active | priority=- | tags=[]
      stream=Modelling & Simulation | project=Carbon Flux Analysis | status=active | priority=- | tags=[]
    program=Genomics Initiative (schema_v=2)
      stream=Computational Bio | project=Protein Folding Study | status=active | priority=- | tags=[]
      stream=Computational Bio | project=CRISPR Toolkit Dev | status=planning | priority=- | tags=[]

[MongoDB] V3 migration: add priority + tags (selective update)
  ✓ updated Arctic Ice Modelling
  ✓ updated Carbon Flux Analysis
  ✓ updated Protein Folding Study

  === V3 data (with priority + tags) ===
    program=Climate Science (schema_v=3)
      stream=Modelling & Simulation | project=Arctic Ice Modelling | status=active | priority=1 | tags=['ice', 'modelling']
      stream=Modelling & Simulation | project=Carbon Flux Analysis | status=active | priority=2 | tags=['carbon', 'climate']
    program=Genomics Initiative (schema_v=3)
      stream=Computational Bio | project=Protein Folding Study | status=active | priority=1 | tags=['proteins', 'computational']
      stream=Computational Bio | project=CRISPR Toolkit Dev | status=planning | priority=- | tags=[]

[MongoDB] Demo complete.
```

## Dolt Demo

Dolt adds **git-like version control** on top of a MySQL-compatible relational database.
Schema migrations can be developed on feature branches, diffed, reviewed, and merged —
just like source code. Rollback is as simple as `dolt checkout`.

Key Dolt capabilities shown:
1. Branch-based schema migration (`feature/add-streams`)
2. `dolt diff` showing exact schema (DDL) and data changes before merge
3. Commit log tracking all schema evolution history
4. **Time-travel queries** using `AS OF '<commit-hash>'` to query historical schema

> Note: `lead` is a reserved keyword in Dolt and must be backtick-quoted in SQL.

```bash
cd /home/runner/work/experiments/experiments/db-portfolio-comparison && PATH="$HOME/.local/bin:$PATH" uv run python dolt_demo.py
```

```output

[Dolt] Setting up version-controlled portfolio database
  ✓ dolt repo initialised at /tmp/portfolio_dolt_repo

[Dolt] V1: programs → projects (committed to main)
  ✓ V1 schema + data committed to main

  === V1 projects ===
    +---------------------+-----------------------+----------+------------+
    | program             | project               | status   | start_year |
    +---------------------+-----------------------+----------+------------+
    | Climate Science     | Arctic Ice Modelling  | active   | 2022       |
    | Climate Science     | Carbon Flux Analysis  | active   | 2023       |
    | Genomics Initiative | CRISPR Toolkit Dev    | planning | 2024       |
    | Genomics Initiative | Protein Folding Study | active   | 2021       |
    +---------------------+-----------------------+----------+------------+

[Dolt] V2 migration: add streams (on feature branch)
  ✓ created branch feature/add-streams
  ✓ V2 migration committed on feature/add-streams branch

  === Schema/data diff: main → feature/add-streams ===
    diff --dolt a/projects b/projects
    --- a/projects
    +++ b/projects
     CREATE TABLE `projects` (
       `id` int NOT NULL AUTO_INCREMENT,
       `program_id` int,
       `name` varchar(200) NOT NULL,
       `status` varchar(30) NOT NULL DEFAULT 'active',
       `start_year` int,
    +  `stream_id` int,
       PRIMARY KEY (`id`)
     ) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
    +---+----+------------+-----------------------+----------+------------+-----------+
    |   | id | program_id | name                  | status   | start_year | stream_id |
    +---+----+------------+-----------------------+----------+------------+-----------+
    | < | 1  | 1          | Arctic Ice Modelling  | active   | 2022       | NULL      |
    | > | 1  | 1          | Arctic Ice Modelling  | active   | 2022       | 1         |
    | < | 2  | 1          | Carbon Flux Analysis  | active   | 2023       | NULL      |
    | > | 2  | 1          | Carbon Flux Analysis  | active   | 2023       | 1         |
    | < | 3  | 2          | Protein Folding Study | active   | 2021       | NULL      |
    | > | 3  | 2          | Protein Folding Study | active   | 2021       | 3         |
    | < | 4  | 2          | CRISPR Toolkit Dev    | planning | 2024       | NULL      |
    | > | 4  | 2          | CRISPR Toolkit Dev    | planning | 2024       | 3         |
    +---+----+------------+-----------------------+----------+------------+-----------+
    diff --dolt a/streams b/streams
    added table
    +CREATE TABLE `streams` (
    +  `id` int NOT NULL AUTO_INCREMENT,
    +  `program_id` int,
    +  `name` varchar(200) NOT NULL,
    +  `lead` varchar(120),
    +  PRIMARY KEY (`id`)
    +) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
    +---+----+------------+------------------------+-----------+
    |   | id | program_id | name                   | lead      |
    +---+----+------------+------------------------+-----------+
    | + | 1  | 1          | Modelling & Simulation | Dr. Park  |
    | + | 2  | 1          | Field Observations     | Dr. Reyes |
    | + | 3  | 2          | Computational Bio      | Dr. Kim   |
    +---+----+------------+------------------------+-----------+

[Dolt] Merge V2 and apply V3 on main
  ✓ merged feature/add-streams into main
  ✓ V3 committed to main

  === V3 final state ===
    +---------------------+------------------------+-----------------------+----------+----------+------------------------+
    | program             | stream                 | project               | status   | priority | tags                   |
    +---------------------+------------------------+-----------------------+----------+----------+------------------------+
    | Climate Science     | Modelling & Simulation | Arctic Ice Modelling  | active   | 1        | ice,modelling          |
    | Climate Science     | Modelling & Simulation | Carbon Flux Analysis  | active   | 2        | carbon,climate         |
    | Genomics Initiative | Computational Bio      | CRISPR Toolkit Dev    | planning | 3        | NULL                   |
    | Genomics Initiative | Computational Bio      | Protein Folding Study | active   | 1        | proteins,computational |
    +---------------------+------------------------+-----------------------+----------+----------+------------------------+

  === Commit log ===
    5fl6foekeaivuaa3ubsbrikka2grg8e4 (HEAD -> main) v3: add priority and tags columns to projects
    vg1nqt4bcjtpgmnbaul4tr64ht80k37i Merge v2 streams branch
    jv5ol0dc58mdv70uk0j7ikt73k9lcn47 (feature/add-streams) v2: add streams table and assign projects
    pn3fne48olvugdvg5ot9ndn3c9vvvcbc v1: programs and projects schema with initial data
    8knbopk239hj1pr60kidplalphd31c7o Initialize data repository

[Dolt] Time-travel: query V1 state from history

  === V1 state (time-travel query – no stream_id, no priority, no tags) ===
    +----+------------+-----------------------+----------+------------+
    | id | program_id | name                  | status   | start_year |
    +----+------------+-----------------------+----------+------------+
    | 1  | 1          | Arctic Ice Modelling  | active   | 2022       |
    | 2  | 1          | Carbon Flux Analysis  | active   | 2023       |
    | 3  | 2          | Protein Folding Study | active   | 2021       |
    | 4  | 2          | CRISPR Toolkit Dev    | planning | 2024       |
    +----+------------+-----------------------+----------+------------+

[Dolt] Demo complete.
```

## Comparison Summary

### Schema Change Experience

| Change type                    | PostgreSQL          | MongoDB              | Dolt                        |
|-------------------------------|---------------------|----------------------|-----------------------------|
| Add a new column              | `ALTER TABLE`      | No migration needed  | `ALTER TABLE` + commit      |
| Add a new hierarchy level     | New table + FK      | Restructure docs     | New table + branch + merge   |
| Rollback a bad migration      | Manual reverse DDL  | Manual update queries | `dolt checkout` / revert   |
| Query data 6 months ago       | Point-in-time recovery | No built-in       | `AS OF '<commit-hash>'`    |
| Review changes before apply   | Read migration SQL  | N/A                  | `dolt diff` on branch       |

---

### Pros and Cons

#### PostgreSQL ✅🔴
**Pros:**
- Mature, battle-tested ACID compliance + rich SQL features
- Extensive ecosystem: PostGIS, pgvector, Metabase, pgAdmin
- Strong referential integrity enforcement
- `ALTER TABLE ADD COLUMN DEFAULT NULL` is instant in PG 11+

**Cons:**
- No built-in schema history — migration scripts maintained manually
- Hierarchical restructuring = new tables + data migrations
- Rolling back requires manually-written reverse-migration scripts
- ALTER TABLE can lock tables on large datasets

---

#### MongoDB 🟡
**Pros:**
- Genuinely schemaless: add new fields with zero DDL
- Nested documents model portfolio hierarchy naturally
- Gradual/partial migrations — not all documents need updating at once
- `_schema_version` pattern allows coexistence of old/new formats

**Cons:**
- No schema enforcement by default → data quality issues accumulate
- No built-in history or audit trail
- `$lookup` (joins) are slower/more verbose than SQL JOINs
- Referential integrity is entirely the application's responsibility

---

#### Dolt ✅✅
**Pros:**
- Full git-like versioning of **both schema and data**
- Branch-and-merge: develop migrations safely, review with `dolt diff` before merging
- Time-travel: `SELECT * FROM projects AS OF '<hash>'` for research provenance
- MySQL-compatible SQL — familiar drivers, tools, and patterns

**Cons:**
- Younger product, smaller community than PostgreSQL/MongoDB
- ~2× performance overhead vs plain MySQL/Postgres on some benchmarks
- Some reserved word conflicts (e.g. `lead` needs backtick-quoting)
- ANSI colour codes in CLI output need stripping when parsing programmatically
- Operational complexity: DoltHub or self-hosted `doltsql` server needed

---

## Recommendation

### **Primary recommendation: Dolt**

For a research portfolio database where structure changes often and **auditability
and research reproducibility matter**, Dolt is the standout choice:

1. **Schema history is first-class** — every DDL change is automatically versioned
2. **Fearless experimentation** — restructure on a branch, review the diff, merge or discard
3. **Research provenance** — query the exact portfolio state at any past date
4. **Familiar SQL** — MySQL-compatible relational model with full ACID compliance

**Choose PostgreSQL instead when:**
Team has deep Postgres expertise, needs specific extensions (PostGIS, pgvector),
or already uses Flyway/Alembic for migration management.

**Choose MongoDB instead when:**
Portfolio documents are genuinely heterogeneous (radically different fields per document),
or schemaless flexibility is more important than data integrity guarantees.

---

## Risk Assessment

| Risk                             | PostgreSQL         | MongoDB              | Dolt               |
|----------------------------------|--------------------|----------------------|--------------------|
| Data loss on bad migration       | 🔴 High (no rollback) | 🟡 Medium          | 🟢 Low (revert)    |
| Schema drift / inconsistency     | 🟢 Low (enforced)  | 🔴 High (unenforced) | 🟢 Low (enforced)  |
| Performance overhead             | 🟢 Low             | 🟢 Low               | 🟡 Medium          |
| Community/vendor lock-in         | 🟢 Low             | 🟡 Medium            | 🟡 Medium          |
| Operational complexity           | 🟢 Low             | 🟡 Medium            | 🟡 Medium–High     |
| Loss of historical query ability | 🔴 High            | 🔴 High              | 🟢 Low (built-in)  |

