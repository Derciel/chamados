# llama_bot.py
from llama_cpp import Llama

llm = Llama(
    model_path="models/llama-2-7b-chat.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4
)

def gerar_resposta(pergunta):
    prompt = f"[INST] {pergunta} [/INST]"
    resposta = llm(prompt, max_tokens=256, stop=["</s>"])
    return resposta["choices"][0]["text"].strip()
