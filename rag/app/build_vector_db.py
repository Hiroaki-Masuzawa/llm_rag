from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from clone_and_extract import clone_repos, extract_all_docstrings

def to_documents(items):
    docs = []
    for item in items:
        content = f"""Name: {item.get('name', '')}
Type: {item.get('type', '')}
Docstring:
{item.get('docstring', '') or 'None'}

Source Code:
{item.get('source_code', '')}
"""
        docs.append(Document(
            page_content=content,
            metadata={"file": item.get("file_path", ""), "name": item.get("name", "")}
        ))
    return docs

def build_db():
    clone_repos()
    raw_docs = extract_all_docstrings()

    documents = to_documents(raw_docs)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    # GPU 対応埋め込みモデル（高速）
    embedding = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        model_kwargs={"device": "cuda"}  # ← GPU を使う
        # model_name="microsoft/codebert-base",
        # model_kwargs={"device": "cuda"}  # ← GPU を使う
    )

    # 埋め込み & 保存
    db = Chroma.from_documents(split_docs, embedding, persist_directory="chroma_db")
    db.persist()
    print("✅ Vector DB built.")

if __name__ == "__main__":
    build_db()
