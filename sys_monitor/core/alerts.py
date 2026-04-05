from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, TypedDict

Severity = Literal["info", "warning", "critical"]


class MonitorEvent(TypedDict):
    """Standard monitor event payload emitted by monitor hooks."""

    timestamp: str
    monitor: str
    metric: str
    value: float
    severity: Severity
    context: dict[str, object]


@dataclass(frozen=True)
class ThresholdRule:
    """Rule mapping a metric value to warning/critical severities."""

    monitor: str
    metric: str
    warning: float
    critical: float

    def evaluate(self, value: float) -> Severity:
        if value >= self.critical:
            return "critical"
        if value >= self.warning:
            return "warning"
        return "info"


class AlertEngine:
    """Generate standardized alert events from monitor snapshots."""

    def __init__(self, rules: list[ThresholdRule] | None = None):
        self.rules = rules or [
            ThresholdRule(monitor="system", metric="cpu_total", warning=50.0, critical=80.0),
            ThresholdRule(monitor="system", metric="ram_total", warning=50.0, critical=80.0),
            ThresholdRule(monitor="network", metric="error_total", warning=1.0, critical=10.0),
            ThresholdRule(monitor="network", metric="drop_total", warning=1.0, critical=10.0),
        ]
        self._rule_map = {(rule.monitor, rule.metric): rule for rule in self.rules}

    def evaluate(self, monitor: str, data: dict[str, object]) -> list[MonitorEvent]:
        if monitor == "system":
            metrics = self._system_metrics(data)
        elif monitor == "network":
            metrics = self._network_metrics(data)
        else:
            metrics = []

        events: list[MonitorEvent] = []
        for metric_name, value, context in metrics:
            rule = self._rule_map.get((monitor, metric_name))
            if not rule:
                continue

            severity = rule.evaluate(value)
            if severity == "info":
                continue

            events.append(
                {
                    "timestamp": self._timestamp(data),
                    "monitor": monitor,
                    "metric": metric_name,
                    "value": float(value),
                    "severity": severity,
                    "context": context,
                }
            )
        return events

    @staticmethod
    def _timestamp(data: dict[str, object]) -> str:
        timestamp_utc = data.get("timestamp_utc")
        if isinstance(timestamp_utc, str) and timestamp_utc:
            return timestamp_utc
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    @staticmethod
    def _system_metrics(data: dict[str, object]) -> list[tuple[str, float, dict[str, object]]]:
        values = data.get("values")
        if not isinstance(values, dict):
            return []

        metrics: list[tuple[str, float, dict[str, object]]] = []
        cpu = values.get("cpu_total")
        if isinstance(cpu, (int, float)):
            metrics.append(("cpu_total", float(cpu), {}))

        ram = values.get("ram_total")
        if isinstance(ram, (int, float)):
            metrics.append(("ram_total", float(ram), {}))
        return metrics

    @staticmethod
    def _network_metrics(data: dict[str, object]) -> list[tuple[str, float, dict[str, object]]]:
        interfaces = data.get("interfaces")
        if not isinstance(interfaces, list):
            return []

        error_total = 0.0
        drop_total = 0.0
        iface_names: list[str] = []

        for interface in interfaces:
            if not isinstance(interface, dict):
                continue
            iface_names.append(str(interface.get("name", "unknown")))
            error_total += float(interface.get("errin", 0) or 0)
            error_total += float(interface.get("errout", 0) or 0)
            drop_total += float(interface.get("dropin", 0) or 0)
            drop_total += float(interface.get("dropout", 0) or 0)

        context = {"interfaces": iface_names}
        return [
            ("error_total", error_total, context),
            ("drop_total", drop_total, context),
        ]
