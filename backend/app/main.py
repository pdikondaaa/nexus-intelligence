# from fastapi import FastAPI
# from app.schemas.chat import ChatRequest

# from app.llm.llm import get_llm
# # from app.agent.graph import build_graph
# from app.memory.memory import ChatMemory
# from app.excel_agent.excel_tool import ExcelAgent
# from app.rag.vectordb import load_db
# from app.config import EXCEL_FILE
# from app.agent.graph import build_graph

# app = FastAPI()

# # Initialize once
# llm = get_llm()
# db = load_db()
# # excel_agent = ExcelAgent(EXCEL_FILE)
# excel_agent = ExcelAgent(EXCEL_FILE, llm)
# memory = ChatMemory()

# agent = build_graph(llm, db, excel_agent)
# # from app.agent.react_agent import react_agent


# @app.post("/chat")
# def chat(req: ChatRequest):
#     result = agent.invoke({
#         "query": req.query
#     })

#     memory.add(req.session_id, req.query, result["answer"])

#     return {
#         "answer": result["answer"],
#         "history": memory.get(req.session_id)
#     }

from fastapi import FastAPI
from pydantic import BaseModel

from app.llm.llm import get_llm
from app.rag.vectordb import load_db
from app.excel_agent.excel_tool import ExcelAgent
from app.memory.memory import ChatMemory
from app.agent.graph import build_graph
from app.config import EXCEL_FILE

app = FastAPI()

llm = get_llm()
db = load_db()
excel_agent = ExcelAgent(EXCEL_FILE, llm)
memory = ChatMemory()

agent = build_graph(llm, db, excel_agent)


class ChatRequest(BaseModel):
    query: str
    session_id: str


@app.post("/chat")
def chat(req: ChatRequest):
    result = agent.invoke({"query": req.query})

    memory.add(req.session_id, req.query, result.get("answer", ""))

    return {
        "answer": result.get("answer", ""),
        "history": memory.get(req.session_id)
    }