# run.py

import eventlet
import os

# ESSENCIAL: Modifica as bibliotecas padrão do Python para serem assíncronas.
# Deve ser a primeira coisa a ser executada no seu app.
eventlet.monkey_patch()

# AGORA, e somente agora, importe a factory da sua aplicação e o objeto socketio.
from app import create_app, socketio

# Cria a instância da aplicação que o servidor irá rodar.
app = create_app()

# Importa os eventos do SocketIO para que sejam registrados corretamente.
from app import events

# Este bloco é apenas para desenvolvimento local e não é usado na Render.
if __name__ == '__main__':
    # Obtém a porta da variável de ambiente, com um padrão de 8080.
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando servidor de desenvolvimento na porta {port}...")
    # Use o socketio.run para rodar o servidor de desenvolvimento compatível.
    socketio.run(app, host='0.0.0.0', port=port, debug=True)