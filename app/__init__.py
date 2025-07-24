import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_cors import CORS
from sqlalchemy.pool import NullPool
from flask_migrate import Migrate

# --- Instâncias Globais ---
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
# ✅ CORREÇÃO: 'async_mode' definido na criação inicial do objeto.
socketio = SocketIO(async_mode='eventlet')

def create_app():
    """
    Factory para criar e configurar a aplicação Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- Configurações da Aplicação ---
    # Usa uma chave secreta do ambiente ou um fallback seguro para desenvolvimento.
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "uma-chave-secreta-forte-para-dev")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Configuração de Banco de Dados (Produção vs. Desenvolvimento) ---
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Ambiente de produção (Render, etc.)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Ambiente de desenvolvimento local
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
    
    # Desativa o pool de conexões do SQLAlchemy para ser compatível com eventlet.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}

    # --- Inicialização das Extensões ---
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    # ✅ MELHORIA: CORS configurado de forma central e clara.
    # Permite requisições de qualquer origem para todas as rotas que começam com /api/
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ✅ CORREÇÃO: 'cors_allowed_origins' ajustado para permitir qualquer origem.
    # Em produção, você pode restringir para o domínio do seu frontend.
    socketio.init_app(app, cors_allowed_origins="*")

    # --- Registro de Blueprints e Rotas ---
    with app.app_context():
        # ✅ CORREÇÃO: Importa apenas o blueprint que realmente existe.
        from app.routes import bp as routes_bp
        app.register_blueprint(routes_bp)
        
        # Anexa as rotas do chatbot à aplicação principal.
        from app.chatbot import init_chatbot_routes
        init_chatbot_routes(app)

        # 💡 MELHORIA: db.create_all() foi removido.
        # A criação e atualização do banco de dados deve ser gerenciada
        # exclusivamente pelos comandos do Flask-Migrate (flask db upgrade).

    return app