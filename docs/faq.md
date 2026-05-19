# Frequently Asked Questions

---

## General

### What is bale-cli?

bale-cli is a command-line interface client for Bale Messenger. It connects to Bale using the internal gRPC API (via the `aiobale` library) and provides messaging capabilities from the terminal, plus an HTTP API server for agent integration.

### Is this official?

No. bale-cli is a third-party tool. It is not affiliated with or endorsed by Bale. It uses Bale's internal gRPC API, which is reverse-engineered.

### Is it safe to use?

bale-cli stores your authentication token locally (like WhatsApp Web). The token is never shared with anyone except Bale's servers. However, as with any third-party tool, use at your own risk.

### What platforms are supported?

Linux, macOS, and Windows (WSL recommended on Windows). Python 3.10+ is required.

---

## Authentication

### How does login work?

1. You provide your phone number
2. bale-cli requests an OTP code from Bale
3. You enter the code received in your Bale app
4. A session file is saved locally for future use

### Can I use a bot token?

No. bale-cli uses user account authentication (phone + OTP), not bot tokens. If you need bot functionality, use Bale's official Bot API.

### Can I use multiple accounts?

Yes. Use the `--profile` flag to manage multiple accounts. See [Multi-Account Guide](multi-account.md).

### How do I logout?

```bash
bale auth logout
```

This deletes your session file. You'll need to log in again to use bale-cli.

---

## Messages

### Why can't I see all my messages after sync?

The aiobale library has a known parsing issue with the `load_history` API response. Use `--follow` mode for real-time sync, which works reliably.

### Can I send images/files?

Yes, with `bale send file --to ID --file path`. Note that the current implementation sends the file as a document.

### Can I forward messages?

The forward command exists but currently fails due to an upstream aiobale library bug. Manual forwarding in the Bale app is the workaround.

### Can I edit messages?

Yes, with `bale messages edit --chat ID --message ID --text "new text"`. You can only edit your own messages.

### Can I delete messages?

Yes, with `bale messages delete --chat ID --message ID`. Use `--just-me` to delete only for yourself.

---

## HTTP Server

### How do I start the HTTP server?

```bash
bale serve start
```

Default: `http://localhost:8765`

### Can I access it from another machine?

Yes, but be careful with security:

```bash
bale serve start --host 0.0.0.0 --api-key your-secret-key
```

Always use `--api-key` when exposing the server to the network.

### Does the server support HTTPS?

Not natively. Put it behind a reverse proxy (nginx, Caddy) for HTTPS.

### How many concurrent connections?

The server uses aiohttp, which handles thousands of concurrent connections. The bottleneck is usually the Bale API rate limits, not the server itself.

---

## Database

### Where is the database stored?

`~/.bale-cli/bale.db` (Linux: `~/.local/state/bale-cli/bale.db`)

### Can I query the database directly?

Yes, it's a standard SQLite database:

```bash
sqlite3 ~/.bale-cli/bale.db "SELECT * FROM messages LIMIT 10;"
```

### How do I backup the database?

```bash
cp ~/.bale-cli/bale.db ~/bale-backup.db
```

### Can I use the database with another app?

Yes, but only for reading. Writing should be done through bale-cli to maintain consistency.

---

## Performance

### How much disk space does it use?

The database grows with message count. Roughly:
- 1,000 messages: ~1 MB
- 10,000 messages: ~5 MB
- 100,000 messages: ~30 MB

### Is follow-mode resource-intensive?

Minimal. It maintains a single WebSocket connection and writes to SQLite on new messages.

### Can I reduce database size?

```bash
# Vacuum (reclaims deleted space)
sqlite3 ~/.bale-cli/bale.db "VACUUM;"

# Or start fresh
rm ~/.bale-cli/bale.db
bale sync start --follow
```

---

## Troubleshooting

### "Not authenticated" but I logged in

Check if you're using the correct profile or store directory:

```bash
bale auth status
bale auth profiles
```

### Commands are slow

Each CLI command creates a new aiobale client connection. For faster operations, use the HTTP server (`bale serve start`).

### How do I get debug output?

```bash
export AIOBALE_LOG_LEVEL=DEBUG
bale sync start --follow
```

---

## Comparison

### bale-cli vs Bale Bot API

| Feature | bale-cli | Bale Bot API |
|---|---|---|
| Account type | User account | Bot account |
| Login | Phone + OTP | Bot token |
| Read messages | Yes (all chats) | Only messages to bot |
| Send messages | Yes (any chat) | Only to bot chats |
| Join groups | Yes | Must be added |
| Admin actions | Yes | Limited |
| Offline store | SQLite | No |
| HTTP API | Built-in | N/A |

### bale-cli vs Bale Web

| Feature | bale-cli | Bale Web |
|---|---|---|
| Interface | Terminal / API | Browser |
| Automation | Yes | No |
| Scriptable | Yes | No |
| Multi-account | Yes (profiles) | One at a time |
| Offline access | Yes (SQLite) | No |
| Agent integration | Yes | No |
