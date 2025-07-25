# app/chatbot.py
import os
from flask import request, jsonify, current_app, session
import google.generativeai as genai
import logging

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

histories = {}
MAX_HISTORY_TURNS = 5

def generate_with_gemini(user_id, message):
    if not gemini_model:
        current_app.logger.error(f"[{user_id}] Chatbot chamado, mas modelo não inicializado.")
        return "Desculpe, o serviço de chatbot está temporariamente indisponível."

    chat_session = histories.setdefault(user_id, gemini_model.start_chat(history=[]))
    
    if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
        chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]

    try:
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        current_app.logger.exception(f"[{user_id}] ❌ Erro na API Gemini: {e}")
        histories.pop(user_id, None)
        return "Desculpe, tive um problema técnico. Tente novamente."

def init_chatbot_routes(app):
    @app.route('/api/chatbot', methods=['POST'])
    def chatbot():
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida."}), 400

        user_message = data.get('message')
        user_id = session.get('usuario_id', request.remote_addr) 
        ai_response = generate_with_gemini(user_id, user_message)
        return jsonify({"reply": ai_response})