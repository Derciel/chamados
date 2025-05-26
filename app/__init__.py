import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    is_production = os.environ.get("RENDER") == "true"

    if is_production:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("⚠️ A variável DATABASE_URL não está configurada!")
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "chave-secreta")
    
    app.config['GLPI_URL'] = os.environ.get("GLPI_URL")
    app.config['GLPI_APP_TOKEN'] = os.environ.get("GLPI_APP_TOKEN")
    app.config['GLPI_USER_TOKEN'] = os.environ.get("GLPI_USER_TOKEN")
    app.config['GLPI_WEBHOOK_SECRET'] = os.environ.get("GLPI_WEBHOOK_SECRET", "kkk@123451")

    db.init_app(app)
    bcrypt.init_app(app)

    # ✅ Blueprints
    from app.routes import bp as routes_bp
    from app.spotify_routes import spotify_bp
    from app.chatbot_routes import chatbot_bp
    from app.grafana_routes import grafana_bp
    from app.integration_routes import integration_bp

    app.register_blueprint(routes_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(grafana_bp)
    app.register_blueprint(integration_bp)

    with app.app_context():
        db.create_all()

    return app
