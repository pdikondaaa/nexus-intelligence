# from langgraph.graph import StateGraph
# from app.agent.state import AgentState
# from app.agent.planner import planner_node
# from app.agent.executor import executor_node

# def build_graph(llm, db, excel_agent):
#     graph = StateGraph(AgentState)

#     graph.add_node("planner", lambda s: planner_node(s, llm))
#     graph.add_node("executor", lambda s: executor_node(s, llm, db, excel_agent))

#     graph.set_entry_point("planner")
#     graph.add_edge("planner", "executor")

#     return graph.compile()

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState

from app.agent.guardrail import guardrail_node
from app.agent.intent import intent_node
from app.agent.probing import probing_node
from app.agent.planner import planner_node
from app.agent.supervisor import supervisor_node
from app.agent.executor import executor_node


def build_graph(llm, db, excel_agent):

    graph = StateGraph(AgentState)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("intent", lambda s: intent_node(s, llm))
    graph.add_node("probing", probing_node)
    graph.add_node("planner", lambda s: planner_node(s, llm))
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("executor", lambda s: executor_node(s, llm, db, excel_agent))

    graph.set_entry_point("guardrail")

    graph.add_edge("guardrail", "intent")
    graph.add_edge("intent", "probing")
    graph.add_edge("probing", "planner")
    graph.add_edge("planner", "supervisor")

    # conditional routing
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next"),
        {
            "executor": "executor",
            "end": END
        }
    )

    graph.add_edge("executor", END)

    return graph.compile()