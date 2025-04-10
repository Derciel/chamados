from __future__ import with_statement
import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
fileConfig(ini_path)

# Este é o objeto de configuração do Alembic
config = context.config

# Interpretar o arquivo .ini para configurar logs
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Importa sua factory de app e o db
from app import create_app, db

# Cria uma instância do app e empurra o contexto
app = create_app()
app.app_context().push()

# Dizemos ao Alembic qual 'metadata' usar
target_metadata = db.metadata

# Configura a url do banco a partir do app
config.set_main_option('sqlalchemy.url', str(db.engine.url))

def run_migrations_offline():
    """Executa migrações em modo offline, sem precisar de DB real."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, 
        target_metadata=target_metadata,
        literal_binds=True, 
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Executa migrações em modo online, conectando-se ao DB."""
    connectable = db.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Decide se roda offline ou online
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
