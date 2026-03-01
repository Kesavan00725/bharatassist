# Chat History Database Documentation

## Overview

BharatAssist uses SQLite for persistent chat history storage. Each chat session maintains a complete message history, enabling multi-turn conversations with context preservation.

## Database File

- **Location**: `backend/bharatassist.db`
- **Type**: SQLite 3
- **Size**: Grows with chat history (typically small)
- **Thread-safe**: Yes (check_same_thread=False)

## Table Schema

### chat_messages

```sql
CREATE TABLE chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Unique message ID
  session_id TEXT NOT NULL,                -- Chat session identifier (uuid)
  role TEXT NOT NULL,                      -- 'user' or 'assistant'
  content TEXT NOT NULL,                   -- Message content/text
  created_at INTEGER NOT NULL              -- Unix timestamp of creation
)
```

**Index:**

- `idx_chat_session` on `(session_id)` - for fast session lookups

## API Functions

### Core Functions

#### `init_db()`

Initialize the database and create tables.

```python
from database import init_db

init_db()  # Creates table if it doesn't exist
```

**Called automatically** in `main.py` on startup.

---

#### `save_message(session_id, role, message)`

Save a message to chat history (recommended API).

```python
from database import save_message

save_message(
    session_id="abc123xyz",
    role="user",
    message="What schemes am I eligible for?"
)
```

**Parameters:**

- `session_id` (str): Chat session ID (typically UUID)
- `role` (str): "user" or "assistant"
- `message` (str): Message text

---

#### `get_chat_history(session_id, limit=12)`

Fetch recent chat messages in chronological order (recommended API).

```python
from database import get_chat_history

history = get_chat_history(
    session_id="abc123xyz",
    limit=10
)

# Returns:
# [
#   {"role": "user", "content": "Hello"},
#   {"role": "assistant", "content": "Hi there!"},
#   ...
# ]
```

**Parameters:**

- `session_id` (str): Chat session ID
- `limit` (int): Maximum messages to fetch (default: 12)

**Returns:**

- List of dicts with `role` and `content` keys, in chronological order

---

### Utility Functions

#### `insert_message(session_id, role, content)`

Lower-level message insertion (same as `save_message`).

```python
from database import insert_message

insert_message("session123", "user", "My message")
```

---

#### `fetch_recent_messages(session_id, limit=12)`

Fetch recent messages (same as `get_chat_history`).

```python
from database import fetch_recent_messages

messages = fetch_recent_messages("session123", limit=10)
```

---

#### `get_all_chat_history(session_id)`

Get complete chat history (all messages, no limit).

```python
from database import get_all_chat_history

all_messages = get_all_chat_history("session123")

# Returns:
# [
#   {
#     "id": 1,
#     "session_id": "session123",
#     "role": "user",
#     "content": "First message",
#     "created_at": 1704067200
#   },
#   ...
# ]
```

---

#### `delete_session_history(session_id)`

Delete all messages in a session.

```python
from database import delete_session_history

deleted_count = delete_session_history("session123")
print(f"Deleted {deleted_count} messages")  # Output: Deleted 15 messages
```

**Returns:** Number of messages deleted

---

#### `get_session_count()`

Get total number of unique chat sessions.

```python
from database import get_session_count

total_sessions = get_session_count()
print(f"Total sessions: {total_sessions}")  # Output: Total sessions: 42
```

**Returns:** Count of distinct session IDs

---

#### `get_message_count(session_id)`

Get message count for a specific session.

```python
from database import get_message_count

message_count = get_message_count("session123")
print(f"Messages in session: {message_count}")  # Output: Messages in session: 15
```

**Returns:** Count of messages in session

---

#### `export_session_to_json(session_id)`

Export a complete session as JSON-serializable dict.

```python
from database import export_session_to_json
import json

export = export_session_to_json("session123")
json_str = json.dumps(export, indent=2)

# Output:
# {
#   "session_id": "session123",
#   "message_count": 15,
#   "messages": [
#     {
#       "id": 1,
#       "session_id": "session123",
#       "role": "user",
#       "content": "Hello",
#       "created_at": 1704067200
#     },
#     ...
#   ]
# }
```

**Returns:** Dict with session metadata and all messages

---

## Usage in Chat Service

The database functions are automatically integrated into the chat service:

```python
from chat_service import chat_reply
from database import get_chat_history

# chat_reply() internally:
# 1. Gets older messages: history = fetch_recent_messages(session_id, limit=10)
# 2. Inserts user message: insert_message(session_id, "user", user_message)
# 3. Calls OpenAI with history
# 4. Saves assistant reply: insert_message(session_id, "assistant", reply)

message = chat_reply(
    session_id="session123",
    user_message="Tell me about PM-KISAN"
)

# Later, get full history:
history = get_chat_history("session123", limit=20)
```

---

## Database Management

### Backup

```bash
cp backend/bharatassist.db backend/bharatassist.db.backup
```

### Query via SQLite CLI

```bash
sqlite3 backend/bharatassist.db

# List all messages
SELECT * FROM chat_messages;

# Messages in a session
SELECT * FROM chat_messages WHERE session_id='abc123' ORDER BY id;

# Message count per session
SELECT session_id, COUNT(*) as message_count FROM chat_messages GROUP BY session_id;

# Recent messages
SELECT * FROM chat_messages ORDER BY id DESC LIMIT 20;
```

### Reset Database

```python
import os
from pathlib import Path

db_path = Path("backend/bharatassist.db")
if db_path.exists():
    os.remove(db_path)

# Import and re-initialize
from database import init_db
init_db()
```

---

## Performance Characteristics

| Operation               | Speed    | Notes                       |
| ----------------------- | -------- | --------------------------- |
| Save message            | O(1)     | Single row insert           |
| Fetch recent (limit=12) | O(log n) | Index on session_id         |
| Get all history         | O(m)     | m = messages in session     |
| Delete session          | O(n)     | n = messages in session     |
| Get session count       | O(1)     | COUNT(DISTINCT) aggregation |

---

## Data Types and Timestamps

**created_at** stores Unix timestamps (seconds since epoch):

```python
import time
from datetime import datetime

# Create datetime from timestamp
timestamp = 1704067200
dt = datetime.fromtimestamp(timestamp)
print(dt)  # 2024-01-01 00:00:00

# Get current timestamp
now = int(time.time())
```

---

## Example: Complete Chat Flow

```python
from chat_service import chat_reply, get_or_create_session_id
from database import get_chat_history, get_all_chat_history, export_session_to_json
import json

# 1. Create or get session
session_id = get_or_create_session_id(None)
print(f"Session: {session_id}")

# 2. First message
reply1 = chat_reply(
    session_id=session_id,
    user_message="What schemes exist for farmers?"
)
print(f"Assistant: {reply1}")

# 3. Follow-up message (history is loaded automatically)
reply2 = chat_reply(
    session_id=session_id,
    user_message="What are the documents needed?"
)
print(f"Assistant: {reply2}")

# 4. Get chat history (10 most recent messages)
history = get_chat_history(session_id, limit=10)
print(f"Recent messages: {len(history)}")
for msg in history:
    print(f"  {msg['role']}: {msg['content'][:50]}...")

# 5. Get all history
all_history = get_all_chat_history(session_id)
print(f"Total messages: {len(all_history)}")

# 6. Export as JSON
export = export_session_to_json(session_id)
print(json.dumps(export, indent=2))
```

---

## Thread Safety

The database module is thread-safe:

```python
from database import get_conn

# Connection pool
conn = get_conn()  # Safe for concurrent use (check_same_thread=False)
```

Each function opens its own connection, uses it, and closes it. Multiple threads can safely access the database simultaneously.

---

## Error Handling

The database functions use try-finally to ensure connections are closed:

```python
def fetch_recent_messages(session_id: str, limit: int = 12) -> list[dict]:
    conn = get_conn()
    try:
        # Query...
    finally:
        conn.close()  # Always closes, even if exception occurs
```

---

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Migration system for schema changes
- [ ] Message archival (move old sessions)
- [ ] Session metadata (user profile, created_time, updated_time)
- [ ] Message search/filtering
- [ ] Conversation summaries
- [ ] Export to CSV/JSON utilities
- [ ] Database cleanup/pruning utilities
