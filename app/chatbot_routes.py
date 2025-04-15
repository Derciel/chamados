import os
import requests
from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint('chatbot_bp', __name__)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

headers = {
    "Authorization": f"Bearer {HUGGING_FACE_TOKEN}"
}

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.json.get("question")
    if not user_input:
        return jsonify({"error": "Pergunta vazia."}), 400

    payload = {
        "inputs": f"Responda de forma clara e objetiva para dúvidas de TI: {user_input}"
    }

    response = requests.post(MODEL_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        return jsonify({"error": "Erro ao consultar o modelo."}), 500

    output = response.json()
    resposta = output[0]["generated_text"] if isinstance(output, list) else output.get("generated_text")
    return jsonify({"answer": resposta})
