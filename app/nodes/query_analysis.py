import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.state import RAGState

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=200
    )

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a search query optimizer for a technical documentation assistant.
Your job is to rewrite the user question to improve search retrieval.
Rules:
- Make it specific and keyword rich
- Expand abbreviations
- Remove filler words like can you, I want to know
- Classify intent as ONE of: conceptual | how-to | troubleshooting | api-reference
Output format exactly like this:
REWRITTEN: <improved query>
TYPE: <classification>"""),
    ("human", "Original question: {question}")
])

def query_analysis_node(state: RAGState) -> RAGState:
    llm = get_llm()
    chain = REWRITE_PROMPT | llm
    result = chain.invoke({"question": state["question"]})
    content = result.content.strip()

    lines = content.split("\n")
    rewritten = state["question"]
    query_type = "conceptual"

    for line in lines:
        if line.startswith("REWRITTEN:"):
            rewritten = line.replace("REWRITTEN:", "").strip()
        elif line.startswith("TYPE:"):
            query_type = line.replace("TYPE:", "").strip()

    print(f"[QueryAnalysis] '{state['question']}' → '{rewritten}' ({query_type})")

    return {
        **state,
        "rewritten_query": rewritten,
        "query_type": query_type
    }