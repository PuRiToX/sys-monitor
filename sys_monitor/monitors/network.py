from __future__ import annotations

import time

from rich import box
from rich.table import Table
import psutil


class NetworkMonitor:
    """Collect and render overall network throughput counters."""

    def __init__(self):
        self._last = None

    def collect(self) -> dict:
        now = time.time()
        counters = psutil.net_io_counters()
        current = {
            "timestamp": now,
            "bytes_sent": counters.bytes_sent,
            "bytes_recv": counters.bytes_recv,
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
        }

        if not self._last:
            rates = {"send_bps": 0.0, "recv_bps": 0.0}
        else:
            elapsed = max(current["timestamp"] - self._last["timestamp"], 1e-6)
            rates = {
                "send_bps": (current["bytes_sent"] - self._last["bytes_sent"]) / elapsed,
                "recv_bps": (current["bytes_recv"] - self._last["bytes_recv"]) / elapsed,
            }

        self._last = current
        return {**current, **rates}

    def render(self, data: dict) -> Table:
        table = Table(title="Network", box=box.SQUARE)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total sent", self._format_bytes(data["bytes_sent"]))
        table.add_row("Total received", self._format_bytes(data["bytes_recv"]))
        table.add_row("Send rate", f"{self._format_bytes(data['send_bps'])}/s")
        table.add_row("Receive rate", f"{self._format_bytes(data['recv_bps'])}/s")
        table.add_row("Packets sent", str(data["packets_sent"]))
        table.add_row("Packets received", str(data["packets_recv"]))

        return table

    @staticmethod
    def _format_bytes(size: float) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} EB"
