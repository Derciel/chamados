from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime
import os, requests, logging

from . import db, bcrypt
from .models import Usuario, Chamado
from sqlalchemy.sql import func

bp = Blueprint('routes_bp', __name__)
spotify_bp = Blueprint('spotify_bp', __name__)

@bp.route('/')
def home():
    if 'email' in session:
        if session['email'] == 'adm@adm':
            return redirect(url_for('routes_bp.dashboard'))
        else:
            return redirect(url_for('routes_bp.novo_chamado'))
    return redirect(url_for('routes_bp.login'))

@bp.route('/dashboard')
def dashboard():
    if 'email' not in session or session.get('email') != 'adm@adm':
        flash('Acesso restrito ao administrador', 'danger')
        return redirect(url_for('routes_bp.novo_chamado'))

    chamados = Chamado.query.order_by(Chamado.criado_em.desc()).all()

    setores = list({c.setor for c in chamados})
    quantidades = [sum(1 for c in chamados if c.setor == setor) for setor in setores]

    tempo_medio = {}
    for setor in setores:
        tempos = []
        for c in chamados:
            if c.setor == setor and c.iniciado_em and c.concluido_em:
                duracao = (c.concluido_em - c.iniciado_em).total_seconds() / 3600
                tempos.append(duracao)
        tempo_medio[setor] = round(sum(tempos) / len(tempos), 1) if tempos else 0

    return render_template(
        "dashboard.html",
        chamados=chamados,
        setores=setores,
        quantidades=quantidades,
        tempo_medio=tempo_medio
    )

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

    email = request.args.get('email', '')
    senha = request.args.get('senha', '')

    return render_template('login.html', email=email, senha=senha)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        funcionario_id = request.form['funcionario_id']
        question = request.form['security_question']
        answer = request.form['security_answer']

        if Usuario.query.filter_by(email=email).first():
            flash("Email já registrado", "warning")
            return redirect(url_for('routes_bp.register'))

        try:
            novo_usuario = Usuario(
                email=email,
                senha_hash=bcrypt.generate_password_hash(senha).decode('utf-8'),
                funcionario_id=funcionario_id,
                security_question=question,
                security_answer=answer
            )
            db.session.add(novo_usuario)
            db.session.commit()
            return redirect(url_for('routes_bp.login', email=email, senha=senha))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro no registro: {str(e)}")
            flash("Erro ao criar conta", "danger")
            return redirect(url_for('routes_bp.register'))

    return render_template('register.html')

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
        flash('Senha atualizada!', 'success')
        return redirect(url_for('routes_bp.login'))
    
    return render_template('reset_password.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada", "info")
    return redirect(url_for('routes_bp.login'))

@bp.route('/novo-chamado', methods=['GET', 'POST'])
def novo_chamado():
    if 'usuario_id' not in session or 'funcionario_id' not in session:
        flash('Faça login primeiro', 'warning')
        return redirect(url_for('routes_bp.login'))

    if request.method == 'POST':
        nome = request.form['nome']
        setor = request.form['setor']
        descricao = request.form['descricao']
        imagem_url = ''
        imagem = request.files.get('imagem')
        user_id = session['usuario_id']
        funcionario_id = session['funcionario_id']

        novo_chamado = Chamado(
            nome=nome,
            setor=setor,
            descricao=descricao,
            status='Aberto',
            user_id=user_id,
            funcionario_id=funcionario_id
        )

        if imagem:
            imgur_client_id = os.getenv('IMGUR_CLIENT_ID')
            if not imgur_client_id:
                flash("Configuração de upload faltando", "danger")
                return redirect(url_for('routes_bp.novo_chamado'))

            headers = {'Authorization': f'Client-ID {imgur_client_id}'}
            files = {'image': (imagem.filename, imagem.read(), imagem.mimetype)}

            try:
                response = requests.post('https://api.imgur.com/3/image', headers=headers, files=files)
                response.raise_for_status()
                imagem_url = response.json()['data']['link']
                novo_chamado.imagem_url = imagem_url
            except Exception as e:
                logging.error(f"Erro no upload: {str(e)}")
                flash("Erro ao enviar imagem", "danger")

        db.session.add(novo_chamado)
        db.session.commit()

        flash("Chamado registrado!", "success")
        return redirect(url_for('routes_bp.meus_chamados_resolvidos'))

    return render_template('novo_chamado.html')

@bp.route('/meus-chamados-resolvidos')
def meus_chamados_resolvidos():
    if 'usuario_id' not in session:
        flash('Faça login primeiro', 'warning')
        return redirect(url_for('routes_bp.login'))

    funcionario_id = session['funcionario_id']
    chamados = Chamado.query.filter(
        Chamado.funcionario_id == funcionario_id,
        Chamado.status.in_(["Finalizado", "Resolvido", "Concluído"])
    ).order_by(Chamado.concluido_em.desc()).all()

    return render_template('chamados_resolvidos.html', chamados=chamados)

@bp.route('/api/chamados', methods=['GET'])
def listar_chamados():
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    status_filtro = request.args.get('status')
    setor_filtro = request.args.get('setor')
    funcionario_id_filtro = request.args.get('funcionario_id')
    q = request.args.get('q')

    query = Chamado.query.order_by(Chamado.criado_em.desc())

    if status_filtro:
        query = query.filter(Chamado.status.ilike(f'%{status_filtro}%'))
    if setor_filtro:
        query = query.filter(Chamado.setor.ilike(f'%{setor_filtro}%'))
    if funcionario_id_filtro and funcionario_id_filtro.isdigit():
        query = query.filter(Chamado.funcionario_id == int(funcionario_id_filtro))
    if q:
        like_q = f'%{q}%'
        query = query.filter(
            (Chamado.nome.ilike(like_q)) |
            (Chamado.setor.ilike(like_q)) |
            (Chamado.descricao.ilike(like_q))
        )

    chamados = query.all()
    return jsonify([
        {
            'id': c.id,
            'nome': c.nome,
            'setor': c.setor,
            'descricao': c.descricao,
            'status': c.status,
            'observacao': c.observacao,
            'imagem_url': c.imagem_url,
            'criado_em': c.criado_em.isoformat() if c.criado_em else None,
            'iniciado_em': c.iniciado_em.isoformat() if c.iniciado_em else None,
            'andamento_em': c.andamento_em.isoformat() if c.andamento_em else None,
            'concluido_em': c.concluido_em.isoformat() if c.concluido_em else None
        } for c in chamados
    ])

@bp.route('/api/chamados/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def chamado_detalhe(id):
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    chamado = Chamado.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify({
            'id': chamado.id,
            'nome': chamado.nome,
            'setor': chamado.setor,
            'descricao': chamado.descricao,
            'status': chamado.status,
            'imagem_url': chamado.imagem_url,
            'observacao': chamado.observacao,
            'criado_em': chamado.criado_em.isoformat() if chamado.criado_em else None,
            'iniciado_em': chamado.iniciado_em.isoformat() if chamado.iniciado_em else None,
            'andamento_em': chamado.andamento_em.isoformat() if chamado.andamento_em else None,
            'concluido_em': chamado.concluido_em.isoformat() if chamado.concluido_em else None
        })

    elif request.method == 'PUT':
        data = request.get_json()
        novo_status = data.get("status", chamado.status)

        if novo_status != chamado.status:
            agora = datetime.utcnow()
            if novo_status in ["Aberto", "Pendente", "Iniciado"] and not chamado.iniciado_em:
                chamado.iniciado_em = agora
                chamado.notificado = False
            elif novo_status == "Em andamento":
                chamado.andamento_em = agora
            elif novo_status in ["Concluído", "Finalizado", "Resolvido"]:
                chamado.concluido_em = agora
                chamado.notificado = False

        chamado.status = novo_status
        chamado.observacao = data.get("observacao", chamado.observacao)
        db.session.commit()
        return jsonify({"mensagem": "Chamado atualizado"})

    elif request.method == 'DELETE':
        db.session.delete(chamado)
        db.session.commit()
        return jsonify({"mensagem": "Chamado excluído"}), 204

@bp.route("/api/graficos")
def graficos():
    if 'email' not in session or session.get('email') != 'adm@adm':
        return jsonify({'erro': 'Acesso não autorizado'}), 403

    total_por_status = db.session.query(
        Chamado.status,
        func.count(Chamado.id)
    ).group_by(Chamado.status).all()

    tempo_resolucao = db.session.query(
        func.avg(func.julianday(Chamado.concluido_em) - func.julianday(Chamado.criado_em))
    ).filter(Chamado.concluido_em.isnot(None)).scalar()

    return jsonify({
        'status_distribuicao': dict(total_por_status),
        'tempo_medio_resolucao_horas': round((tempo_resolucao or 0) * 24, 2)
    })

@bp.route("/api/notificacoes")
def notificacoes():
    if "usuario_id" not in session:
        return jsonify([])

    usuario_id = session["usuario_id"]
    chamados_nao_notificados = Chamado.query.filter_by(
        user_id=usuario_id,
        status="Finalizado",
        notificado=False
    ).all()

    return jsonify([
        {"id": ch.id, "nome": ch.nome, "setor": ch.setor}
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

@bp.route("/spotify")
def spotify():
    return render_template("spotify.html")
