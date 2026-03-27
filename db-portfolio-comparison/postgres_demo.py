"""
PostgreSQL Demo: Research Portfolio with Schema Evolution
Demonstrates schema changes for a multi-level portfolio structure.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

CONN_PARAMS = {
    "host": "localhost",
    "dbname": "portfolio_db",
    "user": "portfolio_user",
    "password": "portfolio123",
}

# ─────────────────────────────────────────────
# V1 SCHEMA: Programs → Projects
# ─────────────────────────────────────────────
V1_DDL = """
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS streams CASCADE;
DROP TABLE IF EXISTS programs CASCADE;

CREATE TABLE programs (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    owner       TEXT NOT NULL,
    budget      NUMERIC(12,2)
);

CREATE TABLE projects (
    id          SERIAL PRIMARY KEY,
    program_id  INT REFERENCES programs(id),
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    start_year  INT
);
"""

V1_DATA = """
INSERT INTO programs (name, owner, budget) VALUES
    ('Climate Science', 'Dr. Chen', 2500000),
    ('Genomics Initiative', 'Prof. Okafor', 4000000);

INSERT INTO projects (program_id, name, status, start_year) VALUES
    (1, 'Arctic Ice Modelling', 'active', 2022),
    (1, 'Carbon Flux Analysis', 'active', 2023),
    (2, 'Protein Folding Study', 'active', 2021),
    (2, 'CRISPR Toolkit Dev', 'planning', 2024);
"""

# ─────────────────────────────────────────────
# V2 MIGRATION: Add Streams between Program→Project
#   programs → streams → projects
# ─────────────────────────────────────────────
V2_MIGRATION = """
-- Step 1: add streams table
CREATE TABLE streams (
    id          SERIAL PRIMARY KEY,
    program_id  INT REFERENCES programs(id),
    name        TEXT NOT NULL,
    lead        TEXT
);

-- Step 2: add stream_id to projects (nullable for backward compat)
ALTER TABLE projects ADD COLUMN stream_id INT REFERENCES streams(id);

-- Step 3: seed streams for existing programs
INSERT INTO streams (program_id, name, lead) VALUES
    (1, 'Modelling & Simulation', 'Dr. Park'),
    (1, 'Field Observations', 'Dr. Reyes'),
    (2, 'Computational Bio', 'Dr. Kim');

-- Step 4: assign existing projects to a stream
UPDATE projects SET stream_id = 1 WHERE name = 'Arctic Ice Modelling';
UPDATE projects SET stream_id = 1 WHERE name = 'Carbon Flux Analysis';
UPDATE projects SET stream_id = 3 WHERE name = 'Protein Folding Study';
UPDATE projects SET stream_id = 3 WHERE name = 'CRISPR Toolkit Dev';
"""

# ─────────────────────────────────────────────
# V3 MIGRATION: Add priority + tags to projects
# ─────────────────────────────────────────────
V3_MIGRATION = """
ALTER TABLE projects ADD COLUMN priority  INT DEFAULT 3;
ALTER TABLE projects ADD COLUMN tags      TEXT[] DEFAULT '{}';

UPDATE projects SET priority = 1, tags = ARRAY['ice','modelling']
    WHERE name = 'Arctic Ice Modelling';
UPDATE projects SET priority = 2, tags = ARRAY['carbon','climate']
    WHERE name = 'Carbon Flux Analysis';
UPDATE projects SET priority = 1, tags = ARRAY['proteins','computational']
    WHERE name = 'Protein Folding Study';
"""


def connect():
    return psycopg2.connect(**CONN_PARAMS)


def run(label, sql, conn):
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"  ✓ {label}")


def column_exists(conn, table, column):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s
        """, (table, column))
        return cur.fetchone() is not None


def table_exists(conn, table):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.tables WHERE table_name=%s
        """, (table,))
        return cur.fetchone() is not None


def show_state(label, conn):
    has_streams  = table_exists(conn, "streams")
    has_stream_col = column_exists(conn, "projects", "stream_id")
    has_priority = column_exists(conn, "projects", "priority")
    has_tags     = column_exists(conn, "projects", "tags")

    select_extra = ""
    join_clause  = ""
    if has_stream_col and has_streams:
        select_extra += ", s.name AS stream"
        join_clause   = "LEFT JOIN streams s ON s.id = p.stream_id"
    if has_priority:
        select_extra += ", p.priority"
    if has_tags:
        select_extra += ", p.tags"

    query = f"""
        SELECT pg.name AS program {select_extra},
               p.name AS project, p.status, p.start_year
        FROM projects p
        JOIN programs pg ON pg.id = p.program_id
        {join_clause}
        ORDER BY pg.name, p.name
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    print(f"\n  === {label} ===")
    for r in rows:
        row = dict(r)
        parts = [f"program={row['program']}"]
        if row.get("stream"):
            parts.append(f"stream={row['stream']}")
        parts.append(f"project={row['project']}")
        parts.append(f"status={row['status']}")
        if row.get("priority") is not None:
            parts.append(f"priority={row['priority']}")
        if row.get("tags"):
            parts.append(f"tags={row['tags']}")
        print("    " + " | ".join(parts))
    return rows


def main():
    conn = connect()

    print("\n[PostgreSQL] V1: programs → projects")
    run("create tables", V1_DDL, conn)
    run("insert mock data", V1_DATA, conn)
    show_state("V1 data", conn)

    print("\n[PostgreSQL] V2 migration: add streams layer")
    run("apply V2 migration", V2_MIGRATION, conn)
    show_state("V2 data (with streams)", conn)

    print("\n[PostgreSQL] V3 migration: add priority + tags columns")
    run("apply V3 migration", V3_MIGRATION, conn)
    show_state("V3 data (with priority + tags)", conn)

    conn.close()
    print("\n[PostgreSQL] Demo complete.")


if __name__ == "__main__":
    main()
