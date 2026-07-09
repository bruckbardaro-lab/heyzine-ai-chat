# Guia de Instalação e Deploy: Chat IA para Heyzine

Este guia explica como colocar o seu chat de Inteligência Artificial no ar gratuitamente e integrá-lo ao seu flipbook no Heyzine.

## 1. O que foi construído
- **Backend (Python):** Uma API Flask que usa LangChain, ChromaDB (banco de vetores) e a API gratuita do Groq (modelo Llama 3) para ler o seu PDF e responder perguntas.
- **Frontend (JavaScript):** Um script flutuante que cria a interface do chat e se comunica com o backend.

---

## 2. Como fazer o Deploy do Backend (Grátis no Render)

O Render é uma excelente plataforma gratuita para hospedar APIs Python.

### Passo 2.1: Preparar o repositório no GitHub
1. Crie uma conta no [GitHub](https://github.com/) (se não tiver).
2. Crie um novo repositório chamado `heyzine-ai-chat`.
3. Faça o upload dos seguintes arquivos para o repositório:
   - `app.py`
   - `ingest.py`
   - `requirements.txt`
   - A pasta `chroma_db` (que contém os dados do seu PDF já processados)

### Passo 2.2: Obter a chave da API do Groq
1. Acesse [Groq Cloud](https://console.groq.com/).
2. Crie uma conta gratuita.
3. Vá em **API Keys** e clique em **Create API Key**.
4. Copie a chave gerada (ela começa com `gsk_...`).

### Passo 2.3: Configurar no Render
1. Acesse [Render](https://render.com/) e crie uma conta (pode usar o login do GitHub).
2. Clique em **New +** e selecione **Web Service**.
3. Conecte sua conta do GitHub e selecione o repositório `heyzine-ai-chat`.
4. Preencha as configurações:
   - **Name:** `heyzine-ai-chat`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Role para baixo até **Environment Variables** e adicione:
   - Key: `GROQ_API_KEY`
   - Value: *(cole a chave que você pegou no Groq)*
6. Selecione o plano **Free** e clique em **Create Web Service**.
7. Aguarde o deploy terminar (pode levar alguns minutos). Quando terminar, copie a URL gerada (ex: `https://heyzine-ai-chat.onrender.com`).

---

## 3. Como configurar o Frontend (Script JS)

1. Abra o arquivo `chat-widget.js` que foi entregue.
2. Na linha 3, substitua `"SUA_URL_DO_RENDER_OU_RAILWAY"` pela URL que você copiou do Render.
   - Exemplo: `const BACKEND_URL = "https://heyzine-ai-chat.onrender.com";`
3. Salve o arquivo.

---

## 4. Como injetar no Heyzine

O Heyzine permite adicionar scripts customizados nos planos pagos, mas se você estiver no plano gratuito, existem alternativas:

### Opção A: Injeção via Heyzine (Se tiver plano compatível)
1. Acesse o painel do seu flipbook no Heyzine.
2. Vá em **Settings** > **Advanced** > **Custom Code** (ou Custom JS).
3. Cole todo o conteúdo do arquivo `chat-widget.js` lá.

### Opção B: Hospedar o Flipbook no seu próprio site (Grátis)
Se você for incorporar (embed) o flipbook no seu próprio site (WordPress, Wix, etc.):
1. Pegue o código de Embed (iframe) do Heyzine.
2. Na mesma página do seu site onde você colocou o iframe, adicione o script do chat:
   ```html
   <script>
     // Cole o conteúdo do chat-widget.js aqui
   </script>
   ```

## 5. Como atualizar o PDF no futuro
Se você mudar o PDF do Guia AN:
1. Substitua o arquivo PDF antigo pelo novo.
2. Rode o script `ingest.py` localmente no seu computador para gerar uma nova pasta `chroma_db`.
3. Suba a nova pasta `chroma_db` para o GitHub.
4. O Render vai atualizar automaticamente.
