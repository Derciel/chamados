from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime
import os, logging
from sqlalchemy import func, case
from . import db, bcrypt
from .models import Usuario, Chamado, HistoricoChamado
from sqlalchemy.sql import func
from sqlalchemy import text
# A rota do spotify é um componente separado, mantemos a importação caso esteja em uso.
# from app.spotify_routes import spotify_bp 

bp = Blueprint('routes_bp', __name__)


@bp.route('/')
def home():
    if 'email' in session:
        if session.get('email') == 'adm@adm':
            return redirect(url_for('routes_bp.dashboard'))
        else:
            # Usuários não-admin são direcionados para abrir um chamado.
            return redirect(url_for('routes_bp.novo_chamado'))
    return redirect(url_for('routes_bp.login'))

# ROTA DO DASHBOARD OTIMIZADA
@bp.route('/dashboard')
def dashboard():
    """
    Esta rota agora apenas serve a página do dashboard.
    Toda a lógica de carregar dados e gráficos foi movida para o JavaScript,
    que consumirá as nossas APIs, tornando a página dinâmica e em tempo real.
    """
    if 'email' not in session or session.get('email') != 'adm@adm':
        flash('Acesso restrito ao administrador', 'danger')
        return redirect(url_for('routes_bp.login'))

    # Não precisamos mais calcular dados aqui. O frontend fará isso.
    return render_template("dashboard.html")

# ROTA '/novo-chamado' ADICIONADA PARA CORRIGIR O ERRO
@bp.route('/novo-chamado', methods=['GET', 'POST'])
def novo_chamado():
    """
    Rota para usuários criarem um novo chamado.
    """
    if 'usuario_id' not in session:
        flash('Faça login para abrir um chamado.', 'warning')
        return redirect(url_for('routes_bp.login'))

    if request.method == 'POST':
        novo_chamado_obj = Chamado(
            nome=request.form.get('nome'),
            setor=request.form.get('setor'),
            descricao=request.form.get('descricao'),
            status='Aberto',
            user_id=session['usuario_id'],
            funcionario_id=session.get('funcionario_id')
        )
        
        # Aqui você pode adicionar a lógica de upload de imagem se necessário
        # ...
        
        db.session.add(novo_chamado_obj)
        db.session.commit()
        
        flash("Chamado registrado com sucesso!", "success")
        return redirect(url_for('routes_bp.novo_chamado'))

    return render_template('novo_chamado.html')


# --- ROTAS DE AUTENTICAÇÃO (Sem alterações) ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
            session['usuario_id'] = usuario.id
            session['email'] = usuario.email
            session['funcionario_id'] = usuario.funcionario_id

            if usuario.email == 'adm@adm':
                flash("Login administrativo realizado!", "success")
                return redirect(url_for('routes_bp.dashboard'))
            else:
                flash("Login de usuário realizado!", "success")
                return redirect(url_for('routes_bp.novo_chamado'))
        
        flash('Credenciais inválidas', 'danger')

    return render_template('login.html', email=request.args.get('email', ''), senha=request.args.get('senha', ''))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            novo_usuario = Usuario(
                email=request.form['email'],
                senha_hash=bcrypt.generate_password_hash(request.form['senha']).decode('utf-8'),
                funcionario_id=request.form['funcionario_id'],
                security_question=request.form['security_question'],
                security_answer=request.form['security_answer']
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Conta criada com sucesso! Faça o login.", "success")
            return redirect(url_for('routes_bp.login', email=request.form['email']))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro no registro: {str(e)}")
            flash("Erro ao criar conta. Verifique os dados.", "danger")
    
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash("Você foi desconectado.")
    return redirect(url_for('routes_bp.login'))

# --- ROTAS DA API (Para o nosso frontend JavaScript) ---

@bp.route('/api/chamados', methods=['GET'])
def listar_chamados():
    """
    API que retorna a lista completa de chamados para a carga inicial do dashboard.
    """
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    chamados = Chamado.query.order_by(Chamado.criado_em.desc()).all()
    
    return jsonify([
        {
            'id': c.id,
            'nome': c.nome,
            'setor': c.setor,
            'descricao': c.descricao,
            'status': c.status,
            'observacao': c.observacao,
            'imagem_url': c.imagem_url,
            'criado_em': c.criado_em.isoformat() + 'Z' if c.criado_em else None,
            'iniciado_em': c.iniciado_em.isoformat() + 'Z' if c.iniciado_em else None,
            'andamento_em': c.andamento_em.isoformat() + 'Z' if c.andamento_em else None,
            'concluido_em': c.concluido_em.isoformat() + 'Z' if c.concluido_em else None
        } for c in chamados
    ])

@bp.route('/api/chamados/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def chamado_detalhe(id):
    """
    API para gerenciar um chamado específico (ver, atualizar, deletar).
    """
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    chamado = Chamado.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify({
            'id': chamado.id, 'nome': chamado.nome, 'setor': chamado.setor,
            'descricao': chamado.descricao, 'status': chamado.status, 'observacao': chamado.observacao,
            'criado_em': chamado.criado_em.isoformat() if chamado.criado_em else None
        })

    elif request.method == 'PUT':
        
        chamado = Chamado.query.get_or_404(id)
        data = request.get_json()
        
        
        status_anterior = chamado.status

        
        if 'status' in data and data['status'] != status_anterior:
            novo_status = data['status']

            novo_historico = HistoricoChamado(
                chamado_id=chamado.id,
                valor_anterior=status_anterior,
                valor_novo=novo_status,
                observacao=data.get('observacao', 'Status alterado pelo painel.')
            )
            db.session.add(novo_historico)

            chamado.status = novo_status
            if novo_status == "Em andamento" and not chamado.andamento_em:
                chamado.andamento_em = datetime.utcnow()
            elif novo_status in ["Concluído", "Finalizado", "Resolvido"] and not chamado.concluido_em:
                chamado.concluido_em = datetime.utcnow()
        
        # A lógica para atualizar a observação principal também pode ser ajustada
        if 'observacao' in data:
            chamado.observacao = data['observacao']
            
        db.session.commit()
        return jsonify({'mensagem': 'Chamado atualizado com sucesso'})

    elif request.method == 'DELETE':
        db.session.delete(chamado)
        db.session.commit()
        return jsonify({'mensagem': 'Chamado excluído'}), 204

    elif request.method == 'DELETE':
        # O histórico é deletado automaticamente por causa do 'cascade' que configuramos no modelo
        db.session.delete(chamado)
        db.session.commit()
        return jsonify({'mensagem': 'Chamado excluído com sucesso'}), 200
    
@bp.route("/api/graficos")
def graficos():
    """
    API que retorna dados agregados para os gráficos do dashboard.
    """
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    total_por_status = dict(db.session.query(Chamado.status, func.count(Chamado.id)).group_by(Chamado.status).all())
    total_por_setor = dict(db.session.query(Chamado.setor, func.count(Chamado.id)).group_by(Chamado.setor).all())

    return jsonify({
        'status_distribuicao': total_por_status,
        'setor_distribuicao': total_por_setor
    })

@bp.route("/api/notificacoes")
def notificacoes():
    """
    API que busca chamados com status importantes que ainda não foram notificados ao usuário.
    """
    if "usuario_id" not in session:
        return jsonify([])

    usuario_id = session["usuario_id"]

    # ✅ CORREÇÃO: Agora busca por múltiplos status relevantes.
    status_para_notificar = ["Finalizado", "Resolvido", "Concluído", "Pendente"]

    chamados_nao_notificados = Chamado.query.filter(
        Chamado.user_id == usuario_id,
        Chamado.status.in_(status_para_notificar), # Usa .in_() para verificar a lista de status
        Chamado.notificado == False
    ).all()

    # Retorna uma lista mais completa para a notificação
    return jsonify([
        {
            "id": ch.id, 
            "nome": ch.nome, 
            "setor": ch.setor,
            "status": ch.status # Inclui o status para a mensagem ser mais clara
        }
        for ch in chamados_nao_notificados
    ])

@bp.route("/api/notificacoes/<int:id>/marcar", methods=["POST"])
def marcar_notificacao(id):
    if "usuario_id" not in session:
        return jsonify({"erro": "Não logado"}), 403

    usuario_id = session["usuario_id"]
    chamado = Chamado.query.get(id)
    if not chamado or chamado.user_id != usuario_id:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    chamado.notificado = True
    db.session.commit()
    return jsonify({"mensagem": "Notificação marcada"}), 200

@bp.route('/meus-chamados-resolvidos', endpoint='meus_chamados_resolvidos')
def meus_chamados_resolvidos():
    if 'usuario_id' not in session:
        flash('Faça login para ver seus chamados.', 'warning')
        return redirect(url_for('routes_bp.login'))

    usuario_id = session['usuario_id']
    
    status_visiveis = ["Aberto", "Em andamento", "Pendente", "Finalizado", "Resolvido", "Concluído"]
    
    chamados = Chamado.query.filter(
        Chamado.user_id == usuario_id,
        Chamado.status.in_(status_visiveis)
    ).order_by(Chamado.concluido_em.desc()).all()

    return render_template('chamados_resolvidos.html', chamados=chamados)

@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        question = request.form['security_question']
        answer = request.form['security_answer']
        nova_senha = request.form['nova_senha']

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            flash('Email não encontrado', 'danger')
            return redirect(url_for('routes_bp.reset_password'))

        # Verifica pergunta/resposta de segurança
        if usuario.security_question != question or usuario.security_answer.lower() != answer.lower():
            flash('Pergunta ou resposta de segurança inválida', 'danger')
            return redirect(url_for('routes_bp.reset_password'))

        # Redefine a senha
        usuario.senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
        db.session.commit()
        
        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('routes_bp.login'))
    
    return render_template('reset_password.html')

@bp.route('/api/chamados/<int:id>/historico', methods=['GET'])
def historico_chamado(id):
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    historico = HistoricoChamado.query.filter_by(chamado_id=id).order_by(HistoricoChamado.timestamp.asc()).all()

    return jsonify([
        {
            'id': h.id,
            'de': h.valor_anterior,
            'para': h.valor_novo,
            'timestamp': h.timestamp.isoformat() + 'Z',
            'observacao': h.observacao
        } for h in historico
    ])
    
@bp.route('/api/estatisticas/tempo-por-etapa')
def tempo_por_etapa():
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    # Query para calcular a duração em cada etapa (SQLite & PostgreSQL compatível)
    # Pega o timestamp de um registro e o subtrai do timestamp do registro SEGUINTE para o mesmo chamado.
    subquery = db.session.query(
        HistoricoChamado.id,
        HistoricoChamado.valor_anterior.label('status'),
        (func.lead(HistoricoChamado.timestamp).over(
            partition_by=HistoricoChamado.chamado_id, 
            order_by=HistoricoChamado.timestamp
        ) - HistoricoChamado.timestamp).label('duracao')
    ).subquery()

    # Agrupa as durações por status e calcula a média em segundos
    resultados = db.session.query(
        subquery.c.status,
        func.avg(func.strftime('%s', subquery.c.duracao)).label('media_segundos')
    ).filter(subquery.c.duracao.isnot(None)).group_by(subquery.c.status).all()

    # Formata para horas para ficar mais legível
    tempo_medio_por_etapa = {
        status: round((media_segundos or 0) / 3600, 2) 
        for status, media_segundos in resultados
        if status # Ignora status nulos
    }

    return jsonify(tempo_medio_por_etapa)


@bp.route('/api/chamados/<int:id>/metricas')
def metricas_chamado(id):
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    chamado = Chamado.query.get_or_404(id)
    
    # 1. Cálculo do Tempo Total de Resolução (em minutos)
    tempo_resolucao_minutos = 0
    if chamado.criado_em and chamado.concluido_em:
        delta = chamado.concluido_em - chamado.criado_em
        tempo_resolucao_minutos = round(delta.total_seconds() / 60)

    # 2. Cálculo do Tempo Total em Status "Pendente" (em minutos)
    historico = HistoricoChamado.query.filter_by(chamado_id=id).order_by(HistoricoChamado.timestamp.asc()).all()
    tempo_pendente_segundos = 0
    for i, item in enumerate(historico):
        if item.valor_novo == 'Pendente':
            # Se não for o último item do histórico, calcula a duração até o próximo evento
            if i + 1 < len(historico):
                proximo_item = historico[i+1]
                delta_pendente = proximo_item.timestamp - item.timestamp
                tempo_pendente_segundos += delta_pendente.total_seconds()

    tempo_pendente_minutos = round(tempo_pendente_segundos / 60)

    return jsonify({
        'tempo_total_resolucao_minutos': tempo_resolucao_minutos,
        'tempo_total_pendente_minutos': tempo_pendente_minutos
    })