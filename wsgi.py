# wsgi.py

import eventlet

# ESSENCIAL: Modifica as bibliotecas padrão do Python para serem compatíveis com eventlet.
# Deve ser a PRIMEIRA coisa a ser executada no seu app.
eventlet.monkey_patch()

# AGORA, e somente agora, importe a factory da sua aplicação e o objeto socketio.
from app import create_app, socketio

# Cria a instância da aplicação que o Gunicorn irá servir.
app = create_app()

# Importa os eventos do SocketIO para que sejam registrados corretamente.
# É importante que isso venha DEPOIS de create_app() e da inicialização do socketio.
from app import events 

# Este bloco é apenas para desenvolvimento local e não é usado pelo Gunicorn.
if __name__ == "__main__":
    # Inicia o servidor de desenvolvimento na porta 8080
    socketio.run(app, debug=True, port=8080)