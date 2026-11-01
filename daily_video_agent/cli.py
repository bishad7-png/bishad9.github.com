from __future__ import annotations

import argparse
import logging

from .agent import VideoAgent
from .config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the configurable daily video agent")
    parser.add_argument("--once", action="store_true", help="run one job and exit")
    parser.add_argument("--dry-run", action="store_true", help="write the script/state but do not render or deliver")
    parser.add_argument("--job-id", help="stable job ID for retries or external schedulers")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = Config.from_env()
    config.validate()
    agent = VideoAgent(config)
    if args.once or args.dry_run:
        agent.run_with_retries(args.job_id, args.dry_run)
    else:
        agent.run_forever()
