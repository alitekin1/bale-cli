import asyncio
from pathlib import Path

import click
from rich.console import Console

from bale_cli.store import Store
from bale_cli.utils import output, get_session_path, get_db_path
from bale_cli.aiobale_patch import patch_aiobale

console = Console()

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def to_ascii_digits(s: str) -> str:
    """Convert Persian and Arabic digits to ASCII."""
    for i, d in enumerate(PERSIAN_DIGITS):
        s = s.replace(d, str(i))
    for i, d in enumerate(ARABIC_DIGITS):
        s = s.replace(d, str(i))
    return s


@click.group()
def auth():
    """Authentication and session management."""
    pass


@auth.command("login")
@click.option("--phone", prompt="Phone number (e.g. 989123456789)", help="Phone number")
@click.option("--profile", type=str, default=None, help="Account profile name (for multi-account)")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def auth_login(phone, profile, store, json_output):
    """Login to Bale with phone number + OTP."""
    from aiobale import Client, Dispatcher
    from aiobale.enums import AuthErrors

    store_dir = store or Path.home() / ".bale-cli"
    store_dir.mkdir(parents=True, exist_ok=True)
    session_file = get_session_path(store_dir, profile)

    phone_clean = to_ascii_digits(phone).replace("+", "").replace(" ", "")

    async def _login():
        patch_aiobale()

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)

        try:
            profile_label = f" (profile: {profile})" if profile else ""
            console.print(f"Initiating login for [bold]{phone_clean}[/bold]{profile_label}...")

            phone_digits = int(phone_clean)
            resp = await client.start_phone_auth(phone_number=phone_digits)

            if isinstance(resp, AuthErrors):
                error_map = {
                    AuthErrors.NUMBER_BANNED: "Phone number is temporarily banned.",
                    AuthErrors.RATE_LIMIT: "Rate limit exceeded. Try again later.",
                    AuthErrors.INVALID: "Invalid phone number.",
                    AuthErrors.UNKNOWN: "Unknown error occurred.",
                }
                console.print(f"[red]Error:[/red] {error_map.get(resp, resp)}")
                return

            console.print(f"[green]Code sent![/green] Transaction: {resp.transaction_hash[:16]}...")

            code = click.prompt("Enter the verification code")
            result = await client.validate_code(code, resp.transaction_hash)

            if isinstance(result, AuthErrors):
                error_map = {
                    AuthErrors.WRONG_CODE: "Wrong verification code.",
                    AuthErrors.PASSWORD_NEEDED: "Password (2FA) is required. Re-run login.",
                    AuthErrors.SIGN_UP_NEEDED: "This phone number is not registered.",
                    AuthErrors.UNKNOWN: "Unknown error.",
                }
                console.print(f"[red]Error:[/red] {error_map.get(result, result)}")
                return

            me = client.me
            user_name = me.user.name if me and me.user else "Unknown"
            user_id = me.id if me else "Unknown"

            if json_output:
                output({"status": "success", "profile": profile, "user": {"id": user_id, "name": user_name}}, json_mode=True)
            else:
                console.print(f"[green]Login successful![/green] Welcome, [bold]{user_name}[/bold] (ID: {user_id})")

        finally:
            await client.stop()

    asyncio.run(_login())


@auth.command("status")
@click.option("--profile", type=str, default=None, help="Account profile name")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def auth_status(profile, store, json_output):
    """Show current authentication status."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = get_session_path(store_dir, profile)

    if session_file.exists():
        profile_label = f" (profile: {profile})" if profile else ""
        if json_output:
            output({"authenticated": True, "profile": profile, "session": str(session_file)}, json_mode=True)
        else:
            console.print(f"[green]Authenticated[/green]{profile_label} — Session: {session_file}")
    else:
        profile_label = f" (profile: {profile})" if profile else ""
        if json_output:
            output({"authenticated": False, "profile": profile}, json_mode=True)
        else:
            console.print(f"[red]Not authenticated[/red]{profile_label} — Run [bold]bale auth login[/bold]")


@auth.command("logout")
@click.option("--profile", type=str, default=None, help="Account profile name")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.confirmation_option(prompt="Are you sure you want to logout?")
def auth_logout(profile, store):
    """Logout and delete session."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = get_session_path(store_dir, profile)

    if session_file.exists():
        session_file.unlink()
        profile_label = f" (profile: {profile})" if profile else ""
        console.print(f"[green]Logged out{profile_label}. Session deleted.[/green]")
    else:
        profile_label = f" (profile: {profile})" if profile else ""
        console.print(f"No active session found{profile_label}.")


@auth.command("profiles")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def auth_profiles(store, json_output):
    """List all available account profiles."""
    store_dir = store or Path.home() / ".bale-cli"

    profiles = []
    if store_dir.exists():
        for f in store_dir.glob("session_*.bale"):
            name = f.stem.replace("session_", "")
            profiles.append({"name": name, "session": str(f)})
        if (store_dir / "session.bale").exists():
            profiles.insert(0, {"name": "default", "session": str(store_dir / "session.bale")})

    if json_output:
        output({"profiles": profiles}, json_mode=True)
    else:
        if profiles:
            console.print("[bold]Available profiles:[/bold]")
            for p in profiles:
                default_marker = " (default)" if p["name"] == "default" else ""
                console.print(f"  [cyan]{p['name']}{default_marker}[/cyan] — {p['session']}")
        else:
            console.print("No profiles found.")
