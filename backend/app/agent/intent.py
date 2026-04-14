def intent_node(state, llm):
    q = state["query"].lower()

    # =========================
    # 🔥 1. STRONG RULES (PRIMARY)
    # =========================

    # PDF / RAG signals
    if any(word in q for word in [
        "salary", "department", "revenue",
        "report", "growth", "insight", "region"
    ]):
        print("INTENT: rag (rule)")
        return {"intent": "rag"}

    # Excel signals
    if any(word in q for word in [
        "claim", "average", "mean", "sum",
        "row", "column", "index"
    ]):
        print("INTENT: excel (rule)")
        return {"intent": "excel"}

    # =========================
    # 🤖 2. LLM FALLBACK (SECONDARY)
    # =========================

    prompt = f"""
Classify intent:

- rag → document/report/salary/revenue questions
- excel → claim/data/table questions
- general → others

Query: {q}

Answer ONLY:
rag OR excel OR general
"""

    try:
        intent = llm.invoke(prompt).content.strip().lower()
        intent = intent.split()[0]

        if intent not in ["rag", "excel", "general"]:
            intent = "general"

    except Exception as e:
        print("Intent LLM Error:", e)
        intent = "general"

    print("INTENT:", intent)

    return {"intent": intent}