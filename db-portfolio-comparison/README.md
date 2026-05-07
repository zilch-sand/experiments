# Database Options for Research Portfolio Management

**Question:** Which database best supports a multi-level research portfolio
(Programs → Streams → Projects) in an organisation where the structure
changes frequently?

**Candidates evaluated:** Dolt · PostgreSQL · MongoDB

---

## The Problem

A research portfolio at scale has multiple hierarchy levels:

```
Organisation
└── Programs        (e.g. "Climate Science")
    └── Streams     (e.g. "Modelling & Simulation")
        └── Projects (e.g. "Arctic Ice Modelling")
```

The structure is not stable:
- New hierarchy levels are added (e.g. "Streams" inserted mid-lifecycle)
- New fields are required on existing entities (priority, tags, …)
- Relationships between entities change
- Historical queries are needed ("what did the portfolio look like 18 months ago?")

---

## Demo

See [`demo.md`](demo.md) for a fully-executable showboat document that runs all
three database comparisons end-to-end and captures the output.

Run it yourself:
```bash
cd db-portfolio-comparison
uvx showboat verify demo.md
```

The three Python scripts can also be run independently:
```bash
uv run python postgres_demo.py
uv run python mongodb_demo.py
uv run python dolt_demo.py
```

### Mock Data

Two programs, two streams, four projects:

| Program             | Stream                 | Project               | Status   |
|---------------------|------------------------|-----------------------|----------|
| Climate Science     | Modelling & Simulation | Arctic Ice Modelling  | active   |
| Climate Science     | Modelling & Simulation | Carbon Flux Analysis  | active   |
| Genomics Initiative | Computational Bio      | Protein Folding Study | active   |
| Genomics Initiative | Computational Bio      | CRISPR Toolkit Dev    | planning |

### Three Schema Migrations

| Version | Change                                          |
|---------|-------------------------------------------------|
| V1      | Baseline: Programs → Projects (flat)            |
| V2      | Add Streams as middle layer                     |
| V3      | Add `priority` (int) and `tags` (array) columns |

---

## Comparison

### Schema Change Experience

| Change type                    | PostgreSQL          | MongoDB              | Dolt                        |
|-------------------------------|---------------------|----------------------|-----------------------------|
| Add a new column              | `ALTER TABLE`       | No migration needed  | `ALTER TABLE` + commit       |
| Add a new hierarchy level     | New table + FK      | Restructure docs     | New table + branch + merge   |
| Rollback a bad migration      | Manual reverse DDL  | Manual update queries | `dolt checkout` / revert    |
| Query data 6 months ago       | Point-in-time recovery | No built-in support | `AS OF '<commit-hash>'`     |
| Review changes before applying | Read migration SQL | N/A                  | `dolt diff` on branch        |

---

## Pros and Cons

### PostgreSQL

**Pros**
- Mature, battle-tested ACID compliance with rich SQL features
- Extensive ecosystem: triggers, views, stored procedures, extensions (PostGIS, pgvector)
- Wide tooling support (pgAdmin, DBeaver, Metabase, etc.)
- Strong referential integrity enforcement
- `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL` is instant in PostgreSQL 11+

**Cons**
- No built-in schema history — migration scripts must be maintained manually
- Hierarchical restructuring requires new tables + data migrations
- Rolling back requires manually-written reverse-migration scripts
- ALTER TABLE can lock tables (matters for large datasets)

### MongoDB

**Pros**
- Genuinely schemaless: add new fields to any document with zero DDL
- Nested documents naturally model portfolio hierarchies
- Gradual/partial migrations — not all documents need updating simultaneously
- Easy horizontal scaling
- Application-level `_schema_version` pattern allows coexistence of old/new formats

**Cons**
- No schema enforcement by default → data quality issues accumulate over time
- No built-in schema history or audit trail
- `$lookup` (joins) are slower and less expressive than SQL JOINs
- Referential integrity is entirely the application's responsibility
- Complex nested array updates require verbose aggregation pipeline syntax

### Dolt

**Pros**
- Full git-like versioning of **both schema and data** — the killer feature
- Branch-and-merge workflow: develop migrations safely, review with `dolt diff` before merging
- Time-travel queries: `SELECT * FROM projects AS OF '<hash>'` for research provenance
- MySQL-compatible SQL — most MySQL tools, drivers, and patterns work
- Full ACID compliance with transactional guarantees

**Cons**
- Younger product, smaller community than PostgreSQL or MongoDB
- ~2× performance overhead vs plain MySQL/PostgreSQL on some benchmarks
- Some reserved word conflicts with standard SQL (e.g. `lead` requires backtick-quoting)
- ANSI colour codes in CLI output require stripping when parsing programmatically
- Operational complexity: DoltHub cloud or self-hosted `doltsql` server needed
- Steeper learning curve for the git-for-data paradigm

---

## Recommendation

### **Primary recommendation: Dolt**

For a research portfolio database where structure changes often and **auditability
and reproducibility matter**, Dolt is the standout choice:

1. **Schema history is first-class** — every DDL change is automatically versioned  
2. **Fearless experimentation** — restructure on a branch, review the diff, merge or discard safely  
3. **Research provenance** — time-travel queries let you reproduce the portfolio at any past point  
4. **Familiar SQL** — the MySQL-compatible relational model is easy to adopt

### When to choose PostgreSQL instead
- Team has deep Postgres expertise and existing tooling
- Need specific Postgres extensions (PostGIS, pg_vector, etc.)
- Combine with Flyway/Alembic for migration management and a CDC audit table

### When to choose MongoDB instead
- Portfolio documents are genuinely heterogeneous (each has radically different fields)
- Schemaless flexibility is more important than data integrity guarantees
- Need to scale horizontally beyond a single server

---

## Risk Assessment

| Risk                             | PostgreSQL         | MongoDB              | Dolt               |
|----------------------------------|--------------------|----------------------|--------------------|
| Data loss on bad migration       | 🔴 High (no rollback) | 🟡 Medium          | 🟢 Low (revert branch) |
| Schema drift / inconsistency     | 🟢 Low (enforced)  | 🔴 High (unenforced) | 🟢 Low (enforced) |
| Performance overhead             | 🟢 Low             | 🟢 Low               | 🟡 Medium          |
| Community/vendor lock-in         | 🟢 Low             | 🟡 Medium            | 🟡 Medium          |
| Operational complexity           | 🟢 Low             | 🟡 Medium            | 🟡 Medium–High     |
| Loss of historical query ability | 🔴 High            | 🔴 High              | 🟢 Low (built-in)  |

---

## Setup Notes

Requirements to run the demos:
- **PostgreSQL 16**: `pg_ctlcluster 16 main start`
- **MongoDB 8.0**: `sudo mongod --dbpath /var/lib/mongodb --fork --logpath /var/log/mongodb/mongod.log`
- **Dolt**: download from [github.com/dolthub/dolt/releases](https://github.com/dolthub/dolt/releases)
- **Python deps**: `uv add psycopg2-binary pymongo`
