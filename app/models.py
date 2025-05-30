from datetime import datetime
from . import db

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128))
    funcionario_id = db.Column(db.Integer, unique=True)
    security_question = db.Column(db.String(50))   # Pergunta de segurança
    security_answer = db.Column(db.String(255))    # Resposta de segurança
    chamados = db.relationship('Chamado', backref='autor', lazy=True)


class Chamado(db.Model):
    __tablename__ = 'chamados'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Aberto')
    imagem_url = db.Column(db.String(200))
    observacao = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    funcionario_id = db.Column(db.Integer)
    glpi_ticket_id = db.Column(db.Integer, nullable=True, unique=True)
    notificado = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    iniciado_em = db.Column(db.DateTime)
    andamento_em = db.Column(db.DateTime)
    concluido_em = db.Column(db.DateTime)

