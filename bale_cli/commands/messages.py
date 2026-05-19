import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output

console = Console()


@click.group()
def messages():
    """Search and list messages."""
    pass


@messages.command("search")
@click.argument("query")
@click.option("--chat", type=int, default=None, help="Filter by chat ID")
@click.option("--sender", type=int, default=None, help="Filter by sender ID")
@click.option("--type", "msg_type", default=None, help="Filter by message type (text, photo, document)")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
@click.option("--full", is_flag=True, default=False, help="Show full message details")
def messages_search(query, chat, sender, msg_type, limit, offset, store, json_output, full):
    """Search messages in local store (FTS5 with LIKE fallback)."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _search():
        await db.init()
        results = await db.search_messages_fts(
            query=query,
            chat_id=chat,
            limit=limit,
            offset=offset,
        )

        if json_output:
            output(results, json_mode=True)
        else:
            columns = ["message_id", "chat_title", "sender_name", "text", "date"]
            if full:
                columns = list(results[0].keys()) if results else columns
            output(results, json_mode=False, title=f"Search: {query}", columns=columns)

    asyncio.run(_search())


@messages.command("list")
@click.option("--chat", type=int, default=None, help="Filter by chat ID")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--offset", type=int, default=0, help="Offset for pagination")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
@click.option("--full", is_flag=True, default=False, help="Show full message details")
def messages_list(chat, limit, offset, store, json_output, full):
    """List messages from local store."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _list():
        await db.init()
        results = await db.search_messages(
            query="",
            chat_id=chat,
            limit=limit,
            offset=offset,
        )

        if json_output:
            output(results, json_mode=True)
        else:
            columns = ["message_id", "chat_title", "sender_name", "text", "date"]
            if full:
                columns = list(results[0].keys()) if results else columns
            output(results, json_mode=False, title="Messages", columns=columns)

    asyncio.run(_list())


@messages.command("count")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def messages_count(store, json_output):
    """Show total message count in local store."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _count():
        await db.init()
        count = await db.message_count()
        if json_output:
            output({"total_messages": count}, json_mode=True)
        else:
            console.print(f"Total messages: [bold]{count}[/bold]")

    asyncio.run(_count())
