# ia_server.py
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
app.secret_key = os.urandom(24)  # Necessário para sessões
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuração do CORS mais restritiva para segurança
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuração da API Gemini
GEMINI_API_KEY = os.getenv("key")
gemini_model = None

SYSTEM_INSTRUCTION = """
Você é um assistente virtual especializado em Tecnologia da Informação (TI) da empresa Nicopel Embalagens.
Sua única função é responder perguntas sobre hardware, software, redes, programação e problemas técnicos.
Se o usuário perguntar sobre qualquer outro assunto, recuse educadamente e reafirme sua especialidade.
Respostas curtas e diretas são preferíveis.
"""

# Inicialização do modelo Gemini
if not GEMINI_API_KEY:
    logging.warning("Variável de ambiente GEMINI_API_KEY não configurada.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",  # Modelo mais leve
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config={"max_output_tokens": 500}  # Limita o tamanho da resposta
        )
        logging.info("✅ Modelo Gemini configurado com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao configurar Gemini: {e}")

# Histórico em memória (será perdido a cada reinicialização)
histories = {}
MAX_HISTORY_TURNS = 3  # Reduzido para economizar memória

# Rota de health check para o Render
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "timestamp": time.time()})

# Rota principal para servir o frontend
@app.route('/')
def index():
    return app.send_static_file('chatbot.html')

# Lógica do chatbot otimizada
def generate_with_gemini(user_id, message):
    if not gemini_model:
        return "Desculpe, o serviço de chatbot está temporariamente indisponível."
    
    try:
        # Tenta obter a sessão do usuário ou cria uma nova
        chat_session = histories.get(user_id)
        if not chat_session:
            chat_session = gemini_model.start_chat(history=[])
            histories[user_id] = chat_session
        
        # Limita o histórico para economizar memória
        if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
            chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]
        
        # Envia a mensagem para o Gemini
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        logging.exception(f"Erro na API Gemini: {e}")
        # Remove a sessão do usuário em caso de erro
        if user_id in histories:
            del histories[user_id]
        return "Desculpe, tive um problema técnico. Tente novamente."

# Rota da API do chatbot
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Mensagem não fornecida."}), 400
    
    user_message = data.get('message')
    # Usa session ID ou IP como identificador
    user_id = session.get('user_id', request.remote_addr)
    
    # Salva o ID do usuário na sessão
    if 'user_id' not in session:
        session['user_id'] = user_id
    
    ai_response = generate_with_gemini(user_id, user_message)
    return jsonify({"reply": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)