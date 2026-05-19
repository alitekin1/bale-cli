import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.aiobale_patch import patch_aiobale
from bale_cli.utils import output
from bale_cli.store import Store

console = Console()


@click.group()
def admin():
    """Group/channel admin commands."""
    pass


def _get_chat_type(type_str):
    from aiobale.enums import ChatType
    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    return type_map.get(type_str.lower(), ChatType.PRIVATE)


@admin.command("add-member")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to add")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_add_member(group, user, chat_type, store, json_output):
    """Add a user to a group."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _add():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.invite_users(group_id=group, user_ids=[user], chat_type=ct)
            if json_output:
                output({"status": "added", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} added to group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to add user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_add())


@admin.command("kick-member")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to kick")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_kick_member(group, user, chat_type, store, json_output):
    """Kick a user from a group."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _kick():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.kick_user(group_id=group, user_id=user, chat_type=ct)
            if json_output:
                output({"status": "kicked", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} kicked from group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to kick user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_kick())


@admin.command("make-admin")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to promote")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_make_admin(group, user, chat_type, store, json_output):
    """Make a user admin in a group."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _make_admin():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.make_user_admin(group_id=group, user_id=user, chat_type=ct)
            if json_output:
                output({"status": "promoted", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} made admin in group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to make admin: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_make_admin())


@admin.command("remove-admin")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to demote")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_remove_admin(group, user, chat_type, store, json_output):
    """Remove admin rights from a user."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _remove_admin():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.remove_user_admin(group_id=group, user_id=user, chat_type=ct)
            if json_output:
                output({"status": "demoted", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]Admin rights removed from user {user} in group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to remove admin: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_remove_admin())


@admin.command("ban")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to ban")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_ban(group, user, chat_type, store, json_output):
    """Ban a user from a group."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _ban():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.set_restriction(
                group_id=group, user_id=user, chat_type=ct, restriction="ban"
            )
            if json_output:
                output({"status": "banned", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} banned from group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to ban user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_ban())


@admin.command("unban")
@click.option("--group", type=int, required=True, help="Group ID")
@click.option("--user", type=int, required=True, help="User ID to unban")
@click.option("--type", "chat_type", default="super_group", help="Group type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_unban(group, user, chat_type, store, json_output):
    """Unban a user from a group."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _unban():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.unban_user(group_id=group, user_id=user, chat_type=ct)
            if json_output:
                output({"status": "unbanned", "group_id": group, "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} unbanned from group {group}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to unban user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_unban())


@admin.command("pin")
@click.option("--chat", type=int, required=True, help="Chat ID")
@click.option("--message", type=int, required=True, help="Message ID to pin")
@click.option("--date", type=int, default=None, help="Message date (auto-detected if not provided)")
@click.option("--type", "chat_type", default="private", help="Chat type")
@click.option("--just-me", is_flag=True, default=False, help="Pin only for yourself")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_pin(chat, message, date, chat_type, just_me, store, json_output):
    """Pin a message in a chat."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _pin():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)
        db = Store(store_dir)
        await db.init()

        try:
            await client.start(run_in_background=True, signal_handling=False)
            msg_date = date
            if msg_date is None:
                results = await db.search_messages_fts(query="", chat_id=chat, limit=200)
                for r in results:
                    if r["message_id"] == message:
                        msg_date = r["date"]
                        break
            if msg_date is None:
                try:
                    history = await client.load_history(chat_id=chat, chat_type=ct, limit=100)
                    for m in history:
                        if m.message_id == message:
                            msg_date = m.date
                            break
                except Exception:
                    pass
            if msg_date is None:
                msg_date = 0
                console.print(f"[yellow]Message date not found, using 0[/yellow]")
            result = await client.pin_message(
                message_id=message,
                message_date=msg_date,
                chat_id=chat,
                chat_type=ct,
                just_me=just_me,
            )
            if json_output:
                output({"status": "pinned", "message_id": message, "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Message {message} pinned in chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to pin message: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_pin())


@admin.command("unpin")
@click.option("--chat", type=int, required=True, help="Chat ID")
@click.option("--message", type=int, required=True, help="Message ID to unpin")
@click.option("--date", type=int, default=None, help="Message date (auto-detected if not provided)")
@click.option("--type", "chat_type", default="private", help="Chat type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_unpin(chat, message, date, chat_type, store, json_output):
    """Unpin a message from a chat."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    ct = _get_chat_type(chat_type)

    async def _unpin():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)
        db = Store(store_dir)
        await db.init()

        try:
            await client.start(run_in_background=True, signal_handling=False)
            msg_date = date
            if msg_date is None:
                results = await db.search_messages_fts(query="", chat_id=chat, limit=200)
                for r in results:
                    if r["message_id"] == message:
                        msg_date = r["date"]
                        break
            if msg_date is None:
                try:
                    history = await client.load_history(chat_id=chat, chat_type=ct, limit=100)
                    for m in history:
                        if m.message_id == message:
                            msg_date = m.date
                            break
                except Exception:
                    pass
            if msg_date is None:
                msg_date = 0
                console.print(f"[yellow]Message date not found, using 0[/yellow]")
            result = await client.unpin_message(
                message_id=message,
                message_date=msg_date,
                chat_id=chat,
                chat_type=ct,
            )
            if json_output:
                output({"status": "unpinned", "message_id": message, "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Message {message} unpinned from chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to unpin message: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_unpin())


@admin.command("block")
@click.option("--user", type=int, required=True, help="User ID to block")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_block(user, store, json_output):
    """Block a user."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    async def _block():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.block_user(user_id=user)
            if json_output:
                output({"status": "blocked", "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} blocked[/green]")
        except Exception as e:
            console.print(f"[red]Failed to block user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_block())


@admin.command("unblock")
@click.option("--user", type=int, required=True, help="User ID to unblock")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def admin_unblock(user, store, json_output):
    """Unblock a user."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher

    async def _unblock():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.unblock_user(user_id=user)
            if json_output:
                output({"status": "unblocked", "user_id": user}, json_mode=True)
            else:
                console.print(f"[green]User {user} unblocked[/green]")
        except Exception as e:
            console.print(f"[red]Failed to unblock user: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_unblock())
