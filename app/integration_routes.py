# app/integration_routes.py

import logging
from flask import Blueprint, request, jsonify, current_app
from . import db
from .models import Chamado
from datetime import datetime

integration_bp = Blueprint('integration_bp', __name__, url_prefix='/api/integration')

def _reverse_map_status(glpi_status_id: int) -> str:
    """Mapeia o ID de status do GLPI para o nome do status local."""
    # IDs Padrão do GLPI: 1:Novo, 2:Em atendimento, 4:Pendente, 5:Solucionado, 6:Fechado
    mapping = {
        1: 'Aberto',
        2: 'Em andamento',
        4: 'Pendente',
        5: 'Finalizado',
        6: 'Finalizado' # Mapeamos Fechado para Finalizado também
    }
    return mapping.get(glpi_status_id, 'Em andamento') # Padrão

@integration_bp.route('/glpi-webhook', methods=['POST'])
def glpi_webhook():
    """
    Recebe e processa webhooks vindos do GLPI.
    """
    # 1. Validação de Segurança
    secret_recebido = request.headers.get('X-Webhook-Secret')
    secret_esperado = current_app.config['GLPI_WEBHOOK_SECRET']

    if not secret_recebido or secret_recebido != secret_esperado:
        logging.warning("Webhook recebido com segredo inválido ou ausente.")
        return jsonify({"erro": "Acesso não autorizado"}), 403

    # 2. Processamento do Payload
    data = request.get_json()
    if not data or 'event' not in data:
        return jsonify({"erro": "Payload inválido"}), 400

    logging.info(f"Webhook do GLPI recebido. Evento: {data['event']}")
    
    try:
        # Pega o ID do ticket do GLPI a partir do payload
        # A estrutura do payload pode variar um pouco, por isso usamos .get()
        ticket_data = data.get('ticket', {})
        glpi_id = ticket_data.get('id')

        if not glpi_id:
            logging.warning("Webhook não continha um ID de ticket do GLPI.")
            return jsonify({"status": "recebido, mas ignorado (sem ID)"})

        # Encontra o chamado correspondente no nosso banco de dados
        chamado_local = Chamado.query.filter_by(glpi_ticket_id=glpi_id).first()
        if not chamado_local:
            logging.warning(f"Recebido webhook para GLPI ID {glpi_id}, mas nenhum chamado local corresponde.")
            return jsonify({"status": "recebido, mas ignorado (chamado local não encontrado)"})
        
        # 3. Lógica baseada no evento
        if data['event'] == 'ticket_update':
            novo_status_id = ticket_data.get('status')
            if novo_status_id:
                chamado_local.status = _reverse_map_status(novo_status_id)
                logging.info(f"Status do chamado {chamado_local.id} atualizado para '{chamado_local.status}' via webhook.")

        elif data['event'] == 'followup_add':
            followup_data = data.get('followup', {})
            conteudo_followup = followup_data.get('content_text') # O GLPI envia o texto puro aqui
            if conteudo_followup:
                # Adiciona o acompanhamento do GLPI à observação local
                observacao_atual = chamado_local.observacao or ""
                nova_observacao = f"{observacao_atual}\n\n[Acompanhamento GLPI - {datetime.now().strftime('%d/%m/%Y %H:%M')}]:\n{conteudo_followup}"
                chamado_local.observacao = nova_observacao.strip()
                logging.info(f"Acompanhamento adicionado ao chamado {chamado_local.id} via webhook.")
        
        db.session.commit()

    except Exception as e:
        logging.error(f"Erro ao processar webhook do GLPI: {e}")
        db.session.rollback()
        return jsonify({"erro": "Erro interno ao processar o webhook"}), 500

    return jsonify({"status": "recebido com sucesso"}), 200