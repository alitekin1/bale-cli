# Commands Reference

Complete documentation for all bale-cli commands, options, and examples.

---

## Table of Contents

- [Auth Commands](#auth-commands)
- [Sync Commands](#sync-commands)
- [Messages Commands](#messages-commands)
- [Typing Commands](#typing-commands)
- [Send Commands](#send-commands)
- [Admin Commands](#admin-commands)
- [Chats Commands](#chats-commands)
- [Contacts Commands](#contacts-commands)
- [Groups Commands](#groups-commands)
- [Serve Commands](#serve-commands)
- [Doctor Command](#doctor-command)

---

## Auth Commands

Authentication and session management.

### `bale auth login`

Login to Bale with phone number + OTP verification.

```bash
bale auth login --phone 989123456789
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--phone` | string | Yes | Phone number with country code (no +) |
| `--profile` | string | No | Account profile name for multi-account |
| `--store` | path | No | Custom store directory |
| `--json` | flag | No | Output in JSON format |

**Examples:**

```bash
# Basic login
bale auth login --phone 989123456789

# Login with profile name
bale auth login --phone 989123456789 --profile support

# JSON output
bale auth login --phone 989123456789 --json
```

**Output (success):**
```
Login successful! Welcome, John Doe (ID: 12345678)
```

**Output (JSON):**
```json
{
  "status": "success",
  "profile": null,
  "user": {"id": 12345678, "name": "John Doe"}
}
```

**Error codes:**
- `NUMBER_BANNED` — Phone number is temporarily banned
- `RATE_LIMIT` — Too many login attempts, try again later
- `INVALID` — Invalid phone number format
- `WRONG_CODE` — Incorrect OTP code
- `PASSWORD_NEEDED` — 2FA password required
- `SIGN_UP_NEEDED` — Phone number not registered on Bale

---

### `bale auth status`

Check current authentication status.

```bash
bale auth status
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--profile` | string | No | Check specific profile |
| `--store` | path | No | Custom store directory |
| `--json` | flag | No | JSON output |

**Examples:**

```bash
# Check default profile
bale auth status

# Check specific profile
bale auth status --profile support

# JSON output
bale auth status --json
```

**Output:**
```
Authenticated — Session: /home/user/.bale-cli/session.bale
```

---

### `bale auth logout`

Logout and delete session file.

```bash
bale auth logout
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--profile` | string | No | Logout specific profile |
| `--store` | path | No | Custom store directory |

**Requires confirmation** before deleting the session.

---

### `bale auth profiles`

List all available account profiles.

```bash
bale auth profiles
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--store` | path | No | Custom store directory |
| `--json` | flag | No | JSON output |

**Output:**
```
Available profiles:
  default — /home/user/.bale-cli/session.bale
  support — /home/user/.bale-cli/session_support.bale
  sales — /home/user/.bale-cli/session_sales.bale
```

---

## Sync Commands

Synchronize messages from Bale to the local SQLite store.

### `bale sync start`

Sync messages from Bale to the local database.

```bash
bale sync start
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--follow` | flag | false | Continuous sync (real-time) |
| `--limit` | int | 500 | Max messages to sync (one-shot mode) |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |
| `--events` | flag | false | Emit NDJSON events to stderr |
| `--media` | flag | false | Download media attachments |

**Examples:**

```bash
# One-shot sync (default)
bale sync start

# Sync 1000 messages
bale sync start --limit 1000

# Continuous real-time sync
bale sync start --follow

# With NDJSON events
bale --events sync start --follow 2> events.ndjson

# With media download
bale sync start --follow --media
```

**NDJSON Event Format (stderr):**
```json
{"event": "message", "data": {"message_id": 123, "chat_id": 456, "text": "Hello", "sender": "John", "date": 1700000000000}}
```

---

## Messages Commands

Search, list, and manage messages.

### `bale messages search`

Search messages using FTS5 full-text search (with LIKE fallback).

```bash
bale messages search "query"
```

| Option | Type | Default | Description |
|---|---|---|---|
| `query` | string | **Required** | Search query |
| `--chat` | int | — | Filter by chat ID |
| `--sender` | int | — | Filter by sender ID |
| `--type` | string | — | Filter by message type (text, photo, document) |
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Pagination offset |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |
| `--full` | flag | false | Show full message details |

**Examples:**

```bash
# Basic search
bale messages search "meeting"

# Search in specific chat
bale messages search "report" --chat 123456

# Search with sender filter
bale messages search "hello" --sender 789012

# Pagination
bale messages search "test" --limit 20 --offset 40

# Full details
bale messages search "important" --full --json
```

---

### `bale messages list`

List messages from the local store.

```bash
bale messages list
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | — | Filter by chat ID |
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Pagination offset |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |
| `--full` | flag | false | Show full message details |

---

### `bale messages count`

Show total message count in the local store.

```bash
bale messages count
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--store` | path | No | Custom store directory |
| `--json` | flag | No | JSON output |

**Output:**
```
Total messages: 1234
```

---

### `bale messages mark-read`

Mark a chat as read (clear unread messages indicator).

```bash
bale messages mark-read --chat 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID to mark as read |
| `--type` | string | private | Chat type: private, group, channel, super_group |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Examples:**

```bash
# Mark private chat as read
bale messages mark-read --chat 123456

# Mark group as read
bale messages mark-read --chat 789012 --type group

# JSON output
bale messages mark-read --chat 123456 --json
```

**JSON Output:**
```json
{"status": "marked_read", "chat_id": 123456}
```

---

### `bale messages delete`

Delete a message from a chat.

```bash
bale messages delete --chat 123456 --message 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID containing the message |
| `--message` | int | **Required** | Message ID to delete |
| `--date` | int | auto | Message date/timestamp (auto-detected) |
| `--type` | string | private | Chat type |
| `--just-me` | flag | false | Delete only for yourself |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Examples:**

```bash
# Delete message (auto-detect date)
bale messages delete --chat 123456 --message 789012

# Delete only for yourself
bale messages delete --chat 123456 --message 789012 --just-me

# With explicit date
bale messages delete --chat 123456 --message 789012 --date 1700000000000
```

**Note:** If `load_history` fails due to aiobale parsing bugs, use `--date` with the message timestamp (milliseconds since epoch).

---

### `bale messages edit`

Edit an existing message (must be your own message).

```bash
bale messages edit --chat 123456 --message 789012 --text "New text"
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID containing the message |
| `--message` | int | **Required** | Message ID to edit |
| `--text` / `-m` | string | **Required** | New message text |
| `--type` | string | private | Chat type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Examples:**

```bash
# Edit message
bale messages edit --chat 123456 --message 789012 --text "Updated message"

# Short form
bale messages edit --chat 123456 --message 789012 -m "Updated message"
```

---

### `bale messages forward`

Forward a message from one chat to another.

```bash
bale messages forward --from-chat 123 --to-chat 456 --message 789
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--from-chat` | int | **Required** | Source chat ID |
| `--to-chat` | int | **Required** | Target chat ID |
| `--message` | int | **Required** | Message ID to forward |
| `--date` | int | auto | Message date (auto-detected) |
| `--from-type` | string | private | Source chat type |
| `--to-type` | string | private | Target chat type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Examples:**

```bash
# Forward within same chat
bale messages forward --from-chat 123 --to-chat 123 --message 456

# Forward between different chats
bale messages forward --from-chat 111 --to-chat 222 --message 333

# Forward from group to private
bale messages forward --from-chat 111 --to-chat 222 --message 333 --from-type group
```

**Known Issue:** Forward may fail with `Internal` error due to an upstream aiobale library bug. Use `--date` with the exact message timestamp as a workaround.

---

### `bale messages watch`

Watch for new messages in real-time. Outputs NDJSON to stdout.

```bash
bale messages watch
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | — | Watch specific chat only |
| `--store` | path | — | Custom store directory |
| `--json` | flag | true | JSON output (default true) |

**Examples:**

```bash
# Watch all chats
bale messages watch

# Watch specific chat
bale messages watch --chat 123456

# Pipe to jq for pretty printing
bale messages watch | jq .

# Process with a script
bale messages watch | while read line; do
  echo "$line" | jq -r '.text'
done
```

**Output Format (NDJSON, one per line):**
```json
{"message_id": 123, "chat_id": 456, "chat_type": "private", "text": "Hello!", "sender_id": 789, "sender_name": "John", "date": 1700000000000}
```

Messages are also stored in the local SQLite database automatically.

---

## Typing Commands

Manage typing indicators.

### `bale typing start`

Show typing indicator in a chat.

```bash
bale typing start --chat 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID |
| `--type` | string | private | Chat type |
| `--mode` | string | typing | Typing mode |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Available Modes:**

| Mode | Description |
|---|---|
| `typing` | Text typing indicator |
| `record` | Recording audio |
| `upload` | Uploading file |
| `play` | Choosing sticker |

**Examples:**

```bash
# Show typing
bale typing start --chat 123456

# Show recording audio
bale typing start --chat 123456 --mode record

# Show uploading file
bale typing start --chat 123456 --mode upload
```

---

### `bale typing stop`

Stop typing indicator in a chat.

```bash
bale typing stop --chat 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID |
| `--type` | string | private | Chat type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

## Send Commands

Send messages, files, and reactions.

### `bale send text`

Send a text message.

```bash
bale send text --to 123456 --message "Hello"
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--to` | string | **Required** | Recipient (chat ID, phone, or title) |
| `--message` / `-m` | string | **Required** | Message text |
| `--reply-to` | int | — | Reply to message ID |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

**Examples:**

```bash
# Send text
bale send text --to 123456 --message "Hello from CLI"

# Reply to a message
bale send text --to 123456 --message "Thanks!" --reply-to 789012

# By phone number
bale send text --to 989123456789 --message "Hi"

# By chat title
bale send text --to "My Group" --message "Hello everyone"
```

---

### `bale send file`

Send a file (document, photo, video, audio).

```bash
bale send file --to 123456 --file /path/to/file.pdf
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--to` | string | **Required** | Recipient |
| `--file` | path | **Required** | File path (must exist) |
| `--caption` | string | — | Caption for the file |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale send reaction`

Add a reaction to a message.

```bash
bale send reaction --chat 123456 --message 789012 --emoji "👍"
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID |
| `--message` | int | **Required** | Message ID to react to |
| `--emoji` | string | **Required** | Reaction emoji |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

## Admin Commands

Group/channel administration tools.

### `bale admin add-member`

Add a user to a group.

```bash
bale admin add-member --group 123456 --user 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--group` | int | **Required** | Group ID |
| `--user` | int | **Required** | User ID to add |
| `--type` | string | super_group | Group type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin kick-member`

Kick a user from a group.

```bash
bale admin kick-member --group 123456 --user 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--group` | int | **Required** | Group ID |
| `--user` | int | **Required** | User ID to kick |
| `--type` | string | super_group | Group type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin ban`

Ban a user from a group.

```bash
bale admin ban --group 123456 --user 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--group` | int | **Required** | Group ID |
| `--user` | int | **Required** | User ID to ban |
| `--type` | string | super_group | Group type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin unban`

Unban a user from a group.

```bash
bale admin unban --group 123456 --user 789012
```

---

### `bale admin make-admin`

Promote a user to admin in a group.

```bash
bale admin make-admin --group 123456 --user 789012
```

---

### `bale admin remove-admin`

Remove admin rights from a user.

```bash
bale admin remove-admin --group 123456 --user 789012
```

---

### `bale admin pin`

Pin a message in a chat.

```bash
bale admin pin --chat 123456 --message 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID |
| `--message` | int | **Required** | Message ID to pin |
| `--date` | int | auto | Message date (auto-detected from DB) |
| `--type` | string | private | Chat type |
| `--just-me` | flag | false | Pin only for yourself |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin unpin`

Unpin a message from a chat.

```bash
bale admin unpin --chat 123456 --message 789012
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--chat` | int | **Required** | Chat ID |
| `--message` | int | **Required** | Message ID to unpin |
| `--date` | int | auto | Message date (auto-detected from DB) |
| `--type` | string | private | Chat type |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin block`

Block a user.

```bash
bale admin block --user 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--user` | int | **Required** | User ID to block |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale admin unblock`

Unblock a user.

```bash
bale admin unblock --user 123456
```

---

## Chats Commands

List and manage chats.

### `bale chats list`

List chats from the local store.

```bash
bale chats list
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Pagination offset |
| `--type` | string | — | Filter by type: private, group, channel, bot, super_group |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale chats search`

Search chats by title or username.

```bash
bale chats search "group"
```

| Option | Type | Default | Description |
|---|---|---|---|
| `query` | string | **Required** | Search query |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale chats live`

Fetch live chat list from the Bale API.

```bash
bale chats live
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit` | int | 50 | Max results |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

## Contacts Commands

### `bale contacts list`

List contacts from the local store.

```bash
bale contacts list
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Pagination offset |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale contacts search`

Search contacts by name or phone.

```bash
bale contacts search "john"
```

---

### `bale contacts live`

Fetch live contacts from the Bale API.

```bash
bale contacts live
```

---

## Groups Commands

### `bale groups list`

List groups and channels.

```bash
bale groups list
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--channels` | flag | false | Show channels only |
| `--groups-only` | flag | false | Show groups only |
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Pagination offset |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale groups search`

Search groups by title.

```bash
bale groups search "tech"
```

---

### `bale groups info`

Show group details.

```bash
bale groups info 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `group_id` | int | **Required** | Group ID |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

### `bale groups members`

List group members.

```bash
bale groups members 123456
```

| Option | Type | Default | Description |
|---|---|---|---|
| `group_id` | int | **Required** | Group ID |
| `--limit` | int | 50 | Max results |
| `--store` | path | — | Custom store directory |
| `--json` | flag | false | JSON output |

---

## Serve Commands

Run bale-cli as a persistent HTTP API server.

### `bale serve start`

Start the HTTP API server with WebSocket support.

```bash
bale serve start
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--host` | string | 127.0.0.1 | HTTP server host |
| `--port` | int | 8765 | HTTP server port |
| `--store` | path | — | Custom store directory |
| `--api-key` | string | — | API key for authentication |

**Examples:**

```bash
# Default (localhost:8765)
bale serve start

# Custom port
bale serve start --port 9000

# With API key authentication
bale serve start --api-key my-secret-key

# Bind to all interfaces (use with caution)
bale serve start --host 0.0.0.0 --port 8765
```

**See [HTTP API Documentation](http-api.md) for full endpoint reference.**

---

## Doctor Command

### `bale doctor`

Run diagnostics and report system health.

```bash
bale doctor
```

| Option | Type | Required | Description |
|---|---|---|---|
| `--store` | path | No | Custom store directory |
| `--json` | flag | No | JSON output |

**Checks performed:**
- bale-cli version
- Python version
- Platform info
- Store directory existence
- Session file status
- Database size
- Message count
- aiobale library version
- Available disk space

**JSON Output:**
```json
{
  "bale_cli_version": "0.1.0",
  "python_version": "3.12.0",
  "platform": "Linux-6.5.0-x86_64",
  "store": "/home/user/.bale-cli",
  "session_exists": true,
  "db_size_bytes": 1048576,
  "message_count": 1234,
  "aiobale_version": "0.1.5",
  "disk_free_bytes": 5368709120
}
```
