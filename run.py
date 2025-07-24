# run.py (Corrected for dotenv)

import os
import socket
from dotenv import load_dotenv # Add this import!

# --- Load environment variables from .env file FIRST ---
load_dotenv() # This line must come before anything that tries to read os.getenv/os.environ
# --- End .env loading ---

from app import create_app, socketio
# from app import events  # Ensure events are imported/registered as needed

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
    porta_inicial = int(os.environ.get('PORT', 5000))
    porta = porta_inicial

    while not porta_disponivel(porta) and porta < 5010: # Adjust upper limit if needed
        porta += 1

    if not porta_disponivel(porta):
        print(f"❌ Nenhuma porta disponível entre {porta_inicial} e {porta-1}.")
        exit(1)

    print(f"🚀 Iniciando servidor Flask-SocketIO na porta {porta}...")
    print(f"🌐 Acesse: http://localhost:{porta}")

    socketio.run(app, host='0.0.0.0', port=porta, debug=True)