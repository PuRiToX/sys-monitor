from __future__ import annotations

import csv
import json
from pathlib import Path

from .alerts import MonitorEvent


class EventExporter:
    """Write alert events to JSONL and/or CSV files."""

    def __init__(self, jsonl_path: str | None = None, csv_path: str | None = None):
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        self.csv_path = Path(csv_path) if csv_path else None

        if self.csv_path and not self.csv_path.exists():
            self._write_csv_header()

    def export(self, events: list[MonitorEvent]) -> None:
        if not events:
            return
        if self.jsonl_path:
            self._write_jsonl(events)
        if self.csv_path:
            self._write_csv(events)

    def _write_jsonl(self, events: list[MonitorEvent]) -> None:
        assert self.jsonl_path is not None
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as outfile:
            for event in events:
                outfile.write(json.dumps(event, separators=(",", ":"), sort_keys=True))
                outfile.write("\n")

    def _write_csv_header(self) -> None:
        assert self.csv_path is not None
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["timestamp", "monitor", "metric", "value", "severity", "context"])

    def _write_csv(self, events: list[MonitorEvent]) -> None:
        assert self.csv_path is not None
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("a", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            for event in events:
                writer.writerow(
                    [
                        event["timestamp"],
                        event["monitor"],
                        event["metric"],
                        event["value"],
                        event["severity"],
                        json.dumps(event["context"], sort_keys=True),
                    ]
                )
