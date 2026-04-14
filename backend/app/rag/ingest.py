from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

from app.config import CHROMA_PATH, PDF_FILE


def ingest():
    print("Loading PDF...")

    loader = PyPDFLoader(PDF_FILE)
    docs = loader.load()

    print(f"Loaded {len(docs)} pages")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    print(f"Created {len(chunks)} chunks")

    embedding = OllamaEmbeddings(model="llama3")

    db = Chroma.from_documents(
        chunks,
        embedding,
        persist_directory=CHROMA_PATH
    )

    db.persist()

    print("Ingestion complete!")


if __name__ == "__main__":
    ingest()