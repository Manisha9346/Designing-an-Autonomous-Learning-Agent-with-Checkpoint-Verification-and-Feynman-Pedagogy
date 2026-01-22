import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from checkpoints import CHECKPOINTS
from learning_agent import (
    gather_context,
    validate_context,
    explain_concept,
    generate_quiz,
    evaluate_student,
    feynman_explain
)

from database import (
    init_db,
    save_progress,
    load_progress_by_user
)

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(page_title="AI Learning Agent", layout="wide")
init_db()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.title("🎓 AI Personalized Learning Agent")
    st.caption("Learn • Practice • Improve")

    username = st.text_input("👤 Enter your name to continue")

    if st.button("Login") and username.strip():
        st.session_state.username = username.strip()
        st.rerun()

    st.stop()

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = None

# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------
st.sidebar.title("📚 Dashboard")
st.sidebar.success(f"👋 {st.session_state.username}")

page = st.sidebar.radio(
    "Navigation",
    ["📘 Learn", "📊 Progress", "🏅 Badges"]
)

# ==================================================
# PAGE: LEARN
# ==================================================
if page == "📘 Learn":
    st.title("📘 Learn a Concept")

    concept = st.selectbox("Choose a topic", ["Select"] + CHECKPOINTS)

    # -------- INITIAL LOAD --------
    if concept != "Select" and st.session_state.state is None:
        st.session_state.state = {
            "concept": concept,
            "context": "",
            "relevance_score": 0,
            "explanation": "",
            "quiz_questions": [],
            "student_answers": {},
            "student_score": 0,
            "attempts": 0
        }

        state = st.session_state.state
        state = gather_context(state)
        state = validate_context(state)
        state = explain_concept(state)
        state = generate_quiz(state)

        st.session_state.state = state

    # -------- ACTIVE LEARNING --------
    if st.session_state.state:
        state = st.session_state.state

        if state["attempts"] >= 5:
            st.error("🚫 Maximum attempts reached. Try again later.")
            save_progress(
                st.session_state.username,
                state["concept"],
                state["student_score"],
                state["attempts"]
            )
            st.session_state.state = None
            st.stop()

        st.success(f"📊 Context Relevance: {state['relevance_score']} / 100")
        st.caption(f"Attempt {state['attempts'] + 1} / 5")

        # ---------------- Explanation ----------------
        st.markdown("## 🧠 Explanation")
        st.write(state["explanation"])

        # ---------------- Quiz ----------------
        st.markdown("## 📝 Quiz")
        state["student_answers"] = {}

        for idx, q in enumerate(state["quiz_questions"], start=1):
            st.markdown(f"**Q{idx}. {q['question']}**")

            selected = st.radio(
                label="Choose one option",
                options=list(q["options"].values()),
                key=f"attempt_{state['attempts']}_q{idx}"
            )

            for k, v in q["options"].items():
                if v == selected:
                    state["student_answers"][idx] = k

        # ---------------- Submit ----------------
        if st.button("Submit Quiz"):
            state = evaluate_student(state)

            save_progress(
                st.session_state.username,
                state["concept"],
                state["student_score"],
                state["attempts"]
            )

            st.divider()
            st.info(f"📊 Score: {state['student_score']} / 100")

            # ---------- FEEDBACK ----------
            st.markdown("### 🧾 Feedback")

            for idx, q in enumerate(state["quiz_questions"], start=1):
                student_ans = state["student_answers"].get(idx)

                if student_ans == q["answer"]:
                    st.success(f"✔ Q{idx}: Correct")
                else:
                    st.error(f"❌ Q{idx}: Incorrect")
                    st.markdown("**Explanation:**")
                    st.write(q.get("feedback", "Explanation unavailable"))

            # ---------- RETRY ----------
            if state["student_score"] < 70:
                if st.button("🔁 Retry with Simple Explanation (Feynman)"):
                    state = feynman_explain(state)
                    st.session_state.state = state
                    st.rerun()
            else:
                st.success("🎉 You mastered this concept!")
                st.session_state.state = None

# ==================================================
# PAGE: PROGRESS
# ==================================================
if page == "📊 Progress":
    st.title("📊 Learning Progress")

    data = load_progress_by_user(st.session_state.username)

    if not data:
        st.info("No progress yet. Start learning!")
    else:
        df = pd.DataFrame(
            data,
            columns=["Concept", "Score", "Attempts", "Status", "Badge"]
        )

        st.dataframe(df, use_container_width=True)

        st.markdown("### 📈 Score Trend")
        fig, ax = plt.subplots()
        ax.plot(df["Score"], marker="o")
        ax.set_xlabel("Attempts")
        ax.set_ylabel("Score")
        st.pyplot(fig)

# ==================================================
# PAGE: BADGES
# ==================================================
if page == "🏅 Badges":
    st.title("🏆 Your Achievements")

    data = load_progress_by_user(st.session_state.username)

    if not data:
        st.info("No badges earned yet.")
    else:
        for d in data:
            st.success(f"{d[0]} → {d[4]}")

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("---")
st.caption("🌱 Keep learning. Every attempt makes you better.")
