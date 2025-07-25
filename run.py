# run.py

import eventlet
import os
import logging

# Essencial para o SocketIO
eventlet.monkey_patch()

from app import create_app, socketio

# Cria a instância do sistema de chamados
app = create_app()

# Importa os eventos do SocketIO
from app import events

if __name__ == '__main__':
    # Este servidor rodará em uma porta diferente, como a 8080
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"🚀 Iniciando servidor do Sistema de Chamados na porta {port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)