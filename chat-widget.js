(function() {
    // Configurações - O usuário deve trocar a URL após o deploy
    const BACKEND_URL = "SUA_URL_DO_RENDER_OU_RAILWAY"; 

    // Estilos do Widget
    const styles = `
        #ai-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 450px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 25px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            z-index: 999999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            border: 1px solid #eee;
        }
        #ai-chat-header {
            background: #4A90E2;
            color: white;
            padding: 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        #ai-chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #f9f9f9;
        }
        .ai-msg {
            padding: 10px;
            border-radius: 10px;
            max-width: 85%;
            font-size: 14px;
            line-height: 1.4;
        }
        .user-msg {
            background: #4A90E2;
            color: white;
            align-self: flex-end;
        }
        .bot-msg {
            background: #e1e1e1;
            color: #333;
            align-self: flex-start;
        }
        #ai-chat-input-container {
            padding: 10px;
            border-top: 1px solid #eee;
            display: flex;
            gap: 5px;
        }
        #ai-chat-input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 8px 15px;
            outline: none;
        }
        #ai-chat-send {
            background: #4A90E2;
            color: white;
            border: none;
            border-radius: 50%;
            width: 35px;
            height: 35px;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #ai-chat-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #4A90E2;
            border-radius: 50%;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            cursor: pointer;
            z-index: 999998;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 24px;
        }
        .typing {
            font-style: italic;
            font-size: 12px;
            color: #888;
        }
    `;

    // Injetar Estilos
    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    // Criar Elementos HTML
    const widget = document.createElement("div");
    widget.id = "ai-chat-widget";
    widget.innerHTML = `
        <div id="ai-chat-header">
            <span>Assistente Guia AN</span>
            <span id="ai-chat-close" style="cursor:pointer">×</span>
        </div>
        <div id="ai-chat-messages">
            <div class="ai-msg bot-msg">Olá! Sou o assistente do Guia AN para Cães. Como posso te ajudar hoje?</div>
        </div>
        <div id="ai-chat-input-container">
            <input type="text" id="ai-chat-input" placeholder="Pergunte sobre a dieta...">
            <button id="ai-chat-send">➤</button>
        </div>
    `;

    const toggle = document.createElement("div");
    toggle.id = "ai-chat-toggle";
    toggle.innerHTML = "💬";

    document.body.appendChild(widget);
    document.body.appendChild(toggle);

    // Lógica do Chat
    const input = document.getElementById("ai-chat-input");
    const sendBtn = document.getElementById("ai-chat-send");
    const messages = document.getElementById("ai-chat-messages");
    const closeBtn = document.getElementById("ai-chat-close");

    function toggleChat() {
        const isVisible = widget.style.display === "flex";
        widget.style.display = isVisible ? "none" : "flex";
        toggle.style.display = isVisible ? "flex" : "none";
    }

    toggle.onclick = toggleChat;
    closeBtn.onclick = toggleChat;

    async function sendMessage() {
        const query = input.value.trim();
        if (!query) return;

        // Add user message
        addMessage(query, 'user-msg');
        input.value = "";

        // Add typing indicator
        const typingId = "typing-" + Date.now();
        const typingDiv = document.createElement("div");
        typingDiv.id = typingId;
        typingDiv.className = "ai-msg bot-msg typing";
        typingDiv.innerText = "Pensando...";
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch(`${BACKEND_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            
            document.getElementById(typingId).remove();
            
            if (data.answer) {
                addMessage(data.answer, 'bot-msg');
            } else {
                addMessage("Desculpe, tive um problema ao processar sua pergunta.", 'bot-msg');
            }
        } catch (error) {
            document.getElementById(typingId).remove();
            addMessage("Erro de conexão com o servidor.", 'bot-msg');
            console.error(error);
        }
    }

    function addMessage(text, className) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `ai-msg ${className}`;
        msgDiv.innerText = text;
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    sendBtn.onclick = sendMessage;
    input.onkeypress = (e) => { if (e.key === "Enter") sendMessage(); };

})();
