# Gamified OWASP Quiz CDK Project

## Stacks
- `GamifiedCognitoStack`: Creates a Cognito user pool and client for authentication
- `GamifiedBackendStack`: Handles all API Gateway, Lambda, SQS, and DynamoDB infrastructure

## Deployment

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cdk bootstrap
cdk deploy GamifiedCognitoStack
cdk deploy GamifiedBackendStack
```

## Lambda Functions

Place your Python Lambda files in the `lambda/` directory:
- `submit.py`
- `quizgen.py`
- `get_result.py`

Each should implement `lambda_handler(event, context)`.
---

## 🧠 Project Overview Summary

This platform allows secure coding education through gamified quizzes based on the OWASP Top 10. The system is built using AWS CDK and includes:

- Cognito-based secure login
- API Gateway protected with JWT
- Lambda functions for submission, generation, evaluation, and feedback
- SQS and DynamoDB for async handling and state tracking
- Bedrock Agent integration to adapt content

---

## 🏗️ Architecture Diagram

The system uses two CDK stacks:

1. **GamifiedCognitoStack**  
   - AWS Cognito User Pool + App Client  
   - Handles secure authentication (OAuth2 / PKCE)

2. **GamifiedBackendStack**  
   - API Gateway with JWT Authorizer  
   - SQS Queues for async Lambda triggers  
   - Lambda functions for quiz generation, evaluation, hints, etc.  
   - DynamoDB table to store quiz session status and results  
   - Bedrock Agent (via API call) for LLM-based quiz generation  

```plaintext
+----------+       +-------------+       +--------------+       +-------------+
|   User   | <---> |   Cognito   | <---> | API Gateway  | <---> | Lambda Pool |
+----------+       +-------------+       +--------------+       +-------------+
                                                    |                |
                                             +------+                |
                                             |      |                |
                                         +---v--+ +--v---+      +----v-----+
                                         | SQS  | | SQS  | ...  | DynamoDB |
                                         +------+ +------+      +----------+
```

---

## 📡 API Endpoints

### `POST /generate-quiz`

- **Auth**: Bearer JWT (Cognito)
- **Body**:
```json
{
  "userId": "student001",
  "category": "SQL Injection"
}
```

- **Response**:
```json
{ "sessionId": "abc123" }
```

---

### `GET /quiz-result?sessionId=abc123`

- **Auth**: Bearer JWT
- **Response**:
```json
{
  "status": "completed",
  "quiz": {
    "questions": [...],
    "hints": [...],
    "explanation": [...]
  }
}
```

- **Error** (unauthenticated or not ready):
```json
{ "status": "pending" }
```

---

Would you like to test the APIs with Postman or generate OpenAPI spec next?


---

## 🧠 Lambda Functions

| Lambda Function        | Description                                                             | Trigger            |
|------------------------|-------------------------------------------------------------------------|--------------------|
| `submit.py`            | Handles quiz request submission, stores session, sends messages to SQS | API Gateway (POST) |
| `quizgen.py`           | Generates quizzes using Bedrock agent                                   | SQS: QuizGenQueue  |
| `get_result.py`        | Returns quiz result or session status from DynamoDB                     | API Gateway (GET)  |
| `evaluate.py`          | Evaluates student answers and scores them                               | SQS: EvaluationQueue |
| `record.py`            | Records the quiz attempt (for audit/tracking)                           | SQS: RecordQueue   |
| `hint.py`              | Provides hint information for a specific quiz question                  | SQS                |
| `explain.py`           | Provides explanation for a question or answer                           | SQS                |
| `quizgen_feedback.py`  | Improves or adapts the quiz post-evaluation                             | SQS                |

Each Lambda should implement:

```python
def lambda_handler(event, context):
    ...
```
# Gamified OWASP Quiz Platform

## 🔄 Quiz Generation Flow (SQS + Bedrock + DynamoDB)

### 🧠 Components Overview

| Component       | Role                                                                 |
|----------------|----------------------------------------------------------------------|
| API Gateway `/generate-quiz` | Entry point for students to request a quiz               |
| **Submit Lambda** | Validates input, pushes job to SQS                                  |
| **SQS Queue (`quizgen`)** | Holds quiz generation requests until processed             |
| **quizgen Lambda** | Triggered by SQS, uses Bedrock agent to generate quiz content     |
| **DynamoDB Table** | Stores quiz status and results under a session ID                |

---

### 🔄 Flow Description

1. **Student requests a quiz** via `POST /generate-quiz`
2. **Submit Lambda** validates input, initializes `status: pending` in DynamoDB, and sends a message to SQS.
3. **SQS** delivers the message to **quizgen Lambda**.
4. **quizgen Lambda** calls the Bedrock agent with a prompt.
5. **Agent** returns questions, hints, and explanation.
6. **quizgen Lambda** updates DynamoDB with `status: completed` and the quiz content.
7. **Student** retrieves the quiz via `GET /quiz-result?sessionId=...`

✅ Retries and DLQ ensure failed quiz generations are logged and retryable.