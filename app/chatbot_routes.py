import os
from flask import Blueprint, request, jsonify

# Cria um blueprint para rotas do chatbot
chatbot_bp = Blueprint('chatbot_bp', __name__)

# Tenta importar o modelo local apenas se não for o Render
if not os.getenv("RENDER_ENV"):
    from llama_bot import gerar_resposta
else:
    def gerar_resposta(pergunta):
        return "🤖 Assistente LLaMA está disponível apenas no ambiente local."

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    pergunta = data.get("question", "")
    if not pergunta:
        return jsonify({"error": "Pergunta não enviada"}), 400

    try:
        resposta = gerar_resposta(pergunta)
        return jsonify({"answer": resposta})
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar resposta: {str(e)}"}), 500
