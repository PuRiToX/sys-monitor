from __future__ import annotations

from dataclasses import dataclass
import argparse


@dataclass
class MonitorConfig:
    """Configuration for monitor refresh and rendering behavior."""

    refresh_seconds: float = 1.0
    refresh_per_second: int = 2
    top_processes: int = 10



def parse_args() -> MonitorConfig:
    """Parse CLI arguments into a MonitorConfig."""
    parser = argparse.ArgumentParser(description="Terminal system monitor")
    parser.add_argument(
        "--refresh-seconds",
        type=float,
        default=1.0,
        help="Delay between monitor updates in seconds.",
    )
    parser.add_argument(
        "--refresh-per-second",
        type=int,
        default=2,
        help="Rich Live refresh rate.",
    )
    parser.add_argument(
        "--top-processes",
        type=int,
        default=10,
        help="Number of top processes shown in system table.",
    )
    args = parser.parse_args()

    return MonitorConfig(
        refresh_seconds=args.refresh_seconds,
        refresh_per_second=args.refresh_per_second,
        top_processes=args.top_processes,
    )
