# run.py
import eventlet
import os
import logging
eventlet.monkey_patch()
from app import create_app, socketio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    app = create_app()
    logging.info("Aplicativo Flask inicializado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao inicializar o aplicativo Flask: {e}")
    raise

from app import events

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"🚀 Iniciando servidor completo (Sistema + IA) na porta {port}...")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logging.error(f"Erro ao iniciar o servidor: {e}")
        raise