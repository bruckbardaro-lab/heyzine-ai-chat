import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurações
DB_DIR = "./chroma_db"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar Embeddings e Vectorstore
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# Prompt customizado para garantir que a IA use apenas o PDF e cite a página
prompt_template = """Você é um assistente especializado no "Guia AN para Cães". 
Use APENAS o contexto fornecido abaixo para responder às perguntas. 
Se a resposta não estiver no contexto, diga educadamente que não possui essa informação no guia.
Sempre que possível, cite o número da página onde a informação foi encontrada (use o metadado "page_label").

Contexto:
{context}

Pergunta: {question}

Resposta (em português do Brasil):"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# Inicializar o LLM (Groq)
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY
)

# Criar a Chain de QA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_query = data.get("query")
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        result = qa_chain.invoke({"query": user_query})
        answer = result["result"]
        
        # Extrair páginas das fontes
        pages = list(set([doc.metadata.get("page_label", "N/A") for doc in result["source_documents"]]))
        
        return jsonify({
            "answer": answer,
            "pages": pages
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "Heyzine AI Chat Backend is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
