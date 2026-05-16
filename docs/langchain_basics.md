# LangChain Basics

## What is LangChain?
LangChain is a framework for building applications powered by large language models. It provides tools for connecting prompts, models, memory, and retrievers together.

## Chat Models
Chat models take messages and return a response.

from langchain_groq import ChatGroq

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)

result = llm.invoke("What is Python?")
print(result.content)

## Prompt Templates
Prompt templates create dynamic prompts with variables.

from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])

chain = prompt | llm
result = chain.invoke({"question": "What is FastAPI?"})

## Chains
Chains connect components using the pipe operator symbol.

from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"topic": "Python"})

## Document Loaders
Load documents from files or URLs.

from langchain_community.document_loaders import TextLoader

loader = TextLoader("document.txt")
documents = loader.load()

## Text Splitters
Split long documents into smaller chunks for better retrieval.

from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)

## Embeddings
Convert text into numbers for similarity search.

from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

## Vector Stores
Store and search document embeddings locally.

from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

results = vectorstore.similarity_search("Python basics", k=4)

## Retrievers
Retrievers fetch the most relevant documents for a query.

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
docs = retriever.invoke("How to use FastAPI?")

## Output Parsers
Parse and structure the LLM output into usable formats.

from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
chain = prompt | llm | parser

## LangGraph Integration
LangGraph extends LangChain for building stateful workflows.
It uses a graph where nodes are functions and edges are connections between them.
StateGraph manages the flow of data between nodes using a shared state.
Conditional edges allow dynamic routing based on results at runtime.