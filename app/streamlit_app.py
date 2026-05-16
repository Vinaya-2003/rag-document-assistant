import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}

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
                        requests.post(f"{API_URL}/feedback", json={
                            "question": st.session_state.messages[i-1]["content"],
                            "answer": message["content"],
                            "thumbs_up": True
                        })
                        st.session_state.feedback_given[i] = "helpful"
                        st.rerun()
                with col_b:
                    if st.button("no", key=f"down_{i}"):
                        requests.post(f"{API_URL}/feedback", json={
                            "question": st.session_state.messages[i-1]["content"],
                            "answer": message["content"],
                            "thumbs_up": False
                        })
                        st.session_state.feedback_given[i] = "not helpful"
                        st.rerun()
            else:
                st.markdown(
                    f'<div class="meta-row">feedback: {st.session_state.feedback_given[i]}</div>',
                    unsafe_allow_html=True
                )

with st.sidebar:
    st.markdown('<p class="sidebar-title">Loaded Documents</p>', unsafe_allow_html=True)
    try:
        res = requests.get(f"{API_URL}/documents")
        if res.status_code == 200:
            data = res.json()
            st.markdown(f'<p class="chunk-count">{data.get("total_chunks", 0)} chunks indexed</p>', unsafe_allow_html=True)
            for doc in data.get("documents", []):
                st.markdown(f'<div class="doc-item">{doc}</div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<p class="chunk-count">Server not running</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p class="sidebar-title">Upload Document</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Accepts .txt or .md", type=["txt", "md"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Add to knowledge base"):
            with st.spinner("Ingesting..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                res = requests.post(f"{API_URL}/ingest", files=files)
                if res.status_code == 200:
                    st.success("Done")
                    st.rerun()
                else:
                    st.error("Failed")

    st.divider()
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.session_state.feedback_given = {}
        st.rerun()

    st.divider()
    st.markdown('<p class="chunk-count">LangGraph · FastAPI · Groq · ChromaDB</p>', unsafe_allow_html=True)

if prompt := st.chat_input("Ask anything about the documentation"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                response = requests.post(f"{API_URL}/query", json={"question": prompt})
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    query_type = data.get("query_type", "unknown")
                    retry_count = data.get("retry_count", 0)
                    fallback = data.get("fallback", False)
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
                else:
                    st.error("Server error. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to server. Start it with: uvicorn app.main:app --reload --port 8000")