
# OWASP Quiz Generator – Streamlit Client

This Streamlit application allows users to:
- Generate quizzes on OWASP Top 10 topics
- Choose difficulty levels (Low, Medium, High)
- Submit answers and get instant feedback
- Download quizzes in JSON format
- View quiz attempt history in a dashboard

---

## 📁 Project Structure

```
streamlit_quiz_app/
├── app.py                     # Streamlit client application
├── history.json              # Local storage for past answers and scores
├── requirements.txt          # Required Python libraries
└── .streamlit/
    └── config.toml           # Configuration with API base URL
```

---

## 🚀 How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API endpoint** in `.streamlit/config.toml`:
   ```toml
   [api]
   base_url = "https://your-api-id.execute-api.region.amazonaws.com/prod"
   ```

3. **Launch the app**:
   ```bash
   streamlit run app.py
   ```

---

## 📦 Features

- **Category selection** from OWASP Top 10
- **Difficulty levels** with mapped internal values
- **Answer feedback** and scoring
- **Downloadable quiz** as JSON
- **Dashboard** showing last 10 submissions

---

## 🛠 Optional Enhancements

- Save quiz history to a backend or S3
- Integrate with Cognito for authentication
- Add filters or CSV export to dashboard

---

Built for secure coding education and OWASP quiz automation.


---

## 🚀 Deployment Options

### ✅ Deploy to Streamlit Cloud

1. Push this project to a public GitHub repository.
2. Visit: [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Click **“New App”** and select your GitHub repo.
4. Choose `app.py` as the main file.
5. Click **Deploy**.

### 🐳 Run with Docker (Optional)

1. Create a `Dockerfile`:
   ```Dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. Build and run:
   ```bash
   docker build -t owasp-quiz .
   docker run -p 8501:8501 owasp-quiz
   ```

---

## 🔐 Notes

- This client depends on a backend API (Lambda + API Gateway) with `/submit` and `/result/{sessionId}` endpoints.
- Configure your `config.toml` with the correct base URL before deployment.
