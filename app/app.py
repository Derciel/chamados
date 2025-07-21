import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# --- 1. Configuração do Ambiente e Modelo ---

# ✅ Mude para False se você não tem uma GPU NVIDIA ou se estiver tendo problemas.
# Isso forçará o uso da CPU (será lento, mas é bom para testar).
USE_GPU = True
MODEL_NAME = "LGAI-EXAONE/EXAONE-4.0-1.2B"

# Aponta o cache da Hugging Face para uma pasta local para evitar redownloads
os.environ['HF_HOME'] = './huggingface_cache'

print("--- INICIANDO SERVIÇO DE IA ---")
print(f"Modelo a ser carregado: {MODEL_NAME}")
print(f"Modo de uso de GPU: {'ATIVADO' if USE_GPU else 'DESATIVADO'}")

model = None
tokenizer = None

try:
    print("\n[ETAPA 1/3] Carregando o Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("✅ Tokenizer carregado com sucesso!")

    print("\n[ETAPA 2/3] Carregando o modelo EXAONE...")
    print("Atenção: Esta etapa pode consumir muita RAM e demorar vários minutos.")
    
    device_map_config = "auto" if USE_GPU else "cpu"
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map=device_map_config
    )
    print("✅ Modelo EXAONE carregado com sucesso na memória!")

except Exception as e:
    print(f"\n❌ ERRO CRÍTICO AO CARREGAR O MODELO: {e}")
    print("Causas comuns: Falta de RAM/VRAM, problema de drivers da GPU, ou falha no download do modelo.")

# --- 2. Aplicação Flask ---
print("\n[ETAPA 3/3] Configurando o servidor web (Flask)...")
app = Flask(__name__)
CORS(app)
print("✅ Servidor web configurado.")

@app.route('/')
def health_check():
    """Rota de 'health check' para verificar se o servidor está no ar."""
    if model and tokenizer:
        return "Servidor da IA está no ar e o modelo está carregado."
    else:
        return "Servidor da IA está no ar, mas HOUVE UM ERRO AO CARREGAR O MODELO. Verifique os logs.", 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    if not model or not tokenizer:
        return jsonify({"error": "O modelo de IA não está carregado. Verifique os logs do servidor."}), 503

    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({"error": "Mensagem não encontrada"}), 400

    user_message = data.get('message')
    prompt = f"<|user|>\n{user_message}<|endoftext|>\n<|assistant|>\n"
    
    try:
        print(f"\nRecebendo prompt: {user_message}")
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        print("Gerando resposta...")
        outputs = model.generate(**inputs, max_new_tokens=250, eos_token_id=tokenizer.eos_token_id)
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        bot_reply = full_response.split("<|assistant|>")[-1].strip()
        print(f"Resposta gerada: {bot_reply}")

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"❌ Erro durante a geração da resposta: {e}")
        return jsonify({"error": "Ocorreu um erro ao gerar a resposta."}), 500


if __name__ == '__main__':
    print("\n🚀 Servidor pronto! Pressione CTRL+C para parar.")
    app.run(host='0.0.0.0', port=5000)