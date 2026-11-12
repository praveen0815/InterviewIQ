from typing import Callable

from app.agents.answer_evaluator import evaluate_answer
from app.agents.followup_generator import generate_followup
from app.agents.interview_planner import plan_interview
from app.agents.interview_state import InterviewState
from app.agents.interviewer import display_question
from app.agents.question_generator import generate_question
from app.services.llm_service import GeminiLLMService


class _Invokable:
    def __init__(self, function: Callable[[InterviewState], InterviewState]) -> None:
        self._function = function

    def invoke(self, state: InterviewState) -> InterviewState:
        return self._function(state)


def _build_fallback(llm_service: GeminiLLMService) -> Callable[[InterviewState], InterviewState]:
    def run(state: InterviewState) -> InterviewState:
        state = plan_interview(state, llm_service)
        state = generate_question(state, llm_service)
        return display_question(state)
    return _Invokable(run)


def build_interview_graph(llm_service: GeminiLLMService):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return _build_fallback(llm_service)

    graph = StateGraph(InterviewState)
    graph.add_node("plan_interview", lambda state: plan_interview(state, llm_service))
    graph.add_node("generate_question", lambda state: generate_question(state, llm_service))
    graph.add_node("display_question", display_question)
    graph.add_edge(START, "plan_interview")
    graph.add_edge("plan_interview", "generate_question")
    graph.add_edge("generate_question", "display_question")
    graph.add_edge("display_question", END)
    return graph.compile()


def build_answer_graph(llm_service: GeminiLLMService):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return _Invokable(
            lambda state: generate_followup(evaluate_answer(state, llm_service), llm_service)
        )

    graph = StateGraph(InterviewState)
    graph.add_node("evaluate_answer", lambda state: evaluate_answer(state, llm_service))
    graph.add_node("generate_followup", lambda state: generate_followup(state, llm_service))
    graph.add_edge(START, "evaluate_answer")
    graph.add_edge("evaluate_answer", "generate_followup")
    graph.add_edge("generate_followup", END)
    return graph.compile()
