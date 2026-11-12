from typing import Any

from app.agents.interview_state import InterviewState
from app.services.llm_service import GeminiLLMService


def plan_interview(state: InterviewState, llm_service: GeminiLLMService) -> InterviewState:
    prompt = f"""Create a focused interview plan as JSON. Use only the supplied candidate and job evidence.
Return keys: focus_areas (array of strings), question_types (array of strings), rationale (string).
Interview type: {state['interview_type']}
Difficulty: {state['difficulty']}
Questions: {state['question_count']}
Candidate evidence: {state.get('resume_context', '')}
Job evidence: {state.get('job_context', '')}
RAG evidence: {state.get('rag_context', [])}
"""
    plan = llm_service.generate_json(prompt)
    return {**state, "plan": plan}
