from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    niche: str
    output_dir: Path
    state_dir: Path
    schedule_time: str
    timezone: str
    script_mode: str
    voiceover_mode: str
    voiceover_command: str
    visuals_mode: str
    delivery: str
    drive_folder_id: str
    drive_access_token: str
    ffmpeg_bin: str
    keep_failed_assets: bool
    max_retries: int
    retry_delay_seconds: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            niche=_env("VIDEO_NICHE", "general knowledge"),
            output_dir=Path(_env("VIDEO_OUTPUT_DIR", "output")),
            state_dir=Path(_env("VIDEO_STATE_DIR", ".video-agent")),
            schedule_time=_env("VIDEO_SCHEDULE_TIME", "09:00"),
            timezone=_env("VIDEO_TIMEZONE", "local"),
            script_mode=_env("VIDEO_SCRIPT_MODE", "template"),
            voiceover_mode=_env("VIDEO_VOICEOVER_MODE", "silence"),
            voiceover_command=_env("VIDEO_VOICEOVER_COMMAND"),
            visuals_mode=_env("VIDEO_VISUALS_MODE", "color"),
            delivery=_env("VIDEO_DELIVERY", "local"),
            drive_folder_id=_env("GOOGLE_DRIVE_FOLDER_ID"),
            drive_access_token=_env("GOOGLE_DRIVE_ACCESS_TOKEN"),
            ffmpeg_bin=_env("FFMPEG_BIN", "ffmpeg"),
            keep_failed_assets=_bool("VIDEO_KEEP_FAILED_ASSETS", True),
            max_retries=max(1, int(_env("VIDEO_MAX_RETRIES", "3"))),
            retry_delay_seconds=max(0, int(_env("VIDEO_RETRY_DELAY_SECONDS", "10"))),
        )

    def validate(self) -> None:
        if self.script_mode not in {"template"}:
            raise ValueError(f"Unsupported VIDEO_SCRIPT_MODE: {self.script_mode}")
        if self.voiceover_mode not in {"silence", "command"}:
            raise ValueError(f"Unsupported VIDEO_VOICEOVER_MODE: {self.voiceover_mode}")
        if self.voiceover_mode == "command" and not self.voiceover_command:
            raise ValueError("VIDEO_VOICEOVER_COMMAND is required for command voiceover mode")
        if self.visuals_mode not in {"color"}:
            raise ValueError(f"Unsupported VIDEO_VISUALS_MODE: {self.visuals_mode}")
        if self.delivery not in {"local", "google_drive"}:
            raise ValueError(f"Unsupported VIDEO_DELIVERY: {self.delivery}")
        if self.delivery == "google_drive":
            if not self.drive_folder_id:
                raise ValueError("GOOGLE_DRIVE_FOLDER_ID is required for Google Drive delivery")
            if not self.drive_access_token:
                raise ValueError("GOOGLE_DRIVE_ACCESS_TOKEN is required for Google Drive delivery")
        try:
            datetime.strptime(self.schedule_time, "%H:%M")
        except ValueError as error:
            raise ValueError("VIDEO_SCHEDULE_TIME must use HH:MM") from error
