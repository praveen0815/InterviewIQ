from app.agents.interview_state import InterviewState
from app.services.llm_service import GeminiLLMService


def generate_followup(state: InterviewState, llm_service: GeminiLLMService) -> InterviewState:
    prompt = f"""Generate one concise next interview question as JSON.
Return keys: question and question_type. Ask a relevant follow-up only when the answer
has an important gap; otherwise ask the next planned question. Never ask two questions.
Current question: {state['current_question']}
Answer evaluation: {state.get('evaluation', {})}
Plan: {state.get('plan', {})}
"""
    result = llm_service.generate_json(prompt)
    question = str(result.get("question", "")).strip()
    if not question:
        raise ValueError("Follow-up generation returned an empty question.")
    return {
        **state,
        "current_question": question,
        "current_question_type": str(result.get("question_type", state["interview_type"])),
    }
