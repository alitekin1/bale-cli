import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output

console = Console()


@click.group()
def contacts():
    """List and search contacts."""
    pass


@contacts.command("list")
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def contacts_list(limit, store, json_output):
    """List contacts from local store."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _list():
        await db.init()
        results = await db.get_contacts(limit=limit)
        if json_output:
            output(results, json_mode=True)
        else:
            output(results, json_mode=False, title="Contacts", columns=["peer_id", "first_name", "last_name", "phone"])

    asyncio.run(_list())


@contacts.command("search")
@click.argument("query")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def contacts_search(query, limit, store, json_output):
    """Search contacts by name or phone."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _search():
        await db.init()
        all_contacts = await db.get_contacts(limit=10000)
        query_lower = query.lower()
        results = [
            c for c in all_contacts
            if query_lower in (c.get("first_name") or "").lower()
            or query_lower in (c.get("last_name") or "").lower()
            or query_lower in (c.get("phone") or "").lower()
            or query_lower in (c.get("username") or "").lower()
        ]
        if json_output:
            output(results, json_mode=True)
        else:
            output(results, json_mode=False, title=f"Contacts matching '{query}'", columns=["peer_id", "first_name", "last_name", "phone"])

    asyncio.run(_search())


@contacts.command("live")
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def contacts_live(limit, store, json_output):
    """Fetch live contacts from Bale API."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.methods import GetContacts

    async def _live():
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True)

            db = Store(store_dir)
            await db.init()

            try:
                result = await client(GetContacts())
                contacts_data = result.contacts if hasattr(result, "contacts") else []

                results = []
                for c in contacts_data:
                    contact = {
                        "peer_id": c.id if hasattr(c, "id") else None,
                        "first_name": c.first_name if hasattr(c, "first_name") else None,
                        "last_name": c.last_name if hasattr(c, "last_name") else None,
                        "phone": c.phone if hasattr(c, "phone") else None,
                        "username": c.username if hasattr(c, "username") else None,
                    }
                    results.append(contact)

                    await db.upsert_contact(
                        peer_id=contact["peer_id"],
                        first_name=contact["first_name"] or "",
                        last_name=contact["last_name"] or "",
                        phone=contact["phone"] or "",
                        username=contact["username"] or "",
                    )

                if json_output:
                    output(results, json_mode=True)
                else:
                    output(results, json_mode=False, title="Live Contacts", columns=["peer_id", "first_name", "last_name", "phone"])
            except Exception as e:
                console.print(f"[red]Failed to fetch contacts: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_live())
