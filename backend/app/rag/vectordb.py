# app/rag/vectordb.py

# from langchain.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import CHROMA_PATH

def get_embedding():
    return OllamaEmbeddings(model="llama3")

def load_db():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding()
    )