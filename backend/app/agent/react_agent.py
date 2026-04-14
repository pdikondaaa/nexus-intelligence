from app.agent.tools import rag_tool, excel_tool
import re

def react_agent(query, llm, db, excel_agent, max_steps=3):

    tools = {
        "rag": lambda q: rag_tool(q, db),
        "excel": lambda q: excel_tool(q, excel_agent),
    }

    scratchpad = ""
    last_action = None
    observation = None

    for step in range(max_steps):

        # ✅ DEFINE PROMPT HERE (VERY IMPORTANT)
        prompt = f"""
You are an intelligent agent.

You already have access to a pandas DataFrame called df.

DO NOT ask for data.
DO NOT ask for tables.

Use the tools directly.

---
Query: {query}
{scratchpad}
"""
#         prompt = f"""
# You are an intelligent agent.

# You can use tools:
# - rag → for PDF/document questions
# - excel → for table/data questions

# STRICT FORMAT:

# Thought: reasoning
# Action: rag OR excel OR final
# Action Input: input

# RULES:
# - Use tools when needed
# - If answer is ready → Action: final
# - DO NOT repeat same action

# ---

# Query: {query}

# {scratchpad}
# """

        # ✅ NOW prompt is defined
        response = llm.invoke(prompt).content

        print("\nLLM RESPONSE:\n", response)


        # Extract action
        action_match = re.search(r"Action\s*:\s*(\w+)", response)

        if not action_match:
            return f"Parsing error: No action found\nResponse: {response}"

        action = action_match.group(1).lower()

        # Extract action input (optional)
        input_match = re.search(r"Action Input\s*:\s*(.*)", response, re.DOTALL)

        if input_match:
            action_input = input_match.group(1).strip()
        else:
            action_input = query   # fallback

        # ✅ FINAL → RETURN TOOL RESULT
        if action == "final":
            return observation

        if action not in tools:
            return f"Unknown action: {action}"

        # ✅ EXECUTE TOOL
        # observation = tools[action](action_input)
        # 🔥 If excel → bypass ReAct parsing
        if action == "excel":
            return excel_agent.query(query)

        if action == "rag":
            return rag_tool(query, db)

        if action == "final":
            return observation

        # ✅ STOP LOOP IF REPEATING
        if action == last_action:
            return observation

        last_action = action

        # ✅ ADD MEMORY
        scratchpad += f"""
Thought: used {action}
Observation: {observation}
"""

        # ✅ FORCE RETURN
        if step == max_steps - 1:
            return observation