from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime
import logging
from . import db, bcrypt
from .models import Usuario, Chamado, HistoricoChamado
from sqlalchemy import func

bp = Blueprint('routes_bp', __name__)

# --- FUNÇÕES AUXILIARES DE AUTENTICAÇÃO ---

def is_admin():
    """Verifica se o usuário na sessão é um administrador."""
    return session.get('role') == 'admin'

def is_logged_in():
    """Verifica se há um usuário logado na sessão."""
    return 'usuario_id' in session

# --- ROTAS DE PÁGINAS (Renderização de HTML) ---

@bp.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('routes_bp.login'))
    
    if is_admin():
        return redirect(url_for('routes_bp.dashboard'))
    else:
        return redirect(url_for('routes_bp.novo_chamado'))

@bp.route('/dashboard')
def dashboard():
    if not is_admin():
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('routes_bp.home'))
    return render_template("dashboard.html")

@bp.route('/novo-chamado', methods=['GET', 'POST'])
def novo_chamado():
    if not is_logged_in():
        flash('Faça login para abrir um chamado.', 'warning')
        return redirect(url_for('routes_bp.login'))

    if request.method == 'POST':
        novo = Chamado(
            nome=request.form['nome'],
            setor=request.form['setor'],
            descricao=request.form['descricao'],
            user_id=session['usuario_id'],
            funcionario_id=session.get('funcionario_id'),
            sistema_origem='novo' # Garante que novos chamados são do sistema atual
        )
        db.session.add(novo)
        db.session.commit()
        flash("Chamado registrado com sucesso! Você pode abrir outro se necessário.", "success")
        return redirect(url_for('routes_bp.novo_chamado'))

    return render_template('novo_chamado.html')

@bp.route('/meus-chamados')
def meus_chamados():
    if not is_logged_in():
        flash('Faça login para ver seus chamados.', 'warning')
        return redirect(url_for('routes_bp.login'))

    usuario_id = session['usuario_id']
    chamados = Chamado.query.filter_by(user_id=usuario_id).order_by(Chamado.criado_em.desc()).all()
    # ✅ CORREÇÃO: Renderiza o template correto.
    return render_template('meus_chamados.html', chamados=chamados)


# --- ROTAS DE AUTENTICAÇÃO ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('routes_bp.home'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
            session.clear()
            session['usuario_id'] = usuario.id
            session['email'] = usuario.email
            session['funcionario_id'] = usuario.funcionario_id
            # ✅ CORREÇÃO: Armazena a 'role' do usuário na sessão. Assume 'user' como padrão.
            session['role'] = getattr(usuario, 'role', 'user')
            
            flash(f"Login como {session['role']} realizado com sucesso!", "success")
            return redirect(url_for('routes_bp.home'))
        
        flash('Credenciais inválidas. Verifique seu email e senha.', 'danger')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash("Você foi desconectado com segurança.", "info")
    return redirect(url_for('routes_bp.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # ✅ CORREÇÃO: Adiciona a role 'user' para todos os novos registros.
            novo_usuario = Usuario(
                email=request.form['email'],
                senha_hash=bcrypt.generate_password_hash(request.form['senha']).decode('utf-8'),
                funcionario_id=request.form['funcionario_id'],
                security_question=request.form['security_question'],
                security_answer=request.form['security_answer'],
                role='user' 
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Conta criada com sucesso! Faça o login.", "success")
            return redirect(url_for('routes_bp.login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro no registro: {str(e)}")
            flash("Erro ao criar conta. O email ou ID do funcionário pode já estar em uso.", "danger")
    
    return render_template('register.html')

@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        question = request.form['security_question']
        answer = request.form['security_answer']
        nova_senha = request.form['nova_senha']
        usuario = Usuario.query.filter_by(email=email).first()

        if not (usuario and usuario.security_question == question and usuario.security_answer.lower() == answer.lower()):
            flash('Dados de recuperação inválidos.', 'danger')
            return redirect(url_for('routes_bp.reset_password'))

        usuario.senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
        db.session.commit()
        
        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('routes_bp.login'))
    
    return render_template('reset_password.html')

# --- ROTAS DE API (Para o Frontend do Dashboard) ---

@bp.route('/api/chamados', methods=['GET'])
def api_listar_chamados():
    if not is_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403

    # ✅ CORREÇÃO: Filtra para mostrar apenas chamados do novo sistema.
    chamados = Chamado.query.filter_by(sistema_origem='novo').order_by(Chamado.criado_em.desc()).all()
    
    return jsonify([{
        'id': c.id, 'nome': c.nome, 'setor': c.setor, 'descricao': c.descricao,
        'status': c.status, 'observacao': c.observacao, 'imagem_url': c.imagem_url,
        'criado_em': c.criado_em.isoformat() + 'Z' if c.criado_em else None,
        'concluido_em': c.concluido_em.isoformat() + 'Z' if c.concluido_em else None
    } for c in chamados])

@bp.route('/api/chamados/<int:id>', methods=['PUT', 'DELETE'])
def api_gerenciar_chamado(id):
    if not is_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403

    chamado = Chamado.query.filter_by(id=id, sistema_origem='novo').first_or_404()

    if request.method == 'PUT':
        data = request.get_json()
        status_anterior = chamado.status
        novo_status = data.get('status')

        if novo_status and novo_status != status_anterior:
            chamado.status = novo_status
            if novo_status == "Em andamento" and not chamado.andamento_em:
                chamado.andamento_em = datetime.utcnow()
            elif novo_status in ["Concluído", "Finalizado", "Resolvido"] and not chamado.concluido_em:
                chamado.concluido_em = datetime.utcnow()

            db.session.add(HistoricoChamado(
                chamado_id=id, valor_anterior=status_anterior, valor_novo=novo_status,
                observacao=data.get('observacao', 'Status alterado via painel.')
            ))
        
        if 'observacao' in data:
            chamado.observacao = data['observacao']
            
        db.session.commit()
        return jsonify({'message': 'Chamado atualizado com sucesso.'})

    elif request.method == 'DELETE':
        db.session.delete(chamado)
        db.session.commit()
        return jsonify({'message': 'Chamado excluído com sucesso.'})

@bp.route("/api/graficos")
def api_graficos():
    if not is_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403

    # ✅ CORREÇÃO: Filtra para incluir apenas chamados do novo sistema.
    query_base = db.session.query(Chamado).filter_by(sistema_origem='novo')
    total_por_status = dict(query_base.with_entities(Chamado.status, func.count(Chamado.id)).group_by(Chamado.status).all())
    total_por_setor = dict(query_base.with_entities(Chamado.setor, func.count(Chamado.id)).group_by(Chamado.setor).all())

    return jsonify({
        'status_distribuicao': total_por_status,
        'setor_distribuicao': total_por_setor
    })

@bp.route("/api/notificacoes")
def api_notificacoes():
    if not is_logged_in():
        return jsonify([])

    usuario_id = session["usuario_id"]
    status_para_notificar = ["Finalizado", "Resolvido", "Concluído", "Pendente"]
    chamados = Chamado.query.filter(
        Chamado.user_id == usuario_id,
        Chamado.status.in_(status_para_notificar),
        Chamado.notificado == False
    ).all()

    return jsonify([{'id': ch.id, 'nome': ch.nome, 'setor': ch.setor, 'status': ch.status} for ch in chamados])

@bp.route("/api/notificacoes/<int:id>/marcar", methods=["POST"])
def api_marcar_notificacao(id):
    if not is_logged_in():
        return jsonify({"error": "Não logado"}), 403

    chamado = Chamado.query.filter_by(id=id, user_id=session["usuario_id"]).first_or_404()
    chamado.notificado = True
    db.session.commit()
    return jsonify({"message": "Notificação marcada como lida."})

@bp.route('/api/chamados/<int:id>/historico', methods=['GET'])
def api_historico_chamado(id):
    if not is_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    try:
        historico = HistoricoChamado.query.filter_by(chamado_id=id).order_by(HistoricoChamado.timestamp.asc()).all()
        return jsonify([{'id': h.id, 'de': h.valor_anterior, 'para': h.valor_novo, 'timestamp': h.timestamp.isoformat() + 'Z', 'observacao': h.observacao} for h in historico])
    except Exception as e:
        logging.error(f"Erro ao buscar histórico do chamado {id}: {e}")
        return jsonify({'error': 'Erro interno ao buscar histórico.'}), 500

@bp.route('/api/chamados/<int:id>/metricas')
def api_metricas_chamado(id):
    if not is_admin():
        return jsonify({'error': 'Acesso não autorizado'}), 403
    try:
        chamado = Chamado.query.get_or_404(id)
        tempo_resolucao_minutos = 0
        if chamado.criado_em and chamado.concluido_em:
            delta = chamado.concluido_em - chamado.criado_em
            tempo_resolucao_minutos = round(delta.total_seconds() / 60)
        
        historico = HistoricoChamado.query.filter_by(chamado_id=id).order_by(HistoricoChamado.timestamp.asc()).all()
        tempo_pendente_segundos = 0
        for i, item in enumerate(historico):
            if item.valor_novo == 'Pendente':
                if i + 1 < len(historico):
                    proximo_item = historico[i+1]
                    delta_pendente = proximo_item.timestamp - item.timestamp
                    tempo_pendente_segundos += delta_pendente.total_seconds()
        
        tempo_pendente_minutos = round(tempo_pendente_segundos / 60)
        return jsonify({
            'tempo_total_resolucao_minutos': tempo_resolucao_minutos,
            'tempo_total_pendente_minutos': tempo_pendente_minutos
        })
    except Exception as e:
        logging.error(f"Erro ao calcular métricas do chamado {id}: {e}")
        return jsonify({'error': 'Erro interno ao calcular métricas.'}), 500