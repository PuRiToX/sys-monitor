from __future__ import annotations

import time
from collections import Counter

from rich import box
from rich.console import Group
from rich.table import Table
import psutil


class NetworkMonitor:
    """Collect and render per-interface network counters and connection states."""

    def __init__(self, iface: str | None = None):
        self.iface = iface
        self._last_snapshot: dict[str, object] | None = None

    def collect(self) -> dict:
        now = time.time()
        pernic = psutil.net_io_counters(pernic=True)

        current_snapshot = {
            "timestamp": now,
            "interfaces": {
                name: {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout,
                }
                for name, counters in pernic.items()
                if not self.iface or name == self.iface
            },
        }

        elapsed = 0.0
        if self._last_snapshot:
            elapsed = max(now - float(self._last_snapshot["timestamp"]), 1e-6)

        interfaces = []
        for name, counters in current_snapshot["interfaces"].items():
            previous = None
            if self._last_snapshot:
                previous = self._last_snapshot["interfaces"].get(name)

            if previous and elapsed > 0.0:
                rx_bps = (counters["bytes_recv"] - previous["bytes_recv"]) / elapsed
                tx_bps = (counters["bytes_sent"] - previous["bytes_sent"]) / elapsed
                rx_pps = (counters["packets_recv"] - previous["packets_recv"]) / elapsed
                tx_pps = (counters["packets_sent"] - previous["packets_sent"]) / elapsed
            else:
                rx_bps = tx_bps = rx_pps = tx_pps = 0.0

            interfaces.append(
                {
                    "name": name,
                    **counters,
                    "rx_bps": max(0.0, rx_bps),
                    "tx_bps": max(0.0, tx_bps),
                    "rx_pps": max(0.0, rx_pps),
                    "tx_pps": max(0.0, tx_pps),
                }
            )

        interfaces.sort(key=lambda item: item["rx_bps"] + item["tx_bps"], reverse=True)

        try:
            connections = psutil.net_connections(kind="inet")
            connection_states = dict(sorted(Counter(conn.status for conn in connections).items()))
            connection_error = None
        except (psutil.AccessDenied, psutil.Error) as exc:
            connection_states = {}
            connection_error = str(exc)

        self._last_snapshot = current_snapshot
        return {
            "interfaces": interfaces,
            "connection_states": connection_states,
            "connection_error": connection_error,
            "iface": self.iface,
        }

    def render(self, data: dict) -> Group:
        iface_title = data["iface"] if data["iface"] else "all"
        interface_table = Table(title=f"Network Interfaces ({iface_title})", box=box.SQUARE)
        interface_table.add_column("IFACE", style="bold", no_wrap=True)
        interface_table.add_column("RX/s", justify="right")
        interface_table.add_column("TX/s", justify="right")
        interface_table.add_column("RX", justify="right")
        interface_table.add_column("TX", justify="right")
        interface_table.add_column("PKT RX/s", justify="right")
        interface_table.add_column("PKT TX/s", justify="right")
        interface_table.add_column("ERR in/out", justify="right")
        interface_table.add_column("DROP in/out", justify="right")

        if data["interfaces"]:
            for nic in data["interfaces"]:
                interface_table.add_row(
                    nic["name"],
                    f"{self._format_bytes(nic['rx_bps'])}/s",
                    f"{self._format_bytes(nic['tx_bps'])}/s",
                    self._format_bytes(nic["bytes_recv"]),
                    self._format_bytes(nic["bytes_sent"]),
                    self._format_rate(nic["rx_pps"]),
                    self._format_rate(nic["tx_pps"]),
                    f"{nic['errin']}/{nic['errout']}",
                    f"{nic['dropin']}/{nic['dropout']}",
                )
        else:
            interface_table.add_row("-", "-", "-", "-", "-", "-", "-", "-", "-")

        conn_table = Table(title="Connections (inet)", box=box.SQUARE)
        conn_table.add_column("State", style="bold")
        conn_table.add_column("Count", justify="right")

        if data["connection_states"]:
            for state, count in data["connection_states"].items():
                conn_table.add_row(state, str(count))
        elif data["connection_error"]:
            conn_table.add_row("ERROR", data["connection_error"])
        else:
            conn_table.add_row("None", "0")

        return Group(interface_table, conn_table)

    @staticmethod
    def _format_bytes(size: float) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} EB"

    @staticmethod
    def _format_rate(value: float) -> str:
        return f"{value:,.1f}"
