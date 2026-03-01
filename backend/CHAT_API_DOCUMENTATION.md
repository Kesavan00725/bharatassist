# Chat Assistant with Eligibility Integration

## Overview

BharatAssist now includes an AI-powered chat assistant that integrates eligibility results to provide informed, accurate recommendations about government schemes.

## Features

✅ **Eligibility-Aware**: Chat uses actual eligibility calculation results
✅ **Context-Aware**: Remembers conversation history via SQLite
✅ **Structured Output**: Returns scheme suggestions and clarification needs
✅ **Safe & Deterministic**: Uses gpt-4o-mini with temperature=0.3 for consistency
✅ **JSON Mode**: Enforces structured JSON responses
✅ **No Hallucination**: System prompt prevents making up scheme details

## API Endpoints

### 1. POST /chat - Simple Text Reply

Returns a text response from the assistant.

**Request:**

```json
{
  "message": "What schemes am I eligible for?",
  "session_id": "optional-session-id",
  "user_profile": {
    "age": 45,
    "income_inr": 150000,
    "state": "maharashtra",
    "occupation": "farmer",
    "rural": true
  },
  "eligibility_results": {
    "best_match": {...},
    "eligible_schemes": [...],
    "not_eligible_schemes": [...]
  }
}
```

**Response:**

```json
{
  "session_id": "generated-or-provided-session-id",
  "reply": "Based on your profile, you're eligible for PM-KISAN and Ayushman Bharat..."
}
```

---

### 2. POST /chat-with-json - Structured JSON Response

Returns structured JSON with scheme suggestions and clarification needs.

**Request:** (same as above)

**Response:**

```json
{
  "session_id": "session-id",
  "reply": "Based on your profile, you're eligible for PM-KISAN and Ayushman Bharat...",
  "scheme_suggestions": ["pm-kisan", "pmjay"],
  "clarification_needed": []
}
```

---

## System Prompt

The assistant operates under these strict guidelines:

```
You are BharatAssist, a helpful assistant for Indian government schemes.

You MUST:
- Use only the provided eligibility results to inform responses
- Never hallucinate or claim knowledge beyond what was provided
- If unsure or data is insufficient, say "Insufficient data."
- Be concise and practical
- Never claim official authority; suggest verifying on official portals
- Help users understand their eligibility and next steps

Guidelines:
- Ask 1-3 clarifying questions about missing eligibility details if needed
- Provide actionable next steps
- Reference specific schemes by name when relevant
- Highlight required documents for eligible schemes
```

---

## Usage Examples

### Example 1: Farmer with Complete Profile

**Request:**

```bash
curl -X POST http://localhost:8000/chat-with-json \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I apply for government support?",
    "user_profile": {
      "age": 45,
      "income_inr": 150000,
      "state": "maharashtra",
      "occupation": "farmer",
      "rural": true,
      "category": "general"
    },
    "eligibility_results": {
      "best_match": {
        "scheme_name": "PM-KISAN",
        "score": 100,
        "id": "pm-kisan",
        "official_link": "https://pmkisan.gov.in",
        "required_documents": ["Aadhaar", "Land Record", "Bank Passbook"]
      },
      "eligible_schemes": [
        {
          "id": "pm-kisan",
          "scheme_name": "PM-KISAN",
          "score": 100,
          "required_documents": ["Aadhaar", "Land Record", "Bank Passbook"],
          "official_link": "https://pmkisan.gov.in"
        },
        {
          "id": "pmjay",
          "scheme_name": "Ayushman Bharat (PM-JAY)",
          "score": 100,
          "required_documents": ["Aadhaar", "Ration Card"],
          "official_link": "https://pmjay.gov.in"
        }
      ],
      "not_eligible_schemes": []
    }
  }'
```

**Expected Response:**

```json
{
  "session_id": "abc123...",
  "reply": "Based on your profile as a 45-year-old farmer in Maharashtra with income of INR 150,000, you're eligible for PM-KISAN and Ayushman Bharat. For PM-KISAN, gather your Aadhaar, Land Record, and Bank Passbook, then visit https://pmkisan.gov.in. You should also apply for Ayushman Bharat at https://pmjay.gov.in with your Aadhaar and Ration Card.",
  "scheme_suggestions": ["pm-kisan", "pmjay"],
  "clarification_needed": []
}
```

---

### Example 2: Incomplete Profile - Requesting Clarification

**Request:**

```bash
curl -X POST http://localhost:8000/chat-with-json \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Am I eligible for any schemes?",
    "user_profile": {
      "age": 28
    }
  }'
```

**Expected Response:**

```json
{
  "session_id": "def456...",
  "reply": "I see you're 28 years old. To recommend suitable schemes, I need a bit more information: What's your annual income (in INR)? What state are you in? And what's your primary occupation?",
  "scheme_suggestions": [],
  "clarification_needed": ["income_inr", "state", "occupation"]
}
```

---

### Example 3: Multi-Turn Conversation

**First Turn:**

```bash
curl -X POST http://localhost:8000/chat-with-json \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need government support",
    "session_id": "session-123"
  }'
```

Response suggests providing profile data.

**Second Turn:**

```bash
curl -X POST http://localhost:8000/chat-with-json \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I'm a 62-year-old senior with monthly income of about 15,000 rupees and I live in rural Delhi",
    "session_id": "session-123"
  }'
```

The assistant remembers the context from the first message and provides targeted recommendations based on the new information.

---

## Request Format

### ChatRequest Schema

```python
{
  "message": str,                      # Required: user message (1-4000 chars)
  "session_id": str | null,             # Optional: chat session identifier
  "user_profile": dict | null,          # Optional: user eligibility profile
  "eligibility_results": dict | null    # Optional: results from /check-eligibility
}
```

### User Profile Fields

```python
{
  "age": int,                    # 0-120
  "income_inr": int,             # Annual income in INR
  "state": str,                  # State name
  "category": str,               # sc/st/obc/ews/general
  "occupation": str,             # e.g., farmer, student, retired
  "is_disabled": bool,           # Disability status
  "rural": bool                  # Rural area resident
}
```

---

## Response Format

### ChatResponse (Simple)

```python
{
  "session_id": str,
  "reply": str
}
```

### ChatResponseWithJSON (Structured)

```python
{
  "session_id": str,
  "reply": str,
  "scheme_suggestions": list[str],      # scheme IDs
  "clarification_needed": list[str]     # missing fields
}
```

---

## Integration with Eligibility Engine

### Recommended Workflow

1. **Step 1: Check Eligibility**

   ```bash
   POST /check-eligibility
   Input: user profile
   Output: eligibility_results
   ```

2. **Step 2: Chat with Results**

   ```bash
   POST /chat-with-json
   Input: message + user_profile + eligibility_results (from Step 1)
   Output: reply + scheme_suggestions
   ```

3. **Step 3: Multi-turn Conversation**
   - Use returned `session_id` for follow-up questions
   - Assistant remembers context from previous messages
   - Can refine recommendations as user provides more details

---

## Conversation State

- **Stored in SQLite** (`bharatassist.db`)
- **Table**: `chat_messages` (session_id, role, content, timestamp)
- **Index**: `idx_chat_session` for fast lookup
- **History Limit**: Last 10 messages per session

---

## Error Handling

If `OPENAI_API_KEY` is not set, the chat service returns:

```json
{
  "session_id": "session-id",
  "reply": "OpenAI is not configured (missing OPENAI_API_KEY). Please provide your profile details.",
  "scheme_suggestions": [],
  "clarification_needed": ["age", "income_inr", "state", "occupation"]
}
```

---

## Configuration

Set environment variables:

```bash
export OPENAI_API_KEY="sk-..."           # OpenAI API key
export OPENAI_MODEL="gpt-4o-mini"        # Model (default: gpt-4o-mini)
```

---

## AI Safety Features

✅ **Deterministic Output**: temperature=0.3 (low randomness)
✅ **JSON Validation**: Enforces schema with `response_format`
✅ **No Hallucination**: System prompt prevents fabrication
✅ **Scope Limited**: Only discusses schemes in provided eligibility results
✅ **Context Window**: 10 recent messages (avoids context explosion)

---

## Testing

Run the backend:

```bash
cd backend
python -m uvicorn main:app --reload
```

Access API docs:

```
http://localhost:8000/docs
```

Test endpoints via Swagger UI or curl.
