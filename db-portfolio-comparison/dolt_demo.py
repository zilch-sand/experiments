"""
Dolt Demo: Research Portfolio with Version-Controlled Schema Evolution
Demonstrates Dolt's git-like branching for safe schema changes.
"""
import re
import subprocess
import os
import shutil

DOLT_REPO = "/tmp/portfolio_dolt_repo"
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def run_cmd(*args, cwd=DOLT_REPO, raise_on_error=False):
    """Run a command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return _strip_ansi(result.stdout.strip()), _strip_ansi(result.stderr.strip()), result.returncode


def dolt(*args, cwd=DOLT_REPO):
    out, err, rc = run_cmd("dolt", *args, cwd=cwd)
    if rc != 0 and err:
        print(f"  [dolt err] {err[:200]}")
    return out


def sql(query, cwd=DOLT_REPO):
    return dolt("sql", "-q", query, cwd=cwd)


def sql_show(label, query, cwd=DOLT_REPO):
    out = dolt("sql", "-q", query, "--result-format", "tabular", cwd=cwd)
    print(f"\n  === {label} ===")
    for line in out.splitlines():
        print("    " + line)


def setup_repo():
    # ensure global git identity exists for dolt
    run_cmd("dolt", "config", "--global", "--add", "user.email", "demo@experiment.test", cwd="/tmp")
    run_cmd("dolt", "config", "--global", "--add", "user.name", "Demo User", cwd="/tmp")

    if os.path.exists(DOLT_REPO):
        shutil.rmtree(DOLT_REPO)
    os.makedirs(DOLT_REPO)
    dolt("init", cwd=DOLT_REPO)
    print("  ✓ dolt repo initialised at", DOLT_REPO)


def v1_schema_and_data():
    sql("CREATE TABLE programs ("
        "  id    INT PRIMARY KEY AUTO_INCREMENT,"
        "  name  VARCHAR(120) NOT NULL,"
        "  owner VARCHAR(120) NOT NULL,"
        "  budget DECIMAL(14,2)"
        ")")
    sql("CREATE TABLE projects ("
        "  id         INT PRIMARY KEY AUTO_INCREMENT,"
        "  program_id INT,"
        "  name       VARCHAR(200) NOT NULL,"
        "  status     VARCHAR(30) NOT NULL DEFAULT 'active',"
        "  start_year INT"
        ")")

    sql("INSERT INTO programs (name, owner, budget) VALUES "
        "('Climate Science', 'Dr. Chen', 2500000),"
        "('Genomics Initiative', 'Prof. Okafor', 4000000)")

    sql("INSERT INTO projects (program_id, name, status, start_year) VALUES "
        "(1, 'Arctic Ice Modelling', 'active', 2022),"
        "(1, 'Carbon Flux Analysis', 'active', 2023),"
        "(2, 'Protein Folding Study', 'active', 2021),"
        "(2, 'CRISPR Toolkit Dev', 'planning', 2024)")

    dolt("add", ".")
    dolt("commit", "-m", "v1: programs and projects schema with initial data")
    print("  ✓ V1 schema + data committed to main")


def v2_migration_on_branch():
    dolt("checkout", "-b", "feature/add-streams")
    print("  ✓ created branch feature/add-streams")

    # 'lead' is a reserved keyword in Dolt – backtick-quote it
    sql("CREATE TABLE streams ("
        "  id         INT PRIMARY KEY AUTO_INCREMENT,"
        "  program_id INT,"
        "  name       VARCHAR(200) NOT NULL,"
        "  `lead`     VARCHAR(120)"
        ")")
    sql("ALTER TABLE projects ADD COLUMN stream_id INT")

    sql("INSERT INTO streams (program_id, name, `lead`) VALUES "
        "(1, 'Modelling & Simulation', 'Dr. Park'),"
        "(1, 'Field Observations', 'Dr. Reyes'),"
        "(2, 'Computational Bio', 'Dr. Kim')")
    sql("UPDATE projects SET stream_id = 1 WHERE name = 'Arctic Ice Modelling'")
    sql("UPDATE projects SET stream_id = 1 WHERE name = 'Carbon Flux Analysis'")
    sql("UPDATE projects SET stream_id = 3 WHERE name = 'Protein Folding Study'")
    sql("UPDATE projects SET stream_id = 3 WHERE name = 'CRISPR Toolkit Dev'")

    dolt("add", ".")
    dolt("commit", "-m", "v2: add streams table and assign projects")
    print("  ✓ V2 migration committed on feature/add-streams branch")


def show_diff_between_branches():
    out = dolt("diff", "main", "feature/add-streams")
    print("\n  === Schema/data diff: main → feature/add-streams ===")
    lines = out.splitlines()[:50]
    for line in lines:
        print("    " + line)
    if len(out.splitlines()) > 50:
        print(f"    ... ({len(out.splitlines()) - 50} more lines) ...")


def merge_v2_and_add_v3():
    dolt("checkout", "main")
    dolt("merge", "feature/add-streams", "--no-ff", "-m", "Merge v2 streams branch")
    print("  ✓ merged feature/add-streams into main")

    sql("ALTER TABLE projects ADD COLUMN priority INT DEFAULT 3")
    sql("ALTER TABLE projects ADD COLUMN tags VARCHAR(500)")

    sql("UPDATE projects SET priority=1, tags='ice,modelling' WHERE name='Arctic Ice Modelling'")
    sql("UPDATE projects SET priority=2, tags='carbon,climate' WHERE name='Carbon Flux Analysis'")
    sql("UPDATE projects SET priority=1, tags='proteins,computational' WHERE name='Protein Folding Study'")

    dolt("add", ".")
    dolt("commit", "-m", "v3: add priority and tags columns to projects")
    print("  ✓ V3 committed to main")


def show_log():
    out = dolt("log", "--oneline")
    print("\n  === Commit log ===")
    for line in out.splitlines():
        print("    " + line)


def main():
    print("\n[Dolt] Setting up version-controlled portfolio database")
    setup_repo()

    print("\n[Dolt] V1: programs → projects (committed to main)")
    v1_schema_and_data()
    sql_show(
        "V1 projects",
        "SELECT pg.name AS program, p.name AS project, p.status, p.start_year "
        "FROM projects p JOIN programs pg ON pg.id=p.program_id "
        "ORDER BY pg.name, p.name",
    )

    print("\n[Dolt] V2 migration: add streams (on feature branch)")
    v2_migration_on_branch()

    show_diff_between_branches()

    print("\n[Dolt] Merge V2 and apply V3 on main")
    merge_v2_and_add_v3()

    sql_show(
        "V3 final state",
        "SELECT pg.name AS program, s.name AS stream, p.name AS project, "
        "p.status, p.priority, p.tags "
        "FROM projects p "
        "JOIN programs pg ON pg.id=p.program_id "
        "LEFT JOIN streams s ON s.id=p.stream_id "
        "ORDER BY pg.name, s.name, p.name",
    )

    show_log()

    print("\n[Dolt] Time-travel: query V1 state from history")
    log = dolt("log", "--oneline")
    # find the v1 commit (skip init and later commits – take the one with 'v1' in message)
    v1_commit = None
    for line in log.splitlines():
        if "v1:" in line:
            v1_commit = line.split()[0]
            break
    if not v1_commit:
        # fallback: second-to-last commit (first data commit)
        commits = [line.split()[0] for line in log.splitlines() if line.strip()]
        v1_commit = commits[-2] if len(commits) >= 2 else commits[-1]
    sql_show(
        "V1 state (time-travel query – no stream_id, no priority, no tags)",
        f"SELECT * FROM `projects` AS OF '{v1_commit}' ORDER BY id",
    )

    print("\n[Dolt] Demo complete.")


if __name__ == "__main__":
    main()
