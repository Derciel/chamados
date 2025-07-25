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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
socketio = SocketIO(async_mode='eventlet')

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    logging.info("Iniciando a criação da aplicação Flask...")

    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'banco.db')}")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app, cors_allowed_origins="*")
    logging.info("Extensões Flask inicializadas.")

    with app.app_context():
        from app.routes import bp as routes_bp
        app.register_blueprint(routes_bp)
        logging.info("✅ Rotas do sistema de chamados registradas.")
        
        from app.chatbot import init_chatbot_routes
        init_chatbot_routes(app)
        logging.info("✅ Rotas da IA (chatbot) registradas.")

    return app