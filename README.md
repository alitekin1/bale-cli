# bale-cli — Bale Messenger CLI: sync, search, send

A scriptable Bale Messenger client built on [`aiobale`](https://github.com/Enalite/aiobale). Pairs as a linked device, mirrors your messages into a local SQLite store, and gives you offline search, sending, and chat/group/contact management from the command line.

> Third-party tool. Uses Bale's internal gRPC API via `aiobale`. Not affiliated with Bale.

## Features

- **Auth + sync** — Phone number + OTP login, one-shot or follow-mode sync, session persistence
- **Offline message store** — SQLite with FTS5 search, filterable by chat, sender, type, and date
- **Sending** — text messages, files, reactions
- **Contacts / chats / groups / channels** — list, search, manage
- **Diagnostics** — `doctor` command for health checks
- **Scriptable** — `--json` everywhere, `--events` NDJSON lifecycle stream

## Install

### From source

```bash
git clone https://github.com/yourusername/bale-cli.git
cd bale-cli
pip install -e .
```

### Direct install

```bash
pip install git+https://github.com/yourusername/bale-cli.git
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

# 5. Diagnostics
bale doctor
```

## Commands

### Auth

| Command | Description |
|---|---|
| `bale auth login --phone NUMBER` | Login with phone + OTP |
| `bale auth status` | Check authentication status |
| `bale auth logout` | Logout and delete session |

### Sync

| Command | Description |
|---|---|
| `bale sync start` | One-shot sync (loads recent messages) |
| `bale sync start --follow` | Continuous sync (real-time) |
| `bale sync start --limit 1000` | Sync up to N messages |

### Messages

| Command | Description |
|---|---|
| `bale messages search "query"` | Search messages (FTS5) |
| `bale messages list` | List messages from store |
| `bale messages count` | Show total message count |

### Send

| Command | Description |
|---|---|
| `bale send text --to ID --message "text"` | Send text message |
| `bale send file --to ID --file path` | Send file |
| `bale send reaction --chat ID --message ID --emoji "👍"` | React to message |

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

### Doctor

| Command | Description |
|---|---|
| `bale doctor` | Run diagnostics |

## Global Flags

| Flag | Description |
|---|---|
| `--store DIR` | Custom store directory |
| `--json` | Output in JSON format |
| `--events` | Stream lifecycle events as NDJSON |
| `--timeout DUR` | Request timeout (e.g. 30s, 5m) |
| `--read-only` | Enable read-only mode |

## Configuration

Default store: `~/.bale-cli` (or `~/.local/state/bale-cli` on Linux).

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
