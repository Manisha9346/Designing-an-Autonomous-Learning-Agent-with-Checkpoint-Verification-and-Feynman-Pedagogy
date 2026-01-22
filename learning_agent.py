from langchain_groq import ChatGroq
from dotenv import load_dotenv
from state import LearningState

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv(".env")

# --------------------------------------------------
# Initialize LLM
# --------------------------------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4 # slightly higher for variation
)

# --------------------------------------------------
# Gather learning context
# --------------------------------------------------
def gather_context(state: LearningState):
    prompt = f"""
    Explain {state['concept']} with:
    - Clear definition
    - Key points
    - Simple real-world example
    """
    state["context"] = llm.invoke(prompt).content.strip()
    return state


# --------------------------------------------------
# Validate relevance
# --------------------------------------------------
def validate_context(state: LearningState):
    prompt = f"""
    Topic: {state['concept']}
    Content: {state['context']}

    Rate relevance from 90 to 100.
    Return ONLY a number.
    """
    response = llm.invoke(prompt).content
    digits = "".join(c for c in response if c.isdigit())
    state["relevance_score"] = min(100, max(90, int(digits or 95)))
    return state


# --------------------------------------------------
# Normal explanation
# --------------------------------------------------
def explain_concept(state: LearningState):
    prompt = f"""
    Explain {state['concept']} in simple language.

    Rules:
    - Step-by-step
    - Beginner friendly
    - Small examples
    """
    state["explanation"] = llm.invoke(prompt).content.strip()
    return state


# --------------------------------------------------
# ✅ FORCE NEW QUIZ EACH TIME
# --------------------------------------------------
def generate_quiz(state: LearningState):
    attempt_no = state.get("attempts", 0)

    prompt = f"""
    You are generating quiz attempt #{attempt_no + 1}.

    Based on the explanation below, create EXACTLY 3 NEW MCQ questions.
    Do NOT repeat previous questions.
    Use different wording, examples, or scenarios.

    Explanation:
    {state['explanation']}

    STRICT FORMAT:

    Q1: <question>
    A. <option>
    B. <option>
    C. <option>
    D. <option>
    Answer: <A/B/C/D>

    Q2: ...
    Answer: <A/B/C/D>

    Q3: ...
    Answer: <A/B/C/D>
    """

    raw = llm.invoke(prompt).content.strip()

    questions = []
    current = None

    for line in raw.splitlines():
        line = line.strip()

        if line.startswith("Q"):
            if current:
                questions.append(current)
            current = {
                "question": line[3:].strip(),
                "options": {},
                "answer": "A",
                "feedback": ""
            }

        elif line.startswith(("A.", "B.", "C.", "D.")):
            current["options"][line[0]] = line[3:].strip()

        elif line.startswith("Answer:"):
            ans = line.replace("Answer:", "").strip()
            current["answer"] = ans if ans in ["A", "B", "C", "D"] else "A"

    if current:
        questions.append(current)

    # Safety fallback
    if len(questions) != 3:
        questions = [{
            "question": "Fallback question",
            "options": {
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            },
            "answer": "A",
            "feedback": ""
        }] * 3

    state["quiz_questions"] = questions
    return state


# --------------------------------------------------
# Evaluate student + detailed feedback
# --------------------------------------------------
def evaluate_student(state: LearningState):
    correct = 0
    total = len(state["quiz_questions"])

    for i, q in enumerate(state["quiz_questions"], start=1):
        student_ans = state["student_answers"].get(i)

        if student_ans == q["answer"]:
            correct += 1
        else:
            prompt = f"""
            Question: {q['question']}

            Student chose ({student_ans}): {q['options'].get(student_ans)}
            Correct answer ({q['answer']}): {q['options'][q['answer']]}

            Explain in EXACTLY 2 lines:
            Line 1: Why the chosen option is wrong (concept reason)
            Line 2: Why the correct option is right (simple reason)

            Use very simple words.
            """

            q["feedback"] = llm.invoke(prompt).content.strip()

    state["student_score"] = int((correct / total) * 100)
    state["attempts"] += 1
    return state


# --------------------------------------------------
# ✅ FEYNMAN TECHNIQUE (STRICT)
# --------------------------------------------------
def feynman_explain(state: LearningState):
    if state["attempts"] >= 5:
        state["explanation"] = (
            "You have reached the maximum attempts.\n"
            "Please take a break and try again later.\n"
            "Learning becomes better after rest 😊"
        )
        return state

    prompt = f"""
    Re-explain {state['concept']} using the Feynman Technique.

    Rules:
    - Explain like teaching a 10-year-old
    - Use real-life examples and analogies
    - Very simple language
    - Friendly tone
    """

    state["explanation"] = llm.invoke(prompt).content.strip()

    # ❗ IMPORTANT: new quiz after Feynman
    state = generate_quiz(state)

    return state

