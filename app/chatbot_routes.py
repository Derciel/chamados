from flask import Blueprint, request, jsonify
from app.llama_bot import gerar_resposta

chatbot_bp = Blueprint('chatbot_bp', __name__)

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.json.get("question")
    if not user_input:
        return jsonify({"error": "Pergunta vazia."}), 400

    try:
        resposta = gerar_resposta(user_input)
        return jsonify({"answer": resposta})
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar resposta: {str(e)}"}), 500
