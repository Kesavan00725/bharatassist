# BharatAssist MVP

**BharatAssist** is an intelligent AI-powered platform that helps Indian citizens discover and verify their eligibility for government schemes. The system provides personalized scheme recommendations, document verification, and real-time chat assistance.

---

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

BharatAssist is an MVP (Minimum Viable Product) designed to bridge the gap between Indian citizens and government welfare schemes. The platform intelligently analyzes user profiles and matches them with eligible schemes, while also providing document verification capabilities.

### Key Problem It Solves
- Citizens are unaware of available government schemes
- Complex eligibility criteria are hard to understand
- Manual document verification is time-consuming
- No single platform aggregates all scheme information

### Solution
- **Unified Platform**: All Indian government schemes in one place
- **Eligibility Matching**: AI-powered matching against user profiles
- **Document Verification**: Automated PDF document analysis
- **Chat Assistance**: Real-time conversational guidance

---

## ✨ Features

### 1. **Eligibility Checker**
   - Input user profile (age, income, state, occupation, category)
   - Get matched government schemes based on eligibility
   - View best matches and scoring breakdown
   - See detailed scheme information

### 2. **Document Verification**
   - Upload PDF documents (Income Certificate, Aadhaar, Caste Certificate, etc.)
   - Automated document type detection
   - Field extraction (name, income, certificate number, etc.)
   - Confidence scoring and risk assessment
   - Profile matching validation

### 3. **Chat Assistant**
   - Natural language query support
   - Multi-turn conversation history
   - Session-based chat management
   - Integrated eligibility suggestions
   - Real-time scheme recommendations

### 4. **Scheme Database**
   - Pre-loaded government schemes
   - Detailed eligibility criteria
   - Required documents listing
   - Official links and resources

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WEB BROWSER                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Frontend (HTML/CSS/JavaScript)                      │  │
│  │  • index.html (Landing Page)                         │  │
│  │  • eligibility.html (Eligibility Checker)            │  │
│  │  • chat.html (Chat Interface)                        │  │
│  │  • style.css (Styling)                               │  │
│  │  • script.js (Interactive Logic)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓ (HTTP/REST)
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND API (FastAPI)                        │
│                   Port: 8000                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                          │  │
│  │  • POST /chat - Chat with assistant                 │  │
│  │  • POST /check-eligibility - Check eligibility      │  │
│  │  • POST /verify-pdf - Verify PDF documents          │  │
│  │  • GET /schemes - List all schemes                  │  │
│  │  • GET /health - Health check                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services & Modules:                                 │  │
│  │  • chat_service.py - Chat & NLP processing          │  │
│  │  • eligibility_engine.py - Scheme matching logic    │  │
│  │  • document_verifier.py - PDF analysis              │  │
│  │  • database.py - Session management                 │  │
│  │  • schemas.py - Data validation                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Storage & Support:                                  │  │
│  │  • bharatassist.db (SQLite Database)                │  │
│  │  • schemes.json (Scheme definitions)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) | Latest |
| **Backend** | Python 3.9+ | 3.9+ |
| **Framework** | FastAPI | 0.100+ |
| **Server** | Uvicorn | 0.20+ |
| **Database** | SQLite | 3.x |
| **AI/LLM** | OpenAI GPT-4o-mini | Latest |
| **PDF Processing** | PyPDF2 | 3.x |
| **Data Validation** | Pydantic | 2.x |
| **HTTP Server** | Python http.server | Built-in |

---

## 📦 Installation & Setup

### Prerequisites
- **Python 3.9+** installed
- **pip** (Python package manager)
- **OpenAI API Key** (for chat features)
- Modern web browser

### Step 1: Clone/Navigate to Project
```bash
cd c:\Users\KESAVAN SEKAR\OneDrive\Desktop\bharat assist
```

### Step 2: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Set Environment Variables
Create a `.env` file in the `backend/` directory:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///bharatassist.db
```

### Step 4: Start Backend Server
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
✅ Backend running on: `http://localhost:8000`

### Step 5: Start Frontend Server (New Terminal)
```bash
cd frontend
python -m http.server 3000
```
✅ Frontend running on: `http://localhost:3000`

### Step 6: Access Application
- **Main Website**: http://localhost:3000/index.html
- **Eligibility Checker**: http://localhost:3000/eligibility.html
- **Chat Interface**: http://localhost:3000/chat.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🚀 Usage

### Using Eligibility Checker

1. **Navigate** to `http://localhost:3000/eligibility.html`
2. **Fill in your profile:**
   - Age (18-120)
   - Annual Income (in INR)
   - State
   - Occupation
   - Category (SC/ST/OBC/EWS/General)
   - Disability status (if applicable)
   - Rural/Urban area

3. **Click "Check Eligibility"**
4. **View Results:**
   - ✅ Best scheme match with details
   - ✅ All eligible schemes (score ≥ 60)
   - ✗ Not eligible schemes (score < 60)

### Using Chat Interface

1. **Navigate** to `http://localhost:3000/chat.html`
2. **Type a message**, for example:
   ```
   I am 50 years old, earn 1 crore annually, from Bangalore, business owner
   ```
3. **Get instant eligibility check and suggestions**
4. **Ask follow-up questions** for more details

### Using Document Verification

1. **In Eligibility Checker**, select a scheme
2. **Upload PDF documents** (Income Certificate, Aadhaar, etc.)
3. **Get verification results:**
   - Document type detected
   - Fields extracted
   - Confidence score
   - Risk assessment
   - Issues identified

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Core Endpoints

#### 1. **POST /check-eligibility**
Check user eligibility for schemes
```json
Request:
{
  "age": 50,
  "income_inr": 10000000,
  "state": "Karnataka",
  "occupation": "business",
  "category": "GENERAL",
  "is_disabled": false,
  "rural": false
}

Response:
{
  "best_match": {
    "id": "scheme_001",
    "scheme_name": "Pradhan Mantri Scheme",
    "score": 85,
    "benefits": ["₹50,000 subsidy", "Tax benefits"],
    "official_link": "https://..."
  },
  "eligible_schemes": [...],
  "not_eligible_schemes": [...]
}
```

#### 2. **POST /chat**
Chat with AI assistant
```json
Request:
{
  "message": "I am 50 years old, earn 1 crore, from Bangalore",
  "session_id": "optional_session_id",
  "user_profile": {...},
  "eligibility_results": {...}
}

Response:
{
  "session_id": "generated_or_provided_id",
  "reply": "Based on your profile..."
}
```

#### 3. **POST /verify-pdf**
Verify PDF document
```
Form Data:
- req_json: VerifyRequest as JSON string
- file: PDF file upload

Response:
{
  "scheme_id": "scheme_001",
  "scheme_name": "Scheme Name",
  "required_documents": ["Income Certificate", ...],
  "declared_documents": ["Income Certificate"],
  "missing_declared": [],
  "pdf_found_keywords": {},
  "verdict": "Looks okay based on declared docs."
}
```

#### 4. **GET /schemes**
Get all available schemes
```
Response:
{
  "schemes": [
    {
      "id": "scheme_001",
      "name": "Pradhan Mantri Scheme",
      "description": "...",
      "documents_required": [...],
      "eligibility_criteria": {...}
    },
    ...
  ]
}
```

#### 5. **GET /health**
Health check
```
Response:
{
  "ok": true,
  "details": {
    "service": "bharatassist-backend"
  }
}
```

---

## 📂 Project Structure

```
bharat assist/
│
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── chat_service.py            # Chat & NLP logic
│   ├── eligibility_engine.py      # Scheme matching algorithm
│   ├── document_verifier.py       # PDF document analysis
│   ├── database.py                # Database operations
│   ├── schemas.py                 # Pydantic data models
│   ├── requirements.txt           # Python dependencies
│   ├── bharatassist.db            # SQLite database
│   └── schemes.json               # Government schemes data
│
├── frontend/
│   ├── index.html                 # Landing page
│   ├── eligibility.html           # Eligibility checker page
│   ├── chat.html                  # Chat interface page
│   ├── style.css                  # Styling & responsive design
│   └── script.js                  # Frontend logic & API calls
│
├── README.md                      # This file
├── FEATURE_VERIFICATION.md        # Feature checklist
├── FINAL_SUMMARY.md               # Project summary
└── INTEGRATION_TEST_GUIDE.md      # Testing documentation
```

---

## ⚙️ Configuration

### Backend Configuration

**Environment Variables** (in `.env`):
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Database Configuration
DATABASE_URL=sqlite:///bharatassist.db

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Frontend Configuration

**API Base URL** (in `script.js`):
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Database

SQLite database file: `backend/bharatassist.db`
- Stores chat session history
- Stores user interactions
- Auto-created on first run

### Schemes Data

File: `backend/schemes.json`
Contains:
- Scheme definitions
- Eligibility criteria
- Required documents
- Official links

---

## 🧪 Testing

### Manual Testing

1. **Basic Eligibility Check:**
   ```
   Age: 35, Income: 2.5 lakh, State: Maharashtra, Occupation: Farmer
   Expected: Show eligible schemes
   ```

2. **Income Parsing (Fixed):**
   ```
   Message: "I am 50 years old, earn 1 crore annually, from Bangalore"
   Expected: Income = ₹10,000,000 (not ₹500,000,000)
   ```

3. **Chat Flow:**
   ```
   Message: "What schemes am I eligible for?"
   Expected: AI asks clarifying questions for profile
   ```

4. **Document Upload:**
   ```
   Action: Upload Income Certificate PDF
   Expected: Shows document type, extracted fields, confidence score
   ```

### API Testing

Use the interactive docs: `http://localhost:8000/docs`

Or use curl:
```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 50,
    "income_inr": 10000000,
    "state": "Karnataka",
    "occupation": "business"
  }'
```

---

## 🔧 Troubleshooting

### Issue: Backend won't start
**Solution:**
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port 8000 is not in use
netstat -ano | findstr :8000
```

### Issue: Income parsing incorrect
**Status:** ✅ FIXED (v2)
- Previous: 1.5 lakh was parsed as 62 lakh
- Fixed: Refined regex pattern in `chat_service.py:67`
- Now correctly parses: 1.5 lakh → ₹150,000

### Issue: Frontend can't reach backend
**Solution:**
```javascript
// Check API URL in script.js
const API_BASE_URL = 'http://localhost:8000';

// Verify backend is running
curl http://localhost:8000/health
```

### Issue: PDF upload fails
**Solution:**
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Check file size (max recommended: 5MB)
- Use standard PDF format

### Issue: OpenAI API errors
**Solution:**
```bash
# Verify API key is set
echo %OPENAI_API_KEY%

# Test API connection
python -c "from openai import OpenAI; print('OK')"
```

---

## 📊 Data Flow Diagram

```
┌──────────────────┐
│   User Input     │
│  (Chat/Form)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  NLP Extraction & Parsing    │
│  (Extract age, income, etc)  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Eligibility Engine          │
│  (Match schemes)             │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  AI Chat Processing          │
│  (Generate response)         │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Frontend Display            │
│  (Show results to user)      │
└──────────────────────────────┘
```

---

## 📈 Recent Updates

### Version 2.0 - Income Parsing Fix
- ✅ Fixed income extraction regex
- ✅ Proper lakh/crore multiplication
- ✅ Tested with "1 crore" → ₹10,000,000

### Known Limitations
- ⚠️ PDF extraction accuracy depends on PDF format
- ⚠️ Scheme data is sample/demo data - not official
- ⚠️ Requires OpenAI API key for chat features

---

## 🤝 Contributing

To add improvements:
1. Update relevant module (e.g., `eligibility_engine.py`)
2. Test changes with sample data
3. Update this README if adding new features

---

## ⚖️ Legal Disclaimer

**BharatAssist** is a reference implementation for educational purposes only. It is **NOT** an official government portal. Always verify eligibility on official government websites:
- https://www.pmjdy.gov.in (Pradhan Mantri Jan Dhan Yojana)
- https://www.pmkisan.gov.in (PM-KISAN)
- State-specific government portals

---

## 📞 Support

For issues or questions:
1. Check the **Troubleshooting** section
2. Review API documentation at `http://localhost:8000/docs`
3. Check logs in backend console
4. Verify environment variables are set

---

## 📄 License

This project is provided as-is for educational and reference purposes.

---

**Last Updated:** March 2, 2026
**Status:** MVP (Minimum Viable Product)
**Next Steps:** Integration with official APIs, production deployment, mobile app development
