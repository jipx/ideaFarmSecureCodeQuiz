import streamlit as st
import requests
import time
import toml
import json



# ✅ Load API base from Streamlit secret
API_BASE = st.secrets["api"]["base_url"]



st.set_page_config(page_title="OWASP Quiz Generator", layout="centered")
st.title("☁️ OWASP Quiz Generator")

# --- Submission Form ---
with st.form("quiz_form"):
    user_id = st.text_input("User ID", value="student001")

    category = st.selectbox("Select OWASP Category", [
        "Broken Access Control", "Broken Authentication", "Insecure Deserialization",
        "Insufficient Logging & Monitoring", "SQL Injection", "Security Misconfiguration",
        "Sensitive Data Exposure", "Server-Side Request Forgery",
        "Using Components with Known Vulnerabilities", "XSS"
    ])

    difficulty_label = st.selectbox("Select Difficulty Level", ["Low", "Medium", "High"])
    difficulty = difficulty_label.lower()
    submitted = st.form_submit_button("Generate Quiz")

if submitted:
    with st.spinner("Submitting..."):
        try:
            submit_payload = {
                "userId": user_id, "category": category, "difficulty": difficulty
            }
            submit_response = requests.post(f"{API_BASE}/generate-quiz", json=submit_payload)
            if submit_response.status_code != 200:
                st.error("❌ Failed to submit request.")
            else:
                session_id = submit_response.json().get("sessionId", "")
                st.success(f"✅ Session created! ID: {session_id}")
                st.session_state.session_id = session_id
        except Exception as e:
            st.exception(e)

# --- Result Section ---
if "session_id" in st.session_state:
    session_id = st.session_state.session_id
    st.subheader("📥 Quiz Result")
    quiz_result = None

    with st.spinner("⏳ Waiting for quiz generation..."):
        for _ in range(10):
            try:
                result_response = requests.get(f"{API_BASE}/quiz-result/", params={"sessionId": session_id})
            except Exception as e:
                st.error(f"❌ Exception during fetch: {e}")
                break

            if result_response.status_code == 200:
                data = result_response.json()
                status = data.get("status", "unknown")

                if status == "completed":
                    st.success("✅ Quiz is ready!")
                    quiz_result = data.get("quiz", {})
                    break
                elif status == "pending":
                    time.sleep(2)
                else:
                    st.error(f"❌ Unexpected status: {status}")
                    break
            else:
                st.error("❌ Failed to fetch result from server.")
                break

    if not quiz_result:
        st.warning("⚠️ Quiz not ready yet.")
        if st.button("🔄 Retry Now"):
            st.rerun()

    if quiz_result:
        user_answers = {}
        with st.form("answer_form"):
            for i, q in enumerate(quiz_result["questions"], 1):
                st.markdown(f"**Q{i}. {q['question']}**")
                selected = st.radio(f"Your Answer (Q{i})", q["options"], key=f"q{i}")
                user_answers[q["question"]] = selected
            answer_submitted = st.form_submit_button("Check My Answers")

        if answer_submitted:
            correct = 0
            st.subheader("📝 Results")
            for i, q in enumerate(quiz_result["questions"], 1):
                user_ans = user_answers[q["question"]]
                correct_ans = q["answer"]
                st.markdown(f"**Q{i}: {q['question']}**")
                st.markdown(f"- Your answer: {user_ans}")
                st.markdown(f"- Correct answer: {correct_ans}")
                if user_ans == correct_ans:
                    st.success("✅ Correct")
                    correct += 1
                else:
                    st.error("❌ Incorrect")
            st.info(f"Score: {correct} / {len(quiz_result['questions'])}")

            try:
                with open("history.json", "r") as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = {"answers": []}

            history["answers"].append({
                "sessionId": session_id, "userId": user_id, "category": category,
                "difficulty": difficulty, "score": correct,
                "total": len(quiz_result["questions"]),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

            with open("history.json", "w") as f:
                json.dump(history, f, indent=2)

            st.download_button(
                label="📄 Download Quiz as JSON",
                file_name=f"quiz_{session_id}.json",
                mime="application/json",
                data=json.dumps(quiz_result, indent=2)
            )
