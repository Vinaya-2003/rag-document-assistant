import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.state import RAGState

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0.2,
        max_tokens=600
    )

GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a technical documentation assistant.
Answer the user question using ONLY the provided context chunks.
Rules:
- If the context answers the question, give a clear and accurate answer.
- After each factual claim, add [Source: filename] to show where you found it.
- If the context does NOT fully answer the question, say so honestly.
- Do NOT invent information. Only use what is in the context.
- Be concise. Aim for 3 to 5 sentences unless more detail is needed."""),
    ("human", """Question: {question}

Context:
{context}

Answer:""")
])

def generator_node(state: RAGState) -> RAGState:
    docs = state["relevant_docs"]

    context_parts = []
    sources = []

    for i, doc in enumerate(docs):
        source_name = doc["source"].split("\\")[-1].split("/")[-1]
        context_parts.append(f"[Chunk {i+1} from {source_name}]\n{doc['content']}")
        if source_name not in sources:
            sources.append(source_name)

    context = "\n\n".join(context_parts)

    llm = get_llm()
    chain = GENERATE_PROMPT | llm

    result = chain.invoke({
        "question": state["question"],
        "context": context
    })

    print(f"[Generator] Answer generated ({len(result.content)} chars)")

    return {
        **state,
        "answer": result.content.strip(),
        "sources": sources
    }

def fallback_node(state: RAGState) -> RAGState:
    return {
        **state,
        "answer": (
            f"I could not find relevant information in the documentation "
            f"to answer: '{state['question']}'. "
            f"Please try rephrasing your question or check if this topic "
            f"is covered in the loaded documents."
        ),
        "sources": [],
        "fallback": True
    }