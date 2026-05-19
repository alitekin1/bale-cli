# Getting Started with bale-cli

A complete guide to installing, configuring, and using bale-cli — the agent-optimized command-line client for Bale Messenger.

---

## Table of Contents

- [What is bale-cli?](#what-is-bale-cli)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [First Login](#first-login)
- [Syncing Messages](#syncing-messages)
- [Basic Usage](#basic-usage)
- [Next Steps](#next-steps)

---

## What is bale-cli?

**bale-cli** is a scriptable command-line interface (CLI) client for **Bale Messenger**, an Iranian messaging platform. It connects to Bale using the internal gRPC API (via the `aiobale` library) and provides:

- **Full messaging capabilities** — send, receive, edit, delete, forward, and react to messages
- **Offline message store** — SQLite database with FTS5 full-text search
- **Agent-optimized design** — JSON output everywhere, NDJSON event streaming, HTTP API server
- **Multi-account support** — manage multiple Bale accounts via profiles
- **Admin tools** — group management, pin/unpin, block/unblock, ban/unban

It works like a linked device (similar to WhatsApp Web) — you log in with your phone number + OTP, and the session persists on disk.

> **Warning:** This is a third-party tool using Bale's internal gRPC API. It is not affiliated with or endorsed by Bale. Use at your own risk and follow Bale's terms of service.

---

## System Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.10 or higher |
| **OS** | Linux, macOS, Windows (WSL recommended on Windows) |
| **Disk** | ~50 MB for installation + SQLite database space |
| **Network** | Internet connection (Bale API access) |
| **Phone** | An active Bale account with a verified phone number |

---

## Installation

### Method 1: From Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/alitekin1/bale-cli.git
cd bale-cli

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Method 2: Direct Install

```bash
pip install git+https://github.com/alitekin1/bale-cli.git
```

### Method 3: Using pipx (Isolated Install)

```bash
pipx install git+https://github.com/alitekin1/bale-cli.git
```

### Verify Installation

```bash
bale --version
# Output: bale, version 0.1.0
```

---

## First Login

### Step 1: Run the Login Command

```bash
bale auth login --phone 989123456789
```

Replace `989123456789` with your Bale phone number (with country code, no `+`).

### Step 2: Enter the OTP Code

The CLI will send a verification code to your Bale app. Enter it when prompted:

```
Initiating login for 989123456789...
Code sent! Transaction: abc123def456...
Enter the verification code: 12345
```

### Step 3: Verify Login Success

```bash
bale auth status
# Output: Authenticated — Session: /home/user/.bale-cli/session.bale
```

Or in JSON mode:

```bash
bale auth status --json
# Output: {"authenticated": true, "session": "/home/user/.bale-cli/session.bale"}
```

### Session Files

After login, bale-cli stores:

| File | Location | Purpose |
|---|---|---|
| `session.bale` | `~/.bale-cli/` (Linux) | Authentication token (JWT) |
| `bale.db` | `~/.bale-cli/` | SQLite message database |

On Linux with XDG: `~/.local/state/bale-cli/`

---

## Syncing Messages

### One-Shot Sync

Load recent messages and exit:

```bash
bale sync start --limit 500
```

### Continuous Sync (Follow Mode)

Keep running and sync new messages in real-time:

```bash
bale sync start --follow
```

Press `Ctrl+C` to stop.

### With Events Stream

Emit NDJSON events to stderr for programmatic processing:

```bash
bale --events sync start --follow 2> events.ndjson
```

### With Media Download

```bash
bale sync start --follow --media
```

---

## Basic Usage

### Search Messages

```bash
# Full-text search
bale messages search "meeting"

# Search in JSON format
bale messages search "hello" --json

# Search with filters
bale messages search "report" --chat 123456 --limit 20

# Show full message details
bale messages search "test" --full
```

### Send a Message

```bash
bale send text --to 123456789 --message "Hello from bale-cli!"
```

The `--to` parameter accepts:
- Numeric chat ID: `--to 123456789`
- Phone number: `--to 989123456789`
- Chat title/username: `--to "My Group"`

### List Chats

```bash
# From local store
bale chats list

# From Bale API (live)
bale chats live

# Search chats
bale chats search "group"
```

### Run Diagnostics

```bash
bale doctor
```

Shows: version, Python, platform, store path, session status, DB size, message count, disk space.

---

## Global Flags

These flags work with any command:

| Flag | Description | Example |
|---|---|---|
| `--store DIR` | Custom store directory | `bale --store /tmp/bale auth status` |
| `--profile NAME` | Account profile name | `bale --profile work messages search "test"` |
| `--json` | JSON output | `bale --json chats list` |
| `--events` | NDJSON event stream | `bale --events sync start --follow` |
| `--timeout DUR` | Request timeout | `bale --timeout 5m sync start` |
| `--read-only` | Read-only mode | `bale --read-only messages search "test"` |

---

## Next Steps

- [Commands Reference](commands-reference.md) — Full command documentation
- [Agent Integration](agent-integration.md) — Use bale-cli with AI agents
- [HTTP API](http-api.md) — Run as a persistent HTTP server
- [Multi-Account](multi-account.md) — Manage multiple Bale accounts
- [Troubleshooting](troubleshooting.md) — Common issues and solutions
