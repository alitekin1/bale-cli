import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


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

    table = Table(title=title)
    for col in columns:
        table.add_column(col, overflow="fold")

    for row in rows:
        table.add_row(*[str(row.get(c, "")) for c in columns])

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
