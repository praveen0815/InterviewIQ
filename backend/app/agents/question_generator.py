from app.agents.interview_state import InterviewState
from app.services.llm_service import GeminiLLMService


def generate_question(state: InterviewState, llm_service: GeminiLLMService) -> InterviewState:
    prompt = f"""Generate the next single interview question as JSON.
Return keys: question and question_type. Do not generate an answer or multiple questions.
Use the candidate evidence, job requirements, interview plan, type, and difficulty.
Interview type: {state['interview_type']}
Difficulty: {state['difficulty']}
Plan: {state.get('plan', {})}
Candidate evidence: {state.get('resume_context', '')}
Job evidence: {state.get('job_context', '')}
RAG evidence: {state.get('rag_context', [])}
"""
    result = llm_service.generate_json(prompt)
    question = str(result.get("question", "")).strip()
    question_type = str(result.get("question_type", state["interview_type"]))
    if not question:
        raise ValueError("Question generation returned an empty question.")
    return {**state, "current_question": question, "current_question_type": question_type}
