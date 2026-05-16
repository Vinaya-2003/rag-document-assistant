import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.state import RAGState

def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=10
    )

GRADE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a relevance checker.
Given a question and a document chunk, reply with ONLY one word.
Reply yes if the chunk helps answer the question.
Reply no if it does not.
No explanation. One word only."""),
    ("human", "Question: {question}\n\nChunk: {chunk}")
])

def grader_node(state: RAGState) -> RAGState:
    llm = get_llm()
    chain = GRADE_PROMPT | llm

    relevant_docs = []

    for doc in state["retrieved_docs"]:
        result = chain.invoke({
            "question": state["question"],
            "chunk": doc["content"][:400]
        })
        verdict = result.content.strip().lower()

        if "yes" in verdict:
            relevant_docs.append(doc)
            print(f"[Grader] RELEVANT: {doc['source'][:50]}")
        else:
            print(f"[Grader] IRRELEVANT: {doc['source'][:50]}")

    print(f"[Grader] {len(relevant_docs)}/{len(state['retrieved_docs'])} chunks passed")

    return {**state, "relevant_docs": relevant_docs}