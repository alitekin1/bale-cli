# Troubleshooting Guide

Common issues and their solutions when using bale-cli.

---

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Sync Issues](#sync-issues)
- [Message Issues](#message-issues)
- [HTTP Server Issues](#http-server-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

---

## Authentication Issues

### "Not authenticated" Error

**Symptom:**
```
Not authenticated. Run bale auth login first.
```

**Causes & Solutions:**

1. **Never logged in:**
   ```bash
   bale auth login --phone 989123456789
   ```

2. **Session file deleted or moved:**
   ```bash
   # Check if session exists
   ls ~/.bale-cli/session.bale

   # Check status
   bale auth status
   ```

3. **Wrong profile:**
   ```bash
   # List available profiles
   bale auth profiles

   # Use the correct profile
   bale --profile support auth status
   ```

4. **Custom store directory:**
   ```bash
   # If you used --store, you must use it every time
   bale --store /custom/path auth status
   ```

### Login Fails with "PHONE_NUMBER_INVALID"

**Cause:** The phone number format is incorrect.

**Solution:**
- Use country code without `+`: `989123456789`
- No spaces or dashes
- Persian/Arabic digits are automatically converted

```bash
# Correct
bale auth login --phone 989123456789

# Also works (auto-converts)
bale auth login --phone "+98 912 051 8560"
```

### Login Fails with "Rate limit exceeded"

**Cause:** Too many login attempts in a short time.

**Solution:** Wait 10-30 minutes and try again. Bale's API has rate limiting on OTP requests.

### Login Fails with "Password needed"

**Cause:** The account has 2FA (two-factor authentication) enabled.

**Solution:** The current CLI doesn't support 2FA password input interactively. You may need to:
1. Temporarily disable 2FA in the Bale app
2. Login via CLI
3. Re-enable 2FA

---

## Sync Issues

### "Could not load dialogs" Warning

**Symptom:**
```
Warning: Could not load dialogs: '1'
Continuing with stored chats + live sync
```

**Cause:** This is a known issue with the aiobale library's response parsing. The API response structure may have changed.

**Impact:** One-shot sync may not load all dialogs, but follow-mode will still receive new messages in real-time.

**Solution:**
1. Use follow-mode for real-time sync:
   ```bash
   bale sync start --follow
   ```
2. Messages will still be stored in the database as they arrive
3. The warning can be safely ignored if follow-mode works

### Sync is Slow

**Cause:** Loading history for many chats.

**Solutions:**
1. Limit the number of messages:
   ```bash
   bale sync start --limit 100
   ```
2. Use follow-mode for ongoing sync:
   ```bash
   bale sync start --follow
   ```

### No Messages After Sync

**Cause:** The database may be empty or the sync didn't complete.

**Solutions:**
1. Check message count:
   ```bash
   bale messages count
   ```
2. Re-run sync:
   ```bash
   bale sync start --follow
   ```
3. Check if session is valid:
   ```bash
   bale auth status
   ```

---

## Message Issues

### "Failed to delete message: validation errors for HistoryResponse"

**Cause:** The aiobale library has parsing bugs when loading message history. The API response structure doesn't match the expected Pydantic model.

**Solution:** Use the `--date` flag with the message timestamp:

```bash
# Find the date from the database
bale messages search "" --chat 123456 --json | jq '.[].date'

# Delete with explicit date
bale messages delete --chat 123456 --message 789012 --date 1700000000000
```

### Forward Fails with "Internal" Error

**Cause:** Upstream aiobale library bug in the `ForwardMessages` method. Bale's server returns an internal error.

**Status:** This is a known limitation. The CLI constructs the forward request correctly, but the Bale API rejects it.

**Workaround:** Manually forward the message in the Bale app.

### "Chat not found" When Sending

**Cause:** The `--to` parameter couldn't be resolved.

**Solutions:**
1. Use the numeric chat ID:
   ```bash
   bale chats list --json | jq '.[].peer_id'
   bale send text --to 48859866 --message "Hello"
   ```
2. Use the exact chat title (case-sensitive):
   ```bash
   bale send text --to "Exact Group Name" --message "Hello"
   ```
3. Use the phone number:
   ```bash
   bale send text --to 989123456789 --message "Hello"
   ```

---

## HTTP Server Issues

### "Port already in use"

**Cause:** Another process is using the port.

**Solution:**
```bash
# Find what's using the port
lsof -i :8765

# Kill the process
kill <PID>

# Or use a different port
bale serve start --port 8766
```

### "aiohttp is required"

**Cause:** The `aiohttp` package is not installed.

**Solution:**
```bash
pip install aiohttp
# Or reinstall bale-cli
pip install -e .
```

### Server Starts but Returns Errors

**Cause:** The Bale session may be expired or invalid.

**Solution:**
1. Check session:
   ```bash
   bale auth status
   ```
2. Re-login if needed:
   ```bash
   bale auth login --phone 989123456789
   ```
3. Restart the server

### WebSocket Connection Fails

**Cause:** The server may not have started properly or a firewall is blocking.

**Solution:**
```bash
# Test HTTP first
curl http://localhost:8765/status

# Check server logs (stderr)
bale serve start 2> server.log &

# Test WebSocket
wscat -c ws://localhost:8765/ws
```

---

## Database Issues

### Database is Corrupted

**Symptom:** SQLite errors when searching or listing messages.

**Solution:**
```bash
# Backup first
cp ~/.bale-cli/bale.db ~/.bale-cli/bale.db.backup

# Re-sync (recreates the database)
rm ~/.bale-cli/bale.db
bale sync start --follow
```

### Database is Too Large

**Symptom:** Slow searches or high disk usage.

**Solution:**
```bash
# Check database size
bale doctor --json | jq '.db_size_bytes'

# Vacuum the database (reclaims space)
sqlite3 ~/.bale-cli/bale.db "VACUUM;"

# Or start fresh
rm ~/.bale-cli/bale.db
bale sync start --follow
```

---

## Performance Issues

### Slow Search

**Cause:** Large database or FTS5 index needs rebuilding.

**Solution:**
```bash
# Rebuild FTS5 index
sqlite3 ~/.bale-cli/bale.db "INSERT INTO messages_fts(messages_fts) VALUES('rebuild');"
```

### High Memory Usage

**Cause:** Follow-mode sync keeps all dialogs in memory.

**Solution:**
1. Limit the number of dialogs
2. Restart the sync periodically
3. Use the HTTP server instead (more efficient)

---

## Common Error Messages

| Error | Cause | Solution |
|---|---|---|
| `Not authenticated` | No session file | Run `bale auth login` |
| `PHONE_NUMBER_INVALID` | Wrong format | Use `989123456789` (no +) |
| `Rate limit exceeded` | Too many OTP requests | Wait 10-30 minutes |
| `validation errors for HistoryResponse` | aiobale parsing bug | Use `--date` flag |
| `Internal` (forward) | Bale API bug | Manual forward in app |
| `Port already in use` | Port conflict | Use different port |
| `aiohttp is required` | Missing dependency | `pip install aiohttp` |
| `Chat not found` | Can't resolve recipient | Use numeric chat ID |

---

## Debug Mode

Enable verbose output:

```bash
# Run with Python debug
python -m bale_cli.main --json doctor 2>&1 | head -50

# Check aiobale logs
export AIOBALE_LOG_LEVEL=DEBUG
bale sync start --follow
```

---

## Getting Help

1. **Check this guide** — Most issues are covered above
2. **Run diagnostics** — `bale doctor`
3. **Check GitHub issues** — https://github.com/alitekin1/bale-cli/issues
4. **Create an issue** — Include:
   - `bale doctor --json` output
   - The command you ran
   - The full error message
   - Steps to reproduce
