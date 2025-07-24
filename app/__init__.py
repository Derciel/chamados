# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_cors import CORS
from sqlalchemy.pool import NullPool
from flask_migrate import Migrate

# Configura o logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Instâncias Globais ---
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
socketio = SocketIO(async_mode='eventlet')

def create_app():
    """
    Factory para criar e configurar a aplicação Flask completa.
    """
    app = Flask(__name__, instance_relative_config=True)
    logging.info("Iniciando a criação da aplicação Flask...")

    # --- Configurações da Aplicação ---
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "uma-chave-secreta-forte-para-dev")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    database_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'banco.db')}")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
    
    # Garante que a pasta 'instance' exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Inicialização das Extensões ---
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app, cors_allowed_origins="*")
    logging.info("Extensões Flask (DB, Bcrypt, Migrate, CORS, SocketIO) inicializadas.")

    with app.app_context():
        # --- Registro de Blueprints e Rotas ---
        
        # 1. Carrega as rotas do sistema principal de chamados
        from app.routes import bp as routes_bp
        app.register_blueprint(routes_bp)
        logging.info("✅ Rotas do sistema de chamados registradas com sucesso.")
        
        # 2. ✅ CORREÇÃO: Carrega e anexa as rotas do chatbot
        from app.chatbot import init_chatbot_routes
        init_chatbot_routes(app)
        logging.info("✅ Rotas da IA (chatbot) registradas com sucesso.")

    return app