from __future__ import annotations

from typing import Iterable

from rich.console import Group
from rich.panel import Panel



def render_monitors(renderables: Iterable[object]) -> Panel:
    """Wrap all monitor renderables in one panel for the app loop."""
    return Panel(Group(*renderables), title="Sys Monitor", border_style="cyan")
