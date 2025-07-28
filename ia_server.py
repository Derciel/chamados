# ia_server.py

import os
import logging
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import google.generativeai as genai

# --- Configuração do Servidor e Logging ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configura o CORS para aceitar requisições de qualquer origem para a rota da API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Configuração da API Gemini ---
# ✅ CORREÇÃO: Usa o nome de variável padrão e mais explícito.
GEMINI_API_KEY = os.getenv("key") 
gemini_model = None
SYSTEM_INSTRUCTION = """
Você é um assistente virtual especializado em Tecnologia da Informação (TI) da empresa Nicopel Embalagens.
Sua única função é responder perguntas sobre hardware, software, redes, programação e problemas técnicos.
Se o usuário perguntar sobre qualquer outro assunto, recuse educadamente e reafirme sua especialidade.
"""

if not GEMINI_API_KEY:
    logging.warning("Variável de ambiente GEMINI_API_KEY não configurada. O chatbot não será inicializado.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            system_instruction=SYSTEM_INSTRUCTION
        )
        logging.info("✅ Modelo Gemini (API) configurado com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao configurar Gemini API: {e}")

# O histórico em memória é perdido a cada reinicialização.
histories = {}
MAX_HISTORY_TURNS = 5 

# --- Lógica do Chatbot ---
def generate_with_gemini(user_id, message):
    if not gemini_model:
        app.logger.error(f"[{user_id}] Tentativa de uso do chatbot com modelo não inicializado.")
        return "Desculpe, o serviço de chatbot está temporariamente indisponível."

    chat_session = histories.setdefault(user_id, gemini_model.start_chat(history=[]))
    
    if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
        chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]

    try:
        app.logger.info(f"[{user_id}] Enviando para Gemini: '{message}'")
        # ✅ MELHORIA: Removido o 'stream=True' para uma requisição mais simples e direta.
        response = chat_session.send_message(message)
        full_reply = response.text
        app.logger.info(f"[{user_id}] Resposta recebida: '{full_reply}'")
        return full_reply
    except Exception as e:
        app.logger.exception(f"[{user_id}] ❌ Erro inesperado na API Gemini: {e}")
        histories.pop(user_id, None) # Limpa o histórico do usuário em caso de erro
        return "Desculpe, tive um problema técnico ao processar sua pergunta. Tente novamente."

# --- Rota da API ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Mensagem não fornecida."}), 400

    user_message = data.get('message')
    user_id = request.remote_addr # Usa o IP como identificador

    ai_response = generate_with_gemini(user_id, user_message)
    return jsonify({"reply": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Para desenvolvimento local, o debug=True é útil.
    # Em produção com Gunicorn, o debug deve ser False.
    app.run(host='0.0.0.0', port=port, debug=True)