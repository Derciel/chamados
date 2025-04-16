# llama_bot.py
from llama_cpp import Llama
from googletrans import Translator

# Inicializa modelo LLaMA
llm = Llama(
    model_path="models/llama-2-7b-chat.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4
)

# Inicializa tradutor
tradutor = Translator()

def gerar_resposta(pergunta):
    prompt = f"[INST] {pergunta} [/INST]"
    resposta_bruta = llm(prompt, max_tokens=256, stop=["</s>"])
    resposta = resposta_bruta["choices"][0]["text"].strip()

    # Traduz automaticamente para português
    traduzida = tradutor.translate(resposta, dest="pt").text
    return traduzida
