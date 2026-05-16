# RAG Documentation Assistant

A self-corrective Retrieval-Augmented Generation (RAG) system built with LangGraph and FastAPI. It answers questions about technical documentation accurately, cites its sources, and honestly says "I don't know" instead of making things up.

---

## What This Project Does

Think of this system like a smart librarian who has read every document you gave it.

When you ask a question, it does not just guess an answer. Instead it goes through these steps every single time:

1. Rewrites your question to make it easier to search
2. Searches through the documents to find the most relevant pages
3. Checks each page to verify it actually answers your question
4. Writes a clear answer using only what it found, with citations
5. If nothing useful is found, it retries up to 3 times with different search terms
6. If it still finds nothing, it honestly says it could not find the answer

This approach prevents the biggest problem with AI systems which is making up incorrect information.

---

## Architecture
+---------------------------+
|       User Question       |
+---------------------------+
|
v
+---------------------------+
|   Node 1: Query Analysis  |
|                           |
|  Rewrites the question    |
|  to improve search        |
|                           |
|  Classifies intent as     |
|  how-to, conceptual,      |
|  troubleshooting, or      |
|  api-reference            |
+---------------------------+
|
v
+---------------------------+
|    Node 2: Retrieval      |
|                           |
|  Searches ChromaDB using  |
|  vector similarity        |
|                           |
|  Returns top 4 most       |
|  relevant chunks with     |
|  source metadata          |
+---------------------------+
|
v
+---------------------------+
|  Node 3: Document Grading |
|                           |
|  LLM grades each chunk    |
|  as relevant or not       |
|                           |
|  Filters out irrelevant   |
|  chunks before generation |
+---------------------------+
|
|
|             |
v             v
Relevant       Not relevant
docs found     docs found
|             |
v             v
+----------+    Retry count
| Node 4:  |    below 3?
| Generate |         |
|          |        YES
| Creates  |         |
| answer   |    Back to Node 1
| with     |    with different
| citations|    search terms
+----------+         |
|            NO
v             |
Final answer       v
returned to   +----------+
user          | Fallback |
|          |
| Honestly |
| says I   |
| don't    |
| know     |
+----------+
---

## LangGraph State

A shared state bag travels through every node in the graph. Each node reads from it and writes back its results.

| Field | Type | Description |
|---|---|---|
| question | string | Original user question |
| rewritten_query | string | Improved version for search |
| query_type | string | how-to, conceptual, troubleshooting, api-reference |
| retrieved_docs | list | Raw chunks returned from ChromaDB |
| relevant_docs | list | Chunks that passed the grading check |
| answer | string | Final generated answer |
| sources | list | Document filenames that were cited |
| retry_count | int | Number of retries attempted, max 3 |
| fallback | bool | True if system could not find an answer |

---

## Free Tech Stack

Everything in this project is free. No credit card required.

| Component | Tool | Why |
|---|---|---|
| LLM | Groq API with Llama 3.1 8b | Generous free tier, very fast inference |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Runs locally, zero API cost, 80MB model |
| Vector Database | ChromaDB | Runs locally, open source, no setup needed |
| Workflow Graph | LangGraph | Open source, built for agent workflows |
| API Framework | FastAPI | Open source, auto-generates docs at /docs |
| Chat UI | Streamlit | Open source, runs in browser instantly |

---

## Project Structure
rag-document-assistant/
├── app/
│   ├── nodes/
│   │   ├── init.py
│   │   ├── query_analysis.py   # Node 1: rewrites and classifies the query
│   │   ├── retrieval.py        # Node 2: searches ChromaDB for similar chunks
│   │   ├── grader.py           # Node 3: grades each chunk as relevant or not
│   │   └── generator.py        # Node 4: generates cited answer or fallback
│   ├── init.py
│   ├── state.py                # Shared state schema that flows between nodes
│   ├── ingest.py               # Document loading, chunking, embedding, storage
│   ├── graph.py                # LangGraph workflow, routing, and retry logic
│   ├── main.py                 # FastAPI application with all endpoints
│   └── streamlit_app.py        # Streamlit chat interface
├── docs/
│   ├── fastapi_basics.md       # FastAPI documentation corpus
│   ├── pydantic_basics.md      # Pydantic documentation corpus
│   └── langchain_basics.md     # LangChain documentation corpus
├── .gitignore                  # Protects API keys and venv from being uploaded
├── requirements.txt            # All Python dependencies
└── README.md                   # This file
---

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- A free Groq API key from https://console.groq.com/keys

### 1. Clone the repository
```bash
git clone https://github.com/Vinaya-2003/rag-document-assistant.git
cd rag-document-assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install all dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your environment file
Create a file called `.env` in the root folder and add your Groq API key:
GROQ_API_KEY=your_groq_key_here
Get your free key at https://console.groq.com/keys

### 5. Ingest the documents
This step loads the documents, splits them into chunks, generates embeddings, and saves everything to ChromaDB. Run it once before starting the server.
```bash
python -m app.ingest
```

You should see:
Loaded 3 documents from ./docs
Split into 18 chunks
Ingested 18 chunks into ChromaDB at ./chroma_db
### 6. Start the FastAPI server
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Start the Streamlit UI
Open a second terminal, activate venv, then run:
```bash
streamlit run app/streamlit_app.py
```

### 8. Open the app
Go to http://localhost:8501 in your browser to use the chat interface.

To test the raw API go to http://127.0.0.1:8000/docs

---

## API Endpoints

### POST /query
Submit a question and receive an answer with source citations.

Request:
```json
{
  "question": "How do I create a GET endpoint in FastAPI?"
}
```

Response:
```json
{
  "answer": "To create a GET endpoint in FastAPI, use the @app.get() decorator. [Source: fastapi_basics.md]",
  "sources": ["fastapi_basics.md"],
  "query_type": "how-to",
  "retry_count": 0,
  "fallback": false
}
```

### POST /ingest
Upload a new .txt or .md file to add it to the knowledge base without restarting the server.

### GET /documents
List all documents currently indexed in ChromaDB and the total number of chunks.

Response:
```json
{
  "total_chunks": 18,
  "documents": ["fastapi_basics.md", "pydantic_basics.md", "langchain_basics.md"]
}
```

### POST /feedback
Submit thumbs up or down feedback on an answer with an optional comment.

Request:
```json
{
  "question": "How do I create a GET endpoint?",
  "answer": "Use the @app.get() decorator...",
  "thumbs_up": true,
  "comment": "Very helpful and accurate"
}
```

### GET /health
Check that the server is running and see which models are loaded.

Response:
```json
{
  "status": "ok",
  "model": "llama-3.1-8b-instant",
  "vector_db": "ChromaDB",
  "embedding": "all-MiniLM-L6-v2"
}
```

---

## Real Example Responses

### When the answer is in the documents
```json
{
  "question": "How do I create a POST endpoint in FastAPI?",
  "answer": "To create a POST endpoint in FastAPI, use the @app.post() decorator with a Pydantic model for the request body. [Source: fastapi_basics.md]",
  "sources": ["fastapi_basics.md"],
  "query_type": "how-to",
  "retry_count": 0,
  "fallback": false
}
```

### When the topic is not in the documents
```json
{
  "question": "How do I make a pizza?",
  "answer": "I could not find relevant information in the documentation to answer this question. Please try rephrasing or check if this topic is covered in the loaded documents.",
  "sources": [],
  "query_type": "how-to",
  "retry_count": 3,
  "fallback": true
}
```

---

## Design Decisions and Tradeoffs

### Why Groq instead of OpenAI?
Groq provides a generous free tier with no credit card required. Its Llama 3.1 8b model is fast enough for real-time responses and accurate enough for document grading and answer generation.

### Why run embeddings locally with HuggingFace?
Running the all-MiniLM-L6-v2 model locally means zero embedding API costs and no rate limits. The model is only 80MB, downloads once, and runs on CPU without any GPU needed.

### Why ChromaDB instead of Pinecone?
ChromaDB runs entirely on your local machine with no account, no API key, and no size limits for small corpora. It persists data to disk so the embeddings survive server restarts without needing to re-ingest.

### Why chunk size 512 with 50 overlap?
Chunks that are too large include irrelevant content that confuses the LLM. Chunks that are too small lose important context. 512 characters balances both. The 50 character overlap ensures that answers spanning chunk boundaries are never lost at the seams.

### Token efficiency strategy
The system is designed to use the minimum tokens necessary at each step to keep API costs near zero.

- Query analysis uses max_tokens of 200 because it only needs a short rewrite
- Document grading uses max_tokens of 10 because the answer is just yes or no
- Answer generation uses max_tokens of 600 for a complete detailed response

Grading 4 chunks costs almost nothing because each call uses only 10 tokens for the output.

### Why document grading matters
Vector similarity search finds text that is mathematically similar, not always contextually relevant. For example searching for "list all endpoints" might return a chunk about Python lists because both contain the word "list". The LLM grader catches these false positives and removes them before they reach the answer generator. This is what prevents hallucination.

### Self-corrective retry loop
If all chunks are graded as irrelevant, the system does not give up immediately. It rewrites the query differently and searches again up to 3 times. Only after exhausting all retries does it return an honest fallback response. This makes the system much more robust than a simple one-shot retrieval pipeline.

---

## What I Would Improve With More Time

- Add conversation memory so users can ask follow-up questions
- Add a hallucination checker node that verifies the answer is supported by the retrieved context, inspired by Self-RAG
- Add web search fallback using Tavily so the system can answer questions not covered by the documents
- Support PDF document ingestion using PyMuPDF
- Store feedback responses in a SQLite database for analysis and fine-tuning
- Add user authentication to the API endpoints
- Deploy the FastAPI backend on Render and the Streamlit UI on Streamlit Cloud for public access

---

## Assumptions Made

- All documents are written in English
- Users ask one question at a time without follow-up context
- The docs folder contains only .txt and .md files
- ChromaDB local storage is sufficient for the document corpus size
- The Groq free tier is sufficient for the expected query volume during evaluation

---

## Chunking Strategy

The project uses RecursiveCharacterTextSplitter from LangChain with a chunk size of 512 characters and an overlap of 50 characters.

This splitter tries to divide text at natural boundaries in this order: paragraph breaks, then sentence endings, then word boundaries, and finally individual characters as a last resort. This preserves meaning better than splitting at fixed character positions regardless of content.

Technical content like code examples generally stays intact because most code blocks in documentation are under 512 characters. The overlap ensures that if an answer spans two chunks, both chunks contain enough shared context for the retrieval system to find them.
