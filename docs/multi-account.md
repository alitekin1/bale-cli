# Multi-Account Guide

Manage multiple Bale accounts using bale-cli profiles.

---

## Table of Contents

- [Overview](#overview)
- [Setting Up Profiles](#setting-up-profiles)
- [Using Profiles](#using-profiles)
- [Profile File Structure](#profile-file-structure)
- [Profile with HTTP Server](#profile-with-http-server)
- [Use Cases](#use-cases)
- [Limitations](#limitations)

---

## Overview

bale-cli supports **multiple Bale accounts** through a profile system. Each profile has its own:

- Session file (`session_<name>.bale`)
- Database file (`bale_<name>.db`)

This means each profile is completely isolated — separate messages, contacts, and authentication.

---

## Setting Up Profiles

### Login with a Profile

```bash
# Default profile (no name)
bale auth login --phone 989111111111

# Named profiles
bale auth login --phone 989222222222 --profile support
bale auth login --phone 989333333333 --profile sales
bale auth login --phone 989444444444 --profile personal
```

### List All Profiles

```bash
bale auth profiles
```

**Output:**
```
Available profiles:
  default — /home/user/.bale-cli/session.bale
  support — /home/user/.bale-cli/session_support.bale
  sales — /home/user/.bale-cli/session_sales.bale
  personal — /home/user/.bale-cli/session_personal.bale
```

**JSON Output:**
```bash
bale auth profiles --json
```
```json
{
  "profiles": [
    {"name": "default", "session": "/home/user/.bale-cli/session.bale"},
    {"name": "support", "session": "/home/user/.bale-cli/session_support.bale"},
    {"name": "sales", "session": "/home/user/.bale-cli/session_sales.bale"},
    {"name": "personal", "session": "/home/user/.bale-cli/session_personal.bale"}
  ]
}
```

### Check Profile Status

```bash
bale auth status --profile support
```

---

## Using Profiles

### Global `--profile` Flag

The `--profile` flag works with **every command**:

```bash
# Search messages in support account
bale --profile support messages search "ticket"

# Send message from sales account
bale --profile sales send text --to 123456 --message "Follow up"

# Sync personal account
bale --profile personal sync start --follow

# Check doctor on specific profile
bale --profile support doctor
```

### Profile-Specific Commands

```bash
# Login to a profile
bale auth login --phone 989... --profile work

# Logout from a profile
bale auth logout --profile work

# Check status of a profile
bale auth status --profile work
```

### Profile in Scripts

```bash
#!/bin/bash
# Multi-account message broadcaster

PROFILES="support sales personal"
MESSAGE="System maintenance tonight at 2 AM"

for profile in $PROFILES; do
  echo "Sending from $profile..."
  bale --profile $profile send text --to 123456 --message "$MESSAGE"
done
```

---

## Profile File Structure

```
~/.bale-cli/
├── session.bale              # Default profile session
├── bale.db                   # Default profile database
├── session_support.bale      # Support profile session
├── bale_support.db           # Support profile database
├── session_sales.bale        # Sales profile session
├── bale_sales.db             # Sales profile database
└── session_personal.bale     # Personal profile session
    └── bale_personal.db      # Personal profile database
```

### Custom Store Directory

You can combine `--store` with `--profile`:

```bash
bale --store /opt/bale-data --profile support auth status
```

This uses:
- Session: `/opt/bale-data/session_support.bale`
- Database: `/opt/bale-data/bale_support.db`

---

## Profile with HTTP Server

Run separate HTTP servers for each profile:

```bash
# Support account on port 8765
bale --profile support serve start --port 8765 &

# Sales account on port 8766
bale --profile sales serve start --port 8766 &

# Personal account on port 8767
bale --profile personal serve start --port 8767 &
```

Each server operates independently with its own account.

---

## Use Cases

### 1. Customer Support Team

```bash
# Support agent account
bale auth login --phone 989100000001 --profile support-1
bale auth login --phone 989100000002 --profile support-2

# Route messages based on content
bale --profile support-1 messages watch | jq -r '.text' | while read msg; do
  if echo "$msg" | grep -i "billing"; then
    bale --profile support-2 send text --to ... --message "Billing inquiry: $msg"
  fi
done
```

### 2. Business + Personal Separation

```bash
# Business hours: monitor work account
bale --profile work messages watch --chat $WORK_CHAT_ID | process_work_messages

# After hours: only personal
bale --profile personal messages watch | process_personal_messages
```

### 3. Multi-Channel Broadcasting

```python
import subprocess

def broadcast(message, profiles=None):
    """Send a message from all specified profiles."""
    profiles = profiles or ["default"]
    results = {}
    for profile in profiles:
        result = subprocess.run(
            ["bale", "--profile", profile, "send", "text",
             "--to", "123456", "--message", message, "--json"],
            capture_output=True, text=True
        )
        results[profile] = result.stdout
    return results

# Broadcast from all accounts
broadcast("Important announcement!", ["support", "sales", "personal"])
```

---

## Limitations

1. **No cross-profile operations** — You cannot send a message from profile A to a chat in profile B's database
2. **Separate sync required** — Each profile needs its own `sync start` to populate its database
3. **No profile switching in serve** — The HTTP server uses the profile specified at startup
4. **Session isolation** — Logging out of one profile does not affect others
