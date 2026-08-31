import os
import csv
import io
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, flash, session
from models import db, Usuario, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo, Atividade, EntregaAtividade, SlideAula, DuvidaAluno
from database import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'montebot-ufu-facom-lina-secret-2026')

# Configuração de Banco de Dados:
# Vercel / Supabase Postgres ou SQLite local
db_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or 'sqlite:///lego_chamada.db'
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

if 'postgresql' in db_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args'] = {
        'connect_timeout': 5,
        'sslmode': 'require'
    }

db.init_app(app)

# Inicializa banco de dados com dados iniciais e migrations
try:
    init_db(app)
except Exception as e:
    print(f"[Aviso Inicializacao DB]: {e}")


# ==========================================
# HELPERS DE AUTENTICAÇÃO E CONTROLE DE ACESSO (RBAC)
# ==========================================

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(Usuario, user_id)
    return None

def get_current_aluno():
    aluno_id = session.get('aluno_id')
    if aluno_id:
        return db.session.get(Aluno, aluno_id)
    return None

@app.context_processor
def inject_auth_context():
    return {
        'current_user': get_current_user(),
        'current_aluno': get_current_aluno(),
        'hoje_data': date.today().strftime('%Y-%m-%d'),
        'hoje_formatado': date.today().strftime('%d/%m/%Y')
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') and not session.get('aluno_id'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash('Acesso restrito aos Responsáveis pelas Aulas.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash('Acesso restrito a Professores e Responsáveis.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# ROTAS DE AUTENTICAÇÃO & TELA INICIAL (LOGIN)
# ==========================================

@app.route('/')
def home():
    user = get_current_user()
    aluno = get_current_aluno()

    if aluno:
        return redirect(url_for('portal_aluno'))
    if user:
        if user.is_admin:
            return redirect(url_for('painel_admin'))
        else:
            return redirect(url_for('painel_escola'))

    return redirect(url_for('login_page'))


@app.route('/login', methods=['GET'])
def login_page():
    user = get_current_user()
    aluno = get_current_aluno()

    if aluno:
        return redirect(url_for('portal_aluno'))
    if user:
        return redirect(url_for('painel_admin' if user.is_admin else 'painel_escola'))

    turmas = Turma.query.all()
    alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.nome.asc()).all()
    return render_template('login.html', turmas=turmas, alunos=alunos)


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    dados = request.get_json() or {}
    tipo = dados.get('tipo', 'usuario') # 'aluno' ou 'usuario'

    if tipo == 'aluno':
        aluno_id = dados.get('aluno_id')
        pin = str(dados.get('pin', '')).strip()

        if not aluno_id or not pin:
            return jsonify({'error': 'Selecione seu nome e digite o PIN de acesso.'}), 400

        aluno = db.session.get(Aluno, int(aluno_id))
        if not aluno or not aluno.ativo:
            return jsonify({'error': 'Aluno não encontrado no sistema.'}), 404

        pin_correto = aluno.pin_acesso or '1234'
        if pin != pin_correto:
            return jsonify({'error': 'PIN incorreto! Solicite auxílio ao seu professor.'}), 401

        session.clear()
        session['aluno_id'] = aluno.id
        return jsonify({
            'success': True,
            'message': f'Bem-vindo(a), {aluno.nome}!',
            'redirect': url_for('portal_aluno')
        })

    else:
        email = str(dados.get('email', '')).strip().lower()
        senha = str(dados.get('senha', '')).strip()

        if not email or not senha:
            return jsonify({'error': 'E-mail e senha são obrigatórios.'}), 400

        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if not usuario or not usuario.verificar_senha(senha):
            return jsonify({'error': 'Credenciais inválidas! Verifique e-mail e senha.'}), 401

        session.clear()
        session['user_id'] = usuario.id
        redirect_target = url_for('painel_admin' if usuario.is_admin else 'painel_escola')
        return jsonify({
            'success': True,
            'message': f'Olá, {usuario.nome} ({usuario.perfil_nome})!',
            'redirect': redirect_target
        })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# ==========================================
# PAINÉIS DOS 3 PERFIS
# ==========================================

# 1. Painel Master (Responsáveis pelas Aulas - UFU / FACOM / LINA / MONTE BOT)
@app.route('/painel-admin')
@admin_required
def painel_admin():
    turmas = Turma.query.all()
    total_alunos = Aluno.query.filter_by(ativo=True).count()
    total_chamadas = SessaoChamada.query.count()
    total_anotacoes = DiarioBordo.query.count()
    total_atividades = Atividade.query.count()
    total_slides = SlideAula.query.count()
    total_duvidas = DuvidaAluno.query.count()

    hoje = date.today()
    chamadas_hoje = SessaoChamada.query.filter_by(data=hoje).all()
    turmas_feitas_hoje = {c.turma_id for c in chamadas_hoje}
    
    top_alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.pontos_xp.desc()).limit(5).all()
    ultimas_anotacoes = DiarioBordo.query.order_by(DiarioBordo.data.desc(), DiarioBordo.id.desc()).limit(3).all()
    atividades_recentes = Atividade.query.filter_by(status='ativo').order_by(Atividade.id.desc()).limit(3).all()

    return render_template('admin_dashboard.html',
                           turmas=turmas,
                           total_alunos=total_alunos,
                           total_chamadas=total_chamadas,
                           total_anotacoes=total_anotacoes,
                           total_atividades=total_atividades,
                           total_slides=total_slides,
                           total_duvidas=total_duvidas,
                           turmas_feitas_hoje=turmas_feitas_hoje,
                           top_alunos=top_alunos,
                           ultimas_anotacoes=ultimas_anotacoes,
                           atividades_recentes=atividades_recentes)


# 2. Painel dos Professores da Escola (Colégio Alfa COC / Melo Viana - READ ONLY)
@app.route('/painel-escola')
@teacher_or_admin_required
def painel_escola():
    user = get_current_user()
    turmas = Turma.query.all()

    # Se professor da escola, filtra os alunos da sua instituição
    turma_filtro = request.args.get('turma_id', type=int)
    alunos_query = Aluno.query.filter_by(ativo=True)
    if turma_filtro:
        alunos_query = alunos_query.filter_by(turma_id=turma_filtro)
    
    alunos = alunos_query.order_by(Aluno.pontos_xp.desc()).all()
    sessoes = SessaoChamada.query.order_by(SessaoChamada.data.desc()).limit(10).all()
    diarios = DiarioBordo.query.order_by(DiarioBordo.data.desc()).limit(5).all()
    atividades = Atividade.query.all()
    entregas = EntregaAtividade.query.order_by(EntregaAtividade.created_at.desc()).all()

    return render_template('teacher_portal.html',
                           usuario=user,
                           turmas=turmas,
                           alunos=alunos,
                           sessoes=sessoes,
                           diarios=diarios,
                           atividades=atividades,
                           entregas=entregas,
                           turma_filtro=turma_filtro)


# 3. Portal do Aluno (Estudo Remoto, Entregas e Dúvidas)
@app.route('/portal-aluno')
@login_required
def portal_aluno():
    aluno = get_current_aluno()
    if not aluno:
        # Se for usuário professor/admin visitando o portal do aluno
        aluno_id = request.args.get('aluno_id', type=int)
        if aluno_id:
            aluno = db.session.get(Aluno, aluno_id)
        else:
            aluno = Aluno.query.first()

    if not aluno:
        return redirect(url_for('login_page'))

    slides = SlideAula.query.filter(
        (SlideAula.turma_id == aluno.turma_id) | (SlideAula.turma_id == None)
    ).order_by(SlideAula.numero_aula.asc()).all()

    atividades = Atividade.query.filter(
        (Atividade.turma_id == aluno.turma_id) | (Atividade.turma_id == None)
    ).filter_by(status='ativo').order_by(Atividade.id.desc()).all()

    minhas_entregas = EntregaAtividade.query.filter_by(aluno_id=aluno.id).order_by(EntregaAtividade.created_at.desc()).all()
    entregas_dict = {e.atividade_id: e for e in minhas_entregas}
    minhas_duvidas = DuvidaAluno.query.filter_by(aluno_id=aluno.id).order_by(DuvidaAluno.created_at.desc()).all()
    conquistas = ConquistaAluno.query.filter_by(aluno_id=aluno.id).all()

    # Ranking da turma do aluno
    colegas_grupo = Aluno.query.filter_by(turma_id=aluno.turma_id, ativo=True).order_by(Aluno.pontos_xp.desc()).all()

    return render_template('student_portal.html',
                           aluno=aluno,
                           slides=slides,
                           atividades=atividades,
                           minhas_entregas=minhas_entregas,
                           entregas_dict=entregas_dict,
                           minhas_duvidas=minhas_duvidas,
                           conquistas=conquistas,
                           colegas_grupo=colegas_grupo)


# ==========================================
# ROTAS DO MÓDULO MASTER (CHAMADA, ATIVIDADES, NOTAS)
# ==========================================

@app.route('/chamada')
@admin_required
def chamada():
    turmas = Turma.query.all()
    turma_selecionada = request.args.get('turma_id', type=int)
    if not turma_selecionada and turmas:
        turma_selecionada = turmas[0].id
    
    data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    return render_template('attendance.html', 
                           turmas=turmas, 
                           turma_selecionada=turma_selecionada, 
                           data_atual=data_str)


@app.route('/atividades')
@login_required
def atividades_page():
    user = get_current_user()
    aluno = get_current_aluno()

    if aluno:
        return redirect(url_for('portal_aluno'))

    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    status_filtro = request.args.get('status', '')

    query = Atividade.query
    if turma_filtro:
        query = query.filter((Atividade.turma_id == turma_filtro) | (Atividade.turma_id == None))
    if status_filtro:
        query = query.filter_by(status=status_filtro)

    atividades = query.order_by(Atividade.id.desc()).all()
    
    entregas_query = EntregaAtividade.query
    if turma_filtro:
        entregas_query = entregas_query.join(Aluno).filter(Aluno.turma_id == turma_filtro)
    entregas = entregas_query.order_by(EntregaAtividade.created_at.desc()).all()

    alunos_query = Aluno.query.filter_by(ativo=True)
    if turma_filtro:
        alunos_query = alunos_query.filter_by(turma_id=turma_filtro)
    alunos = alunos_query.order_by(Aluno.nome.asc()).all()

    return render_template('activities.html',
                           turmas=turmas,
                           atividades=atividades,
                           entregas=entregas,
                           alunos=alunos,
                           turma_filtro=turma_filtro,
                           status_filtro=status_filtro,
                           is_admin=user.is_admin if user else False)


@app.route('/slides')
@login_required
def slides_page():
    user = get_current_user()
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    tipo_filtro = request.args.get('tipo', '')

    query = SlideAula.query
    if turma_filtro:
        query = query.filter((SlideAula.turma_id == turma_filtro) | (SlideAula.turma_id == None))
    if tipo_filtro:
        query = query.filter_by(tipo=tipo_filtro)

    slides = query.order_by(SlideAula.numero_aula.asc(), SlideAula.id.asc()).all()

    return render_template('slides.html',
                           turmas=turmas,
                           slides=slides,
                           turma_filtro=turma_filtro,
                           tipo_filtro=tipo_filtro,
                           is_admin=user.is_admin if user else False)


@app.route('/duvidas')
@login_required
def forum_page():
    user = get_current_user()
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    categoria_filtro = request.args.get('categoria', '')
    status_filtro = request.args.get('status', '')

    query = DuvidaAluno.query
    if turma_filtro:
        query = query.filter((DuvidaAluno.turma_id == turma_filtro) | (DuvidaAluno.turma_id == None))
    if categoria_filtro:
        query = query.filter_by(categoria=categoria_filtro)
    if status_filtro:
        query = query.filter_by(status=status_filtro)

    duvidas = query.order_by(DuvidaAluno.created_at.desc()).all()
    alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.nome.asc()).all()

    return render_template('forum.html',
                           turmas=turmas,
                           duvidas=duvidas,
                           alunos=alunos,
                           turma_filtro=turma_filtro,
                           categoria_filtro=categoria_filtro,
                           status_filtro=status_filtro,
                           is_admin=user.is_admin if user else False)


@app.route('/anotacoes')
@teacher_or_admin_required
def anotacoes_page():
    user = get_current_user()
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    categoria_filtro = request.args.get('categoria', '')

    query = DiarioBordo.query
    if turma_filtro:
        query = query.filter_by(turma_id=turma_filtro)
    if categoria_filtro:
        query = query.filter_by(categoria=categoria_filtro)

    diarios = query.order_by(DiarioBordo.data.desc(), DiarioBordo.id.desc()).all()
    
    query_sessoes = SessaoChamada.query
    if turma_filtro:
        query_sessoes = query_sessoes.filter_by(turma_id=turma_filtro)
    sessoes_com_notas = [s for s in query_sessoes.order_by(SessaoChamada.data.desc()).all() if s.observacoes or s.proxima_aula]

    return render_template('notes.html', 
                           turmas=turmas, 
                           diarios=diarios, 
                           sessoes_com_notas=sessoes_com_notas,
                           turma_filtro=turma_filtro,
                           categoria_filtro=categoria_filtro,
                           is_admin=user.is_admin if user else False)


@app.route('/alunos')
@teacher_or_admin_required
def alunos_page():
    user = get_current_user()
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    
    query = Aluno.query.filter_by(ativo=True)
    if turma_filtro:
        query = query.filter_by(turma_id=turma_filtro)
    
    alunos = query.order_by(Aluno.nome.asc()).all()
    medalhas = Medalha.query.all()
    
    return render_template('students.html', 
                           turmas=turmas, 
                           alunos=alunos, 
                           turma_filtro=turma_filtro,
                           medalhas=medalhas,
                           is_admin=user.is_admin if user else False)


@app.route('/gamificacao')
@login_required
def gamificacao():
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    
    query = Aluno.query.filter_by(ativo=True)
    if turma_filtro:
        query = query.filter_by(turma_id=turma_filtro)
        
    ranking = query.order_by(Aluno.pontos_xp.desc()).all()
    medalhas = Medalha.query.all()
    
    equipes_stats = {}
    for a in Aluno.query.filter_by(ativo=True).all():
        eq = a.equipe or 'Geral'
        if eq not in equipes_stats:
            equipes_stats[eq] = {'nome': eq, 'xp_total': 0, 'membros': 0}
        equipes_stats[eq]['xp_total'] += a.pontos_xp
        equipes_stats[eq]['membros'] += 1
        
    ranking_equipes = sorted(equipes_stats.values(), key=lambda x: x['xp_total'], reverse=True)

    return render_template('gamification.html', 
                           turmas=turmas, 
                           ranking=ranking, 
                           ranking_equipes=ranking_equipes,
                           medalhas=medalhas, 
                           turma_filtro=turma_filtro)


@app.route('/historico')
@teacher_or_admin_required
def historico():
    user = get_current_user()
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    data_filtro = request.args.get('data', '')

    query = SessaoChamada.query
    if turma_filtro:
        query = query.filter_by(turma_id=turma_filtro)
    if data_filtro:
        try:
            d = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            query = query.filter_by(data=d)
        except ValueError:
            pass

    sessoes = query.order_by(SessaoChamada.data.desc(), SessaoChamada.id.desc()).all()

    return render_template('history.html', 
                           turmas=turmas, 
                           sessoes=sessoes, 
                           turma_filtro=turma_filtro, 
                           data_filtro=data_filtro,
                           is_admin=user.is_admin if user else False)


# ==========================================
# APIS REST PROTEGIDAS POR PERFIL (RBAC)
# ==========================================

@app.route('/api/atividades', methods=['GET', 'POST'])
def api_atividades():
    if request.method == 'GET':
        atividades = Atividade.query.order_by(Atividade.id.desc()).all()
        return jsonify([a.to_dict() for a in atividades])
    
    # POST: Somente Admin Responsável
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Ação não permitida para o seu perfil.'}), 403

    dados = request.get_json() or {}
    if not dados.get('titulo') or not dados.get('descricao'):
        return jsonify({'error': 'Título e Descrição são obrigatórios'}), 400

    turma_id = dados.get('turma_id')
    turma_id = int(turma_id) if turma_id and str(turma_id).strip() != '' else None

    data_limite_obj = None
    if dados.get('data_limite'):
        try:
            data_limite_obj = datetime.strptime(dados.get('data_limite'), '%Y-%m-%d').date()
        except ValueError:
            pass

    nova = Atividade(
        turma_id=turma_id,
        titulo=dados.get('titulo').strip(),
        descricao=dados.get('descricao').strip(),
        kit_lego=dados.get('kit_lego', 'Lego SPIKE Prime').strip(),
        xp_recompensa=int(dados.get('xp_recompensa', 50) or 50),
        data_limite=data_limite_obj,
        link_material=dados.get('link_material', '').strip(),
        status=dados.get('status', 'ativo')
    )
    db.session.add(nova)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Desafio de robótica publicado!', 'atividade': nova.to_dict()})


@app.route('/api/atividades/<int:atividade_id>', methods=['PUT', 'DELETE'])
def api_atividade_detalhe(atividade_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Ação não permitida para o seu perfil.'}), 403

    atividade = db.session.get(Atividade, atividade_id)
    if not atividade:
        return jsonify({'error': 'Atividade não encontrada'}), 404

    if request.method == 'DELETE':
        db.session.delete(atividade)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Desafio excluído com sucesso!'})

    dados = request.get_json() or {}
    if 'titulo' in dados: atividade.titulo = dados['titulo'].strip()
    if 'descricao' in dados: atividade.descricao = dados['descricao'].strip()
    if 'kit_lego' in dados: atividade.kit_lego = dados['kit_lego'].strip()
    if 'xp_recompensa' in dados: atividade.xp_recompensa = int(dados['xp_recompensa'])
    if 'status' in dados: atividade.status = dados['status']
    if 'link_material' in dados: atividade.link_material = dados['link_material'].strip()
    if 'data_limite' in dados:
        if dados['data_limite']:
            try: atividade.data_limite = datetime.strptime(dados['data_limite'], '%Y-%m-%d').date()
            except ValueError: pass
        else:
            atividade.data_limite = None

    db.session.commit()
    return jsonify({'success': True, 'message': 'Desafio atualizado com sucesso!', 'atividade': atividade.to_dict()})


@app.route('/api/atividades/entregar', methods=['POST'])
def api_entregar_atividade():
    dados = request.get_json() or {}
    atividade_id = dados.get('atividade_id')
    aluno_id = dados.get('aluno_id') or session.get('aluno_id')
    
    if not atividade_id or not aluno_id:
        return jsonify({'error': 'Atividade e Aluno são obrigatórios'}), 400

    atividade = db.session.get(Atividade, int(atividade_id))
    aluno = db.session.get(Aluno, int(aluno_id))
    if not atividade or not aluno:
        return jsonify({'error': 'Atividade ou Aluno inválido'}), 404

    entrega = EntregaAtividade.query.filter_by(atividade_id=atividade.id, aluno_id=aluno.id).first()
    if not entrega:
        entrega = EntregaAtividade(
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            equipe=dados.get('equipe', aluno.equipe),
            descricao_solucao=dados.get('descricao_solucao', '').strip(),
            link_foto_video=dados.get('link_foto_video', '').strip(),
            status='pendente'
        )
        db.session.add(entrega)
    else:
        entrega.descricao_solucao = dados.get('descricao_solucao', '').strip()
        entrega.link_foto_video = dados.get('link_foto_video', '').strip()
        entrega.status = 'pendente'

    db.session.commit()
    return jsonify({'success': True, 'message': 'Solução enviada com sucesso ao laboratório!', 'entrega': entrega.to_dict()})


@app.route('/api/entregas/<int:entrega_id>/avaliar', methods=['POST'])
def api_avaliar_entrega(entrega_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Apenas os responsáveis pelas aulas podem avaliar entregas.'}), 403

    entrega = db.session.get(EntregaAtividade, entrega_id)
    if not entrega:
        return jsonify({'error': 'Entrega não encontrada'}), 404

    dados = request.get_json() or {}
    novo_status = dados.get('status', 'aprovado')
    feedback = dados.get('feedback_professor', '').strip()
    xp_a_conceder = int(dados.get('xp_concedido', entrega.atividade.xp_recompensa if entrega.atividade else 50))

    aluno = db.session.get(Aluno, entrega.aluno_id)

    if novo_status == 'aprovado' and entrega.status != 'aprovado':
        if aluno:
            aluno.pontos_xp += xp_a_conceder
        entrega.xp_concedido = xp_a_conceder
    elif novo_status != 'aprovado' and entrega.status == 'aprovado':
        if aluno:
            aluno.pontos_xp = max(0, aluno.pontos_xp - entrega.xp_concedido)
        entrega.xp_concedido = 0

    entrega.status = novo_status
    entrega.feedback_professor = feedback
    entrega.avaliado_em = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Entrega avaliada com sucesso (+{xp_a_conceder} XP)!' if novo_status == 'aprovado' else 'Avaliação salva!',
        'entrega': entrega.to_dict()
    })


@app.route('/api/chamada/carregar', methods=['GET'])
def api_carregar_chamada():
    turma_id = request.args.get('turma_id', type=int)
    data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    
    if not turma_id: return jsonify({'error': 'Turma não informada'}), 400
    try: data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError: return jsonify({'error': 'Data inválida'}), 400

    turma = db.session.get(Turma, turma_id)
    if not turma: return jsonify({'error': 'Turma não encontrada'}), 404

    alunos = Aluno.query.filter_by(turma_id=turma_id, ativo=True).order_by(Aluno.nome.asc()).all()
    sessao = SessaoChamada.query.filter_by(turma_id=turma_id, data=data_obj).first()
    
    registros_dict = {r.aluno_id: r.to_dict() for r in sessao.registros} if sessao else {}

    alunos_data = []
    for a in alunos:
        reg = registros_dict.get(a.id)
        alunos_data.append({
            'aluno': a.to_dict(),
            'status': reg['status'] if reg else 'presente',
            'justificativa': reg['justificativa'] if reg else '',
            'pontos_bonus': reg['pontos_bonus'] if reg else 0,
            'motivo_bonus': reg['motivo_bonus'] if reg else ''
        })

    return jsonify({
        'turma': turma.to_dict(),
        'data': data_str,
        'existe_sessao': bool(sessao),
        'sessao_id': sessao.id if sessao else None,
        'topico': sessao.topico if sessao else 'Oficina de Robótica',
        'observacoes': sessao.observacoes if sessao else '',
        'proxima_aula': sessao.proxima_aula if sessao else '',
        'alunos': alunos_data
    })


@app.route('/api/chamada/salvar', methods=['POST'])
def api_salvar_chamada():
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Apenas os responsáveis pelas aulas podem salvar chamadas.'}), 403

    dados = request.get_json() or {}
    turma_id = dados.get('turma_id')
    data_str = dados.get('data')
    topico = dados.get('topico', 'Oficina de Robótica')
    observacoes = dados.get('observacoes', '')
    proxima_aula = dados.get('proxima_aula', '')
    lista_presenca = dados.get('registros', [])

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Data inválida'}), 400

    sessao = SessaoChamada.query.filter_by(turma_id=turma_id, data=data_obj).first()
    
    if sessao:
        for r_antigo in sessao.registros:
            aluno = db.session.get(Aluno, r_antigo.aluno_id)
            if aluno:
                xp_remover = (r_antigo.pontos_ganhos or 0) + (r_antigo.pontos_bonus or 0)
                aluno.pontos_xp = max(0, aluno.pontos_xp - xp_remover)
        
        RegistroPresenca.query.filter_by(sessao_id=sessao.id).delete()
        sessao.topico = topico
        sessao.observacoes = observacoes
        sessao.proxima_aula = proxima_aula
    else:
        sessao = SessaoChamada(
            turma_id=turma_id,
            data=data_obj,
            topico=topico,
            observacoes=observacoes,
            proxima_aula=proxima_aula
        )
        db.session.add(sessao)
        db.session.flush()

    total_xp_distribuido = 0
    alunos_atualizados = []

    for item in lista_presenca:
        aluno_id = item.get('aluno_id')
        status = item.get('status', 'presente')
        justificativa = item.get('justificativa', '')
        pontos_bonus = int(item.get('pontos_bonus', 0) or 0)
        motivo_bonus = item.get('motivo_bonus', '')

        pontos_base = 10 if status == 'presente' else (2 if status == 'justificada' else 0)

        aluno = db.session.get(Aluno, aluno_id)
        if aluno:
            aluno.pontos_xp += (pontos_base + pontos_bonus)
            total_xp_distribuido += (pontos_base + pontos_bonus)
            alunos_atualizados.append({
                'id': aluno.id,
                'nome': aluno.nome,
                'novo_xp': aluno.pontos_xp,
                'nivel': aluno.info_nivel
            })

            total_presencas = sum(1 for r in aluno.registros if r.status == 'presente')
            if total_presencas >= 5:
                med_freq = Medalha.query.filter_by(codigo="super_frequencia").first()
                if med_freq and not ConquistaAluno.query.filter_by(aluno_id=aluno.id, medalha_id=med_freq.id).first():
                    db.session.add(ConquistaAluno(aluno_id=aluno.id, medalha_id=med_freq.id))
                    aluno.pontos_xp += med_freq.xp_bonus

        reg = RegistroPresenca(
            sessao_id=sessao.id,
            aluno_id=aluno_id,
            status=status,
            justificativa=justificativa,
            pontos_ganhos=pontos_base,
            pontos_bonus=pontos_bonus,
            motivo_bonus=motivo_bonus
        )
        db.session.add(reg)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Chamada e registros pedagógicos salvos com sucesso!',
        'sessao_id': sessao.id,
        'total_xp_distribuido': total_xp_distribuido,
        'alunos': alunos_atualizados
    })


@app.route('/api/slides', methods=['GET', 'POST'])
def api_slides():
    if request.method == 'GET':
        slides = SlideAula.query.order_by(SlideAula.numero_aula.asc()).all()
        return jsonify([s.to_dict() for s in slides])

    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Apenas responsáveis podem adicionar materiais.'}), 403

    dados = request.get_json() or {}
    if not dados.get('titulo') or not dados.get('link_slide'):
        return jsonify({'error': 'Título e Link são obrigatórios'}), 400

    turma_id = dados.get('turma_id')
    turma_id = int(turma_id) if turma_id and str(turma_id).strip() != '' else None

    novo_slide = SlideAula(
        turma_id=turma_id,
        titulo=dados.get('titulo').strip(),
        descricao=dados.get('descricao', '').strip(),
        numero_aula=int(dados.get('numero_aula', 1) or 1),
        link_slide=dados.get('link_slide').strip(),
        tipo=dados.get('tipo', 'slides')
    )
    db.session.add(novo_slide)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Material didático cadastrado!', 'slide': novo_slide.to_dict()})


@app.route('/api/slides/<int:slide_id>', methods=['DELETE'])
def api_excluir_slide(slide_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Ação não permitida.'}), 403

    slide = db.session.get(SlideAula, slide_id)
    if not slide: return jsonify({'error': 'Não encontrado'}), 404

    db.session.delete(slide)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Material excluído.'})


@app.route('/api/duvidas', methods=['GET', 'POST'])
def api_duvidas():
    if request.method == 'GET':
        duvidas = DuvidaAluno.query.order_by(DuvidaAluno.created_at.desc()).all()
        return jsonify([d.to_dict() for d in duvidas])

    dados = request.get_json() or {}
    aluno_id = dados.get('aluno_id') or session.get('aluno_id')
    aluno = db.session.get(Aluno, int(aluno_id)) if aluno_id else None

    nova_duvida = DuvidaAluno(
        turma_id=aluno.turma_id if aluno else None,
        aluno_id=aluno.id if aluno else None,
        nome_autor=aluno.nome if aluno else dados.get('nome_autor', 'Aluno').strip(),
        titulo=dados.get('titulo', '').strip(),
        pergunta=dados.get('pergunta', '').strip(),
        categoria=dados.get('categoria', 'Programação & Sensores'),
        status='aberta'
    )
    db.session.add(nova_duvida)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Dúvida enviada ao fórum!', 'duvida': nova_duvida.to_dict()})


@app.route('/api/duvidas/<int:duvida_id>/responder', methods=['POST'])
def api_responder_duvida(duvida_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Faça login para responder.'}), 401

    duvida = db.session.get(DuvidaAluno, duvida_id)
    if not duvida: return jsonify({'error': 'Dúvida não encontrada'}), 404

    dados = request.get_json() or {}
    resposta = dados.get('resposta', '').strip()
    if not resposta: return jsonify({'error': 'Resposta não pode ser vazia'}), 400

    duvida.resposta_professor = resposta
    duvida.respondido_por = user.nome
    duvida.status = 'respondida'
    duvida.respondido_em = datetime.now()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Resposta técnica enviada!', 'duvida': duvida.to_dict()})


@app.route('/api/duvidas/<int:duvida_id>/status', methods=['PUT'])
def api_status_duvida(duvida_id):
    user = get_current_user()
    if not user: return jsonify({'error': 'Não autorizado'}), 401

    duvida = db.session.get(DuvidaAluno, duvida_id)
    if not duvida: return jsonify({'error': 'Não encontrada'}), 404

    dados = request.get_json() or {}
    duvida.status = dados.get('status', 'resolvida')
    db.session.commit()
    return jsonify({'success': True, 'message': f'Status alterado para {duvida.status}!'})


@app.route('/api/diario', methods=['POST'])
def api_criar_diario():
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Apenas os responsáveis pelas aulas podem postar no diário.'}), 403

    dados = request.get_json() or {}
    turma_id = dados.get('turma_id')
    titulo = dados.get('titulo')
    conteudo = dados.get('conteudo')
    categoria = dados.get('categoria', 'Anotação Pedagógica')
    data_str = dados.get('data', date.today().strftime('%Y-%m-%d'))

    try: data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError: data_obj = date.today()

    novo_diario = DiarioBordo(
        turma_id=int(turma_id),
        data=data_obj,
        titulo=titulo.strip(),
        conteudo=conteudo.strip(),
        categoria=categoria,
        autor=user.nome
    )
    db.session.add(novo_diario)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Nota adicionada ao Diário de Bordo!', 'diario': novo_diario.to_dict()})


@app.route('/api/aluno/alterar-pin', methods=['PUT'])
def api_aluno_alterar_pin():
    aluno = get_current_aluno()
    if not aluno: return jsonify({'error': 'Não autenticado como aluno'}), 401

    dados = request.get_json() or {}
    novo_pin = str(dados.get('novo_pin', '')).strip()
    if len(novo_pin) < 4 or len(novo_pin) > 8:
        return jsonify({'error': 'O PIN deve conter entre 4 e 8 dígitos'}), 400

    aluno.pin_acesso = novo_pin
    db.session.commit()
    return jsonify({'success': True, 'message': 'PIN atualizado com sucesso!'})


@app.route('/exportar-csv')
@teacher_or_admin_required
def exportar_csv():
    turma_id = request.args.get('turma_id', type=int)
    
    query = Aluno.query.filter_by(ativo=True)
    if turma_id: query = query.filter_by(turma_id=turma_id)
    alunos = query.all()
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(['ID', 'Nome', 'Turma', 'Equipe', 'Pontos XP', 'Nivel', 'Presencas', 'Faltas', 'Justificadas', 'Taxa Presenca (%)'])
    for a in alunos:
        stats = a.estatisticas
        lvl = a.info_nivel
        writer.writerow([
            a.id, a.nome, a.turma.nome if a.turma else '', a.equipe, a.pontos_xp,
            f"Nivel {lvl['nivel']} - {lvl['titulo']}", stats['presentes'], stats['faltas'], stats['justificadas'], f"{stats['porcentagem']}%"
        ])
        
    output.seek(0)
    nome_arquivo = f"frequencia_montebot_turma_{turma_id or 'geral'}_{date.today().strftime('%Y%m%d')}.csv"
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={nome_arquivo}"})


@app.errorhandler(500)
def erro_servidor(e):
    return f"""
    <div style="font-family: sans-serif; text-align: center; padding: 40px; background: #0F172A; color: white; min-height: 100vh;">
      <h1 style="color: #EF4444; font-size: 2.2rem;">🧱 Portal de Robótica - Aviso de Conexão</h1>
      <p style="color: #94A3B8; font-size: 1rem; max-width: 600px; margin: 16px auto;">
        O servidor está reconectando com o banco de dados em nuvem.
      </p>
      <a href="/" style="display: inline-block; background: #2563EB; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold;">
        🔄 Tentar Novamente
      </a>
    </div>
    """, 500


@app.errorhandler(404)
def nao_encontrado(e):
    return redirect(url_for('home'))


if __name__ == '__main__':
    print("\n" + "="*60)
    print("PORTAL INSTITUCIONAL DE ROBOTICA - UFU / FACOM / LINA / MONTE BOT")
    print("Acesse no navegador: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
