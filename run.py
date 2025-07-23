# run.py

import eventlet
import eventlet.wsgi
import socket
import os

eventlet.monkey_patch()

from app import create_app, socketio
from app import events
from socketio import WSGIApp# Garante que os eventos sejam registrados

app = create_app()

def porta_disponivel(porta):
    """Verifica se a porta está disponível."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', porta))
            return True
        except OSError:
            return False

if __name__ == '__main__':
    porta_inicial = int(os.environ.get('PORT', 9090))
    porta = porta_inicial

    # Tenta encontrar uma porta livre entre 9090 e 9100
    while not porta_disponivel(porta) and porta < 9100:
        porta += 1

    if porta > 9099:
        print("❌ Nenhuma porta disponível entre 9090 e 9100.")
        exit(1)

    print(f"🚀 Iniciando servidor Eventlet na porta {porta}...")
    print(f"🌐 Acesse: http://localhost:{porta}")

    eventlet.wsgi.server(eventlet.listen(('', porta)), WSGIApp(socketio, app))
