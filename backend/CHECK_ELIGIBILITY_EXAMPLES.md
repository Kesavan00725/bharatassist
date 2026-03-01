# POST /check-eligibility Endpoint

## Overview

The `/check-eligibility` endpoint evaluates a user's eligibility for government schemes based on their profile.

## Endpoint Details

- **URL**: `POST /check-eligibility`
- **Request Model**: `EligibilityRequest`
- **Response Model**: `EligibilityResponse`

## Request Fields

```json
{
  "age": 45, // integer (0-120)
  "income_inr": 150000, // annual income in INR
  "state": "maharashtra", // state name
  "category": "general", // sc/st/obc/ews/general (optional)
  "occupation": "farmer", // occupation type (optional)
  "is_disabled": false, // boolean (optional)
  "rural": true // boolean, rural area resident (optional)
}
```

## Response Format

```json
{
  "best_match": {
    "id": "pm-kisan",
    "scheme_name": "PM-KISAN",
    "description": "Income support for eligible farmer families.",
    "score": 100,
    "eligible": true,
    "reasons": [
      "Income INR 150,000 <= INR 200,000",
      "Occupation farmer is eligible"
    ],
    "missing_criteria": [],
    "official_link": "https://pmkisan.gov.in",
    "required_documents": ["Aadhaar", "Land Record", "Bank Passbook"],
    "benefits": ["₹6,000 per year in 3 installments"]
  },
  "eligible_schemes": [
    {
      /* PM-KISAN */
    },
    {
      /* Ayushman Bharat (PM-JAY) */
    }
  ],
  "not_eligible_schemes": [
    {
      /* schemes with score < 60 */
    }
  ]
}
```

## Example Requests

### Example 1: Farmer with low income

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "income_inr": 150000,
    "state": "maharashtra",
    "category": "general",
    "occupation": "farmer",
    "is_disabled": false,
    "rural": true
  }'
```

**Expected Result:**

- Best Match: PM-KISAN (Score: 100)
- Eligible: 2 schemes

---

### Example 2: Senior citizen with low income

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 65,
    "income_inr": 180000,
    "state": "delhi",
    "category": "sc",
    "occupation": "retired",
    "is_disabled": false,
    "rural": false
  }'
```

**Expected Result:**

- Best Match: Ayushman Bharat (PM-JAY) (Score: 100)
- Eligible: 3 schemes (PM-JAY, PMUY, NSAP Old Age Pension)

---

### Example 3: Woman from rural area

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "income_inr": 200000,
    "state": "karnataka",
    "category": "general",
    "occupation": "worker",
    "is_disabled": false,
    "rural": true,
    "gender": "female"
  }'
```

**Expected Result:**

- Best Match: Ayushman Bharat (PM-JAY) (Score: 100)
- Eligible: 2 schemes (PM-JAY, PMUY)

---

### Example 4: High income professional

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "income_inr": 500000,
    "state": "maharashtra",
    "category": "general",
    "occupation": "engineer",
    "is_disabled": false,
    "rural": false
  }'
```

**Expected Result:**

- Eligible: 1 scheme (at minimum threshold)
- Most schemes not eligible (income too high)

---

## Scoring Logic

Each scheme evaluates criteria independently:

**PM-KISAN:**

- Max income ≤ ₹200,000 (50 points)
- Occupation = Farmer (50 points)
- Eligible if score ≥ 60

**Ayushman Bharat (PM-JAY):**

- Max income ≤ ₹300,000 (40 points)
- Category in [SC, ST, OBC, EWS, General] (60 points)
- Eligible if score ≥ 60

**Pradhan Mantri Ujjwala Yojana (PMUY):**

- Max income ≤ ₹250,000 (50 points)
- Gender = Female (50 points)
- Eligible if score ≥ 60

**NSAP – Old Age Pension:**

- Age ≥ 60 years (50 points)
- Max income ≤ ₹200,000 (50 points)
- Eligible if score ≥ 60

---

## Notes

- Score ranges from 0-100
- Eligibility threshold: Score ≥ 60
- `best_match` is the highest-scoring eligible scheme, or `null` if none qualify
- `reasons` field explains why criteria matched
- `missing_criteria` field explains unmet requirements
- All fields except `age` and `income_inr` are optional
- String fields (state, category, occupation, gender) are case-insensitive
