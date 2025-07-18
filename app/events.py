# Em um novo arquivo chamado events.py
from sqlalchemy import event
from .models import Chamado
from . import socketio # Importa a instância do __init__.py

def formatar_chamado(chamado):
    """Função auxiliar para formatar os dados do chamado."""
    return {
        'id': chamado.id,
        'nome': chamado.nome,
        'setor': chamado.setor,
        'descricao': chamado.descricao,
        'status': chamado.status,
        'criado_em': chamado.criado_em.isoformat() + 'Z' if chamado.criado_em else None,
        'concluido_em': chamado.concluido_em.isoformat() + 'Z' if chamado.concluido_em else None
    }
@event.listens_for(Chamado, 'after_insert')
def on_chamado_criado(mapper, connection, target):
    """Dispara quando um novo chamado é criado."""
    print(f"EVENTO: Novo chamado criado - ID: {target.id}")
    socketio.emit('novo_chamado', formatar_chamado(target))

@event.listens_for(Chamado, 'after_update')
def on_chamado_atualizado(mapper, connection, target):
    """Dispara quando um chamado existente é atualizado."""
    print(f"EVENTO: Chamado atualizado - ID: {target.id}")
    socketio.emit('chamado_atualizado', formatar_chamado(target))
    
@event.listens_for(Chamado, 'after_delete')
def on_chamado_excluido(mapper, connection, target):
    """Dispara após um chamado ser deletado do banco."""
    print(f"EVENTO: Chamado excluído - ID: {target.id}")
    # Envia um evento para o frontend com o ID do chamado removido
    socketio.emit('chamado_excluido', {'id': target.id})