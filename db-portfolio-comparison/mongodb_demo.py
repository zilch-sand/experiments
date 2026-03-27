"""
MongoDB Demo: Research Portfolio with Schema Evolution
Demonstrates flexible document schema changes for portfolio data.
"""
from pymongo import MongoClient
from datetime import datetime
import json

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME   = "portfolio_demo"

# ─────────────────────────────────────────────
# V1 DOCUMENTS: Programs contain embedded projects
# ─────────────────────────────────────────────
V1_PROGRAMS = [
    {
        "_schema_version": 1,
        "name": "Climate Science",
        "owner": "Dr. Chen",
        "budget": 2500000,
        "projects": [
            {"name": "Arctic Ice Modelling", "status": "active", "start_year": 2022},
            {"name": "Carbon Flux Analysis", "status": "active", "start_year": 2023},
        ],
    },
    {
        "_schema_version": 1,
        "name": "Genomics Initiative",
        "owner": "Prof. Okafor",
        "budget": 4000000,
        "projects": [
            {"name": "Protein Folding Study", "status": "active", "start_year": 2021},
            {"name": "CRISPR Toolkit Dev", "status": "planning", "start_year": 2024},
        ],
    },
]


def connect():
    client = MongoClient(MONGO_URI)
    return client, client[DB_NAME]


def show_state(label, db):
    print(f"\n  === {label} ===")
    for prog in db.programs.find({}, {"_id": 0}):
        schema_v = prog.get("_schema_version", "?")
        print(f"    program={prog['name']} (schema_v={schema_v})")
        for stream in prog.get("streams", []):
            for proj in stream.get("projects", []):
                tags = proj.get("tags", [])
                priority = proj.get("priority", "-")
                print(f"      stream={stream['name']} | project={proj['name']}"
                      f" | status={proj['status']}"
                      f" | priority={priority} | tags={tags}")
        for proj in prog.get("projects", []):
            tags = proj.get("tags", [])
            priority = proj.get("priority", "-")
            print(f"      project={proj['name']} | status={proj['status']}"
                  f" | priority={priority} | tags={tags}")


def main():
    client, db = connect()

    # ── V1: seed ──
    print("\n[MongoDB] V1: programs with embedded projects")
    db.programs.drop()
    db.programs.insert_many(V1_PROGRAMS)
    print("  ✓ inserted V1 documents")
    show_state("V1 data", db)

    # ── V2 migration: restructure to add streams sub-documents ──
    print("\n[MongoDB] V2 migration: introduce 'streams' layer inside programs")

    stream_map = {
        "Climate Science": [
            {
                "name": "Modelling & Simulation",
                "lead": "Dr. Park",
                "projects": [],
            },
            {
                "name": "Field Observations",
                "lead": "Dr. Reyes",
                "projects": [],
            },
        ],
        "Genomics Initiative": [
            {
                "name": "Computational Bio",
                "lead": "Dr. Kim",
                "projects": [],
            },
        ],
    }

    project_stream_assignment = {
        "Arctic Ice Modelling":  ("Climate Science",    "Modelling & Simulation"),
        "Carbon Flux Analysis":  ("Climate Science",    "Modelling & Simulation"),
        "Protein Folding Study": ("Genomics Initiative","Computational Bio"),
        "CRISPR Toolkit Dev":    ("Genomics Initiative","Computational Bio"),
    }

    for prog_doc in db.programs.find():
        prog_name = prog_doc["name"]
        streams = stream_map.get(prog_name, [])
        old_projects = prog_doc.get("projects", [])

        for proj in old_projects:
            target_stream = project_stream_assignment.get(proj["name"])
            if target_stream:
                for s in streams:
                    if s["name"] == target_stream[1]:
                        s["projects"].append(proj)

        db.programs.update_one(
            {"_id": prog_doc["_id"]},
            {
                "$set": {
                    "streams": streams,
                    "_schema_version": 2,
                },
                "$unset": {"projects": ""},
            },
        )

    print("  ✓ applied V2 migration (streams added, projects moved in)")
    show_state("V2 data (with streams)", db)

    # ── V3 migration: add priority + tags to projects (lazy/partial update) ──
    print("\n[MongoDB] V3 migration: add priority + tags (selective update)")

    # Only update specific projects - others keep working without the fields
    updates = [
        ("Arctic Ice Modelling",  1, ["ice", "modelling"]),
        ("Carbon Flux Analysis",  2, ["carbon", "climate"]),
        ("Protein Folding Study", 1, ["proteins", "computational"]),
    ]

    for proj_name, priority, tags in updates:
        result = db.programs.update_one(
            {"streams.projects.name": proj_name},
            {
                "$set": {
                    "streams.$[].projects.$[proj].priority": priority,
                    "streams.$[].projects.$[proj].tags": tags,
                    "_schema_version": 3,
                }
            },
            array_filters=[{"proj.name": proj_name}],
        )
        if result.modified_count:
            print(f"  ✓ updated {proj_name}")

    show_state("V3 data (with priority + tags)", db)

    client.close()
    print("\n[MongoDB] Demo complete.")


if __name__ == "__main__":
    main()
