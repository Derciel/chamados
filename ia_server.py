# ia_server.py

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS # Garanta que a importação está aqui
import google.generativeai as genai

# --- Configuração do Servidor e Logging ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ CORREÇÃO: Configuração de CORS explícita e robusta.
# Permite requisições de qualquer origem para todas as rotas que começam com /api/
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Configuração da API Gemini ---
# ... (o resto do seu código da IA permanece o mesmo) ...
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
gemini_model = None
# ...

# --- Rota da API ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    # ... (sua lógica da rota) ...
    pass

if __name__ == '__main__':
    # Este modo é apenas para desenvolvimento local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)