from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import Ollama

class RAGService:
    def __init__(self, db_path="chroma_db", model_name="gpt-oss:20b"): # nous-hermes2
        embedding = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")
        vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
        retriever = vectordb.as_retriever()
        llm = Ollama(model=model_name, base_url="http://ollama:11434")

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=False  # ✅ run() を使いたいなら False に
        )

    def ask(self, question: str) -> str:
        return self.qa_chain.run(question)
