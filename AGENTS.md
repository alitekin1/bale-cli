# AGENTS.md — bale-cli for AI Agents

This document provides instructions for AI agents that need to interact with Bale Messenger through bale-cli.

---

## Quick Reference

| Task | Command |
|---|---|
| Check auth | `bale auth status --json` |
| Send message | `bale send text --to CHAT_ID --message "TEXT" --json` |
| Get recent messages | `bale messages list --chat CHAT_ID --limit N --json` |
| Search messages | `bale messages search "QUERY" --json` |
| Mark as read | `bale messages mark-read --chat CHAT_ID --json` |
| Show typing | `bale typing start --chat CHAT_ID --json` |
| Stop typing | `bale typing stop --chat CHAT_ID --json` |
| Edit message | `bale messages edit --chat CHAT_ID --message MSG_ID --text "NEW" --json` |
| Delete message | `bale messages delete --chat CHAT_ID --message MSG_ID --json` |
| List chats | `bale chats list --json` |
| Watch messages | `bale messages watch` (NDJSON stream) |
| HTTP server | `bale serve start --port 8765` |

---

## Agent Architecture

### Option A: CLI Subprocess (Simple)

Best for: Simple agents, occasional operations, low-frequency tasks.

```python
import subprocess, json

def bale(cmd_args):
    result = subprocess.run(["bale"] + cmd_args, capture_output=True, text=True)
    if "--json" in cmd_args:
        return json.loads(result.stdout)
    return result.stdout

# Usage
status = bale(["auth", "status", "--json"])
bale(["send", "text", "--to", "123", "--message", "Hello", "--json"])
```

### Option B: HTTP API (Recommended)

Best for: Persistent agents, high-frequency operations, real-time responses.

```python
import aiohttp

API = "http://localhost:8765"

async def send(chat_id, text):
    async with aiohttp.ClientSession() as s:
        return await (await s.post(f"{API}/send/text", json={
            "chat_id": chat_id, "text": text
        })).json()

async def mark_read(chat_id):
    async with aiohttp.ClientSession() as s:
        return await (await s.post(f"{API}/messages/mark-read", json={
            "chat_id": chat_id
        })).json()
```

### Option C: WebSocket (Real-time)

Best for: Ultra-low-latency agents, live message processing.

```python
import websockets, json, asyncio

async def listen():
    async with websockets.connect("ws://localhost:8765/ws") as ws:
        async for msg in ws:
            event = json.loads(msg)
            if event["event"] == "message":
                await handle(event["data"])
```

---

## Agent Workflow: Customer Support Bot

```
1. Start:     bale serve start --port 8765 &
2. Listen:    WebSocket → new message event
3. Process:   LLM generates response
4. Typing:    POST /messages/typing {action: "start"}
5. Wait:      Simulate typing delay
6. StopType:  POST /messages/typing {action: "stop"}
7. Send:      POST /send/text {chat_id, text}
8. MarkRead:  POST /messages/mark-read {chat_id}
9. Loop:      Back to step 2
```

---

## JSON Output Format

All commands with `--json` return structured JSON to stdout. Parse this, don't regex it.

**Send response:**
```json
{"status": "sent", "message_id": 123456, "chat_id": 48859866}
```

**Message event (WebSocket/NDJSON):**
```json
{
  "event": "message",
  "data": {
    "message_id": 123456,
    "chat_id": 48859866,
    "chat_type": "private",
    "text": "Hello!",
    "sender_id": 789012,
    "sender_name": "John",
    "date": 1700000000000
  }
}
```

**Search results:**
```json
[
  {
    "message_id": 123456,
    "chat_title": "Group Name",
    "sender_name": "John",
    "text": "Message text",
    "date": 1700000000000
  }
]
```

---

## Chat Type Values

When a command requires `chat_type`, use these exact strings:

| Value | Description |
|---|---|
| `private` | Private conversation |
| `group` | Regular group |
| `channel` | Broadcast channel |
| `super_group` | Large group |
| `bot` | Bot conversation |

---

## Error Handling

**CLI:** Check `returncode`. `0` = success, `1` = error.

**HTTP API:** Check HTTP status code. `200` = success, `401` = unauthorized, `500` = server error.

**Error response format:**
```json
{"error": "Description of the error"}
```

---

## Rate Limits

- Bale API has rate limits on sending messages
- Space out sends by at least 1 second
- Use exponential backoff on errors
- Don't send more than ~10 messages per minute per chat

---

## Multi-Account

If multiple profiles exist, specify which one:

```bash
bale --profile support send text --to 123 --message "Hello" --json
```

List available profiles:
```bash
bale auth profiles --json
```

---

## Important Notes

1. **Always use `--json`** — Don't parse human-readable output
2. **Chat ID is numeric** — Use `bale chats list --json` to find IDs
3. **Sessions persist** — You only need to login once
4. **Watch mode is blocking** — It runs until Ctrl+C
5. **HTTP server is persistent** — Start it once, use it many times
6. **Forward has a bug** — The `forward` command fails due to an upstream library issue
7. **Date for delete/pin** — If auto-detection fails, use `--date` with the message timestamp (milliseconds since epoch)

---

## Example: Complete Agent Loop

```python
#!/usr/bin/env python3
"""Simple echo agent using bale-cli HTTP API."""

import asyncio
import aiohttp
import websockets
import json

API = "http://localhost:8765"

async def process_message(data):
    """LLM processes the message and returns a response."""
    text = data["text"]
    chat_id = data["chat_id"]

    # Skip own messages
    if data.get("is_from_me"):
        return

    # Show typing
    async with aiohttp.ClientSession() as session:
        await session.post(f"{API}/messages/typing", json={
            "chat_id": chat_id, "action": "start"
        })

    # Simulate processing time
    await asyncio.sleep(1)

    # Generate response (replace with actual LLM call)
    response = f"Echo: {text}"

    # Stop typing
    async with aiohttp.ClientSession() as session:
        await session.post(f"{API}/messages/typing", json={
            "chat_id": chat_id, "action": "stop"
        })

    # Send response
    async with aiohttp.ClientSession() as session:
        await session.post(f"{API}/send/text", json={
            "chat_id": chat_id, "text": response
        })

    # Mark as read
    async with aiohttp.ClientSession() as session:
        await session.post(f"{API}/messages/mark-read", json={
            "chat_id": chat_id
        })

async def main():
    async with websockets.connect(f"{API}/ws") as ws:
        print("Agent connected")
        async for message in ws:
            event = json.loads(message)
            if event.get("event") == "message":
                await process_message(event["data"])

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Security

- The HTTP server binds to `127.0.0.1` by default (localhost only)
- Use `--api-key` for authentication when exposing the server
- Never share session files (`session.bale`)
- Session files contain JWT tokens — treat them like passwords
