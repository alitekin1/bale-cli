import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.aiobale_patch import patch_aiobale

console = Console()


@click.group()
def typing():
    """Manage typing indicators."""
    pass


@typing.command("start")
@click.option("--chat", type=int, required=True, help="Chat ID to show typing in")
@click.option("--type", "chat_type", default="private", help="Chat type: private, group, channel, super_group")
@click.option("--mode", default="typing", help="Typing mode: typing, cancel, record, upload, play")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def typing_start(chat, chat_type, mode, store, json_output):
    """Start typing indicator in a chat."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        return

    from aiobale import Client, Dispatcher
    from aiobale.enums import ChatType, TypingMode

    type_map = {
        "private": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "channel": ChatType.CHANNEL,
        "super_group": ChatType.SUPER_GROUP,
        "bot": ChatType.BOT,
    }
    ct = type_map.get(chat_type.lower(), ChatType.PRIVATE)

    mode_map = {
        "typing": TypingMode.TEXT,
        "cancel": TypingMode.UNKNOWN,
        "record": TypingMode.VOICERECODRING,
        "upload": TypingMode.SENDINGFILE,
        "play": TypingMode.CHOOSINGSTICKER,
    }
    tm = mode_map.get(mode.lower(), TypingMode.TEXT)

    async def _typing_start():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.start_typing(chat_id=chat, chat_type=ct, typing_mode=tm)
            if json_output:
                from bale_cli.utils import output
                output({"status": "typing_started", "chat_id": chat, "mode": mode}, json_mode=True)
            else:
                console.print(f"[green]Typing indicator started in chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to start typing: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_typing_start())


@typing.command("stop")
@click.option("--chat", type=int, required=True, help="Chat ID to stop typing in")
@click.option("--type", "chat_type", default="private", help="Chat type: private, group, channel, super_group")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def typing_stop(chat, chat_type, store, json_output):
    """Stop typing indicator in a chat."""
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

    async def _typing_stop():
        patch_aiobale()
        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            await client.start(run_in_background=True, signal_handling=False)
            result = await client.stop_typing(chat_id=chat, chat_type=ct)
            if json_output:
                from bale_cli.utils import output
                output({"status": "typing_stopped", "chat_id": chat}, json_mode=True)
            else:
                console.print(f"[green]Typing indicator stopped in chat {chat}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to stop typing: {e}[/red]")
        finally:
            await client.stop()

    asyncio.run(_typing_stop())
