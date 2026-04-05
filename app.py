from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from rich.live import Live

from config import parse_args
from core.alerts import AlertEngine
from core.export import EventExporter
from monitors.network import NetworkMonitor
from monitors.system import SystemMonitor
from ui.table_renderer import render_monitors


class Monitor(Protocol):
    def collect(self) -> dict: ...

    def render(self, data: dict): ...


@dataclass
class MonitorBinding:
    name: str
    monitor: Monitor


class MonitorApp:
    def __init__(
        self,
        monitors: list[MonitorBinding],
        mode: str,
        refresh_seconds: float,
        refresh_per_second: int,
        alert_engine: AlertEngine,
        exporter: EventExporter,
    ):
        self.monitors = monitors
        self.mode = mode
        self.refresh_seconds = refresh_seconds
        self.refresh_per_second = refresh_per_second
        self.alert_engine = alert_engine
        self.exporter = exporter

    def _frame(self):
        rendered: dict[str, object] = {}
        for binding in self.monitors:
            data = binding.monitor.collect()
            events = self.alert_engine.evaluate(binding.name, data)
            self.exporter.export(events)
            rendered[binding.name] = binding.monitor.render(data)
        return render_monitors(rendered, self.mode)

    def run(self) -> None:
        with Live(self._frame(), refresh_per_second=self.refresh_per_second, screen=False) as live:
            while True:
                live.update(self._frame())
                time.sleep(self.refresh_seconds)


def _build_monitors(mode: str, top_processes: int, iface: str | None) -> list[MonitorBinding]:
    monitors: list[MonitorBinding] = []
    if mode in {"system", "all"}:
        monitors.append(MonitorBinding(name="system", monitor=SystemMonitor(top_n=top_processes)))
    if mode in {"network", "all"}:
        monitors.append(MonitorBinding(name="network", monitor=NetworkMonitor(iface=iface)))
    return monitors


def main() -> None:
    config = parse_args()
    app = MonitorApp(
        monitors=_build_monitors(config.mode, config.top_processes, config.iface),
        mode=config.mode,
        refresh_seconds=config.refresh_seconds,
        refresh_per_second=config.refresh_per_second,
        alert_engine=AlertEngine(),
        exporter=EventExporter(jsonl_path=config.alerts_jsonl, csv_path=config.alerts_csv),
    )
    app.run()


if __name__ == "__main__":
    main()
