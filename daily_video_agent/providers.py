from __future__ import annotations

import json
import mimetypes
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from .config import Config


def create_script(niche: str) -> str:
    return (
        f"Welcome to today's {niche} short. "
        f"Here is one useful idea you can explore in under a minute. "
        f"Keep learning, test what you discover, and come back tomorrow for another practical insight."
    )


def create_voiceover(script: str, output: Path, config: Config) -> None:
    if config.voiceover_mode == "silence":
        _run_ffmpeg(
            config,
            ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "12", "-q:a", "9", "-y", str(output)],
        )
        return
    command = config.voiceover_command.format(script=script, output=str(output))
    subprocess.run(command, shell=True, check=True, timeout=300)
    if not output.exists():
        raise RuntimeError("Voiceover command completed without creating its output file")


def create_video(script: str, voiceover: Path, output: Path, thumbnail: Path, config: Config) -> None:
    del script
    if config.visuals_mode != "color":
        raise ValueError(f"Unsupported visual mode: {config.visuals_mode}")
    _run_ffmpeg(
        config,
        [
            "-f", "lavfi", "-i", "color=c=0x203040:s=1280x720:r=30",
            "-i", str(voiceover), "-t", "12", "-shortest",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-y", str(output),
        ],
    )
    _run_ffmpeg(config, ["-i", str(output), "-frames:v", "1", "-y", str(thumbnail)])


def deliver(video: Path, thumbnail: Path, config: Config) -> str:
    if config.delivery == "local":
        return str(video)
    return _upload_to_drive(video, thumbnail, config)


def _upload_to_drive(video: Path, thumbnail: Path, config: Config) -> str:
    metadata = json.dumps(
        {"name": video.name, "parents": [config.drive_folder_id], "description": "Daily video agent output"}
    ).encode()
    boundary = f"daily-video-{uuid.uuid4().hex}"
    body = _multipart(boundary, metadata, video)
    request = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.drive_access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google Drive upload failed ({error.code}): {detail}") from error
    _upload_drive_thumbnail(thumbnail, result.get("id", ""), config)
    return result.get("id", "")


def _upload_drive_thumbnail(thumbnail: Path, video_id: str, config: Config) -> None:
    if not video_id:
        return
    metadata = json.dumps({"name": thumbnail.name, "parents": [config.drive_folder_id]}).encode()
    boundary = f"daily-thumbnail-{uuid.uuid4().hex}"
    body = _multipart(boundary, metadata, thumbnail)
    request = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.drive_access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        response.read()


def _multipart(boundary: str, metadata: bytes, file_path: Path) -> bytes:
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    separator = f"--{boundary}\r\n".encode()
    return (
        separator
        + b"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        + metadata
        + b"\r\n"
        + separator
        + f"Content-Type: {content_type}\r\n\r\n".encode()
        + file_path.read_bytes()
        + f"\r\n--{boundary}--\r\n".encode()
    )


def _run_ffmpeg(config: Config, arguments: list[str]) -> None:
    try:
        subprocess.run([config.ffmpeg_bin, *arguments], check=True, timeout=300, capture_output=True)
    except FileNotFoundError as error:
        raise RuntimeError("ffmpeg was not found; install it or set FFMPEG_BIN") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode(errors="replace")[-1000:]
        raise RuntimeError(f"ffmpeg failed: {detail}") from error
