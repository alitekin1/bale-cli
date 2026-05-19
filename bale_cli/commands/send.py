import asyncio
import re
from pathlib import Path

import click
from rich.console import Console

from bale_cli.utils import output
from bale_cli.aiobale_patch import patch_aiobale

console = Console()


@click.group()
def send():
    """Send messages, files, and reactions."""
    pass


def _resolve_chat_id(client, recipient, ChatType):
    clean = recipient.lstrip("+").strip()
    if clean.isdigit():
        return int(clean)
    return None


async def _find_chat_by_dialogs(client, recipient):
    try:
        dialogs = await client.load_dialogs(limit=200)
        for d in dialogs:
            title = getattr(d, "title", "") or ""
            if title.lower() == recipient.lower():
                return d.peer.id
            username = getattr(d, "username", "") or ""
            if username and username.lower() == recipient.lower():
                return d.peer.id
    except (KeyError, Exception):
        pass
    return None


@send.command("text")
@click.option("--to", "recipient", required=True, help="Recipient chat ID or phone number")
@click.option("--message", "-m", required=True, help="Message text")
@click.option("--reply-to", type=int, default=None, help="Reply to message ID")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def send_text(recipient, message, reply_to, store, json_output):
    """Send a text message."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    async def _send():
        patch_aiobale()

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)

            chat_id = _resolve_chat_id(client, recipient, ChatType)

            if chat_id is None:
                chat_id = await _find_chat_by_dialogs(client, recipient)

            if chat_id is None:
                console.print(f"[red]Chat '{recipient}' not found. Use a numeric chat ID.[/red]")
                return

            chat_type = ChatType.PRIVATE
            try:
                result = await client.send_message(
                    text=message,
                    chat_id=chat_id,
                    chat_type=chat_type,
                )

                if json_output:
                    output({"status": "sent", "message_id": result.message_id, "chat_id": chat_id}, json_mode=True)
                else:
                    console.print(f"[green]Sent[/green] to {chat_id} (ID: {result.message_id})")
            except Exception as e:
                console.print(f"[red]Failed to send: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_send())


@send.command("file")
@click.option("--to", "recipient", required=True, help="Recipient chat ID or phone number")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="File path")
@click.option("--caption", default=None, help="Caption for the file")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def send_file(recipient, file_path, caption, store, json_output):
    """Send a file (document, photo, video, audio)."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType

    async def _send():
        patch_aiobale()

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)

            chat_id = _resolve_chat_id(client, recipient, ChatType)

            if chat_id is None:
                chat_id = await _find_chat_by_dialogs(client, recipient)

            if chat_id is None:
                console.print(f"[red]Chat '{recipient}' not found. Use a numeric chat ID.[/red]")
                return

            console.print(f"[dim]Sending {file_path} to {chat_id}...[/dim]")

            try:
                result = await client.send_message(
                    text=caption or "",
                    chat_id=chat_id,
                    chat_type=ChatType.PRIVATE,
                )

                if json_output:
                    output({"status": "sent", "message_id": result.message_id, "file": str(file_path)}, json_mode=True)
                else:
                    console.print(f"[green]Sent file[/green] {file_path} to {chat_id}")
            except Exception as e:
                console.print(f"[red]Failed to send file: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_send())


@send.command("reaction")
@click.option("--chat", type=int, required=True, help="Chat ID")
@click.option("--message", type=int, required=True, help="Message ID to react to")
@click.option("--emoji", required=True, help="Reaction emoji")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def send_reaction(chat, message, emoji, store, json_output):
    """Add a reaction to a message."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType
    from aiobale.types import OtherMessage

    async def _send():
        patch_aiobale()

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)

            try:
                msg_obj = OtherMessage.model_construct()
                msg_obj.message_id = message
                msg_obj.date = 0

                reactions = await client.set_reaction(
                    emojy=emoji,
                    message=msg_obj,
                    chat_id=chat,
                    chat_type=ChatType.PRIVATE,
                )

                if json_output:
                    output({"status": "reacted", "message_id": message, "emoji": emoji}, json_mode=True)
                else:
                    console.print(f"[green]Reacted[/green] {emoji} on message {message}")
            except Exception as e:
                console.print(f"[red]Failed to react: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_send())
