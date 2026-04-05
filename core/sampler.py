from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_utc_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class SampleWindow:
    """Stores previous/current snapshots and computes per-second deltas."""

    previous: dict[str, float] | None = field(default=None, init=False)
    current: dict[str, float] | None = field(default=None, init=False)
    previous_ts: datetime | None = field(default=None, init=False)
    current_ts: datetime | None = field(default=None, init=False)

    def sample(self, values: dict[str, float]) -> dict[str, object]:
        now = _utc_now()
        self.previous = self.current
        self.previous_ts = self.current_ts

        self.current = dict(values)
        self.current_ts = now

        return {
            "values": dict(self.current),
            "timestamp": self.current_ts.timestamp(),
            "timestamp_utc": _format_utc_timestamp(self.current_ts),
            "elapsed": self.elapsed,
            "deltas": self._deltas(),
        }

    @property
    def elapsed(self) -> float:
        if not self.previous_ts or not self.current_ts:
            return 0.0
        return max((self.current_ts - self.previous_ts).total_seconds(), 1e-6)

    def _deltas(self) -> dict[str, float]:
        if not self.previous or not self.current:
            return {key: 0.0 for key in self.current or {}}

        elapsed = self.elapsed
        deltas: dict[str, float] = {}
        for key, value in self.current.items():
            previous_value = float(self.previous.get(key, value))
            deltas[key] = (float(value) - previous_value) / elapsed
        return deltas


def _format_binary_units(value: float, suffix: str = "") -> str:
    normalized = float(value)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if normalized < 1024 or unit == "PB":
            spacer = "" if suffix.startswith("/") else " "
            return f"{normalized:.1f} {unit}{spacer}{suffix}".strip()
        normalized /= 1024
    return f"{normalized:.1f} EB {suffix}".strip()


def format_byte_size(value: float) -> str:
    return _format_binary_units(value)


def format_byte_rate(value: float) -> str:
    return _format_binary_units(value, suffix="/s")
