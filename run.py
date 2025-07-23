# run.py

import eventlet
import eventlet.wsgi
import os

# Essencial: Modifica as bibliotecas padrão do Python para serem assíncronas.
eventlet.monkey_patch()

# Importa a factory da aplicação e o objeto socketio.
from app import create_app, socketio

# Cria a instância da aplicação.
app = create_app()

# Importa os eventos do SocketIO para que sejam registrados.
from app import events

if __name__ == '__main__':
    # Obtém a porta da variável de ambiente PORT, com um padrão de 8080.
    # Plataformas como a Render definem a porta dinamicamente.
    port = int(os.environ.get('PORT', 8080))
    
    print(f"🚀 Iniciando servidor Eventlet na porta {port}...")
    
    # Inicia um servidor WSGI do próprio eventlet, que é totalmente compatível com Socket.IO.
    # Passamos o 'socketio' como a aplicação, pois ele gerencia tanto o Flask quanto os WebSockets.
    eventlet.wsgi.server(eventlet.listen(('', port)), socketio)