import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

st.set_page_config(page_title="📊 Quiz Dashboard", layout="wide")
st.title("📊 OWASP Quiz Dashboard")

# Load history
try:
    with open("history.json", "r") as f:
        history = json.load(f)["answers"]
except FileNotFoundError:
    st.warning("No quiz history found.")
    st.stop()

df = pd.DataFrame(history)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["score_percent"] = df["score"] / df["total"] * 100

# Filter sidebar
st.sidebar.header("🔍 Filters")
selected_user = st.sidebar.selectbox("Filter by User ID", ["All"] + sorted(df["userId"].unique().tolist()))
selected_difficulty = st.sidebar.multiselect("Select Difficulty Level", df["difficulty"].unique(), default=list(df["difficulty"].unique()))

# Apply filters
if selected_user != "All":
    df = df[df["userId"] == selected_user]
if selected_difficulty:
    df = df[df["difficulty"].isin(selected_difficulty)]

# --- Pie chart: Attempts by category ---
st.subheader("📊 Quiz Attempts by OWASP Category")
category_counts = df["category"].value_counts()
fig1, ax1 = plt.subplots()
ax1.pie(category_counts, labels=category_counts.index, autopct="%1.1f%%", startangle=140)
ax1.axis("equal")
st.pyplot(fig1)

# --- Bar chart: Average score per category ---
st.subheader("📈 Average Scores by Category and Difficulty")

fig2, ax2 = plt.subplots(figsize=(10, 6))
sns.barplot(data=df, x="score_percent", y="category", hue="difficulty", ax=ax2)
ax2.set_xlabel("Average Score (%)")
ax2.set_ylabel("Category")
ax2.set_title("Average Scores by OWASP Category and Difficulty")
st.pyplot(fig2)

# --- Data Table ---
st.subheader("📋 Score Summary Table")
summary_table = df.groupby(["category", "difficulty"]).agg(
    Attempts=("score", "count"),
    Avg_Score_Percent=("score_percent", "mean")
).reset_index()

st.dataframe(summary_table)
