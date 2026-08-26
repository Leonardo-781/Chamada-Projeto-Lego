import os
import csv
import io
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, flash
from models import db, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo
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

db.init_app(app)

# Inicializa banco de dados com dados iniciais
init_db(app)


# ==========================================
# ROTAS DE PÁGINAS (TEMPLATES)
# ==========================================

@app.route('/')
def index():
    turmas = Turma.query.all()
    total_alunos = Aluno.query.filter_by(ativo=True).count()
    total_chamadas = SessaoChamada.query.count()
    total_anotacoes = DiarioBordo.query.count()
    
    # Chamadas de hoje
    hoje = date.today()
    chamadas_hoje = SessaoChamada.query.filter_by(data=hoje).all()
    turmas_feitas_hoje = {c.turma_id for c in chamadas_hoje}
    
    # Top 5 alunos em destaque (Ranking Geral)
    top_alunos = Aluno.query.filter_by(ativo=True).order_by(Aluno.pontos_xp.desc()).limit(5).all()
    
    # Últimas anotações do diário de bordo
    ultimas_anotacoes = DiarioBordo.query.order_by(DiarioBordo.data.desc(), DiarioBordo.id.desc()).limit(3).all()
    
    return render_template('index.html', 
                           turmas=turmas, 
                           total_alunos=total_alunos,
                           total_chamadas=total_chamadas,
                           total_anotacoes=total_anotacoes,
                           turmas_feitas_hoje=turmas_feitas_hoje,
                           top_alunos=top_alunos,
                           ultimas_anotacoes=ultimas_anotacoes,
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
    
    # Anotações gerais de chamadas passadas
    query_sessoes = SessaoChamada.query
    if turma_filtro:
        query_sessoes = query_sessoes.filter_by(turma_id=turma_filtro)
    sessoes_com_notas = [s for s in query_sessoes.order_by(SessaoChamada.data.desc()).all() if s.observacoes or s.proxima_aula]

    return render_template('notes.html', 
                           turmas=turmas, 
                           diarios=diarios, 
                           sessoes_com_notas=sessoes_com_notas,
                           turma_filtro=turma_filtro,
                           categoria_filtro=categoria_filtro)


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
    
    # Estatísticas de equipes
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
# ROTAS DA API REST (JSON)
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

            # Verifica conquista automática: "Frequência de Ouro" (5 ou mais presenças)
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


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SISTEMA DE CHAMADA & GAMIFICACAO LEGO INICIADO COM SUCESSO!")
    print("Acesse no navegador: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
