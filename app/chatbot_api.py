from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_bot import gerar_resposta

from pyngrok import ngrok
import os

app = Flask(__name__)
CORS(app)

@app.route("/chatbot", methods=["POST"])
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

if __name__ == "__main__":
    # Inicia ngrok automaticamente na porta 5000
    port = 5000
    public_url = ngrok.connect(port)
    print(f"✅ API LLaMA disponível publicamente em: {public_url}")
    print(f"ℹ️ Use essa URL no front-end do chatbot.")

    # Roda o Flask normalmente
    app.run(port=port)
