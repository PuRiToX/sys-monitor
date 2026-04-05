from __future__ import annotations

from rich import box
from rich.table import Table
import psutil

from core import SampleWindow

CPU_WARNING = 50
CPU_CRITICAL = 80
RAM_WARNING = 50
RAM_CRITICAL = 80


class SystemMonitor:
    """Collect and render CPU/RAM/process usage."""

    def __init__(self, top_n: int = 10, cpu_weight: float = 0.7, ram_weight: float = 0.3):
        self.top_n = top_n
        self.cpu_weight = cpu_weight
        self.ram_weight = ram_weight
        self._sampler = SampleWindow()

    def _get_top_processes(self) -> list[dict]:
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                info["name"] = info.get("name") or "<unknown>"
                info["cpu_percent"] = info.get("cpu_percent") or 0.0
                info["memory_percent"] = info.get("memory_percent") or 0.0
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(
            key=lambda x: x["cpu_percent"] * self.cpu_weight
            + x["memory_percent"] * self.ram_weight,
            reverse=True,
        )
        return processes[: self.top_n]

    @staticmethod
    def _colorize(value: float, warning: float, critical: float) -> str:
        if value >= critical:
            return f"[red]{value:.1f}%[/red]"
        if value >= warning:
            return f"[yellow]{value:.1f}%[/yellow]"
        return f"{value:.1f}%"

    def collect(self) -> dict:
        sampled = self._sampler.sample(
            {
                "cpu_total": psutil.cpu_percent(interval=None),
                "ram_total": psutil.virtual_memory().percent,
            }
        )
        sampled["processes"] = self._get_top_processes()
        return sampled

    def render(self, data: dict) -> Table:
        cpu_total = data["values"]["cpu_total"]
        ram_total = data["values"]["ram_total"]
        cpu_delta = data["deltas"]["cpu_total"]
        ram_delta = data["deltas"]["ram_total"]
        top_procs = data["processes"]

        table = Table(
            title=(
                f"System @ {data['timestamp_utc']} — "
                f"CPU {cpu_total:.1f}% ({cpu_delta:+.2f}%/s) | "
                f"RAM {ram_total:.1f}% ({ram_delta:+.2f}%/s)"
            ),
            box=box.SQUARE,
        )
        table.add_column("PID", justify="right", width=6)
        table.add_column("Name", width=20, overflow="fold")
        table.add_column("CPU %", justify="right", width=6)
        table.add_column("RAM %", justify="right", width=6)

        for proc in top_procs:
            name = proc["name"][:20] if len(proc["name"]) > 20 else proc["name"]
            cpu_str = self._colorize(proc["cpu_percent"], CPU_WARNING, CPU_CRITICAL)
            ram_str = self._colorize(proc["memory_percent"], RAM_WARNING, RAM_CRITICAL)
            table.add_row(
                str(proc["pid"]).rjust(6),
                name,
                cpu_str.rjust(6),
                ram_str.rjust(6),
            )

        for _ in range(len(top_procs), self.top_n):
            table.add_row("-", "-", "-", "-")

        return table
