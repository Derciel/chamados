import os
import logging
import time
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração do CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuração da API Gemini
GEMINI_API_KEY = os.getenv("key")
gemini_model = None

SYSTEM_INSTRUCTION = """
Você é um assistente virtual especializado em TI da Nicopel Embalagens.
Responda apenas perguntas sobre hardware, software, redes e programação.
Seja conciso e direto nas respostas.
"""

# Inicialização do modelo Gemini com tratamento de erro detalhado
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config={"max_output_tokens": 500}
        )
        logger.info("✅ Modelo Gemini configurado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Gemini: {e}")
        logger.error("Verifique se sua API key está correta")
else:
    logger.error("❌ Variável de ambiente 'key' não configurada")
    logger.error("Configure a variável 'key' no painel do Render")

# Histórico em memória
histories = {}
MAX_HISTORY_TURNS = 3

# Rota de health check
@app.route('/health')
def health_check():
    logger.info("Health check solicitado")
    return jsonify({"status": "ok", "timestamp": time.time(), "model_loaded": gemini_model is not None})

# Rota principal
@app.route('/')
def index():
    logger.info("Página inicial solicitada")
    try:
        return app.send_static_file('chatbot.html')
    except Exception as e:
        logger.error(f"Erro ao servir chatbot.html: {e}")
        return "Erro ao carregar a página", 500

# Lógica do chatbot
def generate_with_gemini(user_id, message):
    if not gemini_model:
        logger.error("Tentativa de uso do chatbot com modelo não inicializado")
        return "Desculpe, o serviço está temporariamente indisponível. Tente novamente mais tarde."
    
    try:
        chat_session = histories.get(user_id)
        if not chat_session:
            chat_session = gemini_model.start_chat(history=[])
            histories[user_id] = chat_session
            logger.info(f"Nova sessão criada para o usuário {user_id}")
        
        # Limita histórico
        if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
            chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]
            logger.info(f"Histórico truncado para o usuário {user_id}")
        
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        logger.error(f"Erro na API Gemini para o usuário {user_id}: {e}")
        if user_id in histories:
            del histories[user_id]
        return "Desculpe, tive um problema técnico. Tente novamente mais tarde."

# Rota da API
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    start_time = time.time()
    logger.info("Requisição recebida na rota /api/chatbot")
    
    data = request.json
    if not data or 'message' not in data:
        logger.warning("Requisição sem mensagem")
        return jsonify({"error": "Mensagem não fornecida"}), 400
    
    user_message = data.get('message')
    user_id = session.get('user_id', request.remote_addr)
    
    if 'user_id' not in session:
        session['user_id'] = user_id
        logger.info(f"Novo usuário: {user_id}")
    
    ai_response = generate_with_gemini(user_id, user_message)
    
    # Log de performance
    process_time = time.time() - start_time
    logger.info(f"Requisição processada em {process_time:.2f}s")
    
    return jsonify({"reply": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)