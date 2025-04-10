import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    # Detecta se está rodando no Render (produção) ou local
    is_production = os.environ.get("RENDER") == "true"

    if is_production:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/banco.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'chave-secreta'

    db.init_app(app)
    bcrypt.init_app(app)

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    with app.app_context():
        db.create_all()

    return app
