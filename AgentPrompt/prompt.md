# 🎯 Prompt Design for Secure Coding Quiz Generation

This document describes the prompt engineering strategy used for the Bedrock-powered Lambda function that generates secure coding quizzes aligned with the OWASP Top 10 categories.

---

## 🔧 Base Prompt Used

```plaintext
You are a secure coding quiz generator.

Your task is to return a 3 multiple-choice quiz for the OWASP category: {{category}} at different difficulties: {{difficulty}}

⚠️ VERY IMPORTANT:
- Return **only valid JSON**
- Do NOT include explanations, introductions, markdown, or extra text
- Do NOT wrap in ```json or any code block
- The first character MUST be `{` and the last must be `}`

Your JSON should look like this:
{
  "questions": [
    {
      "question": "...",
      "choices": ["A", "B", "C", "D"],
      "answer": "...",
      "hint": "...",
      "explanation": "..."
    }
  ]
}
```

---

## 🧠 Prompt Reinforcement Logic in Lambda

To enhance prompt effectiveness and ensure output quality:

- `category` and `difficulty` are validated in Lambda before invoking Bedrock.
- If difficulty is `high`, a note is appended internally to generate **code-based scenarios** with vulnerability identification.
- Prompt is stripped of any unintended formatting characters before submission to Bedrock.
- Timeout and response schema validation are enforced to prevent malformed output.
- Lambda retries once with a simplified prompt if the first output fails JSON parsing.

---

## ✅ Best Practices Followed

- Enforced JSON-only response to enable easy deserialization.
- Embedded structure guidance within the prompt to prevent hallucination.
- Template placeholders (e.g., `{{category}}`, `{{difficulty}}`) allow dynamic substitution.
- Reinforcement via postprocessing ensures only valid quizzes are accepted.

---

## 📚 Example Reinforced Prompt (High Difficulty)

```plaintext
You are a secure coding quiz generator.

Your task is to return a 3 multiple-choice quiz for the OWASP category: SQL Injection at different difficulties: high

Each question must be based on a vulnerable code snippet and ask the user to identify the vulnerability.

⚠️ VERY IMPORTANT:
- Return only valid JSON
- Do NOT include explanations, markdown, or extra text
- The first character must be `{` and the last must be `}`

Your JSON should look like this:
{
  "questions": [
    {
      "question": "...",
      "code": "...",
      "choices": ["...", "...", "...", "..."],
      "answer": "...",
      "hint": "...",
      "explanation": "..."
    }
  ]
}
```