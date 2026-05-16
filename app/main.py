import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from app.graph import rag_graph
from app.state import RAGState
from app.ingest import ingest, get_vectorstore, DOCS_PATH

load_dotenv()

app = FastAPI(
    title="RAG Documentation Assistant",
    description="Self-corrective RAG powered by LangGraph and Groq",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    query_type: str
    retry_count: int
    fallback: bool

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    thumbs_up: bool
    comment: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    initial_state: RAGState = {
        "question": request.question,
        "rewritten_query": "",
        "query_type": "",
        "retrieved_docs": [],
        "relevant_docs": [],
        "answer": "",
        "sources": [],
        "retry_count": 0,
        "fallback": False
    }

    try:
        final_state = rag_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    return QueryResponse(
        answer=final_state["answer"],
        sources=final_state["sources"],
        query_type=final_state.get("query_type", "unknown"),
        retry_count=final_state.get("retry_count", 0),
        fallback=final_state.get("fallback", False)
    )

@app.post("/ingest")
async def ingest_docs(file: UploadFile = File(...)):
    if not file.filename.endswith((".txt", ".md")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported"
        )

    save_path = os.path.join(DOCS_PATH, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ingest()
    return {"message": f"Ingested {file.filename} successfully"}

@app.get("/documents")
async def list_documents():
    try:
        vs = get_vectorstore()
        collection = vs._collection.get()
        sources = list(set(
            m.get("source", "unknown").split("\\")[-1].split("/")[-1]
            for m in collection.get("metadatas", [])
        ))
        return {
            "total_chunks": len(collection.get("ids", [])),
            "documents": sources
        }
    except Exception as e:
        return {"error": str(e), "documents": []}

@app.post("/feedback")
async def feedback(fb: FeedbackRequest):
    emoji = "👍" if fb.thumbs_up else "👎"
    print(f"[Feedback] {emoji} | Q: {fb.question[:50]} | Comment: {fb.comment or 'none'}")
    return {"message": "Feedback received, thank you!"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "llama-3.1-8b-instant",
        "vector_db": "ChromaDB",
        "embedding": "all-MiniLM-L6-v2"
    }