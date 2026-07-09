import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurações
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Carregar o conteúdo do PDF uma única vez na memória
def load_guia():
    with open("guia_content.json", "r", encoding="utf-8") as f:
        return json.load(f)

GUIA_DATA = load_guia()

# Formata o guia para o prompt
CONTEXTO_FULL = "\n".join([f"--- PÁGINA {p['page']} ---\n{p['text']}" for p in GUIA_DATA])

SYSTEM_PROMPT = f"""Você é um assistente especializado no "Guia AN para Cães".
Sua função é responder dúvidas baseando-se EXCLUSIVAMENTE no conteúdo do guia fornecido abaixo.

REGRAS IMPORTANTES:
1. Se a informação não estiver no guia, diga: "Desculpe, essa informação não consta no Guia AN para Cães."
2. Sempre cite o número da página onde encontrou a resposta (ex: "De acordo com a página 15...").
3. Para perguntas sobre peso do cão, procure as tabelas de receitas específicas para aquele peso.
4. Seja educado, prestativo e direto.
5. Responda sempre em Português do Brasil.

CONTEÚDO DO GUIA:
{CONTEXTO_FULL}
"""

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_query = data.get("query")
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        
        answer = chat_completion.choices[0].message.content
        
        return jsonify({
            "answer": answer
        })
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "Heyzine AI Chat Backend (Ultra-Light) is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
