from typing import TypedDict, List

class RAGState(TypedDict):
    question: str
    rewritten_query: str
    query_type: str
    retrieved_docs: List[dict]
    relevant_docs: List[dict]
    answer: str
    sources: List[str]
    retry_count: int
    fallback: bool