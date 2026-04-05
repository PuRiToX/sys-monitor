# sys-monitor

`sys-monitor` is a real-time terminal monitor for **system** and **network** health.
It renders live Rich tables and panels for:

- Total CPU and RAM utilization.
- Top processes ranked by weighted CPU + memory usage.
- Per-interface network throughput (bytes/sec and packets/sec).
- Interface error/drop counters.
- Inet connection state counts.
- Alert events (warning/critical) with optional JSONL and CSV export.

The project is implemented in Python with `psutil` for metrics and `rich` for terminal UI.

---

## What the monitor shows

## 1) System monitor

When `--mode system` or `--mode all` is selected, the monitor collects:

- `cpu_total`: total host CPU usage (`psutil.cpu_percent`).
- `ram_total`: total RAM usage (`psutil.virtual_memory().percent`).
- Top processes (PID, name, CPU %, RAM %).

Process ranking is a weighted score:

`score = cpu_percent * 0.7 + memory_percent * 0.3`

Rows are colorized by utilization:

- Yellow when usage is at least **50%**.
- Red when usage is at least **80%**.

The table header also includes rate-of-change deltas (`%/s`) derived from consecutive samples.

## 2) Network monitor

When `--mode network` or `--mode all` is selected, the monitor collects per-interface counters from `psutil.net_io_counters(pernic=True)`:

- Total bytes sent/received.
- Total packets sent/received.
- Error counters (`errin`, `errout`).
- Drop counters (`dropin`, `dropout`).

It computes rates from counter deltas between samples:

- RX/s and TX/s in bytes per second.
- Packet RX/s and TX/s in packets per second.

Interfaces are sorted by highest combined throughput (`rx_bps + tx_bps`).

It also displays inet connection-state counts from `psutil.net_connections(kind="inet")`.
If connection inspection is not permitted, the UI shows an error row instead of state counts.

## 3) Alerts and event export

An alert engine evaluates each frame and emits events for these built-in rules:

- `system.cpu_total`: warning at **50**, critical at **80**.
- `system.ram_total`: warning at **50**, critical at **80**.
- `network.error_total`: warning at **1**, critical at **10**.
- `network.drop_total`: warning at **1**, critical at **10**.

Only warning/critical events are exported (informational events are ignored).

If configured, events can be written to:

- JSONL (`--alerts-jsonl`) — one event object per line.
- CSV (`--alerts-csv`) — columns: `timestamp, monitor, metric, value, severity, context`.

---

## Installation

## Requirements

- Python 3.10+
- A terminal that supports Rich rendering

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the monitor

You can launch either entrypoint:

```bash
python monitor.py
# or
python -m sys_monitor.app
```

By default, this runs both monitors (`--mode all`) with:

- collector refresh interval: `1.0s`
- rich repaint rate: `4` refreshes/second
- top process rows: `10`
- network interface filter: none (all interfaces)

---

## CLI flags

`sys-monitor` currently supports the following flags:

- `--mode {system,network,all}`
  - Selects monitor output.
  - Default: `all`.

- `--refresh <seconds>`
  - Collector sampling interval used by the monitoring loop.
  - Lower values update metrics more frequently.
  - Default: `1.0`.

- `--refresh-per-second <int>`
  - Rich Live repaint rate.
  - Controls UI redraw frequency, separate from sampling interval.
  - Default: `4`.

- `--top-procs <int>`
  - Number of process rows shown in system view.
  - Default: `10`.

- `--iface <name>`
  - Show only a single network interface by exact name (for example `eth0`, `en0`, `wlan0`).
  - Default: all interfaces.

- `--alerts-jsonl <path>`
  - Appends alert events as JSONL.
  - Creates parent directories as needed.

- `--alerts-csv <path>`
  - Appends alert events as CSV.
  - Writes header automatically if the file does not exist.
  - Creates parent directories as needed.

Use `-h` or `--help` to view argparse help text:

```bash
python monitor.py --help
```

---

## Usage examples

Run system-only dashboard:

```bash
python monitor.py --mode system
```

Run network-only dashboard for one interface:

```bash
python monitor.py --mode network --iface eth0
```

Run all monitors faster, with more process rows:

```bash
python monitor.py --mode all --refresh 0.5 --refresh-per-second 8 --top-procs 20
```

Export warning/critical alerts to both JSONL and CSV:

```bash
python monitor.py --alerts-jsonl ./logs/alerts.jsonl --alerts-csv ./logs/alerts.csv
```

---

## Notes and operational behavior

- The monitor runs continuously until interrupted (`Ctrl+C`).
- Timestamps in sampled data and events are UTC-formatted strings.
- Throughput/rates are estimated from consecutive counter snapshots; first frame deltas start at zero.
- `monitor.py` is a compatibility launcher that delegates to `sys_monitor.app:main`.

---

## Troubleshooting

- **No network connection states shown**
  - Your OS permissions may restrict `psutil.net_connections`; the monitor will display an error row.

- **No process names or missing rows**
  - Some processes may be inaccessible (`AccessDenied`) or may exit during iteration.

- **High CPU usage of the monitor itself**
  - Increase `--refresh` (slower sampling) and/or reduce `--refresh-per-second`.

- **No alert files produced**
  - Ensure you provided `--alerts-jsonl` and/or `--alerts-csv`; files are only written when warning/critical alerts occur.
