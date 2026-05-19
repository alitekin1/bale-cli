# Architecture

Understanding how bale-cli works internally.

---

## Table of Contents

- [High-Level Overview](#high-level-overview)
- [Component Diagram](#component-diagram)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Session Management](#session-management)
- [aiobale Integration](#aiobale-integration)
- [Monkey Patches](#monkey-patches)
- [HTTP Server Architecture](#http-server-architecture)
- [Profile System](#profile-system)

---

## High-Level Overview

bale-cli is built in three layers:

```
┌─────────────────────────────────────────────────────────┐
│                    User / Agent Layer                     │
│  CLI Commands │ HTTP API │ WebSocket │ NDJSON Stream     │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                       │
│  bale_cli/commands/ │ bale_cli/utils/ │ bale_cli/store/  │
├─────────────────────────────────────────────────────────┤
│                    Library Layer                          │
│              aiobale (gRPC API client)                   │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                    │
│        Bale gRPC API │ SQLite │ Filesystem               │
└─────────────────────────────────────────────────────────┘
```

---

## Component Diagram

```
                        ┌─────────────────────┐
                        │    bale CLI Entry    │
                        │   (main.py / Click)  │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼─────────┐ ┌───────▼────────┐ ┌────────▼─────────┐
    │  Command Groups   │ │  Global Flags  │ │  Store Manager   │
    │                   │ │                │ │                  │
    │ • auth            │ │ • --json       │ │ • SQLite (FTS5)  │
    │ • sync            │ │ • --events     │ │ • Session files  │
    │ • messages        │ │ • --profile    │ │ • Profile paths  │
    │ • send            │ │ • --store      │ │                  │
    │ • typing          │ │ • --timeout    │ │                  │
    │ • admin           │ │ • --read-only  │ │                  │
    │ • chats           │ │                │ │                  │
    │ • contacts        │ │                │ │                  │
    │ • groups          │ │                │ │                  │
    │ • serve           │ │                │ │                  │
    │ • doctor          │ │                │ │                  │
    └─────────┬─────────┘ └────────────────┘ └────────┬─────────┘
              │                                        │
              └────────────────────┬───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   aiobale Library   │
                        │  (gRPC API client)  │
                        │                     │
                        │ • Client            │
                        │ • Dispatcher        │
                        │ • Methods           │
                        │ • Types             │
                        │ • Enums             │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   Bale gRPC API     │
                        │   (bale.ai)         │
                        └─────────────────────┘
```

---

## Data Flow

### Inbound (Receiving Messages)

```
Bale API
    │
    │ gRPC push
    ▼
aiobale.Client
    │
    │ dispatches via @dp.message()
    ▼
Sync Command / Watch Command / HTTP Server
    │
    ├──► SQLite Store (bale.db)
    │       │
    │       └──► messages table
    │       └──► messages_fts (FTS5 index)
    │       └──► chats table
    │
    ├──► NDJSON Stream (stderr with --events)
    │
    └──► WebSocket (HTTP server)
```

### Outbound (Sending Messages)

```
CLI Command / HTTP API
    │
    │ constructs message
    ▼
aiobale.Client.send_message()
    │
    │ gRPC request
    ▼
Bale API
    │
    │ response
    ▼
CLI: Console output or JSON
HTTP: JSON response
```

### Search

```
CLI: bale messages search "query"
    │
    ▼
Store.search_messages_fts()
    │
    │ SQLite FTS5 query
    ▼
messages_fts virtual table
    │
    │ JOIN with messages, chats
    ▼
Results (list of dicts)
    │
    ├──► Rich table (default)
    └──► JSON (--json flag)
```

---

## Database Schema

The SQLite database (`bale.db`) contains these tables:

### `chats`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `peer_id` | INTEGER | Bale peer ID |
| `peer_type` | TEXT | private, group, channel, etc. |
| `title` | TEXT | Chat title |
| `username` | TEXT | Username (if any) |
| `about` | TEXT | Chat description |
| `photo_id` | TEXT | Photo file ID |
| `last_message_date` | INTEGER | Last message timestamp |
| `unread_count` | INTEGER | Unread message count |
| `is_pinned` | INTEGER | Pinned flag |
| `is_muted` | INTEGER | Muted flag |
| `is_archived` | INTEGER | Archived flag |
| `local_name` | TEXT | Local display name |

### `messages`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `message_id` | INTEGER | Bale message ID |
| `chat_id` | INTEGER | Chat ID |
| `peer_id` | INTEGER | Peer ID |
| `peer_type` | TEXT | Peer type |
| `sender_id` | INTEGER | Sender user ID |
| `sender_name` | TEXT | Sender display name |
| `text` | TEXT | Message text |
| `message_type` | TEXT | text, document, photo, etc. |
| `media_file_id` | TEXT | Media file ID |
| `media_access_hash` | TEXT | Media access hash |
| `media_mime_type` | TEXT | MIME type |
| `media_file_size` | INTEGER | File size |
| `media_duration` | INTEGER | Duration (audio/video) |
| `media_url` | TEXT | Media URL |
| `reply_to_message_id` | INTEGER | Reply target message ID |
| `reply_to_peer_id` | INTEGER | Reply target peer ID |
| `date` | INTEGER | Message timestamp (ms) |
| `seq` | INTEGER | Sequence number |
| `is_from_me` | INTEGER | Sent by current user |
| `is_edited` | INTEGER | Edited flag |
| `is_pinned` | INTEGER | Pinned flag |
| `reactions` | TEXT | JSON array of reactions |
| `raw_json` | TEXT | Full message JSON |

### `messages_fts`

FTS5 virtual table for full-text search on `messages.text`.

### `contacts`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `peer_id` | INTEGER | Bale peer ID |
| `first_name` | TEXT | First name |
| `last_name` | TEXT | Last name |
| `phone` | TEXT | Phone number |
| `username` | TEXT | Username |

### `groups`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key |
| `peer_id` | INTEGER | Bale peer ID |
| `title` | TEXT | Group title |
| `member_count` | INTEGER | Number of members |
| `is_channel` | INTEGER | Channel flag |

### `sync_state`

| Column | Type | Description |
|---|---|---|
| `key` | TEXT | State key |
| `value` | TEXT | State value |

---

## Session Management

### Session File

The session file (`session.bale`) contains:
- JWT authentication token
- User metadata
- Session metadata

It's a binary file with gRPC-encoded data.

### Session Lifecycle

1. **Login:** `auth login` → Phone OTP → JWT token → `session.bale`
2. **Load:** Client starts → reads `session.bale` → extracts JWT
3. **Use:** JWT sent with every API request
4. **Logout:** `auth logout` → deletes `session.bale`

### Session File Locations

| Platform | Default Path |
|---|---|
| Linux (XDG) | `~/.local/state/bale-cli/session.bale` |
| Linux (fallback) | `~/.bale-cli/session.bale` |
| macOS | `~/.bale-cli/session.bale` |
| Windows | `~/.bale-cli/session.bale` |

---

## aiobale Integration

bale-cli uses [`aiobale`](https://github.com/Enalite/aiobale), an async Python library that communicates with Bale's internal gRPC API.

### Key Components Used

| Component | Purpose |
|---|---|
| `Client` | Main API client, handles gRPC connection |
| `Dispatcher` | Event dispatcher for incoming messages |
| `enums.ChatType` | Chat type enumeration |
| `enums.TypingMode` | Typing mode enumeration |
| `types.Message` | Message data model |
| `types.InfoMessage` | Message reference model |
| `types.Peer` | Peer (user/group) model |
| `methods.*` | API method definitions |

### Monkey Patches

bale-cli applies patches to fix known bugs in aiobale (`bale_cli/aiobale_patch.py`):

1. **`Client.stop()`** — Properly cancels tasks and cleans up sessions
2. **`Client.start()`** — Handles reconnection loops and signal handling
3. **`InlineKeyboardButton.validate_keyboard`** — Handles nested dict structures
4. **`PeerData.normalize_nested_fields`** — Flattens nested gRPC response fields

---

## HTTP Server Architecture

The `bale serve` command runs an aiohttp web server:

```
┌────────────────────────────────────────────────┐
│                  aiohttp Server                  │
│                                                  │
│  Routes:                                         │
│  GET  /          → API docs                      │
│  GET  /status    → Health check                  │
│  GET  /ws        → WebSocket handler             │
│  GET  /messages/search → FTS5 search            │
│  GET  /chats     → List chats                    │
│  GET  /contacts  → List contacts                 │
│  GET  /groups    → List groups                   │
│  POST /send/text → Send message                  │
│  POST /messages/* → Message operations           │
│                                                  │
│  Middleware:                                     │
│  • API key authentication (optional)             │
│                                                  │
│  Shared State:                                   │
│  • aiobale.Client (single instance)              │
│  • Store (SQLite database)                       │
│  • WebSocket connections set                     │
│  • Message queue (for WS broadcasting)           │
└────────────────────────────────────────────────┘
```

---

## Profile System

Profiles provide account isolation through file naming:

```
Profile "default":
  session.bale
  bale.db

Profile "support":
  session_support.bale
  bale_support.db

Profile "sales":
  session_sales.bale
  bale_sales.db
```

The `get_session_path()` and `get_db_path()` functions in `bale_cli/utils/__init__.py` handle profile path resolution.
