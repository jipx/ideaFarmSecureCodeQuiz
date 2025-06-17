import streamlit as st
import json

st.set_page_config(page_title="Answer History Dashboard", layout="centered")
st.title("📊 Answer History Dashboard")

try:
    with open("history.json", "r") as f:
        history = json.load(f)["answers"]
except FileNotFoundError:
    history = []

if history:
    st.markdown(f"Total submissions: {len(history)}")
    for record in reversed(history[-10:]):
        st.markdown(f"""
- **User ID:** {record["userId"]}
- **Session ID:** `{record["sessionId"]}`
- **Category:** {record["category"]}
- **Difficulty:** {record["difficulty"]}
- **Score:** {record["score"]} / {record["total"]}
- **Timestamp:** {record["timestamp"]}
---""")
else:
    st.info("No answer history found yet.")