from __future__ import annotations

from rich.layout import Layout
from rich.panel import Panel



def render_monitors(renderables: dict[str, object], mode: str) -> object:
    """Render selected monitor output based on CLI mode."""
    if mode == "all" and {"system", "network"}.issubset(renderables):
        layout = Layout(name="root")
        layout.split_column(
            Layout(Panel(renderables["system"], title="System", border_style="green"), ratio=1),
            Layout(Panel(renderables["network"], title="Network", border_style="blue"), ratio=2),
        )
        return layout

    if mode == "system" and "system" in renderables:
        return Panel(renderables["system"], title="System", border_style="green")

    if mode == "network" and "network" in renderables:
        return Panel(renderables["network"], title="Network", border_style="blue")

    fallback = next(iter(renderables.values()), "No monitor selected")
    return Panel(fallback, title="Sys Monitor", border_style="cyan")
