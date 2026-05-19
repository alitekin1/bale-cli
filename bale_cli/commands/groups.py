import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output

console = Console()


@click.group()
def groups():
    """List and manage groups and channels."""
    pass


@groups.command("list")
@click.option("--channels", is_flag=True, default=False, help="Show only channels")
@click.option("--groups-only", is_flag=True, default=False, help="Show only groups (not channels)")
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def groups_list(channels, groups_only, limit, store, json_output):
    """List groups/channels from local store."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _list():
        await db.init()
        is_channel = True if channels else (False if groups_only else None)
        results = await db.get_groups(limit=limit, is_channel=is_channel)
        if json_output:
            output(results)
        else:
            output(results, title="Groups & Channels", columns=["peer_id", "title", "member_count", "is_channel"])

    asyncio.run(_list())


@groups.command("search")
@click.argument("query")
@click.option("--limit", type=int, default=50, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def groups_search(query, limit, store, json_output):
    """Search groups by title."""
    store_dir = store or Path.home() / ".bale-cli"
    db = Store(store_dir)

    async def _search():
        await db.init()
        all_groups = await db.get_groups(limit=10000)
        query_lower = query.lower()
        results = [
            g for g in all_groups
            if query_lower in (g.get("title") or "").lower()
        ]
        if json_output:
            output(results)
        else:
            output(results, title=f"Groups matching '{query}'", columns=["peer_id", "title", "member_count"])

    asyncio.run(_search())


@groups.command("info")
@click.argument("group_id", type=int)
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def groups_info(group_id, store, json_output):
    """Show group details."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType
    from aiobale.methods import GetFullGroup
    from aiobale.types import Peer

    async def _info():
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True)

            try:
                peer = Peer(id=group_id, type=ChatType.GROUP)
                result = await client(GetFullGroup(peer=peer))

                group_obj = result.group if hasattr(result, "group") else None
                group_info = {
                    "id": group_id,
                    "title": group_obj.title if group_obj and hasattr(group_obj, "title") else None,
                    "about": group_obj.about if group_obj and hasattr(group_obj, "about") else None,
                    "member_count": group_obj.participants_count if group_obj and hasattr(group_obj, "participants_count") else None,
                }

                if json_output:
                    output(group_info)
                else:
                    console.print(f"[bold]{group_info['title']}[/bold] (ID: {group_id})")
                    console.print(f"Members: {group_info['member_count']}")
                    if group_info['about']:
                        console.print(f"About: {group_info['about']}")
            except Exception as e:
                console.print(f"[red]Failed to get group info: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_info())


@groups.command("members")
@click.argument("group_id", type=int)
@click.option("--limit", type=int, default=100, help="Max results")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def groups_members(group_id, limit, store, json_output):
    """List group members."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType
    from aiobale.methods import LoadMembers
    from aiobale.types import Peer

    async def _members():
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True)

            try:
                peer = Peer(id=group_id, type=ChatType.GROUP)
                result = await client(LoadMembers(peer=peer, limit=limit))

                members = result.members if hasattr(result, "members") else []
                member_list = []
                for m in members:
                    member_list.append({
                        "id": m.id if hasattr(m, "id") else None,
                        "name": m.name if hasattr(m, "name") else None,
                        "is_admin": m.is_admin if hasattr(m, "is_admin") else False,
                    })

                if json_output:
                    output(member_list)
                else:
                    output(member_list, title=f"Members of {group_id}", columns=["id", "name", "is_admin"])
            except Exception as e:
                console.print(f"[red]Failed to load members: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_members())
