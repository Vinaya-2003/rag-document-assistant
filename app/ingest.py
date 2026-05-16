import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "./chroma_db"
DOCS_PATH = "./docs"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

def load_documents(folder: str = DOCS_PATH):
    docs = []
    for filepath in Path(folder).rglob("*"):
        if filepath.suffix == ".txt":
            loader = TextLoader(str(filepath), encoding="utf-8")
            docs.extend(loader.load())
        elif filepath.suffix == ".md":
            loader = TextLoader(str(filepath), encoding="utf-8")
            docs.extend(loader.load())
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
        print("No documents found! Add .txt or .md files to docs/")
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