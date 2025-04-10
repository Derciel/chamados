# setup_db.py
from app import create_app, db

def criar_banco():
    app = create_app()  # Cria a instância do Flask
    with app.app_context():
        db.create_all()  # Cria as tabelas se não existirem
        print("Banco de dados criado com sucesso!")

if __name__ == "__main__":
    criar_banco()
