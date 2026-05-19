import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output
from bale_cli.aiobale_patch import patch_aiobale

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


@messages.command("mark-read")
@click.option("--chat", type=int, required=True, help="Chat ID to mark as read")
@click.option("--type", "chat_type", default="private", help="Chat type: private, group, channel, super_group")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def messages_mark_read(chat, chat_type, store, json_output):
    """Mark a chat as read (clear unread messages)."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    ct = type_map.get(chat_type.lower(), ChatType.PRIVATE)

    async def _mark_read():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.seen_chat(chat_id=chat, chat_type=ct)
            if json_output:
                output({"status": "marked_read", "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Chat {chat} marked as read[/green]")
        except Exception as e:
            console.print(f"[red]Failed to mark as read: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_mark_read())


@messages.command("delete")
@click.option("--chat", type=int, required=True, help="Chat ID containing the message")
@click.option("--message", type=int, required=True, help="Message ID to delete")
@click.option("--date", type=int, default=None, help="Message date/timestamp (auto-detected if not provided)")
@click.option("--type", "chat_type", default="private", help="Chat type: private, group, channel, super_group")
@click.option("--just-me", is_flag=True, default=False, help="Delete only for yourself")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def messages_delete(chat, message, date, chat_type, just_me, store, json_output):
    """Delete a message from a chat."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    ct = type_map.get(chat_type.lower(), ChatType.PRIVATE)

    async def _delete():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            msg_date = date
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
            result = await client.delete_message(
                message_id=message,
                message_date=msg_date,
                chat_id=chat,
                chat_type=ct,
                just_me=just_me,
            )
            if json_output:
                output({"status": "deleted", "message_id": message, "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Message {message} deleted from chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to delete message: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_delete())


@messages.command("forward")
@click.option("--from-chat", "from_chat", type=int, required=True, help="Source chat ID")
@click.option("--to-chat", "to_chat", type=int, required=True, help="Target chat ID")
@click.option("--message", type=int, required=True, help="Message ID to forward")
@click.option("--date", type=int, default=None, help="Message date/timestamp (auto-detected if not provided)")
@click.option("--from-type", "from_type", default="private", help="Source chat type")
@click.option("--to-type", "to_type", default="private", help="Target chat type")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def messages_forward(from_chat, to_chat, message, date, from_type, to_type, store, json_output):
    """Forward a message from one chat to another."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType
    from aiobale.types import InfoMessage, Peer

    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    from_ct = type_map.get(from_type.lower(), ChatType.PRIVATE)
    to_ct = type_map.get(to_type.lower(), ChatType.PRIVATE)

    async def _forward():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            msg_date = date
            if msg_date is None:
                try:
                    history = await client.load_history(chat_id=from_chat, chat_type=from_ct, limit=100)
                    for m in history:
                        if m.message_id == message:
                            msg_date = m.date
                            break
                except Exception:
                    pass
            if msg_date is None:
                msg_date = 0
                console.print(f"[yellow]Message date not found, using 0[/yellow]")
            msg_obj = InfoMessage(
                peer=Peer(id=from_chat, type=from_ct),
                message_id=message,
                date=msg_date,
            )
            result = await client.forward_message(
                message=msg_obj,
                chat_id=to_chat,
                chat_type=to_ct,
            )
            if json_output:
                output({"status": "forwarded", "message_id": message, "from_chat": from_chat, "to_chat": to_chat}, json_mode=True)
            else:
                console.print(f"[green]Message {message} forwarded from {from_chat} to {to_chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to forward message: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_forward())


@messages.command("edit")
@click.option("--chat", type=int, required=True, help="Chat ID containing the message")
@click.option("--message", type=int, required=True, help="Message ID to edit")
@click.option("--text", "-m", required=True, help="New message text")
@click.option("--type", "chat_type", default="private", help="Chat type: private, group, channel, super_group")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def messages_edit(chat, message, text, chat_type, store, json_output):
    """Edit an existing message."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    ct = type_map.get(chat_type.lower(), ChatType.PRIVATE)

    async def _edit():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.edit_message(
                text=text,
                message_id=message,
                chat_id=chat,
                chat_type=ct,
            )
            if json_output:
                output({"status": "edited", "message_id": message, "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Message {message} edited in chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to edit message: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_edit())


@messages.command("watch")
@click.option("--chat", type=int, default=None, help="Watch specific chat only")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=True, help="JSON output (default true for watch)")
def messages_watch(chat, store, json_output):
    """Watch for new messages in real-time (NDJSON output to stdout)."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    import signal
    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    async def _watch():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)
        db = Store(store_dir)
        await db.init()

        stop_event = asyncio.Event()
        sender_cache = {}

        def _handle_signal():
            stop_event.set()

        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, _handle_signal)

        async def get_sender_name(sender_id: int) -> str:
            if sender_id in sender_cache:
                return sender_cache[sender_id]
            try:
                from aiobale.types import InfoPeer
                full_user = await client.load_full_user(sender_id, ChatType.PRIVATE)
                name = full_user.name if hasattr(full_user, "name") else str(sender_id)
                sender_cache[sender_id] = name
                return name
            except Exception:
                return str(sender_id)

        @dp.message()
        async def on_message(msg):
            if chat and msg.chat.id != chat:
                return

            chat_id = msg.chat.id
            chat_type = msg.chat.type.name.lower() if hasattr(msg.chat.type, "name") else "private"
            text = msg.text or ""
            sender_id = msg.sender_id
            sender_name = await get_sender_name(sender_id)

            event = {
                "message_id": msg.message_id,
                "chat_id": chat_id,
                "chat_type": chat_type,
                "text": text,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "date": msg.date,
            }

            await db.upsert_chat(peer_id=chat_id, peer_type=chat_type, last_message_date=msg.date)
            await db.insert_message(
                message_id=msg.message_id,
                chat_id=chat_id,
                peer_id=chat_id,
                peer_type=chat_type,
                text=text,
                sender_id=sender_id,
                sender_name=sender_name,
                message_type="text",
                date=msg.date,
            )

            sys.stdout.write(json.dumps(event, default=str) + "\n")
            sys.stdout.flush()

        try:
            await client.start(run_in_background=True, signal_handling=False)
            if json_output:
                console.print(f"[dim]Watching for new messages... (Ctrl+C to stop)[/dim]", err=True)
            await stop_event.wait()
        finally:
            await client.stop()

    asyncio.run(_watch())
