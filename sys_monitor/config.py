from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass
class MonitorConfig:
    """Configuration for monitor refresh and rendering behavior."""

    mode: str = "all"
    refresh_seconds: float = 1.0
    refresh_per_second: int = 4
    top_processes: int = 10
    iface: str | None = None
    alerts_jsonl: str | None = None
    alerts_csv: str | None = None


def parse_args() -> MonitorConfig:
    """Parse CLI arguments into a MonitorConfig."""
    parser = argparse.ArgumentParser(description="Terminal system and network monitor")
    parser.add_argument(
        "--mode",
        choices=["system", "network", "all"],
        default="all",
        help="Select monitor mode: system, network, or both.",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=1.0,
        help="Collector update interval in seconds.",
    )
    parser.add_argument(
        "--refresh-per-second",
        type=int,
        default=4,
        help="Rich Live refresh rate.",
    )
    parser.add_argument(
        "--top-procs",
        type=int,
        default=10,
        help="Number of top processes shown in system mode.",
    )
    parser.add_argument(
        "--iface",
        type=str,
        default=None,
        help="Interface name to display in network mode (default: all interfaces).",
    )
    parser.add_argument(
        "--alerts-jsonl",
        type=str,
        default=None,
        help="Optional JSONL file path for alert events.",
    )
    parser.add_argument(
        "--alerts-csv",
        type=str,
        default=None,
        help="Optional CSV file path for alert events.",
    )
    args = parser.parse_args()

    return MonitorConfig(
        mode=args.mode,
        refresh_seconds=args.refresh,
        refresh_per_second=args.refresh_per_second,
        top_processes=args.top_procs,
        iface=args.iface,
        alerts_jsonl=args.alerts_jsonl,
        alerts_csv=args.alerts_csv,
    )
