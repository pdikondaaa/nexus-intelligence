import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
PDF_FILE = os.path.join(BASE_DIR, "data/sample.pdf")
EXCEL_FILE = os.path.join(BASE_DIR, "data/sample.xlsx")