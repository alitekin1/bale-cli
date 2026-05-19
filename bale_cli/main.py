import os
import sys
from pathlib import Path

import click

from bale_cli import __version__
from bale_cli.commands import auth, sync, messages, send, chats, contacts, groups, doctor


def _default_store() -> Path:
    if sys.platform == "linux":
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        return base / "bale-cli"
    return Path.home() / ".bale-cli"


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="bale")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output in JSON format")
@click.option("--events", is_flag=True, default=False, help="Stream lifecycle events as NDJSON")
@click.option("--timeout", type=str, default="30s", help="Request timeout (e.g. 30s, 5m)")
@click.option("--read-only", is_flag=True, default=False, help="Enable read-only mode")
@click.pass_context
def main(ctx, store, json_output, events, timeout, read_only):
    """bale-cli — Bale Messenger CLI: sync, search, send.

    A scriptable Bale client that pairs as a linked device, mirrors
    messages into a local SQLite store, and gives you offline search,
    sending, and chat/group/contact management from the command line.
    """
    ctx.ensure_object(dict)
    ctx.obj["store"] = store or _default_store()
    ctx.obj["json"] = json_output
    ctx.obj["events"] = events
    ctx.obj["timeout"] = timeout
    ctx.obj["read_only"] = read_only
    ctx.obj["store"].mkdir(parents=True, exist_ok=True)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


main.add_command(auth.auth)
main.add_command(sync.sync)
main.add_command(messages.messages)
main.add_command(send.send)
main.add_command(chats.chats)
main.add_command(contacts.contacts)
main.add_command(groups.groups)
main.add_command(doctor.doctor)


if __name__ == "__main__":
    main()
