from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
import psutil
import time

console = Console()

# Thresholds for highlighting
CPU_WARNING = 50
CPU_CRITICAL = 80
RAM_WARNING = 50
RAM_CRITICAL = 80

def get_top_processes(n=10, cpu_weight=0.7, ram_weight=0.3):
    """Return top n processes sorted by weighted CPU + RAM usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Weighted score: CPU*0.7 + RAM*0.3 by default
    processes = sorted(
        processes,
        key=lambda x: x['cpu_percent'] * cpu_weight + x['memory_percent'] * ram_weight,
        reverse=True
    )
    return processes[:n]

def colorize(value, warning, critical):
    """Return value as colored string based on thresholds."""
    if value >= critical:
        return f"[red]{value:.1f}%[/red]"
    elif value >= warning:
        return f"[yellow]{value:.1f}%[/yellow]"
    else:
        return f"{value:.1f}%"

def make_table():
    cpu_total = psutil.cpu_percent(interval=None)
    ram_total = psutil.virtual_memory().percent

    table = Table(title=f"System Monitor — CPU {cpu_total:.1f}% | RAM {ram_total:.1f}%", box=box.SQUARE)
    table.add_column("PID", justify="right", width=6)
    table.add_column("Name", width=20, overflow="fold")
    table.add_column("CPU %", justify="right", width=6)
    table.add_column("RAM %", justify="right", width=6)

    top_procs = get_top_processes()

    for proc in top_procs:
        name = proc['name'][:20] if len(proc['name']) > 20 else proc['name']
        cpu_str = colorize(proc['cpu_percent'], CPU_WARNING, CPU_CRITICAL)
        ram_str = colorize(proc['memory_percent'], RAM_WARNING, RAM_CRITICAL)
        table.add_row(
            str(proc['pid']).rjust(6),
            name,
            cpu_str.rjust(6),
            ram_str.rjust(6)
        )

    # Fill remaining rows for static height
    for _ in range(len(top_procs), 10):
        table.add_row("-", "-", "-", "-")

    return table

def main():
    with Live(make_table(), refresh_per_second=2, screen=False) as live:
        while True:
            live.update(make_table())
            time.sleep(1)

if __name__ == "__main__":
    main()