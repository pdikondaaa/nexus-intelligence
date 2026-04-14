from app.rag.retriever import retrieve_docs

# 🔍 RAG TOOL
def rag_tool(query, db):
    return retrieve_docs(db, query)


# 📊 EXCEL TOOL
def excel_tool(query, excel_agent):
    return excel_agent.query(query)