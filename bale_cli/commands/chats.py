import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output

console = Console()


@click.group()
def chats():
    """List and manage chats."""
    pass


@chats.command("list")
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--offset", type=int, default=0, help="Offset")
@click.option("--type", "chat_type", default=None, help="Filter by type (private, group, channel, bot, super_group)")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def chats_list(limit, offset, chat_type, store, json_output):
    """List chats from local store."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _list():
        await db.init()
        results = await db.get_chats(limit=limit, offset=offset, peer_type=chat_type)
        if json_output:
            output(results, json_mode=True)
        else:
            output(results, json_mode=False, title="Chats", columns=["peer_id", "peer_type", "title", "last_message_date"])

    asyncio.run(_list())


@chats.command("search")
@click.argument("query")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def chats_search(query, limit, store, json_output):
    """Search chats by title or username."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _search():
        await db.init()
        all_chats = await db.get_chats(limit=10000)
        query_lower = query.lower()
        results = [
            c for c in all_chats
            if query_lower in (c.get("title") or "").lower()
            or query_lower in (c.get("username") or "").lower()
            or query_lower in (c.get("local_name") or "").lower()
        ]
        if json_output:
            output(results, json_mode=True)
        else:
            output(results, json_mode=False, title=f"Chats matching '{query}'", columns=["peer_id", "peer_type", "title"])

    asyncio.run(_search())


@chats.command("live")
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def chats_live(limit, store, json_output):
    """Fetch live chat list from Bale API."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    async def _live():
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True)

            db = Store(store_dir)
            await db.init()

            dialogs = []
            try:
                dialogs = await client.load_dialogs(limit=limit)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load dialogs: {e}[/yellow]")
                console.print("[dim]This may be due to an aiobale parsing bug with inline keyboards.[/dim]")

            results = []
            for d in dialogs:
                peer = d.peer
                chat_data = {
                    "peer_id": peer.id,
                    "peer_type": peer.type.name.lower() if hasattr(peer.type, "name") else str(peer.type),
                    "title": getattr(d, "title", None),
                    "username": getattr(d, "username", None),
                    "unread_count": getattr(d, "unread_count", 0),
                }
                results.append(chat_data)

                await db.upsert_chat(
                    peer_id=peer.id,
                    peer_type=chat_data["peer_type"],
                    title=chat_data["title"],
                    username=chat_data["username"],
                    last_message_date=d.date if hasattr(d, "date") else 0,
                )

            if json_output:
                output(results, json_mode=True)
            else:
                output(results, json_mode=False, title="Live Chats", columns=["peer_id", "peer_type", "title", "unread_count"])
        finally:
            await client.stop()

    asyncio.run(_live())
