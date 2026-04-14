def guardrail_node(state):
    q = state["query"].lower()

    blocked_words = ["hack", "bypass", "delete system"]

    if any(w in q for w in blocked_words):
        return {
            "blocked": True,
            "answer": "❌ Unsafe query detected"
        }

    return {"blocked": False}