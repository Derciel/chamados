# app.py (Atualizado para EXAONE 4.0 1.2B)

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# --- 1. Configuração do Modelo EXAONE ---
MODEL_NAME = "LGAI-EXAONE/EXAONE-4.0-1.2B"

print(f"Carregando o modelo EXAONE: {MODEL_NAME}")
model = None
tokenizer = None
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    print("✅ Modelo EXAONE carregado com sucesso!")
except Exception as e:
    print(f"❌ Erro CRÍTICO ao carregar o modelo EXAONE: {e}")


# --- 2. Aplicação Flask ---
app = Flask(__name__)
CORS(app)


@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    if not model or not tokenizer:
        return jsonify({"error": "O modelo de IA não está carregado. Verifique os logs do servidor."}), 503

    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({"error": "Mensagem não encontrada"}), 400

    user_message = data.get('message')

    # --- 3. Lógica de Geração de Resposta com EXAONE ---
    # O formato do prompt é diferente do LLaMA
    prompt = f"<|user|>\n{user_message}<|endoftext|>\n<|assistant|>\n"
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=250, eos_token_id=tokenizer.eos_token_id)
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extrai apenas a resposta do assistente
        bot_reply = full_response.split("<|assistant|>")[-1].strip()
        
        print(f"Usuário: {user_message}\nIA: {bot_reply}")

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"❌ Erro durante a geração da resposta: {e}")
        return jsonify({"error": "Ocorreu um erro ao gerar a resposta."}), 500


if __name__ == '__main__':
    print("🚀 Servidor pronto! Rodando com o modelo EXAONE.")
    app.run(host='0.0.0.0', port=5000)