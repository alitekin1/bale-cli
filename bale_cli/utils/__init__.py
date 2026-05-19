import json
import os
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def get_session_path(store_dir: Path, profile: str = None) -> Path:
    """Get session file path, optionally with profile name."""
    if profile:
        return store_dir / f"session_{profile}.bale"
    return store_dir / "session.bale"


def get_db_path(store_dir: Path, profile: str = None) -> Path:
    """Get database file path, optionally with profile name."""
    if profile:
        return store_dir / f"bale_{profile}.db"
    return store_dir / "bale.db"


def output_json(data: Any, full: bool = False):
    """Output data as JSON."""
    if isinstance(data, list):
        json.dump(data, sys.stdout, indent=2, default=str)
    elif isinstance(data, dict):
        json.dump(data, sys.stdout, indent=2, default=str)
    else:
        json.dump(data, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def output_table(rows: list[dict], title: str = None, columns: list[str] = None):
    """Output data as a rich table."""
    if not rows:
        console.print("No results found.")
        return

    if columns is None:
        columns = list(rows[0].keys())

    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80

    if len(columns) > 6 or sum(len(c) for c in columns) > term_width - 10:
        for i, row in enumerate(rows):
            if title and i == 0:
                console.print(f"[bold]{title}[/bold]")
            console.print(f"[dim]--- Row {i+1} ---[/dim]")
            for col in columns:
                val = row.get(col, "")
                if val is None:
                    val = "None"
                elif isinstance(val, (dict, list)):
                    val = str(val)[:100]
                else:
                    val = str(val)[:200]
                header = col.replace("_", " ").title()
                console.print(f"  [cyan]{header}:[/cyan] {val}")
        return

    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        header = col.replace("_", " ").title()
        table.add_column(header, overflow="fold", max_width=30, no_wrap=False)

    for row in rows:
        values = []
        for c in columns:
            val = row.get(c, "")
            if val is None:
                values.append("")
            elif isinstance(val, (dict, list)):
                values.append(str(val)[:100])
            else:
                values.append(str(val)[:200])
        table.add_row(*values)

    console.print(table)


def output(data: Any, json_mode: bool = False, title: str = None, columns: list[str] = None):
    """Smart output — JSON if requested, otherwise table."""
    if json_mode:
        output_json(data)
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        output_table(data, title=title, columns=columns)
    else:
        output_json(data)


def emit_event(event_type: str, data: Any):
    """Emit an NDJSON event to stderr."""
    event = {"event": event_type, "data": data}
    sys.stderr.write(json.dumps(event, default=str) + "\n")
    sys.stderr.flush()


def parse_duration(dur: str) -> int:
    """Parse duration string like '30s', '5m' to seconds."""
    dur = dur.strip().lower()
    if dur.endswith("s"):
        return int(dur[:-1])
    elif dur.endswith("m"):
        return int(dur[:-1]) * 60
    elif dur.endswith("h"):
        return int(dur[:-1]) * 3600
    return int(dur)
