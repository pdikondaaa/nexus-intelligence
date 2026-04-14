def supervisor_node(state):
    if state.get("blocked"):
        return {"next": "end"}

    if "answer" in state:
        return {"next": "end"}

    return {"next": "executor"}