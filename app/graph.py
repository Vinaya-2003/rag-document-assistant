from langgraph.graph import StateGraph, END
from app.state import RAGState
from app.nodes.query_analysis import query_analysis_node
from app.nodes.retrieval import retrieval_node
from app.nodes.grader import grader_node
from app.nodes.generator import generator_node, fallback_node

MAX_RETRIES = 3

def route_after_grading(state: RAGState) -> str:
    relevant_count = len(state.get("relevant_docs", []))
    retry_count = state.get("retry_count", 0)

    if relevant_count > 0:
        print(f"[Router] {relevant_count} relevant docs found → Generating answer")
        return "generate"

    if retry_count < MAX_RETRIES:
        print(f"[Router] No relevant docs. Retry {retry_count + 1}/{MAX_RETRIES}")
        return "retry"

    print("[Router] Out of retries → Fallback response")
    return "fallback"

def increment_retry(state: RAGState) -> RAGState:
    return {**state, "retry_count": state.get("retry_count", 0) + 1}

def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("query_analysis", query_analysis_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("grader", grader_node)
    graph.add_node("generator", generator_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("increment_retry", increment_retry)

    graph.set_entry_point("query_analysis")
    graph.add_edge("query_analysis", "retrieval")
    graph.add_edge("retrieval", "grader")

    graph.add_conditional_edges(
        "grader",
        route_after_grading,
        {
            "generate": "generator",
            "retry": "increment_retry",
            "fallback": "fallback"
        }
    )

    graph.add_edge("increment_retry", "query_analysis")
    graph.add_edge("generator", END)
    graph.add_edge("fallback", END)

    return graph.compile()

rag_graph = build_graph()