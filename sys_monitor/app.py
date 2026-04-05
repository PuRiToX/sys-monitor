from __future__ import annotations

import time
from typing import Protocol

from rich.live import Live

from sys_monitor.config import parse_args
from sys_monitor.monitors.network import NetworkMonitor
from sys_monitor.monitors.system import SystemMonitor
from sys_monitor.ui.table_renderer import render_monitors


class Monitor(Protocol):
    def collect(self) -> dict: ...

    def render(self, data: dict): ...


class MonitorApp:
    def __init__(self, monitors: list[Monitor], refresh_seconds: float, refresh_per_second: int):
        self.monitors = monitors
        self.refresh_seconds = refresh_seconds
        self.refresh_per_second = refresh_per_second

    def _frame(self):
        rendered = []
        for monitor in self.monitors:
            data = monitor.collect()
            rendered.append(monitor.render(data))
        return render_monitors(rendered)

    def run(self) -> None:
        with Live(self._frame(), refresh_per_second=self.refresh_per_second, screen=False) as live:
            while True:
                live.update(self._frame())
                time.sleep(self.refresh_seconds)


def main() -> None:
    config = parse_args()
    app = MonitorApp(
        monitors=[SystemMonitor(top_n=config.top_processes), NetworkMonitor()],
        refresh_seconds=config.refresh_seconds,
        refresh_per_second=config.refresh_per_second,
    )
    app.run()


if __name__ == "__main__":
    main()
