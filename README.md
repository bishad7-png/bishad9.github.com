# Daily Video Agent

This repository contains a safe prototype for an unattended daily video job. It creates one short per run, records durable job state, retries failures with a stable job ID, delivers to a configurable adapter, and removes temporary rendered assets only after successful delivery.

The default prototype uses deterministic local providers: a template script, silent audio, a solid-color video rendered with `ffmpeg`, and a local output directory. This is intentionally not presented as an AI provider. Replace the provider functions in `daily_video_agent/providers.py` with an approved local model or API adapter when a content provider is selected. YouTube upload is not implemented.

## Setup

Install Python 3.10+ and `ffmpeg`, then run:

```powershell
python -m pip install -e .
$env:VIDEO_NICHE = "space facts"
$env:VIDEO_DELIVERY = "local"
daily-video-agent --once
```

Outputs are written to `output/`; job state and failed work directories are written to `.video-agent/`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `VIDEO_NICHE` | `general knowledge` | Configurable content niche |
| `VIDEO_OUTPUT_DIR` | `output` | Successful delivered local copies |
| `VIDEO_STATE_DIR` | `.video-agent` | Durable job state and logs/work files |
| `VIDEO_SCHEDULE_TIME` | `09:00` | Local `HH:MM` schedule for the built-in loop |
| `VIDEO_TIMEZONE` | `local` | Documentation/config label; host scheduler should provide timezone guarantees |
| `VIDEO_SCRIPT_MODE` | `template` | Currently `template` only |
| `VIDEO_VOICEOVER_MODE` | `silence` | `silence` or `command` |
| `VIDEO_VOICEOVER_COMMAND` | empty | Command template using `{script}` and `{output}` |
| `VIDEO_VISUALS_MODE` | `color` | Currently `color` only |
| `VIDEO_DELIVERY` | `local` | `local` or `google_drive` |
| `GOOGLE_DRIVE_FOLDER_ID` | empty | Required for Drive delivery |
| `GOOGLE_DRIVE_ACCESS_TOKEN` | empty | Short-lived OAuth bearer token; never commit it |
| `FFMPEG_BIN` | `ffmpeg` | ffmpeg executable path |
| `VIDEO_MAX_RETRIES` | `3` | Attempts per job |
| `VIDEO_RETRY_DELAY_SECONDS` | `10` | Delay between attempts |
| `VIDEO_KEEP_FAILED_ASSETS` | `true` | Preserve failed work for diagnosis |

For Google Drive:

```powershell
$env:VIDEO_DELIVERY = "google_drive"
$env:GOOGLE_DRIVE_FOLDER_ID = "your-folder-id"
$env:GOOGLE_DRIVE_ACCESS_TOKEN = "oauth-access-token"
daily-video-agent --once
```

The adapter uploads the MP4 and thumbnail through the Google Drive REST API. Token acquisition/refresh is deliberately external so secrets are not hardcoded or persisted by this prototype. Email or another destination can be added by implementing the same `deliver(video, thumbnail, config) -> str` contract and adding a configuration value.

## Dry run and scheduling

`daily-video-agent --dry-run` creates the script and a durable `dry_run` job record without invoking ffmpeg or uploading anything. `daily-video-agent` runs the built-in polling loop using `VIDEO_SCHEDULE_TIME`; production deployments may instead invoke `daily-video-agent --once --job-id YYYYMMDD` from cron, Task Scheduler, or another supervisor. Reusing the same job ID is retry-safe: delivered jobs are skipped, and failed jobs retain state and diagnostic assets.

## Prototype boundaries

This version does not claim to generate AI-quality scripts, voices, visuals, or thumbnails. It provides the orchestration, state, cleanup, local rendering path, and Google Drive adapter needed to wire those providers safely once chosen.
