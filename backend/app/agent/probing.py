def probing_node(state):
    query = state["query"]

    if len(query.split()) <= 2:
        return {
            "answer": "Can you please clarify your question?"
        }

    return {}