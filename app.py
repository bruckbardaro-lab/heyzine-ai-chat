import os
import json
import sqlite3
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import warnings

warnings.filterwarnings("ignore")

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurações
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Inicializar modelo de embeddings leve (DistilBERT - ~27MB)
print("Carregando modelo de embeddings...")
model = SentenceTransformer('all-MiniLM-L6-v2')  # ~27MB, muito leve
print("Modelo carregado!")

# Configurações do banco de dados
DB_PATH = "guia_embeddings.db"
CHUNK_SIZE = 500  # Caracteres por chunk
OVERLAP = 50  # Sobreposição entre chunks

def init_database():
    """Inicializa o banco de dados SQLite com embeddings."""
    if os.path.exists(DB_PATH):
        print(f"Banco de dados {DB_PATH} já existe. Pulando inicialização.")
        return
    
    print("Inicializando banco de dados com embeddings...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            page_start INTEGER NOT NULL,
            page_end INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
    """)
    
    # Carregar chunks do arquivo JSON gerado anteriormente
    with open("chunked_sections.json", "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
    
    # Processar cada chunk
    for chunk in chunks_data:
        text = chunk["text"]
        title = chunk["title"]
        page_start = chunk["page_start"]
        page_end = chunk["page_end"]
        
        # Gerar embedding
        embedding = model.encode(text, convert_to_numpy=True)
        embedding_bytes = embedding.astype(np.float32).tobytes()
        
        # Inserir no banco
        cursor.execute("""
            INSERT INTO chunks (title, page_start, page_end, text, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (title, page_start, page_end, text, embedding_bytes))
    
    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado com {len(chunks_data)} chunks!")

def retrieve_relevant_chunks(query, top_k=3):
    """Busca os chunks mais relevantes para a query usando embeddings."""
    # Gerar embedding da query
    query_embedding = model.encode(query, convert_to_numpy=True)
    query_bytes = query_embedding.astype(np.float32).tobytes()
    
    # Conectar ao banco
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Recuperar todos os chunks
    cursor.execute("SELECT id, title, page_start, page_end, text, embedding FROM chunks")
    rows = cursor.fetchall()
    
    # Calcular similaridade cosseno para cada chunk
    similarities = []
    for row in rows:
        chunk_id, title, page_start, page_end, text, embedding_bytes = row
        chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        
        # Similaridade cosseno
        similarity = np.dot(query_embedding, chunk_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding) + 1e-8
        )
        
        similarities.append({
            "id": chunk_id,
            "title": title,
            "page_start": page_start,
            "page_end": page_end,
            "text": text,
            "similarity": float(similarity)
        })
    
    conn.close()
    
    # Ordenar por similaridade e retornar top_k
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:top_k]

def build_context_from_chunks(chunks):
    """Constrói um contexto compacto a partir dos chunks relevantes."""
    context = "INFORMAÇÕES RELEVANTES DO GUIA:\n\n"
    for chunk in chunks:
        context += f"[Páginas {chunk['page_start']}-{chunk['page_end']}] {chunk['title']}\n"
        context += f"{chunk['text']}\n\n"
    return context

SYSTEM_PROMPT_TEMPLATE = """Você é um assistente especializado no "Guia AN para Cães".
Sua função é responder dúvidas baseando-se EXCLUSIVAMENTE no conteúdo do guia fornecido abaixo.

REGRAS IMPORTANTES:
1. Se a informação não estiver no guia, diga: "Desculpe, essa informação não consta no Guia AN para Cães."
2. Sempre cite o número da página onde encontrou a resposta (ex: "De acordo com a página 15...").
3. Para perguntas sobre peso do cão, procure as tabelas de receitas específicas para aquele peso.
4. Seja educado, prestativo e direto.
5. Responda sempre em Português do Brasil.

CONTEÚDO RELEVANTE DO GUIA:
{context}
"""

@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint de chat com busca RAG."""
    data = request.json
    user_query = data.get("query")
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Buscar chunks relevantes
        relevant_chunks = retrieve_relevant_chunks(user_query, top_k=3)
        
        # Construir contexto
        context = build_context_from_chunks(relevant_chunks)
        
        # Construir system prompt com contexto
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        
        # Chamar Groq com contexto reduzido
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        
        answer = chat_completion.choices[0].message.content
        
        return jsonify({
            "answer": answer,
            "sources": [
                {
                    "title": chunk["title"],
                    "pages": f"{chunk['page_start']}-{chunk['page_end']}",
                    "similarity": chunk["similarity"]
                }
                for chunk in relevant_chunks
            ]
        })
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "Heyzine AI Chat Backend (RAG-Enhanced) is running!", 200

@app.route("/stats", methods=["GET"])
def stats():
    """Retorna estatísticas do banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks")
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        "total_chunks": count,
        "db_size_mb": os.path.getsize(DB_PATH) / (1024 * 1024)
    })

if __name__ == "__main__":
    # Inicializar banco de dados na primeira execução
    init_database()
    
    # Rodar servidor
    app.run(host="0.0.0.0", port=5000)
