# models.py
from . import db

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(128), nullable=False)
    funcionario_id = db.Column(db.Integer, unique=True)
    role = db.Column(db.String(20), nullable=False, default='user') 
    security_question = db.Column(db.String(50))
    security_answer = db.Column(db.String(255))
    chamados = db.relationship('Chamado', back_populates='autor', lazy='dynamic')

    def __repr__(self):
        return f"<Usuario {self.email}>"

class Chamado(db.Model):
    __tablename__ = 'chamados'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(50), nullable=False, index=True)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Aberto', nullable=False, index=True)
    anydesk = db.Column(db.String(50), nullable=True) 
    sistema_origem = db.Column(db.String(20), default='novo', nullable=False) 
    
    imagem_url = db.Column(db.String(200))
    observacao = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    funcionario_id = db.Column(db.Integer)
    notificado = db.Column(db.Boolean, default=False)
    
    # ✅ Datas gerenciadas pelo banco de dados para melhor performance
    criado_em = db.Column(db.DateTime, server_default=db.func.now()) 
    iniciado_em = db.Column(db.DateTime)
    andamento_em = db.Column(db.DateTime)
    concluido_em = db.Column(db.DateTime)
    
    autor = db.relationship('Usuario', back_populates='chamados')
    historico = db.relationship('HistoricoChamado', back_populates='chamado', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chamado {self.id} ({self.status})>"

class HistoricoChamado(db.Model):
    __tablename__ = 'historico_chamado'
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados.id'), nullable=False)
    campo_alterado = db.Column(db.String(50), default='status')
    valor_anterior = db.Column(db.String(100))
    valor_novo = db.Column(db.String(100), nullable=False)
    observacao = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    chamado = db.relationship('Chamado', back_populates='historico')

    def __repr__(self):
        return f"<Historico para Chamado {self.chamado_id}>"