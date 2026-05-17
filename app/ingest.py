import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

try:
    import streamlit as st
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

CHROMA_PATH = "/tmp/chroma_db"
DOCS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

def load_documents(folder: str = DOCS_PATH):
    docs = []
    from langchain_community.document_loaders import TextLoader
    for filepath in Path(folder).rglob("*"):
        if filepath.suffix in [".txt", ".md"]:
            try:
                loader = TextLoader(str(filepath), encoding="utf-8")
                docs.extend(loader.load())
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    print(f"Loaded {len(docs)} documents from {folder}")
    return docs

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks

def ingest(folder: str = DOCS_PATH):
    documents = load_documents(folder)
    if not documents:
        print("No documents found!")
        return None
    chunks = chunk_documents(documents)
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f"Ingested {len(chunks)} chunks into ChromaDB at {CHROMA_PATH}")
    return vectorstore

def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embeddings()
    )

if __name__ == "__main__":
    ingest()