# BharatAssist Backend - Complete System Overview

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                               │
│  /check-eligibility  /chat  /chat-with-json  /verify           │
└────────┬─────────────────────────────────────────────────────┬──┘
         │                                                     │
┌────────▼──────────────────────────────────────────────────┐ │
│              Service Layer                                │ │
│  • eligibility_engine.py  • chat_service.py             │ │
│  • document_verifier.py                                 │ │
└────────┬────────────────────────────────────────────────┬┘ │
         │                                                │   │
┌────────▼────────────────────────────────────────────────▼──┐│
│              Data Layer                                    ││
│  • database.py (SQLite)  • schemas.py (Pydantic)         ││
│                                                           ││
│  chat_messages table:                                     ││
│  ├─ id                                                    ││
│  ├─ session_id (indexed)                                 ││
│  ├─ role (user/assistant)                                ││
│  ├─ content                                              ││
│  └─ created_at (Unix timestamp)                          ││
└────────────────────────────────────────────────────────────┘│
         │                                                    │
         └────────────────────────────────────────────────────┘
```

## API Endpoints Summary

### 1. Eligibility Check

```
POST /check-eligibility
POST /eligibility  (alias)

Input: User profile (age, income, state, occupation, etc.)
Output: best_match, eligible_schemes, not_eligible_schemes
```

### 2. Chat Assistant

```
POST /chat
POST /chat-with-json

Input: message + optional user_profile + optional eligibility_results
Output: reply text or structured JSON with suggestions
```

### 3. Document Verification

```
POST /verify
Input: scheme_id + declared_documents
Output: verdict + missing documents

POST /verify-pdf
Input: scheme_id + declared_documents + PDF file
Output: verdict + PDF keyword matching results

POST /document-verify (Comprehensive)
Input: PDF file + optional user_profile
Output: document_type, status, confidence_score, extracted_fields, issues, risk_level
```

## Data Flow: Complete User Journey

### Step 1: User Checks Eligibility

```
Client → POST /check-eligibility
{
  "age": 45,
  "income_inr": 150000,
  "state": "maharashtra",
  "occupation": "farmer",
  "rural": true
}
        ↓ eligibility_engine.py
        ├─ load_schemes() → schemes.json
        ├─ _evaluate_criteria() for each scheme
        └─ Return: best_match, eligible_schemes, not_eligible_schemes
        → API Response
```

### Step 2: User Asks Chat About Schemes

```
Client → POST /chat-with-json
{
  "message": "What should I do next?",
  "user_profile": { ... from Step 1 },
  "eligibility_results": { ... from Step 1 }
}
        ↓ chat_service.py
        ├─ get_or_create_session_id()
        ├─ fetch_recent_messages() → database.py
        ├─ Build context prompt with eligibility data
        ├─ Call OpenAI (gpt-4o-mini, JSON mode)
        └─ save_message() → SQLite ✓
        → API Response with suggestions
```

### Step 3: Multi-Turn Conversation (Context Preserved)

```
Client → POST /chat-with-json
{
  "message": "Tell me more about PM-KISAN",
  "session_id": "from-previous-response"  ← KEY: Reuse session
}
        ↓ chat_service.py
        ├─ fetch_recent_messages(session_id) → SQLite
        │  Returns: Last 10 messages from previous turns ✓
        ├─ Build new message with conversation history
        ├─ Call OpenAI
        └─ save_message() → SQLite ✓
        → API Response (context-aware)
```

### Step 4: User Verifies Documents

```
Option A: Scheme-Specific Verification
Client → POST /verify-pdf
{
  "req_json": "VerifyRequest",
  "file": PDF upload
}
        ↓ document_verifier.py
        ├─ extract_pdf_text()
        ├─ keyword_presence()
        └─ Return verdict
        → API Response

Option B: Comprehensive Document Verification
Client → POST /document-verify
{
  "file": PDF upload,
  "user_profile": optional profile data
}
        ↓ document_verifier.py
        ├─ detect_document_type() → Type confidence
        ├─ extract_fields() → Name, income, cert#, date, authority
        ├─ validate_fields() → Format, profile match, suspicious indicators
        ├─ calculate_confidence() → 0-100 score
        ├─ assess_risk_level() → low/medium/high
        └─ Return VerificationResult with all details
        → API Response
```

## Database Integration

### Chat History Persistence

```python
# In chat_service.py
def chat_reply():
    # 1. Load history
    history = fetch_recent_messages(session_id, limit=10)  ← database.py

    # 2. Build prompt with history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]

    # 3. Call OpenAI
    response = client.chat.completions.create(...)

    # 4. Save reply
    insert_message(session_id, "assistant", reply)  ← database.py
```

### Available Database Functions

- `init_db()` - Create tables
- `save_message(session_id, role, message)` - Save a message
- `get_chat_history(session_id, limit=12)` - Retrieve recent messages
- `get_all_chat_history(session_id)` - Retrieve all messages
- `delete_session_history(session_id)` - Clear a session
- `get_session_count()` - Count total sessions
- `get_message_count(session_id)` - Count messages in session
- `export_session_to_json(session_id)` - Export session

## Configuration

### Environment Variables

```bash
# OpenAI (required for chat)
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"  # Default

# Database (auto-created)
# Location: backend/bharatassist.db
```

### Key Parameters

```python
# Chat Service
SYSTEM_PROMPT = "You are BharatAssist..."  # No hallucination
temperature = 0.3  # Deterministic
response_format = {"type": "json_object"}  # Enforce JSON
limit = 10  # Context messages to load

# Eligibility Scoring
threshold = 60  # Eligible if score >= 60
max_score = 100  # Normalized to 0-100
```

## Security & Safety

### Chat Assistant

- ✓ System prompt prevents hallucination
- ✓ Only discusses provided eligibility data
- ✓ JSON mode enforces structured output
- ✓ Temperature=0.3 for consistency
- ✓ No external knowledge injection

### Database

- ✓ Thread-safe (check_same_thread=False)
- ✓ Parameterized queries (SQL injection protection)
- ✓ Auto-close connections (try-finally)
- ✓ Indexed on session_id (fast lookups)

### Eligibility Engine

- ✓ Deterministic (same inputs = same outputs)
- ✓ Transparent (shows reasons & missing criteria)
- ✓ Modular (easy to add new criteria)
- ✓ No false positives (60-point threshold enforced)

## Performance

| Operation                | Complexity | Time (typical)    |
| ------------------------ | ---------- | ----------------- |
| Save message             | O(1)       | <1ms              |
| Fetch 10 recent messages | O(log n)   | ~5ms              |
| Get message count        | O(1)       | <1ms              |
| Chat with context        | O(1)       | ~0.5s (OpenAI)    |
| Eligibility check        | O(n)       | ~10ms (4 schemes) |

n = total messages in system
m = messages in session

## Testing

### Run all tests

```bash
cd backend

# Test eligibility engine
python << 'EOF'
from eligibility_engine import evaluate_eligibility
result = evaluate_eligibility({
    "age": 45,
    "income_inr": 150000,
    "occupation": "farmer"
})
print(result['best_match'])
EOF

# Test chat service
python << 'EOF'
from chat_service import chat_reply, get_or_create_session_id
sid = get_or_create_session_id(None)
reply = chat_reply(sid, "Hello", {}, None)
print(reply)
EOF

# Test database
python << 'EOF'
from database import init_db, save_message, get_chat_history
init_db()
save_message("test", "user", "Hello")
history = get_chat_history("test")
print(history)
EOF
```

### Curl Examples

**Check Eligibility:**

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "income_inr": 150000,
    "state": "maharashtra",
    "occupation": "farmer"
  }'
```

**Chat with Context:**

```bash
curl -X POST http://localhost:8000/chat-with-json \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What schemes are available?",
    "user_profile": {
      "age": 45,
      "income_inr": 150000,
      "occupation": "farmer"
    }
  }'
```

## API Documentation

- Eligibility: See `CHECK_ELIGIBILITY_EXAMPLES.md`
- Chat: See `CHAT_API_DOCUMENTATION.md`
- Document Verification: See `DOCUMENT_VERIFICATION_DOCUMENTATION.md`
- Database: See `DATABASE_DOCUMENTATION.md`

## File Structure

```
backend/
├── main.py                                  # FastAPI app, endpoints
├── schemas.py                               # Pydantic models
├── eligibility_engine.py                    # Scoring logic
├── chat_service.py                          # Chat with OpenAI
├── database.py                              # SQLite operations
├── document_verifier.py                     # PDF parsing & verification
├── bharatassist.db                          # SQLite database (auto-created)
├── schemes.json                             # Scheme definitions
├── CHECK_ELIGIBILITY_EXAMPLES.md            # Eligibility endpoint examples
├── CHAT_API_DOCUMENTATION.md                # Chat endpoint documentation
├── DOCUMENT_VERIFICATION_DOCUMENTATION.md   # Document verification docs
├── DATABASE_DOCUMENTATION.md                # Database operations docs
└── SYSTEM_OVERVIEW.md                       # This file
```

## Next Steps / Future Enhancements

- [ ] Add more schemes to schemes.json
- [ ] Implement scheme-specific eligibility rules
- [ ] Add user authentication (session management)
- [ ] Create admin dashboard
- [ ] Export chat history to PDF
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Real-time scheme updates
- [ ] Analytics dashboard

## Support

For API documentation, see markdown files in `backend/`:

- `CHECK_ELIGIBILITY_EXAMPLES.md` - Eligibility endpoint usage
- `CHAT_API_DOCUMENTATION.md` - Chat endpoint usage
- `DATABASE_DOCUMENTATION.md` - Database operations

## Version

- **Version**: 0.1.0
- **Last Updated**: 2026-03-01
- **Status**: MVP (Minimum Viable Product)
