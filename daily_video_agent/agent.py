from __future__ import annotations

import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

from .config import Config
from .providers import create_script, create_video, create_voiceover, deliver
from .state import Job, StateStore

LOGGER = logging.getLogger("daily_video_agent")


class VideoAgent:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.state = StateStore(config.state_dir)
        self.state.initialize()
        config.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, job_id: str | None = None, dry_run: bool = False) -> Job:
        job_id = job_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        existing = self.state.load(job_id)
        if existing and existing.status == "delivered":
            LOGGER.info("Job %s is already delivered; skipping", job_id)
            return existing
        job = existing or Job(job_id, "pending", datetime.now().isoformat(), datetime.now().isoformat())
        job.attempts += 1
        self.state.save(job)
        work_dir = self.config.state_dir / "work" / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            script = create_script(self.config.niche)
            (work_dir / "script.txt").write_text(script + "\n", encoding="utf-8")
            if dry_run:
                job.status = "dry_run"
                self.state.save(job)
                return job
            voiceover = work_dir / "voiceover.wav"
            video = work_dir / f"{job_id}.mp4"
            thumbnail = work_dir / f"{job_id}.jpg"
            job.status = "rendering"
            self.state.save(job)
            create_voiceover(script, voiceover, self.config)
            create_video(script, voiceover, video, thumbnail, self.config)
            job.status = "delivering"
            job.video_path = str(video)
            job.thumbnail_path = str(thumbnail)
            self.state.save(job)
            job.delivery_id = deliver(video, thumbnail, self.config)
            job.status = "delivered"
            self.state.save(job)
            shutil.copy2(video, self.config.output_dir / video.name)
            shutil.copy2(thumbnail, self.config.output_dir / thumbnail.name)
            shutil.rmtree(work_dir)
            LOGGER.info("Delivered job %s", job_id)
            return job
        except Exception as error:
            job.status = "failed"
            job.error = str(error)
            self.state.save(job)
            if not self.config.keep_failed_assets:
                shutil.rmtree(work_dir, ignore_errors=True)
            LOGGER.exception("Job %s failed", job_id)
            raise

    def run_with_retries(self, job_id: str | None = None, dry_run: bool = False) -> Job:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                return self.run(job_id, dry_run)
            except Exception as error:
                last_error = error
                if attempt + 1 < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds)
        assert last_error is not None
        raise last_error

    def run_forever(self, dry_run: bool = False) -> None:
        LOGGER.info("Daily schedule: %s (%s)", self.config.schedule_time, self.config.timezone)
        while True:
            if datetime.now().strftime("%H:%M") == self.config.schedule_time:
                self.run_with_retries(dry_run=dry_run)
                time.sleep(61)
            time.sleep(15)
