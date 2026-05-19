import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console

from bale_cli.aiobale_patch import patch_aiobale
from bale_cli.store import Store

console = Console()


@click.group()
def serve():
    """Run bale-cli as a persistent HTTP server."""
    pass


@serve.command("start")
@click.option("--host", default="127.0.0.1", help="HTTP server host")
@click.option("--port", default=8765, type=int, help="HTTP server port")
@click.option("--store", type=click.Path(path_type=Path), default=None, help="Store directory")
@click.option("--api-key", default=None, help="API key for authentication (optional)")
def serve_start(host, port, store, api_key):
    """Start the HTTP API server with WebSocket support."""
    store_dir = store or Path.home() / ".bale-cli"
    session_file = store_dir / "session.bale"

    if not session_file.exists():
        console.print("[red]Not authenticated.[/red] Run [bold]bale auth login[/bold] first.")
        sys.exit(1)

    try:
        from aiohttp import web
    except ImportError:
        console.print("[red]aiohttp is required. Install with: pip install aiohttp[/red]")
        sys.exit(1)

    async def _serve():
        patch_aiobale()

        from aiobale import Client, Dispatcher
        from aiobale.enums import ChatType
        from aiohttp import WSMsgType

        dp = Dispatcher()
        client = Client(dp, session_file=session_file)
        db = Store(store_dir)
        await db.init()

        await client.start(run_in_background=True, signal_handling=False)

        message_queue = asyncio.Queue()
        connected_ws = set()

        @dp.message()
        async def on_message(msg):
            from aiobale.types import Message
            chat_id = msg.chat.id
            chat_type = msg.chat.type.name.lower() if hasattr(msg.chat.type, "name") else "private"
            text = msg.text or ""
            sender_id = msg.sender_id

            event_data = {
                "event": "message",
                "data": {
                    "message_id": msg.message_id,
                    "chat_id": chat_id,
                    "chat_type": chat_type,
                    "text": text[:500],
                    "sender_id": sender_id,
                    "date": msg.date,
                }
            }

            await db.upsert_chat(peer_id=chat_id, peer_type=chat_type, last_message_date=msg.date)
            await db.insert_message(
                message_id=msg.message_id,
                chat_id=chat_id,
                peer_id=chat_id,
                peer_type=chat_type,
                text=text,
                sender_id=sender_id,
                sender_name=str(sender_id),
                message_type="text",
                date=msg.date,
            )

            await message_queue.put(event_data)
            for ws in list(connected_ws):
                try:
                    await ws.send_json(event_data)
                except Exception:
                    connected_ws.discard(ws)

        def _check_api_key(request):
            if api_key:
                provided = request.headers.get("X-API-Key", "")
                if provided != api_key:
                    return web.json_response({"error": "Unauthorized"}, status=401)
            return None

        async def handle_status(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            return web.json_response({"status": "running", "connected": client.session.running})

        async def handle_send_text(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                chat_id = int(body.get("chat_id"))
                text = body.get("text", "")
                chat_type_str = body.get("chat_type", "private")
                reply_to = body.get("reply_to")

                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                    "bot": ChatType.BOT,
                }
                ct = type_map.get(chat_type_str.lower(), ChatType.PRIVATE)

                result = await client.send_message(text=text, chat_id=chat_id, chat_type=ct)
                return web.json_response({"status": "sent", "message_id": result.message_id, "chat_id": chat_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_mark_read(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                chat_id = int(body.get("chat_id"))
                chat_type_str = body.get("chat_type", "private")
                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                }
                ct = type_map.get(chat_type_str.lower(), ChatType.PRIVATE)
                await client.seen_chat(chat_id=chat_id, chat_type=ct)
                return web.json_response({"status": "marked_read", "chat_id": chat_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_typing(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                chat_id = int(body.get("chat_id"))
                action = body.get("action", "start")
                chat_type_str = body.get("chat_type", "private")
                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                }
                ct = type_map.get(chat_type_str.lower(), ChatType.PRIVATE)
                if action == "start":
                    await client.start_typing(chat_id=chat_id, chat_type=ct)
                    return web.json_response({"status": "typing_started", "chat_id": chat_id})
                else:
                    await client.stop_typing(chat_id=chat_id, chat_type=ct)
                    return web.json_response({"status": "typing_stopped", "chat_id": chat_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_delete_message(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                chat_id = int(body.get("chat_id"))
                message_id = int(body.get("message_id"))
                chat_type_str = body.get("chat_type", "private")
                just_me = body.get("just_me", False)
                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                }
                ct = type_map.get(chat_type_str.lower(), ChatType.PRIVATE)
                msg_date = body.get("date")
                if msg_date is None:
                    results = await db.search_messages_fts(query="", chat_id=chat_id, limit=200)
                    for r in results:
                        if r["message_id"] == message_id:
                            msg_date = r["date"]
                            break
                if msg_date is None:
                    msg_date = 0
                await client.delete_message(message_id=message_id, message_date=msg_date, chat_id=chat_id, chat_type=ct, just_me=just_me)
                return web.json_response({"status": "deleted", "message_id": message_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_edit_message(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                chat_id = int(body.get("chat_id"))
                message_id = int(body.get("message_id"))
                text = body.get("text", "")
                chat_type_str = body.get("chat_type", "private")
                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                }
                ct = type_map.get(chat_type_str.lower(), ChatType.PRIVATE)
                await client.edit_message(text=text, message_id=message_id, chat_id=chat_id, chat_type=ct)
                return web.json_response({"status": "edited", "message_id": message_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_forward_message(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                body = await request.json()
                from_chat = int(body.get("from_chat_id"))
                to_chat = int(body.get("to_chat_id"))
                message_id = int(body.get("message_id"))
                from_type_str = body.get("from_chat_type", "private")
                to_type_str = body.get("to_chat_type", "private")
                type_map = {
                    "private": ChatType.PRIVATE,
                    "group": ChatType.GROUP,
                    "channel": ChatType.CHANNEL,
                    "super_group": ChatType.SUPER_GROUP,
                }
                from_ct = type_map.get(from_type_str.lower(), ChatType.PRIVATE)
                to_ct = type_map.get(to_type_str.lower(), ChatType.PRIVATE)
                msg_date = 0
                results = await db.search_messages_fts(query="", chat_id=from_chat, limit=200)
                for r in results:
                    if r["message_id"] == message_id:
                        msg_date = r["date"]
                        break
                from aiobale.types import InfoMessage, Peer
                msg_obj = InfoMessage(
                    peer=Peer(id=from_chat, type=from_ct),
                    message_id=message_id,
                    date=msg_date,
                )
                await client.forward_message(message=msg_obj, chat_id=to_chat, chat_type=to_ct)
                return web.json_response({"status": "forwarded", "message_id": message_id})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_search_messages(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                query = request.query.get("q", "")
                chat_id = request.query.get("chat_id")
                limit = int(request.query.get("limit", 50))
                offset = int(request.query.get("offset", 0))
                results = await db.search_messages_fts(
                    query=query,
                    chat_id=int(chat_id) if chat_id else None,
                    limit=limit,
                    offset=offset,
                )
                return web.json_response({"messages": results})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_list_chats(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                limit = int(request.query.get("limit", 50))
                offset = int(request.query.get("offset", 0))
                chats = await db.get_chats(limit=limit, offset=offset)
                return web.json_response({"chats": chats})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_list_contacts(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                limit = int(request.query.get("limit", 50))
                offset = int(request.query.get("offset", 0))
                contacts = await db.get_contacts(limit=limit, offset=offset)
                return web.json_response({"contacts": contacts})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_list_groups(request):
            auth_error = _check_api_key(request)
            if auth_error:
                return auth_error
            try:
                limit = int(request.query.get("limit", 50))
                offset = int(request.query.get("offset", 0))
                channels = request.query.get("channels", "false").lower() == "true"
                groups = await db.get_groups(limit=limit, offset=offset, is_channel=channels)
                return web.json_response({"groups": groups})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def handle_ws(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            connected_ws.add(ws)
            try:
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        if msg.data == "close":
                            await ws.close()
                        else:
                            try:
                                data = json.loads(msg.data)
                                action = data.get("action")
                                if action == "ping":
                                    await ws.send_json({"event": "pong"})
                            except json.JSONDecodeError:
                                pass
                    elif msg.type == WSMsgType.ERROR:
                        break
            finally:
                connected_ws.discard(ws)
            return ws

        async def handle_api_docs(request):
            docs = {
                "name": "bale-cli HTTP API",
                "version": "0.1.0",
                "endpoints": {
                    "GET /status": "Check server status",
                    "POST /send/text": "Send text message {chat_id, text, chat_type?, reply_to?}",
                    "POST /messages/mark-read": "Mark chat as read {chat_id, chat_type?}",
                    "POST /messages/typing": "Toggle typing {chat_id, action: start|stop, chat_type?}",
                    "POST /messages/delete": "Delete message {chat_id, message_id, chat_type?, just_me?}",
                    "POST /messages/edit": "Edit message {chat_id, message_id, text, chat_type?}",
                    "POST /messages/forward": "Forward message {from_chat_id, to_chat_id, message_id, ...}",
                    "GET /messages/search?q=&chat_id=&limit=&offset=": "Search messages",
                    "GET /chats?limit=&offset=": "List chats",
                    "GET /contacts?limit=&offset=": "List contacts",
                    "GET /groups?limit=&offset=&channels=": "List groups/channels",
                    "WS /ws": "WebSocket for real-time events",
                },
                "auth": "Optional: X-API-Key header"
            }
            return web.json_response(docs)

        app = web.Application()
        app.router.add_get("/", handle_api_docs)
        app.router.add_get("/status", handle_status)
        app.router.add_get("/ws", handle_ws)
        app.router.add_get("/messages/search", handle_search_messages)
        app.router.add_get("/chats", handle_list_chats)
        app.router.add_get("/contacts", handle_list_contacts)
        app.router.add_get("/groups", handle_list_groups)
        app.router.add_post("/send/text", handle_send_text)
        app.router.add_post("/messages/mark-read", handle_mark_read)
        app.router.add_post("/messages/typing", handle_typing)
        app.router.add_post("/messages/delete", handle_delete_message)
        app.router.add_post("/messages/edit", handle_edit_message)
        app.router.add_post("/messages/forward", handle_forward_message)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        console.print(f"[green]bale-cli HTTP server running at http://{host}:{port}[/green]")
        console.print(f"[dim]WebSocket: ws://{host}:{port}/ws[/dim]")
        console.print(f"[dim]API docs: http://{host}:{port}/[/dim]")
        if api_key:
            console.print(f"[yellow]API key authentication enabled[/yellow]")

        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n[yellow]Shutting down server...[/yellow]")
            await runner.cleanup()
            await client.stop()

    asyncio.run(_serve())
