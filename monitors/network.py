from __future__ import annotations

from collections import Counter

from rich import box
from rich.console import Group
from rich.table import Table
import psutil

from core import SampleWindow, format_byte_rate, format_byte_size


class NetworkMonitor:
    """Collect and render per-interface network counters and connection states."""

    def __init__(self, iface: str | None = None):
        self.iface = iface
        self._samplers: dict[str, SampleWindow] = {}

    def collect(self) -> dict:
        pernic = psutil.net_io_counters(pernic=True)
        interfaces = []

        for name, counters in pernic.items():
            if self.iface and name != self.iface:
                continue

            sampler = self._samplers.setdefault(name, SampleWindow())
            sampled = sampler.sample(
                {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                }
            )

            deltas = sampled["deltas"]
            values = sampled["values"]
            interfaces.append(
                {
                    "name": name,
                    **values,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout,
                    "rx_bps": max(0.0, deltas["bytes_recv"]),
                    "tx_bps": max(0.0, deltas["bytes_sent"]),
                    "rx_pps": max(0.0, deltas["packets_recv"]),
                    "tx_pps": max(0.0, deltas["packets_sent"]),
                    "timestamp_utc": sampled["timestamp_utc"],
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

        return {
            "interfaces": interfaces,
            "connection_states": connection_states,
            "connection_error": connection_error,
            "iface": self.iface,
            "timestamp_utc": interfaces[0]["timestamp_utc"] if interfaces else None,
        }

    def render(self, data: dict) -> Group:
        iface_title = data["iface"] if data["iface"] else "all"
        title_suffix = f" @ {data['timestamp_utc']}" if data["timestamp_utc"] else ""
        interface_table = Table(title=f"Network Interfaces ({iface_title}){title_suffix}", box=box.SQUARE)
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
                    format_byte_rate(nic["rx_bps"]),
                    format_byte_rate(nic["tx_bps"]),
                    format_byte_size(nic["bytes_recv"]),
                    format_byte_size(nic["bytes_sent"]),
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
    def _format_rate(value: float) -> str:
        return f"{value:,.1f}"
