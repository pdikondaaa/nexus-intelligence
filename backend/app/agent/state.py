
# from typing import TypedDict

# class AgentState(TypedDict):
#     query: str
#     plan: str
#     answer: str

from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    query: str
    intent: str
    plan: str
    answer: str
    blocked: bool