# Agent Integration Guide

How to integrate bale-cli with AI agents, LLM applications, and automation workflows.

---

## Table of Contents

- [Overview](#overview)
- [Integration Methods](#integration-methods)
- [Method 1: CLI + JSON (Simple)](#method-1-cli--json-simple)
- [Method 2: NDJSON Watch Stream](#method-2-ndjson-watch-stream)
- [Method 3: HTTP API Server](#method-3-http-api-server)
- [Method 4: WebSocket (Real-time)](#method-4-websocket-real-time)
- [Customer Support Bot Pattern](#customer-support-bot-pattern)
- [Personal Assistant Pattern](#personal-assistant-pattern)
- [Message Processing Pipeline](#message-processing-pipeline)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Security Best Practices](#security-best-practices)

---

## Overview

bale-cli is designed from the ground up for **agent integration**. Every command supports `--json` output, and the tool provides multiple integration layers:

| Method | Latency | Complexity | Best For |
|---|---|---|---|
| CLI + JSON | ~500ms | Low | Simple scripts, cron jobs |
| NDJSON Watch | ~100ms | Medium | Real-time message processing |
| HTTP API | ~50ms | Medium | REST-based integrations |
| WebSocket | ~10ms | High | Ultra-low-latency agents |

---

## Integration Methods

### Method 1: CLI + JSON (Simple)

The simplest approach — call CLI commands and parse JSON output.

**Python Example:**

```python
import subprocess
import json

def send_message(chat_id: int, text: str) -> dict:
    """Send a message via bale-cli."""
    result = subprocess.run(
        ["bale", "send", "text", "--to", str(chat_id), "--message", text, "--json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def search_messages(query: str, limit: int = 20) -> list:
    """Search messages in the local store."""
    result = subprocess.run(
        ["bale", "messages", "search", query, "--limit", str(limit), "--json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def mark_read(chat_id: int) -> dict:
    """Mark a chat as read."""
    result = subprocess.run(
        ["bale", "messages", "mark-read", "--chat", str(chat_id), "--json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Usage
response = send_message(48859866, "Hello from the agent!")
print(f"Message sent: {response['message_id']}")
```

**Node.js Example:**

```javascript
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

async function sendMessage(chatId, text) {
  const { stdout } = await execAsync(
    `bale send text --to ${chatId} --message "${text}" --json`
  );
  return JSON.parse(stdout);
}

async function searchMessages(query, limit = 20) {
  const { stdout } = await execAsync(
    `bale messages search "${query}" --limit ${limit} --json`
  );
  return JSON.parse(stdout);
}

// Usage
const response = await sendMessage(48859866, "Hello from Node.js agent!");
console.log(`Message sent: ${response.message_id}`);
```

**Bash Example:**

```bash
#!/bin/bash
# Simple agent loop

CHAT_ID=48859866

# Get recent messages
MESSAGES=$(bale messages list --chat $CHAT_ID --limit 5 --json)

# Extract last message text
LAST_MSG=$(echo "$MESSAGES" | jq -r '.[-1].text')

# Process with your AI/LLM
RESPONSE=$(curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gpt-4\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$LAST_MSG\"}]
  }" | jq -r '.choices[0].message.content')

# Send response
bale send text --to $CHAT_ID --message "$RESPONSE"
```

---

### Method 2: NDJSON Watch Stream

Stream new messages in real-time as NDJSON (Newline-Delimited JSON).

**Python Example:**

```python
import subprocess
import json
import sys

def watch_messages():
    """Watch for new messages in real-time."""
    proc = subprocess.Popen(
        ["bale", "messages", "watch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    for line in proc.stdout:
        event = json.loads(line.strip())
        print(f"New message from {event['sender_name']}: {event['text']}")

        # Process with your agent logic
        process_message(event)

def process_message(event):
    """Agent logic for processing incoming messages."""
    # Example: auto-reply
    if "help" in event["text"].lower():
        subprocess.run([
            "bale", "send", "text",
            "--to", str(event["chat_id"]),
            "--message", "How can I help you?"
        ])

if __name__ == "__main__":
    watch_messages()
```

**Node.js Example:**

```javascript
const { spawn } = require('child_process');

function watchMessages() {
  const watch = spawn('bale', ['messages', 'watch']);

  watch.stdout.on('data', (data) => {
    const lines = data.toString().trim().split('\n');
    for (const line of lines) {
      const event = JSON.parse(line);
      console.log(`New message: ${event.text}`);
      processMessage(event);
    }
  });

  watch.stderr.on('data', (data) => {
    console.error(`Watch stderr: ${data}`);
  });
}

async function processMessage(event) {
  if (event.text.toLowerCase().includes('help')) {
    const { exec } = require('child_process');
    exec(`bale send text --to ${event.chat_id} --message "How can I help?"`);
  }
}

watchMessages();
```

**Processing Pipeline:**

```bash
# Watch and filter
bale messages watch | jq -c 'select(.chat_id == 123456)'

# Watch and extract text only
bale messages watch | jq -r '.text'

# Watch and save to file
bale messages watch >> messages.ndjson

# Watch with summary
bale messages watch | jq -c '{chat: .chat_id, from: .sender_name, text: .text[:50]}'
```

---

### Method 3: HTTP API Server

Run `bale serve start` for a persistent HTTP API server.

**Starting the Server:**

```bash
# Basic
bale serve start

# With API key
bale serve start --api-key your-secret-key

# Custom port
bale serve start --port 9000
```

**Python (aiohttp) Example:**

```python
import aiohttp
import asyncio

API_BASE = "http://localhost:8765"
API_KEY = "your-secret-key"  # If configured

async def send_message(chat_id: int, text: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/send/text",
            json={"chat_id": chat_id, "text": text},
            headers={"X-API-Key": API_KEY} if API_KEY else {}
        ) as resp:
            return await resp.json()

async def mark_read(chat_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/messages/mark-read",
            json={"chat_id": chat_id}
        ) as resp:
            return await resp.json()

async def search_messages(query: str, limit: int = 20):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/messages/search",
            params={"q": query, "limit": limit}
        ) as resp:
            return await resp.json()

async def typing_start(chat_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/messages/typing",
            json={"chat_id": chat_id, "action": "start"}
        ) as resp:
            return await resp.json()

async def typing_stop(chat_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/messages/typing",
            json={"chat_id": chat_id, "action": "stop"}
        ) as resp:
            return await resp.json()

# Usage
async def main():
    await typing_start(48859866)
    await asyncio.sleep(2)  # Simulate typing
    await typing_stop(48859866)
    result = await send_message(48859866, "Hello from HTTP API!")
    print(f"Sent: {result}")

asyncio.run(main())
```

**cURL Examples:**

```bash
# Send message
curl -X POST http://localhost:8765/send/text \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "text": "Hello!"}'

# Mark as read
curl -X POST http://localhost:8765/messages/mark-read \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866}'

# Show typing
curl -X POST http://localhost:8765/messages/typing \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "action": "start"}'

# Delete message
curl -X POST http://localhost:8765/messages/delete \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "message_id": 123456, "just_me": true}'

# Edit message
curl -X POST http://localhost:8765/messages/edit \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 48859866, "message_id": 123456, "text": "Updated text"}'

# Search messages
curl "http://localhost:8765/messages/search?q=hello&limit=10"

# List chats
curl "http://localhost:8765/chats?limit=50"

# With API key
curl -X POST http://localhost:8765/send/text \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"chat_id": 48859866, "text": "Authenticated request"}'
```

---

### Method 4: WebSocket (Real-time)

Use WebSocket for bi-directional real-time communication.

**Python (websockets) Example:**

```python
import asyncio
import json
import websockets

async def ws_listener():
    """Listen for real-time events via WebSocket."""
    uri = "ws://localhost:8765/ws"

    async with websockets.connect(uri) as ws:
        print("Connected to bale-cli WebSocket")

        # Send ping to keep connection alive
        await ws.send(json.dumps({"action": "ping"}))

        async for message in ws:
            event = json.loads(message)

            if event.get("event") == "pong":
                continue

            if event.get("event") == "message":
                data = event["data"]
                print(f"New message: {data['text']}")
                await handle_message(data)

async def handle_message(data):
    """Process incoming message."""
    chat_id = data["chat_id"]
    text = data["text"]

    # Show typing indicator
    # (would need HTTP call for this)

    # Process and respond
    response = f"Echo: {text}"
    # Send via HTTP API
    import aiohttp
    async with aiohttp.ClientSession() as session:
        await session.post(
            "http://localhost:8765/send/text",
            json={"chat_id": chat_id, "text": response}
        )

asyncio.run(ws_listener())
```

**Node.js Example:**

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765/ws');

ws.on('open', () => {
  console.log('Connected to bale-cli WebSocket');
  ws.send(JSON.stringify({ action: 'ping' }));
});

ws.on('message', async (data) => {
  const event = JSON.parse(data);

  if (event.event === 'message') {
    console.log(`New: ${event.data.text}`);
    await handleMessage(event.data);
  }
});

async function handleMessage(data) {
  const { exec } = require('child_process');
  const util = require('util');
  const execAsync = util.promisify(exec);

  const response = `Echo: ${data.text}`;
  await execAsync(
    `bale send text --to ${data.chat_id} --message "${response}"`
  );
}

ws.on('error', (err) => console.error('WebSocket error:', err));
ws.on('close', () => console.log('WebSocket closed'));
```

---

## Customer Support Bot Pattern

A complete customer support bot using bale-cli:

```python
import asyncio
import json
import subprocess
import aiohttp
from datetime import datetime

class SupportBot:
    def __init__(self, api_base="http://localhost:8765"):
        self.api_base = api_base
        self.chat_history = {}  # chat_id -> [messages]
        self.response_templates = {
            "greeting": "سلام! چطور می‌تونم کمکتون کنم؟",
            "hours": "ساعات کاری ما ۹ صبح تا ۶ عصر است.",
            "unknown": "متوجه نشدم. لطفاً سوالتون رو واضح‌تر بفرمایید.",
        }

    async def run(self):
        """Start the support bot."""
        # Connect to WebSocket for real-time events
        import websockets
        async with websockets.connect(f"{self.api_base}/ws") as ws:
            print("Support bot started")
            async for message in ws:
                event = json.loads(message)
                if event.get("event") == "message":
                    await self.handle_message(event["data"])

    async def handle_message(self, data):
        """Process incoming message and respond."""
        chat_id = data["chat_id"]
        text = data["text"].strip().lower()
        sender_id = data["sender_id"]

        # Skip own messages
        if data.get("is_from_me"):
            return

        # Show typing
        await self.typing(chat_id, "start")

        # Generate response
        response = self.generate_response(text)

        # Simulate typing delay
        await asyncio.sleep(min(len(response) * 0.05, 3))

        # Stop typing
        await self.typing(chat_id, "stop")

        # Send response
        await self.send(chat_id, response)

        # Mark as read
        await self.mark_read(chat_id)

        # Log conversation
        self.log_conversation(chat_id, sender_id, text, response)

    def generate_response(self, text: str) -> str:
        """Simple rule-based response generation."""
        if any(w in text for w in ["سلام", "hello", "hi", "درود"]):
            return self.response_templates["greeting"]
        elif any(w in text for w in ["ساعت", "hour", "time", "کار"]):
            return self.response_templates["hours"]
        elif any(w in text for w in ["قیمت", "price", "هزینه", "cost"]):
            return "برای اطلاع از قیمت‌ها لطفاً به سایت ما مراجعه کنید."
        else:
            return self.response_templates["unknown"]

    async def typing(self, chat_id: int, action: str):
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.api_base}/messages/typing",
                json={"chat_id": chat_id, "action": action}
            )

    async def send(self, chat_id: int, text: str):
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.api_base}/send/text",
                json={"chat_id": chat_id, "text": text}
            )

    async def mark_read(self, chat_id: int):
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.api_base}/messages/mark-read",
                json={"chat_id": chat_id}
            )

    def log_conversation(self, chat_id, sender_id, user_msg, bot_msg):
        """Log the conversation for analytics."""
        with open(f"support_log_{chat_id}.jsonl", "a") as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "sender_id": sender_id,
                "user_message": user_msg,
                "bot_response": bot_msg,
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    bot = SupportBot()
    asyncio.run(bot.run())
```

---

## Personal Assistant Pattern

An agent that monitors your messages and provides summaries:

```python
import asyncio
import json
import subprocess
from datetime import datetime, timedelta

class PersonalAssistant:
    def __init__(self):
        self.important_keywords = ["فوری", "urgent", "مهم", "important", "لطفاً"]
        self.summary_interval = 3600  # 1 hour

    async def run(self):
        """Run the personal assistant."""
        proc = subprocess.Popen(
            ["bale", "messages", "watch"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        pending_summaries = {}

        for line in proc.stdout:
            event = json.loads(line.strip())
            chat_id = event["chat_id"]

            # Check if message is important
            if self.is_important(event["text"]):
                await self.notify_urgent(event)

            # Queue for periodic summary
            if chat_id not in pending_summaries:
                pending_summaries[chat_id] = []
            pending_summaries[chat_id].append(event)

    def is_important(self, text: str) -> bool:
        return any(kw in text.lower() for kw in self.important_keywords)

    async def notify_urgent(self, event):
        """Send urgent notification."""
        subprocess.run([
            "bale", "send", "text",
            "--to", str(event["chat_id"]),
            "--message", f"⚠️ پیام فوری دریافت شد: {event['text'][:100]}"
        ])

    def generate_summary(self, messages: list) -> str:
        """Generate a summary of messages."""
        count = len(messages)
        senders = set(m["sender_name"] for m in messages)
        return f"{count} پیام از {', '.join(senders)}"


if __name__ == "__main__":
    assistant = PersonalAssistant()
    asyncio.run(assistant.run())
```

---

## Message Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    bale-cli Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────┐  │
│  │  Bale    │◄──►│  aiobale  │◄──►│  bale-cli Commands   │  │
│  │  API     │    │  Library  │    │  (CLI / HTTP / WS)   │  │
│  └──────────┘    └───────────┘    └──────────────────────┘  │
│                                      │                       │
│                    ┌─────────────────┼─────────────────┐     │
│                    ▼                 ▼                 ▼     │
│              ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│              │  SQLite  │    │  NDJSON   │    │  HTTP    │  │
│              │  Store   │    │  Stream   │    │  Server  │  │
│              └──────────┘    └───────────┘    └──────────┘  │
│                    │                 │                 │     │
│                    ▼                 ▼                 ▼     │
│              ┌──────────────────────────────────────────┐   │
│              │          Your Agent / Application         │   │
│              └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**

1. **Inbound:** Bale API → aiobale → Dispatcher → SQLite Store + NDJSON Stream + WebSocket
2. **Outbound:** Agent → CLI/HTTP → aiobale → Bale API
3. **Search:** Agent → SQLite FTS5 → Results

---

## Error Handling

**CLI Exit Codes:**

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General error (not authenticated, invalid input) |

**Error Response Format (HTTP API):**

```json
{"error": "Description of the error"}
```

**Retry Logic Example (Python):**

```python
import time
import subprocess
import json

def send_with_retry(chat_id, text, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["bale", "send", "text", "--to", str(chat_id),
                 "--message", text, "--json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            print(f"Attempt {attempt + 1} timed out")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    raise Exception(f"Failed after {max_retries} attempts")
```

---

## Rate Limiting

Bale's API has rate limits. Best practices:

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls=10, window_seconds=60):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = deque()

    def wait_if_needed(self):
        now = time.time()
        # Remove calls outside the window
        while self.calls and self.calls[0] < now - self.window:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            sleep_time = self.window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.calls.append(now)

# Usage
limiter = RateLimiter(max_calls=10, window_seconds=60)

def safe_send(chat_id, text):
    limiter.wait_if_needed()
    return send_message(chat_id, text)
```

---

## Security Best Practices

1. **Never commit session files** — `session.bale` contains your auth token
2. **Use API keys** — When running `bale serve`, always use `--api-key`
3. **Bind to localhost** — Don't expose the HTTP server to the internet
4. **Use profiles** — Separate accounts for different purposes
5. **Monitor logs** — Check stderr for errors and warnings

```bash
# Secure server setup
bale serve start --host 127.0.0.1 --port 8765 --api-key "$(openssl rand -hex 32)"

# Check who's listening
lsof -i :8765
```
