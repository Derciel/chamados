import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

# As instâncias continuam sendo criadas aqui, no escopo global.
db = SQLAlchemy()
bcrypt = Bcrypt()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # --- Configurações Essenciais ---
    is_production = os.environ.get("RENDER") == "true"
    if is_production:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("⚠️ A variável DATABASE_URL não está configurada para produção!")
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "uma-chave-secreta-forte-de-fallback")
    
    # Inicialização dos componentes com o app factory
    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # --- Blueprints ---
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # --- Contexto da Aplicação ---
    with app.app_context():
        # A importação do 'events' foi removida daqui para evitar importação circular.
        db.create_all()

    return app