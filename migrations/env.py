import os
from logging.config import fileConfig
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Configuração do Alembic ---
# Este é o objeto de configuração do Alembic, que acessa os valores do alembic.ini
config = context.config

# Interpreta o arquivo .ini para configurar o logging do Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ MELHORIA: Obtém a configuração da aplicação Flask dinamicamente.
# Isso garante que a migração sempre use a mesma configuração da sua aplicação principal.
config.set_main_option("sqlalchemy.url", current_app.config.get('SQLALCHEMY_DATABASE_URI'))

# ✅ MELHORIA: Obtém os metadados do banco de dados a partir da instância do SQLAlchemy
# que está configurada na sua aplicação.
from app import db
target_metadata = db.metadata

# --- Funções de Migração ---

def run_migrations_offline() -> None:
    """Executa migrações em modo 'offline'.
    Isso gera scripts SQL sem se conectar ao banco de dados.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações em modo 'online'.
    Neste modo, o Alembic se conecta ao banco de dados e executa os comandos.
    """
    # ✅ CORREÇÃO: Usa a engine do banco de dados da sua aplicação Flask,
    # garantindo que a conexão seja a mesma.
    connectable = current_app.extensions['sqlalchemy'].engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# --- Lógica Principal ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()