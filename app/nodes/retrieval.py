from app.ingest import get_vectorstore
from app.state import RAGState

def retrieval_node(state: RAGState) -> RAGState:
    vectorstore = get_vectorstore()
    query = state.get("rewritten_query") or state["question"]

    docs = vectorstore.similarity_search(query, k=4)

    retrieved = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown")
        }
        for doc in docs
    ]

    print(f"[Retrieval] Found {len(retrieved)} chunks for: '{query[:60]}'")

    return {**state, "retrieved_docs": retrieved}