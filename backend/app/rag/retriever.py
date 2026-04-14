# app/rag/retriever.py

# def retrieve_docs(db, query):
#     retriever = db.as_retriever(search_kwargs={"k": 3})
#     docs = retriever.get_relevant_documents(query)
#     return "\n".join([d.page_content for d in docs])

# def retrieve_docs(db, query):
#     retriever = db.as_retriever(search_kwargs={"k": 3})

#     docs = retriever.invoke(query)   

#     return "\n".join([d.page_content for d in docs])

# def retrieve_docs(db, query):
#     retriever = db.as_retriever(search_kwargs={"k": 3})
#     docs = retriever.invoke(query)
    

#     print("DEBUG DOCS:", docs)   

#     return "\n".join([d.page_content for d in docs])

def retrieve_docs(db, query):
    retriever = db.as_retriever(search_kwargs={"k": 5})  # increase context

    docs = retriever.invoke(query)

    print("\n🔍 RETRIEVED DOCS:\n")
    for d in docs:
        print(d.page_content[:200], "\n---")

    return "\n\n".join([d.page_content for d in docs])