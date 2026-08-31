from datetime import datetime, timezone, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Turma(db.Model):
    __tablename__ = 'turmas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(255), default='')
    horario = db.Column(db.String(100), default='')
    cor_tema = db.Column(db.String(20), default='#E3000B')  # Vermelho Lego
    icone = db.Column(db.String(50), default='cube')
    anotacoes = db.Column(db.Text, default='')  # Anotações gerais e pedagógicas da turma

    alunos = db.relationship('Aluno', backref='turma', lazy=True, cascade='all, delete-orphan')
    sessoes = db.relationship('SessaoChamada', backref='turma', lazy=True, cascade='all, delete-orphan')
    diarios = db.relationship('DiarioBordo', backref='turma', lazy=True, cascade='all, delete-orphan')
    atividades = db.relationship('Atividade', backref='turma', lazy=True, cascade='all, delete-orphan')
    slides = db.relationship('SlideAula', backref='turma', lazy=True, cascade='all, delete-orphan')
    duvidas = db.relationship('DuvidaAluno', backref='turma', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        total_alunos = len(self.alunos)
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'horario': self.horario,
            'cor_tema': self.cor_tema,
            'icone': self.icone,
            'anotacoes': self.anotacoes or '',
            'total_alunos': total_alunos,
            'total_atividades': len(self.atividades),
            'total_slides': len(self.slides)
        }


class Aluno(db.Model):
    __tablename__ = 'alunos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=False)
    equipe = db.Column(db.String(50), default='Construtores')
    avatar_tipo = db.Column(db.String(50), default='lego-red')
    pontos_xp = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    registros = db.relationship('RegistroPresenca', backref='aluno', lazy=True, cascade='all, delete-orphan')
    conquistas = db.relationship('ConquistaAluno', backref='aluno', lazy=True, cascade='all, delete-orphan')
    entregas = db.relationship('EntregaAtividade', backref='aluno', lazy=True, cascade='all, delete-orphan')
    duvidas = db.relationship('DuvidaAluno', backref='aluno', lazy=True, cascade='all, delete-orphan')

    @property
    def info_nivel(self):
        xp = self.pontos_xp
        if xp < 50:
            return {
                'nivel': 1,
                'titulo': 'Aprendiz de Blocos',
                'badge': '🧱',
                'proximo_xp': 50,
                'progresso': min(100, int((xp / 50) * 100))
            }
        elif xp < 150:
            return {
                'nivel': 2,
                'titulo': 'Construtor Ágil',
                'badge': '⚙️',
                'proximo_xp': 150,
                'progresso': min(100, int(((xp - 50) / 100) * 100))
            }
        elif xp < 300:
            return {
                'nivel': 3,
                'titulo': 'Engenheiro Robótico',
                'badge': '🤖',
                'proximo_xp': 300,
                'progresso': min(100, int(((xp - 150) / 150) * 100))
            }
        elif xp < 500:
            return {
                'nivel': 4,
                'titulo': 'Mestre da Criação',
                'badge': '🚀',
                'proximo_xp': 500,
                'progresso': min(100, int(((xp - 300) / 200) * 100))
            }
        else:
            return {
                'nivel': 5,
                'titulo': 'Mestre Construtor Lendário',
                'badge': '👑',
                'proximo_xp': 1000,
                'progresso': 100
            }

    @property
    def estatisticas(self):
        total_chamadas = len(self.registros)
        if total_chamadas == 0:
            return {'total': 0, 'presentes': 0, 'faltas': 0, 'justificadas': 0, 'porcentagem': 100.0}
        
        presentes = sum(1 for r in self.registros if r.status == 'presente')
        justificadas = sum(1 for r in self.registros if r.status == 'justificada')
        faltas = sum(1 for r in self.registros if r.status == 'falta')
        
        pct = round(((presentes + (justificadas * 0.5)) / total_chamadas) * 100, 1)
        return {
            'total': total_chamadas,
            'presentes': presentes,
            'faltas': faltas,
            'justificadas': justificadas,
            'porcentagem': pct
        }

    def to_dict(self):
        stats = self.estatisticas
        lvl = self.info_nivel
        return {
            'id': self.id,
            'nome': self.nome,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else '',
            'turma_codigo': self.turma.codigo if self.turma else '',
            'equipe': self.equipe,
            'avatar_tipo': self.avatar_tipo,
            'pontos_xp': self.pontos_xp,
            'ativo': self.ativo,
            'nivel': lvl['nivel'],
            'titulo_nivel': lvl['titulo'],
            'badge_nivel': lvl['badge'],
            'proximo_xp': lvl['proximo_xp'],
            'progresso_nivel': lvl['progresso'],
            'presencas': stats['presentes'],
            'faltas': stats['faltas'],
            'justificadas': stats['justificadas'],
            'porcentagem_presenca': stats['porcentagem'],
            'total_chamadas': stats['total'],
            'medalhas_count': len(self.conquistas),
            'entregas_count': len(self.entregas)
        }


class SessaoChamada(db.Model):
    __tablename__ = 'sessoes_chamada'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    topico = db.Column(db.String(200), default='Oficina Lego')
    observacoes = db.Column(db.Text, default='')
    proxima_aula = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=utc_now)

    registros = db.relationship('RegistroPresenca', backref='sessao', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        total = len(self.registros)
        presentes = sum(1 for r in self.registros if r.status == 'presente')
        faltas = sum(1 for r in self.registros if r.status == 'falta')
        justificadas = sum(1 for r in self.registros if r.status == 'justificada')
        
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else '',
            'turma_codigo': self.turma.codigo if self.turma else '',
            'turma_cor': self.turma.cor_tema if self.turma else '#E3000B',
            'data': self.data.strftime('%Y-%m-%d'),
            'data_formatada': self.data.strftime('%d/%m/%Y'),
            'topico': self.topico,
            'observacoes': self.observacoes or '',
            'proxima_aula': self.proxima_aula or '',
            'total_alunos': total,
            'presentes': presentes,
            'faltas': faltas,
            'justificadas': justificadas,
            'porcentagem': round((presentes / total * 100), 1) if total > 0 else 0
        }


class RegistroPresenca(db.Model):
    __tablename__ = 'registros_presenca'

    id = db.Column(db.Integer, primary_key=True)
    sessao_id = db.Column(db.Integer, db.ForeignKey('sessoes_chamada.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='presente')
    justificativa = db.Column(db.String(255), default='')
    pontos_ganhos = db.Column(db.Integer, default=0)
    pontos_bonus = db.Column(db.Integer, default=0)
    motivo_bonus = db.Column(db.String(200), default='')

    def to_dict(self):
        return {
            'id': self.id,
            'sessao_id': self.sessao_id,
            'aluno_id': self.aluno_id,
            'aluno_nome': self.aluno.nome if self.aluno else '',
            'aluno_avatar': self.aluno.avatar_tipo if self.aluno else 'lego-red',
            'aluno_equipe': self.aluno.equipe if self.aluno else '',
            'status': self.status,
            'justificativa': self.justificativa,
            'pontos_ganhos': self.pontos_ganhos,
            'pontos_bonus': self.pontos_bonus,
            'motivo_bonus': self.motivo_bonus,
            'total_pontos': self.pontos_ganhos + self.pontos_bonus
        }


class DiarioBordo(db.Model):
    __tablename__ = 'diarios_bordo'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), default='Anotação Pedagógica')
    autor = db.Column(db.String(100), default='Professor(a)')
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else '',
            'turma_codigo': self.turma.codigo if self.turma else '',
            'turma_cor': self.turma.cor_tema if self.turma else '#E3000B',
            'data': self.data.strftime('%Y-%m-%d'),
            'data_formatada': self.data.strftime('%d/%m/%Y'),
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'categoria': self.categoria,
            'autor': self.autor,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M')
        }


# ==========================================
# NOVOS MODELOS: ATIVIDADES & ENTREGAS
# ==========================================

class Atividade(db.Model):
    __tablename__ = 'atividades'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=True) # Se null, vale para todas
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    kit_lego = db.Column(db.String(100), default='Lego SPIKE Prime') # SPIKE Prime, BricQ, WeDo 2.0, Mindstorms
    xp_recompensa = db.Column(db.Integer, default=50) # Pontos de XP concedidos ao concluir
    data_limite = db.Column(db.Date, nullable=True)
    link_material = db.Column(db.String(255), default='') # Link do guia de montagem / tutorial
    status = db.Column(db.String(20), default='ativo') # ativo, encerrado
    created_at = db.Column(db.DateTime, default=utc_now)

    entregas = db.relationship('EntregaAtividade', backref='atividade', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        total_entregas = len(self.entregas)
        aprovadas = sum(1 for e in self.entregas if e.status == 'aprovado')
        pendentes = sum(1 for e in self.entregas if e.status == 'pendente')
        
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else 'Todas as Turmas',
            'turma_codigo': self.turma.codigo if self.turma else 'GERAL',
            'turma_cor': self.turma.cor_tema if self.turma else '#E3000B',
            'titulo': self.titulo,
            'descricao': self.descricao,
            'kit_lego': self.kit_lego,
            'xp_recompensa': self.xp_recompensa,
            'data_limite': self.data_limite.strftime('%Y-%m-%d') if self.data_limite else '',
            'data_limite_formatada': self.data_limite.strftime('%d/%m/%Y') if self.data_limite else 'Sem prazo',
            'link_material': self.link_material or '',
            'status': self.status,
            'total_entregas': total_entregas,
            'aprovadas': aprovadas,
            'pendentes': pendentes,
            'created_at': self.created_at.strftime('%d/%m/%Y')
        }


class EntregaAtividade(db.Model):
    __tablename__ = 'entregas_atividade'

    id = db.Column(db.Integer, primary_key=True)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividades.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    equipe = db.Column(db.String(100), default='')
    descricao_solucao = db.Column(db.Text, default='')
    link_foto_video = db.Column(db.String(500), default='') # Link do Google Drive, YouTube, Foto, etc.
    arquivo_anexo = db.Column(db.String(500), default='')
    status = db.Column(db.String(20), default='pendente') # pendente, aprovado, revisar
    feedback_professor = db.Column(db.Text, default='')
    xp_concedido = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)
    avaliado_em = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'atividade_id': self.atividade_id,
            'atividade_titulo': self.atividade.titulo if self.atividade else '',
            'aluno_id': self.aluno_id,
            'aluno_nome': self.aluno.nome if self.aluno else '',
            'aluno_avatar': self.aluno.avatar_tipo if self.aluno else 'lego-red',
            'aluno_turma': self.aluno.turma.nome if (self.aluno and self.aluno.turma) else '',
            'equipe': self.equipe or (self.aluno.equipe if self.aluno else ''),
            'descricao_solucao': self.descricao_solucao or '',
            'link_foto_video': self.link_foto_video or '',
            'arquivo_anexo': self.arquivo_anexo or '',
            'status': self.status,
            'feedback_professor': self.feedback_professor or '',
            'xp_concedido': self.xp_concedido,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'avaliado_em': self.avaliado_em.strftime('%d/%m/%Y %H:%M') if self.avaliado_em else ''
        }


# ==========================================
# NOVOS MODELOS: SLIDES & MATERIAIS
# ==========================================

class SlideAula(db.Model):
    __tablename__ = 'slides_aula'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, default='')
    numero_aula = db.Column(db.Integer, default=1)
    link_slide = db.Column(db.String(500), nullable=False) # Link Google Slides, Canva, OneDrive, PDF
    tipo = db.Column(db.String(50), default='slides') # slides, manual_montagem, apostila, video_tutorial, codigo
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else 'Todas as Turmas',
            'turma_codigo': self.turma.codigo if self.turma else 'GERAL',
            'turma_cor': self.turma.cor_tema if self.turma else '#E3000B',
            'titulo': self.titulo,
            'descricao': self.descricao or '',
            'numero_aula': self.numero_aula,
            'link_slide': self.link_slide,
            'tipo': self.tipo,
            'created_at': self.created_at.strftime('%d/%m/%Y')
        }


# ==========================================
# NOVOS MODELOS: FÓRUM & DÚVIDAS
# ==========================================

class DuvidaAluno(db.Model):
    __tablename__ = 'duvidas_aluno'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=True)
    nome_autor = db.Column(db.String(100), default='Aluno Construtor')
    titulo = db.Column(db.String(150), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), default='Programação & Sensores') # Montagem / Mecânica, Programação / Sensores, Peças & Kits, Geral
    status = db.Column(db.String(20), default='aberta') # aberta, respondida, resolvida
    resposta_professor = db.Column(db.Text, default='')
    respondido_por = db.Column(db.String(100), default='Professor(a)')
    created_at = db.Column(db.DateTime, default=utc_now)
    respondido_em = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else 'Geral',
            'turma_codigo': self.turma.codigo if self.turma else 'GERAL',
            'turma_cor': self.turma.cor_tema if self.turma else '#E3000B',
            'aluno_id': self.aluno_id,
            'nome_autor': self.aluno.nome if self.aluno else self.nome_autor,
            'aluno_avatar': self.aluno.avatar_tipo if self.aluno else 'lego-blue',
            'aluno_equipe': self.aluno.equipe if self.aluno else '',
            'titulo': self.titulo,
            'pergunta': self.pergunta,
            'categoria': self.categoria,
            'status': self.status,
            'resposta_professor': self.resposta_professor or '',
            'respondido_por': self.respondido_por or 'Professor(a)',
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'respondido_em': self.respondido_em.strftime('%d/%m/%Y %H:%M') if self.respondido_em else ''
        }


class Medalha(db.Model):
    __tablename__ = 'medalhas'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    icone = db.Column(db.String(50), default='🏆')
    cor = db.Column(db.String(20), default='#FFD700')
    xp_bonus = db.Column(db.Integer, default=20)
    tipo = db.Column(db.String(30), default='presenca')

    conquistas = db.relationship('ConquistaAluno', backref='medalha', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'descricao': self.descricao,
            'icone': self.icone,
            'cor': self.cor,
            'xp_bonus': self.xp_bonus,
            'tipo': self.tipo
        }


class ConquistaAluno(db.Model):
    __tablename__ = 'conquistas_aluno'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    medalha_id = db.Column(db.Integer, db.ForeignKey('medalhas.id'), nullable=False)
    data_conquista = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'aluno_id': self.aluno_id,
            'aluno_nome': self.aluno.nome if self.aluno else '',
            'medalha_id': self.medalha_id,
            'medalha': self.medalha.to_dict() if self.medalha else None,
            'data_conquista': self.data_conquista.strftime('%d/%m/%Y %H:%M')
        }
