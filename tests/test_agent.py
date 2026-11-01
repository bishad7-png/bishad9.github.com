import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from daily_video_agent.agent import VideoAgent
from daily_video_agent.config import Config


class AgentTests(unittest.TestCase):
    def test_dry_run_persists_job_without_rendering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = Config(
                niche="testing",
                output_dir=root / "output",
                state_dir=root / "state",
                schedule_time="09:00",
                timezone="local",
                script_mode="template",
                voiceover_mode="silence",
                voiceover_command="",
                visuals_mode="color",
                delivery="local",
                drive_folder_id="",
                drive_access_token="",
                ffmpeg_bin="ffmpeg",
                keep_failed_assets=True,
                max_retries=1,
                retry_delay_seconds=0,
            )
            with patch("daily_video_agent.agent.create_voiceover") as voiceover:
                job = VideoAgent(config).run("stable-job", dry_run=True)
            voiceover.assert_not_called()
            self.assertEqual(job.status, "dry_run")
            self.assertTrue((root / "state" / "jobs" / "stable-job.json").exists())

    def test_config_rejects_drive_without_credentials(self):
        config = Config.from_env()
        drive_config = replace(config, delivery="google_drive", drive_folder_id="", drive_access_token="")
        with self.assertRaises(ValueError):
            drive_config.validate()


if __name__ == "__main__":
    unittest.main()
