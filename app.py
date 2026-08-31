import os
import csv
import io
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, flash, session
from models import db, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo, Atividade, EntregaAtividade, SlideAula, DuvidaAluno
from database import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lego-chamada-secret-key-2026')

# Configuração de Banco de Dados:
# No Vercel (Postgres gratuito como Neon/Supabase/Vercel Postgres) ou SQLite local
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
# ROTAS DE PÁGINAS (TEMPLATES)
# ==========================================

@app.route('/')
def index():
    turmas = Turma.query.all()
    total_alunos = Aluno.query.filter_by(ativo=True).count()
    total_chamadas = SessaoChamada.query.count()
    total_anotacoes = DiarioBordo.query.count()
    total_atividades = Atividade.query.count()
    total_slides = SlideAula.query.count()
    total_duvidas = DuvidaAluno.query.count()
    
    # Chamadas de hoje
    hoje = date.today()
    chamadas_hoje = SessaoChamada.query.filter_by(data=hoje).all()
    turmas_feitas_hoje = {c.turma_id for c in chamadas_hoje}
    
    # Top 5 alunos em destaque (Ranking Geral)
    top_alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.pontos_xp.desc()).limit(5).all()
    
    # Últimas anotações do diário de bordo
    ultimas_anotacoes = DiarioBordo.query.order_by(DiarioBordo.data.desc(), DiarioBordo.id.desc()).limit(3).all()
    
    # Atividades ativas recentes
    atividades_recentes = Atividade.query.filter_by(status='ativo').order_by(Atividade.id.desc()).limit(3).all()

    return render_template('index.html', 
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
                           atividades_recentes=atividades_recentes,
                           hoje=hoje.strftime('%Y-%m-%d'),
                           hoje_formatado=hoje.strftime('%d/%m/%Y'))


@app.route('/chamada')
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
def atividades_page():
    turmas = Turma.query.all()
    turma_filtro = request.args.get('turma_id', type=int)
    status_filtro = request.args.get('status', '')

    query = Atividade.query
    if turma_filtro:
        query = query.filter((Atividade.turma_id == turma_filtro) | (Atividade.turma_id == None))
    if status_filtro:
        query = query.filter_by(status=status_filtro)

    atividades = query.order_by(Atividade.id.desc()).all()
    
    # Todas as entregas para a aba de correção
    entregas_query = EntregaAtividade.query
    if turma_filtro:
        entregas_query = entregas_query.join(Aluno).filter(Aluno.turma_id == turma_filtro)
    entregas = entregas_query.order_by(EntregaAtividade.created_at.desc()).all()

    # Todos os alunos para o formulário de entrega
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
                           hoje=date.today().strftime('%Y-%m-%d'))


@app.route('/slides')
def slides_page():
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
                           tipo_filtro=tipo_filtro)


@app.route('/duvidas')
def forum_page():
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
                           status_filtro=status_filtro)


# ==========================================
# ROTAS DO PORTAL DO ALUNO (ESTUDOS REMOTOS)
# ==========================================

@app.route('/estudos')
def estudos_page():
    aluno_id = session.get('aluno_id')
    if not aluno_id:
        return redirect(url_for('aluno_login'))
    
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno or not aluno.ativo:
        session.pop('aluno_id', None)
        return redirect(url_for('aluno_login'))
    
    # Slides e materiais didáticos da turma do aluno ou gerais
    slides = SlideAula.query.filter(
        (SlideAula.turma_id == aluno.turma_id) | (SlideAula.turma_id == None)
    ).order_by(SlideAula.numero_aula.asc()).all()

    # Atividades e desafios ativos
    atividades = Atividade.query.filter(
        (Atividade.turma_id == aluno.turma_id) | (Atividade.turma_id == None)
    ).filter_by(status='ativo').order_by(Atividade.id.desc()).all()

    # Entregas feitas pelo próprio aluno
    minhas_entregas = EntregaAtividade.query.filter_by(aluno_id=aluno.id).order_by(EntregaAtividade.created_at.desc()).all()
    entregas_dict = {e.atividade_id: e for e in minhas_entregas}

    # Minhas dúvidas e respostas
    minhas_duvidas = DuvidaAluno.query.filter_by(aluno_id=aluno.id).order_by(DuvidaAluno.created_at.desc()).all()

    # Medalhas do aluno
    conquistas = ConquistaAluno.query.filter_by(aluno_id=aluno.id).all()

    return render_template('student_portal.html',
                           aluno=aluno,
                           slides=slides,
                           atividades=atividades,
                           minhas_entregas=minhas_entregas,
                           entregas_dict=entregas_dict,
                           minhas_duvidas=minhas_duvidas,
                           conquistas=conquistas,
                           hoje=date.today().strftime('%Y-%m-%d'))


@app.route('/aluno/login', methods=['GET', 'POST'])
def aluno_login():
    if request.method == 'GET':
        if session.get('aluno_id'):
            return redirect(url_for('estudos_page'))
        turmas = Turma.query.all()
        alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.nome.asc()).all()
        return render_template('student_login.html', turmas=turmas, alunos=alunos)

    dados = request.get_json() or {}
    aluno_id = dados.get('aluno_id')
    pin = str(dados.get('pin', '')).strip()

    if not aluno_id or not pin:
        return jsonify({'error': 'Selecione seu nome e digite seu PIN de acesso'}), 400

    aluno = db.session.get(Aluno, int(aluno_id))
    if not aluno or not aluno.ativo:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    # Validação do PIN (padrão '1234' se vazio)
    pin_correto = aluno.pin_acesso or '1234'
    if pin != pin_correto:
        return jsonify({'error': 'PIN incorreto! Solicite ajuda ao seu professor.'}), 401

    session['aluno_id'] = aluno.id
    return jsonify({
        'success': True,
        'message': f'Olá, {aluno.nome}! Acesso liberado.',
        'redirect': url_for('estudos_page')
    })


@app.route('/aluno/logout')
def aluno_logout():
    session.pop('aluno_id', None)
    return redirect(url_for('aluno_login'))


@app.route('/api/aluno/alterar-pin', methods=['PUT'])
def api_aluno_alterar_pin():
    aluno_id = session.get('aluno_id')
    if not aluno_id:
        return jsonify({'error': 'Não autenticado'}), 401
    
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    dados = request.get_json() or {}
    novo_pin = str(dados.get('novo_pin', '')).strip()
    if len(novo_pin) < 4 or len(novo_pin) > 8:
        return jsonify({'error': 'O PIN deve conter entre 4 e 8 dígitos'}), 400

    aluno.pin_acesso = novo_pin
    db.session.commit()
    return jsonify({'success': True, 'message': 'PIN de segurança atualizado com sucesso!'})


@app.route('/anotacoes')
def anotacoes_page():
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
                           hoje=date.today().strftime('%Y-%m-%d'))


@app.route('/alunos')
def alunos_page():
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
                           medalhas=medalhas)


@app.route('/gamificacao')
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
def historico():
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
                           data_filtro=data_filtro)


# ==========================================
# ROTAS DA API REST: ATIVIDADES & ENTREGAS
# ==========================================

@app.route('/api/atividades', methods=['GET', 'POST'])
def api_atividades():
    if request.method == 'GET':
        atividades = Atividade.query.order_by(Atividade.id.desc()).all()
        return jsonify([a.to_dict() for a in atividades])
    
    dados = request.get_json() or {}
    if not dados.get('titulo') or not dados.get('descricao'):
        return jsonify({'error': 'Título e Descrição são obrigatórios'}), 400

    turma_id = dados.get('turma_id')
    if turma_id and str(turma_id).strip() != '':
        turma_id = int(turma_id)
    else:
        turma_id = None

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

    return jsonify({'success': True, 'message': 'Desafio Lego cadastrado com sucesso!', 'atividade': nova.to_dict()})


@app.route('/api/atividades/<int:atividade_id>', methods=['PUT', 'DELETE'])
def api_atividade_detalhe(atividade_id):
    atividade = db.session.get(Atividade, atividade_id)
    if not atividade:
        return jsonify({'error': 'Atividade não encontrada'}), 404

    if request.method == 'DELETE':
        db.session.delete(atividade)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Atividade excluída com sucesso!'})

    dados = request.get_json() or {}
    if 'titulo' in dados:
        atividade.titulo = dados['titulo'].strip()
    if 'descricao' in dados:
        atividade.descricao = dados['descricao'].strip()
    if 'kit_lego' in dados:
        atividade.kit_lego = dados['kit_lego'].strip()
    if 'xp_recompensa' in dados:
        atividade.xp_recompensa = int(dados['xp_recompensa'])
    if 'status' in dados:
        atividade.status = dados['status']
    if 'link_material' in dados:
        atividade.link_material = dados['link_material'].strip()
    if 'data_limite' in dados:
        if dados['data_limite']:
            try:
                atividade.data_limite = datetime.strptime(dados['data_limite'], '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            atividade.data_limite = None

    db.session.commit()
    return jsonify({'success': True, 'message': 'Atividade atualizada com sucesso!', 'atividade': atividade.to_dict()})


@app.route('/api/atividades/entregar', methods=['POST'])
def api_entregar_atividade():
    dados = request.get_json() or {}
    atividade_id = dados.get('atividade_id')
    aluno_id = dados.get('aluno_id')
    
    if not atividade_id or not aluno_id:
        return jsonify({'error': 'Atividade e Aluno são obrigatórios'}), 400

    atividade = db.session.get(Atividade, int(atividade_id))
    aluno = db.session.get(Aluno, int(aluno_id))
    if not atividade or not aluno:
        return jsonify({'error': 'Atividade ou Aluno inválido'}), 404

    entrega = EntregaAtividade(
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        equipe=dados.get('equipe', aluno.equipe),
        descricao_solucao=dados.get('descricao_solucao', '').strip(),
        link_foto_video=dados.get('link_foto_video', '').strip(),
        arquivo_anexo=dados.get('arquivo_anexo', '').strip(),
        status='pendente'
    )
    db.session.add(entrega)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Atividade enviada com sucesso! Aguarde a avaliação do professor.', 'entrega': entrega.to_dict()})


@app.route('/api/entregas/<int:entrega_id>/avaliar', methods=['POST'])
def api_avaliar_entrega(entrega_id):
    entrega = db.session.get(EntregaAtividade, entrega_id)
    if not entrega:
        return jsonify({'error': 'Entrega não encontrada'}), 404

    dados = request.get_json() or {}
    novo_status = dados.get('status', 'aprovado') # aprovado, revisar
    feedback = dados.get('feedback_professor', '').strip()
    xp_a_conceder = int(dados.get('xp_concedido', entrega.atividade.xp_recompensa if entrega.atividade else 50))

    aluno = db.session.get(Aluno, entrega.aluno_id)

    # Se aprovado e antes não estava aprovado, concede o XP ao aluno!
    if novo_status == 'aprovado' and entrega.status != 'aprovado':
        if aluno:
            aluno.pontos_xp += xp_a_conceder
        entrega.xp_concedido = xp_a_conceder
    elif novo_status != 'aprovado' and entrega.status == 'aprovado':
        # Se revogou aprovação, remove o XP concedido
        if aluno:
            aluno.pontos_xp = max(0, aluno.pontos_xp - entrega.xp_concedido)
        entrega.xp_concedido = 0

    entrega.status = novo_status
    entrega.feedback_professor = feedback
    entrega.avaliado_em = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Entrega avaliada como "{novo_status.upper()}"! ({xp_a_conceder} XP creditados)' if novo_status == 'aprovado' else 'Entrega avaliada!',
        'entrega': entrega.to_dict(),
        'aluno_xp': aluno.pontos_xp if aluno else 0
    })


# ==========================================
# ROTAS DA API REST: SLIDES & MATERIAIS
# ==========================================

@app.route('/api/slides', methods=['GET', 'POST'])
def api_slides():
    if request.method == 'GET':
        slides = SlideAula.query.order_by(SlideAula.numero_aula.asc()).all()
        return jsonify([s.to_dict() for s in slides])

    dados = request.get_json() or {}
    if not dados.get('titulo') or not dados.get('link_slide'):
        return jsonify({'error': 'Título e Link do Slide/Material são obrigatórios'}), 400

    turma_id = dados.get('turma_id')
    if turma_id and str(turma_id).strip() != '':
        turma_id = int(turma_id)
    else:
        turma_id = None

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

    return jsonify({'success': True, 'message': 'Slide/Material adicionado com sucesso!', 'slide': novo_slide.to_dict()})


@app.route('/api/slides/<int:slide_id>', methods=['DELETE'])
def api_excluir_slide(slide_id):
    slide = db.session.get(SlideAula, slide_id)
    if not slide:
        return jsonify({'error': 'Material não encontrado'}), 404

    db.session.delete(slide)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Material excluído com sucesso!'})


# ==========================================
# ROTAS DA API REST: FÓRUM & DÚVIDAS
# ==========================================

@app.route('/api/duvidas', methods=['GET', 'POST'])
def api_duvidas():
    if request.method == 'GET':
        duvidas = DuvidaAluno.query.order_by(DuvidaAluno.created_at.desc()).all()
        return jsonify([d.to_dict() for d in duvidas])

    dados = request.get_json() or {}
    if not dados.get('titulo') or not dados.get('pergunta'):
        return jsonify({'error': 'Título e Pergunta são obrigatórios'}), 400

    turma_id = dados.get('turma_id')
    if turma_id and str(turma_id).strip() != '':
        turma_id = int(turma_id)
    else:
        turma_id = None

    aluno_id = dados.get('aluno_id')
    if aluno_id and str(aluno_id).strip() != '':
        aluno_id = int(aluno_id)
    else:
        aluno_id = None

    nova_duvida = DuvidaAluno(
        turma_id=turma_id,
        aluno_id=aluno_id,
        nome_autor=dados.get('nome_autor', 'Aluno Construtor').strip(),
        titulo=dados.get('titulo').strip(),
        pergunta=dados.get('pergunta').strip(),
        categoria=dados.get('categoria', 'Programação & Sensores'),
        status='aberta'
    )
    db.session.add(nova_duvida)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Dúvida enviada com sucesso ao fórum!', 'duvida': nova_duvida.to_dict()})


@app.route('/api/duvidas/<int:duvida_id>/responder', methods=['POST'])
def api_responder_duvida(duvida_id):
    duvida = db.session.get(DuvidaAluno, duvida_id)
    if not duvida:
        return jsonify({'error': 'Dúvida não encontrada'}), 404

    dados = request.get_json() or {}
    resposta = dados.get('resposta', '').strip()
    respondido_por = dados.get('respondido_por', 'Professor(a) de Robótica').strip()

    if not resposta:
        return jsonify({'error': 'Resposta não pode ser vazia'}), 400

    duvida.resposta_professor = resposta
    duvida.respondido_por = respondido_por
    duvida.status = 'respondida'
    duvida.respondido_em = datetime.now()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Resposta enviada com sucesso!', 'duvida': duvida.to_dict()})


@app.route('/api/duvidas/<int:duvida_id>/status', methods=['PUT'])
def api_status_duvida(duvida_id):
    duvida = db.session.get(DuvidaAluno, duvida_id)
    if not duvida:
        return jsonify({'error': 'Dúvida não encontrada'}), 404

    dados = request.get_json() or {}
    novo_status = dados.get('status', 'resolvida')
    duvida.status = novo_status
    db.session.commit()

    return jsonify({'success': True, 'message': f'Status alterado para {novo_status}!', 'duvida': duvida.to_dict()})


@app.route('/api/duvidas/<int:duvida_id>', methods=['DELETE'])
def api_excluir_duvida(duvida_id):
    duvida = db.session.get(DuvidaAluno, duvida_id)
    if not duvida:
        return jsonify({'error': 'Dúvida não encontrada'}), 404

    db.session.delete(duvida)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Dúvida excluída com sucesso!'})


# ==========================================
# ROTAS DA API REST: TURMAS, DIÁRIO, ALUNOS
# ==========================================

@app.route('/api/turmas', methods=['GET'])
def api_turmas():
    turmas = Turma.query.all()
    return jsonify([t.to_dict() for t in turmas])


@app.route('/api/turma/<int:turma_id>/anotacoes', methods=['PUT'])
def api_atualizar_anotacao_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        return jsonify({'error': 'Turma não encontrada'}), 404

    dados = request.get_json() or {}
    turma.anotacoes = dados.get('anotacoes', '').strip()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Anotações da {turma.nome} salvas com sucesso!',
        'anotacoes': turma.anotacoes
    })


@app.route('/api/diario', methods=['POST'])
def api_criar_diario():
    dados = request.get_json() or {}
    turma_id = dados.get('turma_id')
    titulo = dados.get('titulo')
    conteudo = dados.get('conteudo')
    categoria = dados.get('categoria', 'Anotação Pedagógica')
    data_str = dados.get('data', date.today().strftime('%Y-%m-%d'))

    if not turma_id or not titulo or not conteudo:
        return jsonify({'error': 'Turma, Título e Conteúdo são obrigatórios'}), 400

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        data_obj = date.today()

    novo_diario = DiarioBordo(
        turma_id=int(turma_id),
        data=data_obj,
        titulo=titulo.strip(),
        conteudo=conteudo.strip(),
        categoria=categoria
    )
    db.session.add(novo_diario)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Anotação adicionada ao Diário de Bordo!', 'diario': novo_diario.to_dict()})


@app.route('/api/diario/<int:diario_id>', methods=['DELETE'])
def api_excluir_diario(diario_id):
    diario = db.session.get(DiarioBordo, diario_id)
    if not diario:
        return jsonify({'error': 'Anotação não encontrada'}), 404

    db.session.delete(diario)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Anotação excluída com sucesso!'})


@app.route('/api/turma/<int:turma_id>/alunos', methods=['GET'])
def api_turma_alunos(turma_id):
    alunos = Aluno.query.filter_by(turma_id=turma_id, ativo=True).order_by(Aluno.nome.asc()).all()
    return jsonify([a.to_dict() for a in alunos])


@app.route('/api/chamada/carregar', methods=['GET'])
def api_carregar_chamada():
    turma_id = request.args.get('turma_id', type=int)
    data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    
    if not turma_id:
        return jsonify({'error': 'Turma não informada'}), 400
        
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Data inválida'}), 400

    turma = db.session.get(Turma, turma_id)
    if not turma:
        return jsonify({'error': 'Turma não encontrada'}), 404

    alunos = Aluno.query.filter_by(turma_id=turma_id, ativo=True).order_by(Aluno.nome.asc()).all()
    
    sessao = SessaoChamada.query.filter_by(turma_id=turma_id, data=data_obj).first()
    
    registros_dict = {}
    if sessao:
        for r in sessao.registros:
            registros_dict[r.aluno_id] = r.to_dict()

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
        'topico': sessao.topico if sessao else 'Oficina Lego',
        'observacoes': sessao.observacoes if sessao else '',
        'proxima_aula': sessao.proxima_aula if sessao else '',
        'alunos': alunos_data
    })


@app.route('/api/chamada/salvar', methods=['POST'])
def api_salvar_chamada():
    dados = request.get_json()
    if not dados:
        return jsonify({'error': 'Dados inválidos'}), 400

    turma_id = dados.get('turma_id')
    data_str = dados.get('data')
    topico = dados.get('topico', 'Oficina Lego')
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

        if status == 'presente':
            pontos_base = 10
        elif status == 'justificada':
            pontos_base = 2
        else:
            pontos_base = 0

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
        'message': 'Chamada e anotações salvas com sucesso!',
        'sessao_id': sessao.id,
        'total_xp_distribuido': total_xp_distribuido,
        'alunos': alunos_atualizados
    })


@app.route('/api/alunos', methods=['POST'])
def api_criar_aluno():
    dados = request.get_json()
    if not dados or not dados.get('nome') or not dados.get('turma_id'):
        return jsonify({'error': 'Nome e Turma são obrigatórios'}), 400

    novo_aluno = Aluno(
        nome=dados.get('nome').strip(),
        turma_id=int(dados.get('turma_id')),
        equipe=dados.get('equipe', 'Equipe Lego').strip(),
        avatar_tipo=dados.get('avatar_tipo', 'lego-red'),
        pontos_xp=int(dados.get('pontos_xp', 0) or 0)
    )

    db.session.add(novo_aluno)
    db.session.flush()

    med_primeiro = Medalha.query.filter_by(codigo="primeiro_bloco").first()
    if med_primeiro:
        db.session.add(ConquistaAluno(aluno_id=novo_aluno.id, medalha_id=med_primeiro.id))

    db.session.commit()
    return jsonify({'success': True, 'aluno': novo_aluno.to_dict()})


@app.route('/api/alunos/<int:aluno_id>', methods=['PUT'])
def api_editar_aluno(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    dados = request.get_json()
    if not dados:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'nome' in dados:
        aluno.nome = dados['nome'].strip()
    if 'turma_id' in dados:
        aluno.turma_id = int(dados['turma_id'])
    if 'equipe' in dados:
        aluno.equipe = dados['equipe'].strip()
    if 'avatar_tipo' in dados:
        aluno.avatar_tipo = dados['avatar_tipo']
    if 'pontos_xp' in dados:
        aluno.pontos_xp = int(dados['pontos_xp'])

    db.session.commit()
    return jsonify({'success': True, 'aluno': aluno.to_dict()})


@app.route('/api/alunos/<int:aluno_id>', methods=['DELETE'])
def api_excluir_aluno(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    db.session.delete(aluno)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Aluno excluído com sucesso'})


@app.route('/api/alunos/<int:aluno_id>/conceder-medalha', methods=['POST'])
def api_conceder_medalha(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    dados = request.get_json() or {}
    medalha_id = dados.get('medalha_id')

    if not medalha_id:
        return jsonify({'error': 'ID da medalha obrigatório'}), 400

    medalha = db.session.get(Medalha, medalha_id)
    if not medalha:
        return jsonify({'error': 'Medalha não encontrada'}), 404
    
    ja_tem = ConquistaAluno.query.filter_by(aluno_id=aluno.id, medalha_id=medalha.id).first()
    if ja_tem:
        return jsonify({'error': 'Aluno já possui esta conquista!'}), 400

    conquista = ConquistaAluno(aluno_id=aluno.id, medalha_id=medalha.id)
    aluno.pontos_xp += medalha.xp_bonus
    db.session.add(conquista)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Medalha "{medalha.nome}" concedida com sucesso! (+{medalha.xp_bonus} XP)',
        'novo_xp': aluno.pontos_xp,
        'nivel': aluno.info_nivel
    })


@app.route('/api/alunos/<int:aluno_id>/ajustar-xp', methods=['POST'])
def api_ajustar_xp(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        return jsonify({'error': 'Aluno não encontrado'}), 404

    dados = request.get_json() or {}
    quantidade = int(dados.get('quantidade', 0))
    motivo = dados.get('motivo', 'Ajuste manual de pontos')

    aluno.pontos_xp = max(0, aluno.pontos_xp + quantidade)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{quantidade} XP aplicados ao aluno!',
        'novo_xp': aluno.pontos_xp,
        'nivel': aluno.info_nivel
    })


@app.route('/api/historico/<int:sessao_id>', methods=['GET'])
def api_detalhes_historico(sessao_id):
    sessao = db.session.get(SessaoChamada, sessao_id)
    if not sessao:
        return jsonify({'error': 'Chamada não encontrada'}), 404

    return jsonify({
        'sessao': sessao.to_dict(),
        'registros': [r.to_dict() for r in sessao.registros]
    })


@app.route('/api/historico/<int:sessao_id>', methods=['DELETE'])
def api_excluir_historico(sessao_id):
    sessao = db.session.get(SessaoChamada, sessao_id)
    if not sessao:
        return jsonify({'error': 'Chamada não encontrada'}), 404
    
    for r in sessao.registros:
        aluno = db.session.get(Aluno, r.aluno_id)
        if aluno:
            aluno.pontos_xp = max(0, aluno.pontos_xp - (r.pontos_ganhos + r.pontos_bonus))

    db.session.delete(sessao)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chamada excluída e pontos revertidos com sucesso!'})


@app.route('/exportar-csv')
def exportar_csv():
    turma_id = request.args.get('turma_id', type=int)
    
    query = Aluno.query.filter_by(ativo=True)
    if turma_id:
        query = query.filter_by(turma_id=turma_id)
        
    alunos = query.all()
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(['ID', 'Nome', 'Turma', 'Equipe', 'Pontos XP', 'Nível', 'Presenças', 'Faltas', 'Justificadas', 'Taxa Presença (%)'])
    
    for a in alunos:
        stats = a.estatisticas
        lvl = a.info_nivel
        writer.writerow([
            a.id,
            a.nome,
            a.turma.nome if a.turma else '',
            a.equipe,
            a.pontos_xp,
            f"Nível {lvl['nivel']} - {lvl['titulo']}",
            stats['presentes'],
            stats['faltas'],
            stats['justificadas'],
            f"{stats['porcentagem']}%"
        ])
        
    output.seek(0)
    nome_arquivo = f"frequencia_lego_turma_{turma_id or 'geral'}_{date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={nome_arquivo}"}
    )


@app.errorhandler(500)
def erro_servidor(e):
    return f"""
    <div style="font-family: sans-serif; text-align: center; padding: 40px; background: #0F172A; color: white; min-height: 100vh;">
      <h1 style="color: #EF4444; font-size: 2.5rem;">🧱 Ops! Erro Temporário de Conexão</h1>
      <p style="color: #94A3B8; font-size: 1.1rem; max-width: 600px; margin: 16px auto;">
        O servidor do banco de dados está sincronizando ou temporariamente indisponível.
      </p>
      <div style="background: #1E293B; padding: 16px; border-radius: 8px; max-width: 600px; margin: 20px auto; border: 1px solid #334155; text-align: left;">
        <code style="color: #F59E0B; font-size: 0.9rem;">{str(e)}</code>
      </div>
      <a href="/" style="display: inline-block; background: #2563EB; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">
        🔄 Recarregar Página
      </a>
    </div>
    """, 500


@app.errorhandler(404)
def nao_encontrado(e):
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SISTEMA DE ROBOTICA & CHAMADA LEGO INICIADO COM SUCESSO!")
    print("Acesse no navegador: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
