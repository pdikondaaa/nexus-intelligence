def planner_node(state, llm):
    query = state["query"]
    q = query.lower()

    # =========================
    # 🔥 0. USE INTENT FIRST (CRITICAL FIX)
    # =========================
    intent = state.get("intent")

    if intent in ["rag", "excel", "general"]:
        print(f"PLAN: {intent} (from intent)")
        return {"plan": intent}

    # =========================
    # 1. STRONG RULES
    # =========================

    if any(word in q for word in ["pdf", "document", "report", "file"]):
        print("PLAN: rag (rule - document detected)")
        return {"plan": "rag"}

    if any(word in q for word in ["excel", "table", "row", "column", "index"]):
        print("PLAN: excel (rule - table detected)")
        return {"plan": "excel"}

    # =========================
    # 2. MEDIUM RULES
    # =========================

    if any(word in q for word in ["average", "mean", "sum", "total"]):
        if any(word in q for word in ["revenue", "region"]):
            print("PLAN: rag (rule - revenue context)")
            return {"plan": "rag"}

        print("PLAN: excel (rule - aggregation)")
        return {"plan": "excel"}

    # =========================
    # 3. LLM FALLBACK
    # =========================

    prompt = f"""
    Decide tool:

    rag → document/report/salary/department/revenue
    excel → claim/data/table
    general → others

    Query: {query}

    Answer: rag or excel or general
    """

    try:
        decision = llm.invoke(prompt).content.strip().lower()
        decision = decision.split()[0]

        if decision not in ["rag", "excel", "general"]:
            decision = "general"

    except Exception as e:
        print("Planner LLM Error:", e)
        decision = "general"

    print(f"PLAN: {decision} (llm fallback)")

    return {"plan": decision}