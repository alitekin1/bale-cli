import asyncio
import json
import signal
import sys
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output, emit_event
from bale_cli.aiobale_patch import patch_aiobale

console = Console()


@click.group()
def sync():
    """Sync messages from Bale to local store."""
    pass


@sync.command()
@click.option("--follow", is_flag=True, default=False, help="Continuously sync (follow mode)")
@click.option("--limit", type=int, default=500, help="Max messages to sync in one-shot mode")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
@click.option("--events", is_flag=True, default=False, help="Emit NDJSON events")
@click.option("--media", is_flag=True, default=False, help="Download media attachments")
def start(follow, limit, store, json_output, events, media):
    """Sync messages from Bale to local SQLite store.

    One-shot mode (default): loads recent messages and exits.
    Follow mode (--follow): keeps running and syncs new messages in real-time.
    """
    store_dir = store or Path.home() / ".bale-cli"
    store_dir.mkdir(parents=True, exist_ok=True)
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        sys.exit(1)

    async def _sync():
        patch_aiobale()

        from aiobale import Client, Dispatcher
        from aiobale.types import Message
        from aiobale.enums import ChatType

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)
        db = Store(store_dir)
        await db.init()

        msg_count = 0
        stop_event = asyncio.Event()
        sender_cache = {}

        def _handle_signal():
            console.print("\n[yellow]Stopping sync...[/yellow]")
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
        async def on_message(msg: Message):
            nonlocal msg_count

            chat_id = msg.chat.id
            chat_type = msg.chat.type
            peer_type = chat_type.name.lower() if hasattr(chat_type, "name") else str(chat_type)

            text = msg.text or ""
            sender_id = msg.sender_id
            sender_name = await get_sender_name(sender_id)

            media_info = {}
            if msg.document:
                media_info = {
                    "type": "document",
                    "file_id": msg.document.file_id,
                    "mime_type": msg.document.mime_type,
                    "file_size": msg.document.size,
                }

            await db.upsert_chat(
                peer_id=chat_id,
                peer_type=peer_type,
                last_message_date=msg.date,
            )

            await db.insert_message(
                message_id=msg.message_id,
                chat_id=chat_id,
                peer_id=chat_id,
                peer_type=peer_type,
                text=text,
                sender_id=sender_id,
                sender_name=sender_name,
                message_type=media_info.get("type", "text"),
                date=msg.date,
                media_file_id=str(media_info.get("file_id")) if media_info.get("file_id") else None,
                media_mime_type=media_info.get("mime_type"),
                media_file_size=media_info.get("file_size"),
                raw_json=json.dumps(msg.model_dump(), default=str) if events else None,
            )

            msg_count += 1

            if events:
                emit_event("message", {
                    "message_id": msg.message_id,
                    "chat_id": chat_id,
                    "text": text[:200],
                    "sender": sender_name,
                    "date": msg.date,
                })

            if not follow and msg_count >= limit:
                stop_event.set()

        try:
            await client.start(run_in_background=True, signal_handling=False)

            dialogs = []
            try:
                dialogs = await client.load_dialogs(limit=200)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load dialogs: {e}[/yellow]")
                console.print("[dim]Continuing with live sync only (follow mode will still work)[/dim]")

            if not dialogs:
                stored_chats = await db.get_chats(limit=500)
                if stored_chats:
                    console.print(f"[dim]Using {len(stored_chats)} stored chats for history sync[/dim]")
                    for chat in stored_chats:
                        chat_id = chat.get("peer_id")
                        peer_type = chat.get("peer_type", "private")
                        type_map = {
                            "private": ChatType.PRIVATE,
                            "group": ChatType.GROUP,
                            "channel": ChatType.CHANNEL,
                            "super_group": ChatType.SUPER_GROUP,
                            "bot": ChatType.BOT,
                        }
                        ct = type_map.get(peer_type, ChatType.PRIVATE)

                        try:
                            history = await client.load_history(
                                chat_id=chat_id,
                                chat_type=ct,
                                limit=50,
                            )
                            for h_msg in history:
                                sender_id = h_msg.sender_id
                                sender_name = await get_sender_name(sender_id)

                                media_info = {}
                                if h_msg.document:
                                    media_info = {
                                        "type": "document",
                                        "file_id": h_msg.document.file_id,
                                        "mime_type": h_msg.document.mime_type,
                                        "file_size": h_msg.document.size,
                                    }

                                await db.insert_message(
                                    message_id=h_msg.message_id,
                                    chat_id=chat_id,
                                    peer_id=chat_id,
                                    peer_type=peer_type,
                                    text=h_msg.text or "",
                                    sender_id=sender_id,
                                    sender_name=sender_name,
                                    message_type=media_info.get("type", "text"),
                                    date=h_msg.date,
                                    media_file_id=str(media_info.get("file_id")) if media_info.get("file_id") else None,
                                    media_mime_type=media_info.get("mime_type"),
                                    media_file_size=media_info.get("file_size"),
                                )
                                msg_count += 1
                        except Exception as e:
                            console.print(f"[dim]Failed to load history for {chat_id}: {e}[/dim]")

            for dialog in dialogs:
                peer = dialog.peer
                chat_id = peer.id
                peer_type = peer.type.name.lower() if hasattr(peer.type, "name") else str(peer.type)

                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                    "bot": ChatType.BOT,
                }
                ct = type_map.get(peer_type, ChatType.PRIVATE)

                await db.upsert_chat(
                    peer_id=chat_id,
                    peer_type=peer_type,
                    title=getattr(dialog, "title", None),
                    username=getattr(dialog, "username", None),
                    last_message_date=dialog.date,
                )

                try:
                    history = await client.load_history(
                        chat_id=chat_id,
                        chat_type=ct,
                        limit=50,
                    )
                    for h_msg in history:
                        sender_id = h_msg.sender_id
                        sender_name = await get_sender_name(sender_id)

                        media_info = {}
                        if h_msg.document:
                            media_info = {
                                "type": "document",
                                "file_id": h_msg.document.file_id,
                                "mime_type": h_msg.document.mime_type,
                                "file_size": h_msg.document.size,
                            }

                        await db.insert_message(
                            message_id=h_msg.message_id,
                            chat_id=chat_id,
                            peer_id=chat_id,
                            peer_type=peer_type,
                            text=h_msg.text or "",
                            sender_id=sender_id,
                            sender_name=sender_name,
                            message_type=media_info.get("type", "text"),
                            date=h_msg.date,
                            media_file_id=str(media_info.get("file_id")) if media_info.get("file_id") else None,
                            media_mime_type=media_info.get("mime_type"),
                            media_file_size=media_info.get("file_size"),
                        )
                        msg_count += 1
                except Exception as e:
                    console.print(f"[dim]Failed to load history for {chat_id}: {e}[/dim]")

            if json_output:
                output({"status": "synced", "messages": msg_count}, json_mode=True)
            else:
                console.print(f"[green]Synced {msg_count} messages[/green]")

            if follow:
                console.print("[dim]Follow mode active. Press Ctrl+C to stop.[/dim]")
                await stop_event.wait()

        finally:
            await client.stop()

        total = await db.message_count()
        if json_output:
            output({"status": "complete", "total_messages": total}, json_mode=True)
        else:
            console.print(f"[green]Done. Total messages in store: {total}[/green]")

    asyncio.run(_sync())
