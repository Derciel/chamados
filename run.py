# run.py

import eventlet
import os
import logging

# ESSENCIAL: Modifica as bibliotecas para serem assíncronas.
# Deve ser a primeira coisa a ser executada.
eventlet.monkey_patch()

# AGORA, importe a factory e o objeto socketio do seu pacote 'app'.
from app import create_app, socketio

# Cria a instância completa da aplicação (que já inclui o sistema E a IA).
app = create_app()

# Importa os eventos do SocketIO para que sejam registrados.
from app import events

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"🚀 Iniciando servidor completo (Sistema + IA) na porta {port}...")
    
    # Inicia o servidor com SocketIO, que gerencia o Flask internamente.
    socketio.run(app, host='0.0.0.0', port=port, debug=True)