# bale-cli — Bale Messenger CLI: sync, search, send, automate

A scriptable Bale Messenger client built on [`aiobale`](https://github.com/Enalite/aiobale). Pairs as a linked device, mirrors your messages into a local SQLite store, and gives you offline search, sending, and chat/group/contact management from the command line.

**Agent-optimized** — designed for AI agents, customer support bots, and automation workflows.

> Third-party tool. Uses Bale's internal gRPC API via `aiobale`. Not affiliated with Bale.

## Features

- **Auth + sync** — Phone number + OTP login, one-shot or follow-mode sync, session persistence
- **Multi-account** — Profile-based sessions for managing multiple accounts
- **Offline message store** — SQLite with FTS5 search, filterable by chat, sender, type, and date
- **Sending** — text messages, files, reactions
- **Message management** — edit, delete, forward, pin/unpin messages
- **Typing indicators** — show/hide typing status
- **Mark as read** — clear unread counters programmatically
- **Admin tools** — kick, ban, unban, add members, manage admins
- **HTTP API server** — `bale serve` for persistent agent integration with WebSocket support
- **Real-time watch** — `bale messages watch` for NDJSON streaming of new messages
- **Contacts / chats / groups / channels** — list, search, manage
- **Diagnostics** — `doctor` command for health checks
- **Scriptable** — `--json` everywhere, `--events` NDJSON lifecycle stream

## Install

### From source

```bash
git clone https://github.com/alitekin1/bale-cli.git
cd bale-cli
pip install -e .
```

### Direct install

```bash
pip install git+https://github.com/alitekin1/bale-cli.git
```

## Quick Start

```bash
# 1. Login (shows OTP prompt)
bale auth login --phone 989123456789

# 2. Sync messages
bale sync start --follow

# 3. Search
bale messages search "meeting"

# 4. Send
bale send text --to 123456789 --message "hello"

# 5. Watch for new messages (NDJSON stream)
bale messages watch

# 6. Start HTTP API server for agents
bale serve start
```

## Commands

### Auth

| Command | Description |
|---|---|
| `bale auth login --phone NUMBER` | Login with phone + OTP |
| `bale auth login --phone NUMBER --profile work` | Login with profile name |
| `bale auth status` | Check authentication status |
| `bale auth status --profile work` | Check profile status |
| `bale auth logout` | Logout and delete session |
| `bale auth profiles` | List all available profiles |

### Sync

| Command | Description |
|---|---|
| `bale sync start` | One-shot sync (loads recent messages) |
| `bale sync start --follow` | Continuous sync (real-time) |
| `bale sync start --limit 1000` | Sync up to N messages |
| `bale sync start --media` | Download media attachments |

### Messages

| Command | Description |
|---|---|
| `bale messages search "query"` | Search messages (FTS5) |
| `bale messages list` | List messages from store |
| `bale messages count` | Show total message count |
| `bale messages mark-read --chat ID` | Mark chat as read |
| `bale messages delete --chat ID --message ID` | Delete a message |
| `bale messages edit --chat ID --message ID --text "new"` | Edit a message |
| `bale messages forward --from-chat ID --to-chat ID --message ID` | Forward a message |
| `bale messages watch` | Watch for new messages (NDJSON stream) |

### Typing

| Command | Description |
|---|---|
| `bale typing start --chat ID` | Start typing indicator |
| `bale typing stop --chat ID` | Stop typing indicator |
| `bale typing start --chat ID --mode record` | Show recording audio |

### Send

| Command | Description |
|---|---|
| `bale send text --to ID --message "text"` | Send text message |
| `bale send file --to ID --file path` | Send file |
| `bale send reaction --chat ID --message ID --emoji "👍"` | React to message |

### Admin (Groups/Channels)

| Command | Description |
|---|---|
| `bale admin add-member --group ID --user ID` | Add user to group |
| `bale admin kick-member --group ID --user ID` | Kick user from group |
| `bale admin ban --group ID --user ID` | Ban user from group |
| `bale admin unban --group ID --user ID` | Unban user from group |
| `bale admin make-admin --group ID --user ID` | Promote user to admin |
| `bale admin remove-admin --group ID --user ID` | Demote admin |
| `bale admin pin --chat ID --message ID` | Pin a message |
| `bale admin unpin --chat ID --message ID` | Unpin a message |
| `bale admin block --user ID` | Block a user |
| `bale admin unblock --user ID` | Unblock a user |

### Chats

| Command | Description |
|---|---|
| `bale chats list` | List chats from store |
| `bale chats search "query"` | Search chats |
| `bale chats live` | Fetch live chat list from API |

### Contacts

| Command | Description |
|---|---|
| `bale contacts list` | List contacts from store |
| `bale contacts search "query"` | Search contacts |
| `bale contacts live` | Fetch live contacts from API |

### Groups

| Command | Description |
|---|---|
| `bale groups list` | List groups/channels |
| `bale groups search "query"` | Search groups |
| `bale groups info ID` | Show group details |
| `bale groups members ID` | List group members |

### Serve (HTTP API Server)

| Command | Description |
|---|---|
| `bale serve start` | Start HTTP API server |
| `bale serve start --port 8765` | Custom port |
| `bale serve start --api-key SECRET` | Enable API key auth |

### Doctor

| Command | Description |
|---|---|
| `bale doctor` | Run diagnostics |

## Global Flags

| Flag | Description |
|---|---|
| `--store DIR` | Custom store directory |
| `--profile NAME` | Account profile name (multi-account) |
| `--json` | Output in JSON format |
| `--events` | Stream lifecycle events as NDJSON |
| `--timeout DUR` | Request timeout (e.g. 30s, 5m) |
| `--read-only` | Enable read-only mode |

## Agent Integration

### HTTP API Server

Start the server:
```bash
bale serve start --port 8765
```

Endpoints:
```
GET  /status                          - Server status
GET  /ws                              - WebSocket for real-time events
GET  /messages/search?q=&limit=       - Search messages
GET  /chats?limit=                    - List chats
GET  /contacts?limit=                 - List contacts
GET  /groups?limit=                   - List groups
POST /send/text                       - Send text {chat_id, text, chat_type?, reply_to?}
POST /messages/mark-read              - Mark read {chat_id, chat_type?}
POST /messages/typing                 - Toggle typing {chat_id, action: start|stop}
POST /messages/delete                 - Delete {chat_id, message_id, just_me?}
POST /messages/edit                   - Edit {chat_id, message_id, text}
POST /messages/forward                - Forward {from_chat_id, to_chat_id, message_id}
```

Example with curl:
```bash
# Send message
curl -X POST http://localhost:8765/send/text \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456, "text": "Hello from agent!"}'

# Mark as read
curl -X POST http://localhost:8765/messages/mark-read \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456}'

# WebSocket (real-time events)
wscat -c ws://localhost:8765/ws
```

### NDJSON Watch Mode

Stream new messages as NDJSON:
```bash
bale messages watch | while read line; do
  echo "$line" | jq .
done
```

### CLI with JSON Output

```bash
# Get unread messages
bale --json messages search --limit 50 | jq '.[].text'

# Send response
bale send text --to 123456 --message "Thanks for your message!"

# Show typing indicator
bale typing start --chat 123456
```

### Multi-Account

```bash
# Login with different profiles
bale auth login --phone 989111111111 --profile support
bale auth login --phone 989222222222 --profile sales

# Use specific profile
bale --profile support messages watch
bale --profile sales send text --to 123 --message "Hello"

# List profiles
bale auth profiles
```

## Configuration

Default store: `~/.bale-cli` (or `~/.local/state/bale-cli` on Linux).

Session files:
- Default: `~/.bale-cli/session.bale`
- Profile: `~/.bale-cli/session_<profile>.bale`

Database files:
- Default: `~/.bale-cli/bale.db`
- Profile: `~/.bale-cli/bale_<profile>.db`

## Library Choice: aiobale

**aiobale** was chosen over **Balethon** because:

| Feature | aiobale | Balethon |
|---|---|---|
| Login type | Phone + OTP (user account) | Bot token only |
| Selfbot support | Yes (tagged `selfbot`) | No |
| API access | Reverse-engineered internal gRPC | Official Bot API only |
| wacli parity | Full (sync, search, send as user) | Bot-only features |

## License

MIT
