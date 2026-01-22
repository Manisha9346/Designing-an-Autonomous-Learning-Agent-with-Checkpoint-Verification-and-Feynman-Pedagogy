from typing import TypedDict

# Shared state used by the agent
class LearningState(TypedDict):
    concept: str
    context: str
    relevance_score: int
    explanation: str
    quiz: str
    correct_answers: str
    student_answers: str
    student_score: int
    attempts: int
