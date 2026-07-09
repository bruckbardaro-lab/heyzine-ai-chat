import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def ingest_pdf(pdf_path, db_dir):
    # 1. Carregar o PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    # Adicionar metadados de página explicitamente se não estiverem presentes
    for i, page in enumerate(pages):
        page.metadata["page_label"] = str(i + 1)

    # 2. Dividir em pedaços (chunks)
    # Como o PDF tem tabelas, vamos usar um chunk size maior para manter o contexto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    docs = text_splitter.split_documents(pages)

    # 3. Criar Embeddings (usando um modelo leve e gratuito que roda localmente)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # 4. Salvar no ChromaDB
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=db_dir
    )
    print(f"Ingestão concluída! {len(docs)} documentos salvos em {db_dir}")

if __name__ == "__main__":
    pdf_input = "/home/ubuntu/upload/ANparacães.pdf"
    db_output = "./chroma_db"
    ingest_pdf(pdf_input, db_output)
