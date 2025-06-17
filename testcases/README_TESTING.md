
# ☁️ OWASP Quiz Generator System – Testing Guide

This guide walks you through testing the OWASP Quiz System in two phases:

---

## 🧪 Phase 1 – Lambda and SQS Testing (Before API Gateway)

### ✅ Components:

- `SubmitQuizLambda` — creates a session and sends SQS message  
- `QuizGenLambda` — processes the SQS message and updates DynamoDB  
- `SESSION_TABLE` — DynamoDB table  
- `QUIZGEN_QUEUE_URL` — SQS queue

---

### 🔧 Step 1: Test `SubmitQuizLambda` in AWS Console

#### 📤 Test Event:

```json
{
  "body": "{\"userId\": \"student123\", \"category\": \"SQL Injection\", \"difficulty\": \"low\"}"
}
```

#### ✅ Expected Result:

```json
{
  "statusCode": 200,
  "body": "{\"sessionId\": \"abc-uuid\"}"
}
```

#### ✅ Check:

- A record is added in DynamoDB with:
  - `userId`, `category`, `difficulty`, `status: pending`
- A message is visible in the SQS queue

---

### 📨 Step 2: Test `QuizGenLambda` with SQS Message

1. Go to the **SQS Console**  
2. Open the `QUIZGEN_QUEUE_URL` queue  
3. Click **Send and receive messages** → Send:

```json
{
  "sessionId": "abc-uuid",
  "userId": "student123",
  "category": "SQL Injection",
  "difficulty": "low"
}
```

4. View logs in **CloudWatch** for `QuizGenLambda`

#### ✅ Result in DynamoDB:

- `status` updated to `"completed"`
- `quiz`: JSON object with questions
- `rawResponse`: full Bedrock text

---

## 🌐 Phase 2 – API Gateway Testing

Once Lambda + SQS work, you can test via the exposed API endpoints.

---

### 🚀 Endpoint 1: `POST /submit`

**Purpose**: Create a new quiz session  
**Payload:**

```json
{
  "userId": "student123",
  "category": "XSS",
  "difficulty": "medium"
}
```

#### ✅ cURL Example:

```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{"userId":"student123","category":"XSS","difficulty":"medium"}'
```

#### ✅ Response:

```json
{
  "sessionId": "abc-uuid"
}
```

---

### 🔎 Endpoint 2: `GET /result/{sessionId}`

**Purpose**: Get quiz result for a session

#### ✅ cURL Example:

```bash
curl https://your-api-id.execute-api.region.amazonaws.com/prod/result/abc-uuid
```

#### ✅ Response (after quizgen Lambda runs):

```json
{
  "sessionId": "abc-uuid",
  "userId": "student123",
  "category": "XSS",
  "difficulty": "medium",
  "status": "completed",
  "quiz": {
    "questions": [
      {
        "question": "What is XSS?",
        "options": ["A", "B", "C", "D"],
        "answer": "A"
      }
    ]
  }
}
```

---

## ❌ Error Handling Test Cases

| Case                  | Request/Scenario                            | Result                         |
|-----------------------|---------------------------------------------|--------------------------------|
| Missing `userId`      | `{"category": "XSS"}`                       | `400`, "Invalid or missing userId" |
| Invalid `category`    | `{"userId": "x", "category": "Hacking"}`    | `400`, "Invalid category"      |
| Unknown `sessionId`   | GET `/result/fake-id`                       | `404`, "Session not found"     |
| SQS failure           | Queue URL missing or permission issue       | `500` on submission            |
| Bedrock fails         | Agent misconfigured or returns invalid JSON | Lambda logs error, no quiz saved |

---

## 🧪 Postman Setup

### POST `/submit`

- Method: POST  
- URL: `https://your-api-id.execute-api.region.amazonaws.com/prod/submit`  
- Headers: `Content-Type: application/json`  
- Body:
```json
{
  "userId": "student123",
  "category": "XSS",
  "difficulty": "low"
}
```

---

### GET `/result/{sessionId}`

- Method: GET  
- URL: `https://your-api-id.execute-api.region.amazonaws.com/prod/result/abc-uuid`

---

## 🔐 Required Environment Variables

| Lambda               | Variables Needed                              |
|----------------------|-----------------------------------------------|
| `SubmitQuizLambda`   | `SESSION_TABLE`, `QUIZGEN_QUEUE_URL`          |
| `QuizGenLambda`      | `SESSION_TABLE`, `AGENT_ID`, `AGENT_ALIAS_ID`, `BEDROCK_REGION` |
| `GetResultLambda`    | `SESSION_TABLE`                               |
