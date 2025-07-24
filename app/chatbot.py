import os
from flask import request, jsonify, current_app, session, Response
import google.generativeai as genai
import logging
import json

# --- Configuração da API Gemini ---
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

# --- Lógica do Chatbot com Streaming ---

# ✅ CORREÇÃO: A função agora aceita 'logger' como argumento.
def generate_with_gemini_stream(user_id, message, logger):
    if not gemini_model:
        yield f"data: {json.dumps({'error': 'Serviço de chatbot indisponível.'})}\n\n"
        return

    chat_session = histories.setdefault(user_id, gemini_model.start_chat(history=[]))
    
    if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
        chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]

    try:
        # ✅ CORREÇÃO: Usa o 'logger' passado como argumento.
        logger.info(f"[{user_id}] Enviando para Gemini (stream): '{message}'")
        response_stream = chat_session.send_message(message, stream=True)
        
        for chunk in response_stream:
            yield f"data: {json.dumps({'reply_chunk': chunk.text})}\n\n"

    except Exception as e:
        # ✅ CORREÇÃO: Usa o 'logger' passado como argumento.
        logger.exception(f"[{user_id}] ❌ Erro na API Gemini: {e}")
        yield f"data: {json.dumps({'error': 'Desculpe, tive um problema técnico.'})}\n\n"
        histories.pop(user_id, None)

# --- Função de Inicialização das Rotas ---
def init_chatbot_routes(app):
    """Anexa as rotas do chatbot à aplicação Flask principal."""
    
    @app.route('/api/chatbot', methods=['POST'])
    def chatbot():
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida."}), 400

        user_message = data.get('message')
        user_id = session.get('usuario_id', request.remote_addr) 

        # ✅ CORREÇÃO: Obtém o logger aqui (onde o contexto é seguro) e o passa para a função.
        logger = current_app.logger
        return Response(generate_with_gemini_stream(user_id, user_message, logger), mimetype='text/event-stream')