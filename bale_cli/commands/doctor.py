import asyncio
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bale_cli.store import Store
from bale_cli import __version__

console = Console()


@click.command()
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def doctor(store, json_output):
    """Run diagnostics and report system health."""
    store_dir = store or Path.home() / ".bale-cli"

    async def _doctor():
        checks = {}

        # Version
        checks["version"] = __version__

        # Python version
        checks["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Platform
        checks["platform"] = sys.platform

        # Store directory
        checks["store_exists"] = store_dir.exists()
        checks["store_path"] = str(store_dir)

        # Session file
        session_file = store_dir / "session.bale"
        checks["session_exists"] = session_file.exists()

        # Database
        db = Store(store_dir)
        await db.init()
        db_size = await db.db_size()
        msg_count = await db.message_count()
        checks["db_exists"] = db.db_path.exists()
        checks["db_size_mb"] = round(db_size / (1024 * 1024), 2)
        checks["message_count"] = msg_count

        # aiobale
        try:
            import aiobale
            checks["aiobale_version"] = getattr(aiobale, "__version__", "unknown")
        except ImportError:
            checks["aiobale_version"] = "not installed"

        # Disk space
        try:
            stat = os.statvfs(store_dir)
            free_gb = (stat.f_frsize * stat.f_bavail) / (1024 ** 3)
            checks["disk_free_gb"] = round(free_gb, 2)
        except Exception:
            checks["disk_free_gb"] = "unknown"

        if json_output:
            from bale_cli.utils import output
            output(checks, json_mode=True)
        else:
            table = Table(title="bale-cli Doctor")
            table.add_column("Check", style="cyan")
            table.add_column("Value", style="green")

            for key, value in checks.items():
                label = key.replace("_", " ").title()
                if isinstance(value, bool):
                    val = "[green]Yes[/green]" if value else "[red]No[/red]"
                else:
                    val = str(value)
                table.add_row(label, val)

            console.print(table)

            if not checks["session_exists"]:
                console.print("\n[red]Not authenticated.[/red] Run [bold]bale auth login[/bold]")
            if checks["message_count"] == 0:
                console.print("\n[yellow]No messages synced.[/yellow] Run [bold]bale sync start[/bold]")

    asyncio.run(_doctor())
