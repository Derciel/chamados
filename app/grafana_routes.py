# app/grafana_routes.py

from flask import Blueprint, jsonify, request
from . import db
from .models import Chamado
from sqlalchemy import func, cast, Date

# Cria um blueprint específico para a API do Grafana
grafana_bp = Blueprint('grafana_bp', __name__, url_prefix='/api/grafana')

# Lista de métricas que nossa API vai oferecer ao Grafana
METRICAS_DISPONIVEIS = [
    {'value': 'chamados_por_status', 'label': 'Contagem de Chamados por Status'},
    {'value': 'chamados_por_setor', 'label': 'Contagem de Chamados por Setor'},
    {'value': 'tempo_medio_resolucao_geral', 'label': 'Tempo Médio de Resolução (Geral)'},
    {'value': 'evolucao_criacao_chamados', 'label': 'Evolução de Chamados Criados (Série Temporal)'},
]

@grafana_bp.route('/', methods=['GET'])
def health_check():
    """
    Endpoint de verificação de saúde. O Grafana usa para confirmar que a API está no ar.
    """
    return jsonify({"status": "ok"})

@grafana_bp.route('/search', methods=['POST'])
def search_metrics():
    """
    Endpoint de busca. O Grafana usa para descobrir quais métricas estão disponíveis.
    """
    return jsonify(METRICAS_DISPONIVEIS)

@grafana_bp.route('/query', methods=['POST'])
def query_metrics():
    """
    Endpoint principal de consulta. O Grafana envia as métricas selecionadas aqui
    para obter os dados.
    """
    req_data = request.get_json()
    target_metric = req_data['targets'][0]['target']
    
    response = []

    if target_metric == 'chamados_por_status':
        # Consulta para contar chamados por status (formato de tabela)
        query_result = db.session.query(
            Chamado.status, func.count(Chamado.id)
        ).group_by(Chamado.status).all()
        
        response.append({
            "type": "table",
            "columns": [
                {"text": "Status", "type": "string"},
                {"text": "Total", "type": "number"}
            ],
            "rows": [[status, total] for status, total in query_result]
        })

    elif target_metric == 'chamados_por_setor':
        # Consulta para contar chamados por setor (formato de tabela)
        query_result = db.session.query(
            Chamado.setor, func.count(Chamado.id)
        ).group_by(Chamado.setor).all()
        
        response.append({
            "type": "table",
            "columns": [
                {"text": "Setor", "type": "string"},
                {"text": "Total", "type": "number"}
            ],
            "rows": [[setor, total] for setor, total in query_result]
        })
    
    elif target_metric == 'tempo_medio_resolucao_geral':
        # Consulta para calcular o tempo médio de resolução em horas
        # Similar à sua consulta original em /api/graficos
        diff_segundos = func.julianday(Chamado.concluido_em) - func.julianday(Chamado.criado_em)
        tempo_medio_dias = db.session.query(
            func.avg(diff_segundos)
        ).filter(Chamado.concluido_em.isnot(None)).scalar()
        
        tempo_medio_horas = round((tempo_medio_dias or 0) * 24, 2)
        
        response.append({
            "type": "table",
            "columns": [
                {"text": "Métrica", "type": "string"},
                {"text": "Valor (horas)", "type": "number"}
            ],
            "rows": [
                ["Tempo Médio de Resolução", tempo_medio_horas]
            ]
        })

    elif target_metric == 'evolucao_criacao_chamados':
        # Consulta de série temporal: quantos chamados foram criados por dia
        query_result = db.session.query(
            cast(Chamado.criado_em, Date).label('dia'),
            func.count(Chamado.id).label('total')
        ).group_by('dia').order_by('dia').all()
        
        datapoints = []
        for dia, total in query_result:
            # O formato é [valor, timestamp_em_milissegundos]
            timestamp = int(datetime.strptime(dia, '%Y-%m-%d').timestamp() * 1000)
            datapoints.append([total, timestamp])
        
        response.append({
            "target": "Chamados Criados",
            "datapoints": datapoints
        })

    return jsonify(response)