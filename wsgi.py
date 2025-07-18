import eventlet
from app import create_app, socketio


app = create_app()

from app import events 

if __name__ == "__main__":
    # Inicia o servidor usando o SocketIO, que gerencia o Flask internamente.
    # ✅ Rodando na porta 8080 para não conflitar com a IA na porta 5000
    socketio.run(app, debug=True, port=8080)