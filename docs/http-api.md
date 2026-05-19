# HTTP API Documentation

Complete reference for the bale-cli HTTP API server (`bale serve`).

---

## Table of Contents

- [Starting the Server](#starting-the-server)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /](#get-)
  - [GET /status](#get-status)
  - [POST /send/text](#post-sendtext)
  - [POST /messages/mark-read](#post-messagesmark-read)
  - [POST /messages/typing](#post-messagestyping)
  - [POST /messages/delete](#post-messagesdelete)
  - [POST /messages/edit](#post-messagesedit)
  - [POST /messages/forward](#post-messagesforward)
  - [GET /messages/search](#get-messagessearch)
  - [GET /chats](#get-chats)
  - [GET /contacts](#get-contacts)
  - [GET /groups](#get-groups)
  - [WebSocket /ws](#websocket-ws)
- [Error Responses](#error-responses)
- [CORS](#cors)

---

## Starting the Server

```bash
# Basic (localhost:8765)
bale serve start

# Custom port and host
bale serve start --host 0.0.0.0 --port 9000

# With API key authentication
bale serve start --api-key your-secret-key
```

---

## Authentication

If `--api-key` is set, all requests must include the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8765/status
```

Without the correct key, the server returns `401 Unauthorized`:

```json
{"error": "Unauthorized"}
```

---

## Endpoints

### GET /

API documentation and endpoint listing.

**Request:**
```bash
curl http://localhost:8765/
```

**Response:**
```json
{
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
    "WS /ws": "WebSocket for real-time events"
  },
  "auth": "Optional: X-API-Key header"
}
```

---

### GET /status

Check server health and connection status.

**Request:**
```bash
curl http://localhost:8765/status
```

**Response:**
```json
{"status": "running", "connected": true}
```

---

### POST /send/text

Send a text message to a chat.

**Request:**
```bash
curl -X POST http://localhost:8765/send/text \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 48859866,
    "text": "Hello from the API!",
    "chat_type": "private",
    "reply_to": null
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `chat_id` | int | Yes | Target chat ID |
| `text` | string | Yes | Message text |
| `chat_type` | string | No | Chat type (default: `private`) |
| `reply_to` | int | No | Message ID to reply to |

**Chat Types:**
- `private` — Private conversation
- `group` — Regular group
- `channel` — Broadcast channel
- `super_group` — Large group
- `bot` — Bot conversation

**Response (200):**
```json
{"status": "sent", "message_id": 123456789, "chat_id": 48859866}
```

**Response (500):**
```json
{"error": "Failed to send message: ..."}
```

---

### POST /messages/mark-read

Mark a chat as read (clear unread counter).

**Request:**
```bash
curl -X POST http://localhost:8765/messages/mark-read \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "chat_type": "private"}'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `chat_id` | int | Yes | Chat ID to mark as read |
| `chat_type` | string | No | Chat type (default: `private`) |

**Response (200):**
```json
{"status": "marked_read", "chat_id": 48859866}
```

---

### POST /messages/typing

Toggle typing indicator in a chat.

**Request:**
```bash
# Start typing
curl -X POST http://localhost:8765/messages/typing \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "action": "start"}'

# Stop typing
curl -X POST http://localhost:8765/messages/typing \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "action": "stop"}'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `chat_id` | int | Yes | Chat ID |
| `action` | string | Yes | `start` or `stop` |
| `chat_type` | string | No | Chat type (default: `private`) |

**Response (200):**
```json
{"status": "typing_started", "chat_id": 48859866}
```
or
```json
{"status": "typing_stopped", "chat_id": 48859866}
```

---

### POST /messages/delete

Delete a message from a chat.

**Request:**
```bash
curl -X POST http://localhost:8765/messages/delete \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 48859866,
    "message_id": 123456,
    "chat_type": "private",
    "just_me": false,
    "date": null
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `chat_id` | int | Yes | Chat ID containing the message |
| `message_id` | int | Yes | Message ID to delete |
| `chat_type` | string | No | Chat type (default: `private`) |
| `just_me` | bool | No | Delete only for yourself (default: `false`) |
| `date` | int | No | Message timestamp (auto-detected from DB) |

**Response (200):**
```json
{"status": "deleted", "message_id": 123456}
```

---

### POST /messages/edit

Edit an existing message (must be your own message).

**Request:**
```bash
curl -X POST http://localhost:8765/messages/edit \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 48859866,
    "message_id": 123456,
    "text": "Updated message text",
    "chat_type": "private"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `chat_id` | int | Yes | Chat ID containing the message |
| `message_id` | int | Yes | Message ID to edit |
| `text` | string | Yes | New message text |
| `chat_type` | string | No | Chat type (default: `private`) |

**Response (200):**
```json
{"status": "edited", "message_id": 123456}
```

---

### POST /messages/forward

Forward a message from one chat to another.

**Request:**
```bash
curl -X POST http://localhost:8765/messages/forward \
  -H "Content-Type: application/json" \
  -d '{
    "from_chat_id": 111111,
    "to_chat_id": 222222,
    "message_id": 123456,
    "from_chat_type": "private",
    "to_chat_type": "private"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `from_chat_id` | int | Yes | Source chat ID |
| `to_chat_id` | int | Yes | Target chat ID |
| `message_id` | int | Yes | Message ID to forward |
| `from_chat_type` | string | No | Source chat type (default: `private`) |
| `to_chat_type` | string | No | Target chat type (default: `private`) |

**Response (200):**
```json
{"status": "forwarded", "message_id": 123456}
```

**Response (404):**
```json
{"error": "Message not found"}
```

---

### GET /messages/search

Search messages using FTS5 full-text search.

**Request:**
```bash
curl "http://localhost:8765/messages/search?q=hello&chat_id=48859866&limit=20&offset=0"
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Search query |
| `chat_id` | int | — | Filter by chat ID |
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
{
  "messages": [
    {
      "id": 1,
      "message_id": 123456,
      "chat_id": 48859866,
      "sender_id": 789012,
      "sender_name": "John",
      "text": "Hello world!",
      "message_type": "text",
      "date": 1700000000000,
      "chat_title": null,
      "rank": -1e-06
    }
  ]
}
```

---

### GET /chats

List chats from the local store.

**Request:**
```bash
curl "http://localhost:8765/chats?limit=50&offset=0"
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
{
  "chats": [
    {
      "id": 1,
      "peer_id": 48859866,
      "peer_type": "1",
      "title": null,
      "username": null,
      "last_message_date": 1700000000000,
      "unread_count": 0,
      "is_pinned": 0,
      "is_muted": 0,
      "is_archived": 0
    }
  ]
}
```

---

### GET /contacts

List contacts from the local store.

**Request:**
```bash
curl "http://localhost:8765/contacts?limit=50&offset=0"
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
{"contacts": [...]}
```

---

### GET /groups

List groups and channels from the local store.

**Request:**
```bash
curl "http://localhost:8765/groups?limit=50&offset=0&channels=false"
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |
| `channels` | bool | `false` | Show channels only |

**Response (200):**
```json
{"groups": [...]}
```

---

### WebSocket /ws

Real-time event stream via WebSocket.

**Connect:**
```bash
wscat -c ws://localhost:8765/ws
```

**Events Received:**

```json
{
  "event": "message",
  "data": {
    "message_id": 123456,
    "chat_id": 48859866,
    "chat_type": "private",
    "text": "Hello!",
    "sender_id": 789012,
    "date": 1700000000000
  }
}
```

**Client Messages:**

```json
{"action": "ping"}
```

**Server Response:**

```json
{"event": "pong"}
```

**Python Example:**

```python
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect("ws://localhost:8765/ws") as ws:
        await ws.send(json.dumps({"action": "ping"}))
        async for msg in ws:
            event = json.loads(msg)
            if event["event"] == "message":
                print(f"New: {event['data']['text']}")

asyncio.run(listen())
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{"error": "Description of what went wrong"}
```

**HTTP Status Codes:**

| Code | Meaning |
|---|---|
| `200` | Success |
| `401` | Unauthorized (invalid/missing API key) |
| `404` | Not found (message not found for forward) |
| `500` | Server error (Bale API failure, network issue) |

---

## CORS

The HTTP API server does not set CORS headers by default. If you need browser access, put the server behind a reverse proxy:

**Nginx Example:**

```nginx
server {
    listen 80;
    server_name bale-api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, X-API-Key";

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
