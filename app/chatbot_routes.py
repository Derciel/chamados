import os
import requests
from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint('chatbot_bp', __name__)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
MODEL_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

headers = {
    "Authorization": f"Bearer {HUGGING_FACE_TOKEN}",
    "Content-Type": "application/json"
}

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.json.get("question")
    if not user_input:
        return jsonify({"error": "Pergunta vazia."}), 400

    prompt = f"Responda de forma clara e objetiva uma dúvida de TI: {user_input}"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 128,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload)
        if response.status_code == 200:
            output = response.json()
            resposta = output[0]["generated_text"] if isinstance(output, list) else output.get("generated_text", "Erro")
            return jsonify({"answer": resposta})
        else:
            return jsonify({
                "error": f"Erro ao consultar o modelo ({response.status_code}): {response.text}"
            }), 500
    except Exception as e:
        return jsonify({"error": f"Erro na requisição: {str(e)}"}), 500
