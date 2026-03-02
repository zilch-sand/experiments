"""
Persistent batch job manager – saves/loads jobs from a JSON file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import BATCH_JOBS_FILE


@dataclass
class BatchJob:
    id: str
    model_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"          # pending | running | completed | failed | cancelled
    input_file: str = ""
    output_file: str = ""
    total_rows: int = 0
    gcs_uri: str = ""
    bq_table: str = ""
    error_message: str = ""


class BatchManager:
    def __init__(self, jobs_file: Path | str = BATCH_JOBS_FILE):
        self._file = Path(jobs_file)
        self._jobs: dict[str, BatchJob] = {}
        self.load_jobs()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_jobs(self) -> None:
        if self._file.exists():
            try:
                raw = json.loads(self._file.read_text())
                self._jobs = {j["id"]: BatchJob(**j) for j in raw}
            except Exception:
                self._jobs = {}

    def _save(self) -> None:
        self._file.write_text(json.dumps([asdict(j) for j in self._jobs.values()], indent=2))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_job(self, job: BatchJob) -> None:
        self._jobs[job.id] = job
        self._save()

    def update_job(self, job_id: str, **kwargs) -> None:
        if job_id in self._jobs:
            job = self._jobs[job_id]
            for k, v in kwargs.items():
                setattr(job, k, v)
            self._save()

    def get_job(self, job_id: str) -> BatchJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[BatchJob]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def remove_job(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._save()

    def cleanup_completed_job(self, job_id: str) -> None:
        """
        Remove GCS / BQ resources for a completed job then delete from tracking.
        TODO: implement actual GCS blob deletion and BQ table deletion.
        """
        self.remove_job(job_id)
