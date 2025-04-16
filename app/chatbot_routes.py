import os
import requests
from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint('chatbot_bp', __name__)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

# URLs dos modelos
DIALOGPT_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
FALCON_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-rw-1b"

headers = {
    "Authorization": f"Bearer {HUGGING_FACE_TOKEN}",
    "Content-Type": "application/json"
}

def consultar_modelo(prompt, model_url):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 128,
            "temperature": 0.7,
            "do_sample": True
        }
    }

    response = requests.post(model_url, headers=headers, json=payload)
    if response.status_code == 200:
        output = response.json()
        if isinstance(output, list) and "generated_text" in output[0]:
            return output[0]["generated_text"]
        else:
            return output.get("generated_text", "")
    elif response.status_code == 503:
        return "O modelo está carregando. Tente novamente em instantes."
    else:
        return f"Erro ao consultar o modelo ({response.status_code}): {response.text}"

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    user_input = request.json.get("question")
    if not user_input:
        return jsonify({"error": "Pergunta vazia."}), 400

    prompt = f"{user_input}"

    # Tenta com DialoGPT-small
    resposta = consultar_modelo(prompt, DIALOGPT_URL)
    if resposta.startswith("Erro ao consultar o modelo"):
        # Fallback para Falcon-RW-1B
        resposta = consultar_modelo(prompt, FALCON_URL)

    return jsonify({"answer": resposta})
