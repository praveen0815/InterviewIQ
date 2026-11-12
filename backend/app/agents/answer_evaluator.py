from app.agents.interview_state import InterviewState
from app.services.llm_service import GeminiLLMService


def evaluate_answer(state: InterviewState, llm_service: GeminiLLMService) -> InterviewState:
    prompt = f"""Evaluate the candidate answer against the question and evidence. Use a 0-100 score
for each criterion and calculate score as the arithmetic mean of the six criteria.
Return JSON keys: score, technical_correctness, relevance, completeness, clarity,
problem_solving, communication, strengths, weaknesses, missing_concepts,
suggested_improved_answer, feedback. Scores must be evidence-based, not random.
Question: {state['current_question']}
Candidate answer: {state['current_answer']}
Candidate evidence: {state.get('resume_context', '')}
Job evidence: {state.get('job_context', '')}
"""
    result = llm_service.generate_json(prompt)
    criteria = [
        "technical_correctness", "relevance", "completeness", "clarity",
        "problem_solving", "communication",
    ]
    scores = [float(result.get(key, 0)) for key in criteria]
    if any(score < 0 or score > 100 for score in scores):
        raise ValueError("Answer evaluation scores must be between 0 and 100.")
    result["score"] = round(sum(scores) / len(scores), 2)
    return {**state, "evaluation": result}
