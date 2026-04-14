# app/agent/executor.py

from app.rag.retriever import retrieve_docs

def executor_node(state, llm, db, excel_agent):
    plan = state["plan"].lower()
    query = state["query"]

    if "excel" in plan:
        answer = excel_agent.query(state["query"])

    elif "rag" in plan:
        context = retrieve_docs(db, state["query"])

        prompt = f"""
You are answering strictly from context.

IMPORTANT RULES:
- Do NOT guess
- Do NOT mix different sections
- If question asks about "department", answer ONLY from department-related data
- Ignore region/country unless asked

Context:
{context}

Question:
{query}

Answer clearly and precisely:
"""

        answer = llm.invoke(prompt).content

    else:
        answer = llm.invoke(state["query"]).content

    return {"answer": answer}