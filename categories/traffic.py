from functools import lru_cache
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph

from categories.shared import get_vectorstore
from categories.traffic_content import (
    build_action_steps,
    build_checklist,
    build_expressions,
    build_final_answer,
    build_warnings,
    get_primary_source,
)
from categories.traffic_rules import (
    CATEGORY_NAME,
    DISPLAY_CATEGORY,
    GENERATION_ERROR_MESSAGE,
    NO_DOCS_WARNING,
    ROUTE_PRIORITY,
    SUB_FIXED_PLACE,
    SUB_TAXI,
    TRAFFIC_FILTER,
    analyze_traffic_input,
    can_handle_traffic,
    extract_destination_phrase,
)
from categories.types import CategoryResult
from prompts.traffic_prompts import (
    TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION,
    TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
    TRAFFIC_UNSUPPORTED_PLACE_QUESTION,
)


class TrafficState(TypedDict):
    user_input: str
    category: str
    sub_category: str
    needs_clarification: bool
    clarifying_question: str
    retrieved_docs: list[Document]
    sources: list[str]
    warnings: list[str]
    action_steps: list[str]
    checklist: list[str]
    expressions: list[str]
    origin: str
    destination: str
    mentioned_places: list[str]
    route_like: bool
    final_answer: str


def can_handle(user_input: str) -> bool:
    return can_handle_traffic(user_input)


def run_category(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    try:
        result = get_graph().invoke(build_initial_state(cleaned_input))
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    if result["needs_clarification"]:
        return CategoryResult.clarification(
            result["clarifying_question"],
            category=CATEGORY_NAME,
            sub_category=result["sub_category"],
            warnings=result["warnings"],
        )

    return CategoryResult.success(
        result["final_answer"],
        category=CATEGORY_NAME,
        sub_category=result["sub_category"],
        sources=result["sources"],
        warnings=result["warnings"],
    )


def build_initial_state(user_input: str) -> TrafficState:
    return {
        "user_input": user_input,
        "category": DISPLAY_CATEGORY,
        "sub_category": "",
        "needs_clarification": False,
        "clarifying_question": "",
        "retrieved_docs": [],
        "sources": [],
        "warnings": [],
        "action_steps": [],
        "checklist": [],
        "expressions": [],
        "origin": "",
        "destination": "",
        "mentioned_places": [],
        "route_like": False,
        "final_answer": "",
    }


def analyze_input_node(state: TrafficState) -> TrafficState:
    return {
        **state,
        **analyze_traffic_input(state["user_input"]),
    }


def route_after_analysis(state: TrafficState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"


def retrieve_node(state: TrafficState) -> TrafficState:
    try:
        docs = get_vectorstore().similarity_search(
            state["user_input"],
            k=3,
            filter=TRAFFIC_FILTER,
        )
    except RuntimeError:
        raise
    except Exception:
        docs = []

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources: list[str] = []
    primary_source = get_primary_source(state["sub_category"])
    if primary_source:
        sources.append(primary_source)

    for doc in docs:
        source = doc.metadata.get("source")
        if source and source not in sources:
            sources.append(source)

    return {
        **state,
        "retrieved_docs": docs,
        "warnings": warnings,
        "sources": sources,
    }


def place_check_node(state: TrafficState) -> TrafficState:
    mentioned_places = list(state["mentioned_places"])
    origin = state["origin"]
    destination = state["destination"]

    if len(mentioned_places) >= 2:
        origin = mentioned_places[0]
        destination = mentioned_places[1]
    elif len(mentioned_places) == 1:
        destination = mentioned_places[0]

    if state["sub_category"] == SUB_FIXED_PLACE:
        if not destination:
            return set_clarification(state, TRAFFIC_UNSUPPORTED_PLACE_QUESTION)
        if not origin:
            return set_clarification(state, TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION)

    if state["sub_category"] == SUB_TAXI and not destination:
        destination = extract_destination_phrase(state["user_input"])
        if not destination and state["route_like"]:
            return set_clarification(state, TRAFFIC_GENERIC_CLARIFICATION_QUESTION)

    return {
        **state,
        "origin": origin,
        "destination": destination,
    }


def route_after_place_check(state: TrafficState) -> str:
    return "final_node" if state["needs_clarification"] else "prepare_response_node"


def prepare_response_node(state: TrafficState) -> TrafficState:
    return {
        **state,
        "action_steps": build_action_steps(
            sub_category=state["sub_category"],
            origin=state["origin"],
            destination=state["destination"],
        ),
        "checklist": build_checklist(state["sub_category"]),
        "expressions": build_expressions(
            sub_category=state["sub_category"],
            origin=state["origin"],
            destination=state["destination"],
        ),
        "warnings": build_warnings(state["warnings"]),
    }


def final_node(state: TrafficState) -> TrafficState:
    if state["needs_clarification"]:
        return {
            **state,
            "final_answer": state["clarifying_question"],
        }

    return {
        **state,
        "final_answer": build_final_answer(
            sub_category=state["sub_category"],
            action_steps=state["action_steps"],
            checklist=state["checklist"],
            expressions=state["expressions"],
            warnings=state["warnings"],
            sources=state["sources"],
            origin=state["origin"],
            destination=state["destination"],
        ),
    }


def set_clarification(state: TrafficState, question: str) -> TrafficState:
    return {
        **state,
        "needs_clarification": True,
        "clarifying_question": question,
    }


def build_graph():
    graph = StateGraph(TrafficState)
    graph.add_node("analyze_input_node", analyze_input_node)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("place_check_node", place_check_node)
    graph.add_node("prepare_response_node", prepare_response_node)
    graph.add_node("final_node", final_node)

    graph.set_entry_point("analyze_input_node")
    graph.add_conditional_edges(
        "analyze_input_node",
        route_after_analysis,
        {
            "retrieve_node": "retrieve_node",
            "final_node": "final_node",
        },
    )
    graph.add_edge("retrieve_node", "place_check_node")
    graph.add_conditional_edges(
        "place_check_node",
        route_after_place_check,
        {
            "prepare_response_node": "prepare_response_node",
            "final_node": "final_node",
        },
    )
    graph.add_edge("prepare_response_node", "final_node")
    graph.add_edge("final_node", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()
