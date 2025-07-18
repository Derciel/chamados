from app import create_app, socketio

app = create_app()

from app import events 

if __name__ == "__main__":
    # Inicia o servidor usando o SocketIO, que gerencia o Flask internamente.
    socketio.run(app, debug=True, port=5000)