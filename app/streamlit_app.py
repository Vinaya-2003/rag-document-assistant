import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

from app.ingest import ingest, get_vectorstore, DOCS_PATH
from app.graph import rag_graph
from app.state import RAGState

st.set_page_config(page_title="RAG Documentation Assistant", layout="centered")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0f0f0f; }
        h1 { font-size: 1.6rem; font-weight: 600; color: #ffffff; letter-spacing: -0.5px; }
        .subtitle { font-size: 0.85rem; color: #666666; margin-bottom: 2rem; }
        .source-tag { display: inline-block; background: #1a1a1a; border: 1px solid #2a2a2a; color: #888888; font-size: 0.75rem; padding: 2px 10px; border-radius: 20px; margin-right: 6px; margin-top: 6px; }
        .meta-row { font-size: 0.75rem; color: #555555; margin-top: 6px; }
        .fallback-tag { color: #cc6666; font-size: 0.75rem; }
        .success-tag { color: #66aa88; font-size: 0.75rem; }
        .stButton button { background-color: #1a1a1a; color: #aaaaaa; border: 1px solid #2a2a2a; border-radius: 6px; font-size: 0.8rem; padding: 4px 14px; }
        .sidebar-title { font-size: 0.8rem; font-weight: 600; color: #888888; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem; }
        .doc-item { font-size: 0.82rem; color: #aaaaaa; padding: 4px 0; border-bottom: 1px solid #1e1e1e; }
        .chunk-count { font-size: 0.75rem; color: #555555; }
        div[data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #1e1e1e; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>RAG Documentation Assistant</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Ask questions about FastAPI, Pydantic, and LangChain</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}
if "ingested" not in st.session_state:
    with st.spinner("Loading knowledge base..."):
        ingest()
    st.session_state.ingested = True

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message:
            if message["sources"]:
                sources_html = "".join([
                    f'<span class="source-tag">{s}</span>'
                    for s in message["sources"]
                ])
                st.markdown(sources_html, unsafe_allow_html=True)
            if message.get("fallback"):
                status = '<span class="fallback-tag">no result found</span>'
            else:
                status = '<span class="success-tag">answered from docs</span>'
            st.markdown(
                f'<div class="meta-row">type: {message.get("query_type", "unknown")} &nbsp;|&nbsp; retries: {message.get("retry_count", 0)} &nbsp;|&nbsp; {status}</div>',
                unsafe_allow_html=True
            )
            if i not in st.session_state.feedback_given:
                col_a, col_b, col_c = st.columns([1, 1, 8])
                with col_a:
                    if st.button("yes", key=f"up_{i}"):
                        st.session_state.feedback_given[i] = "helpful"
                        st.rerun()
                with col_b:
                    if st.button("no", key=f"down_{i}"):
                        st.session_state.feedback_given[i] = "not helpful"
                        st.rerun()
            else:
                st.markdown(
                    f'<div class="meta-row">feedback: {st.session_state.feedback_given[i]}</div>',
                    unsafe_allow_html=True
                )

# Sidebar
with st.sidebar:
    st.markdown('<p class="sidebar-title">Loaded Documents</p>', unsafe_allow_html=True)
    try:
        vs = get_vectorstore()
        collection = vs._collection.get()
        sources = list(set(
            m.get("source", "unknown").split("\\")[-1].split("/")[-1]
            for m in collection.get("metadatas", [])
        ))
        total = len(collection.get("ids", []))
        st.markdown(f'<p class="chunk-count">{total} chunks indexed</p>', unsafe_allow_html=True)
        for doc in sources:
            st.markdown(f'<div class="doc-item">{doc}</div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<p class="chunk-count">Loading...</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p class="sidebar-title">Upload Document</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Accepts .txt or .md", type=["txt", "md"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Add to knowledge base"):
            save_path = os.path.join(DOCS_PATH, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            with st.spinner("Ingesting..."):
                ingest()
            st.success("Done")
            st.rerun()

    st.divider()
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.session_state.feedback_given = {}
        st.rerun()

    st.divider()
    st.markdown('<p class="chunk-count">LangGraph · FastAPI · Groq · ChromaDB</p>', unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask anything about the documentation"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                initial_state: RAGState = {
                    "question": prompt,
                    "rewritten_query": "",
                    "query_type": "",
                    "retrieved_docs": [],
                    "relevant_docs": [],
                    "answer": "",
                    "sources": [],
                    "retry_count": 0,
                    "fallback": False
                }
                final_state = rag_graph.invoke(initial_state)
                answer = final_state["answer"]
                sources = final_state["sources"]
                query_type = final_state.get("query_type", "unknown")
                retry_count = final_state.get("retry_count", 0)
                fallback = final_state.get("fallback", False)

                st.markdown(answer)

                if sources:
                    sources_html = "".join([
                        f'<span class="source-tag">{s}</span>'
                        for s in sources
                    ])
                    st.markdown(sources_html, unsafe_allow_html=True)

                if fallback:
                    status = '<span class="fallback-tag">no result found</span>'
                else:
                    status = '<span class="success-tag">answered from docs</span>'
                st.markdown(
                    f'<div class="meta-row">type: {query_type} &nbsp;|&nbsp; retries: {retry_count} &nbsp;|&nbsp; {status}</div>',
                    unsafe_allow_html=True
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "query_type": query_type,
                    "retry_count": retry_count,
                    "fallback": fallback
                })
            except Exception as e:
                st.error(f"Error: {str(e)}")