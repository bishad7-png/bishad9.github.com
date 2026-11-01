from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Job:
    job_id: str
    status: str
    created_at: str
    updated_at: str
    attempts: int = 0
    video_path: str = ""
    thumbnail_path: str = ""
    delivery_id: str = ""
    error: str = ""


class StateStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.jobs_dir = directory / "jobs"

    def initialize(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def load(self, job_id: str) -> Job | None:
        path = self.path_for(job_id)
        if not path.exists():
            return None
        return Job(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, job: Job) -> None:
        job.updated_at = _now()
        path = self.path_for(job.job_id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(asdict(job), indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
