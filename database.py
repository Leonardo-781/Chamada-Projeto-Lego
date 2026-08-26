import os
import sqlite3
from datetime import date, timedelta
from sqlalchemy import text
from models import db, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo

def init_db(app):
    with app.app_context():
        # Cria tabelas se não existirem
        db.create_all()
        
        # Migração automática de colunas para bancos existentes
        migrar_colunas(app)
        
        seed_database()

def migrar_colunas(app):
    try:
        if 'sqlite' in db.engine.url.drivername:
            with db.engine.connect() as conn:
                # turmas.anotacoes
                res = conn.execute(text("PRAGMA table_info(turmas)")).fetchall()
                colunas_turmas = [r[1] for r in res]
                if 'anotacoes' not in colunas_turmas:
                    conn.execute(text("ALTER TABLE turmas ADD COLUMN anotacoes TEXT DEFAULT ''"))
                    conn.commit()

                # sessoes_chamada.proxima_aula
                res_sess = conn.execute(text("PRAGMA table_info(sessoes_chamada)")).fetchall()
                colunas_sess = [r[1] for r in res_sess]
                if 'proxima_aula' not in colunas_sess:
                    conn.execute(text("ALTER TABLE sessoes_chamada ADD COLUMN proxima_aula TEXT DEFAULT ''"))
                    conn.commit()
    except Exception as e:
        print(f"Aviso de migracao: {e}")

def seed_database():
    # Verifica se já existem turmas
    if Turma.query.first():
        return

    print("Inicializando banco de dados com as 3 turmas, anotações e dados iniciais Lego...")

    # 1. Criação das 3 Turmas com Anotações Pedagógicas
    turma_a = Turma(
        nome="Turma A - Construtores Júnior",
        codigo="TURMA-A",
        descricao="Iniciação ao mundo Lego, estruturas básicas, engrenagens e criatividade.",
        horario="Segundas e Quartas, 14:00 - 15:30",
        cor_tema="#E3000B",  # Vermelho Lego
        icone="cube",
        anotacoes="📌 **Kits em Uso:** Lego Education BricQ Motion Essential (Kits 01 a 06).\n🎯 **Foco Pedagógico:** Coordenação motora, estruturas estáveis e noções de força/atrito.\n📦 **Organização:** Todas as equipes devem guardar as peças nas bandejas coloridas 5 min antes do término."
    )

    turma_b = Turma(
        nome="Turma B - Robótica & Mecanismos",
        codigo="TURMA-B",
        descricao="Mecanismos avançados, motores, sensores e lógica de automação.",
        horario="Terças e Quintas, 14:00 - 15:30",
        cor_tema="#0055BF",  # Azul Lego
        icone="robot",
        anotacoes="📌 **Kits em Uso:** Lego SPIKE Prime (Kits 07 a 12).\n🎯 **Foco Pedagógico:** Programação em blocos, calibração de sensores ultrassônicos e motores angulares.\n🚀 **Projeto Atual:** Veículos autônomos para desvio de obstáculos."
    )

    turma_c = Turma(
        nome="Turma C - Mestres Construtores",
        codigo="TURMA-C",
        descricao="Projetos complexos, desafios FLL/robótica e desafios em equipe.",
        horario="Sextas-feiras, 14:00 - 17:00",
        cor_tema="#00852B",  # Verde Lego
        icone="rocket",
        anotacoes="📌 **Kits em Uso:** Lego SPIKE Prime Avançado & Mindstorms.\n🎯 **Foco Pedagógico:** Estratégia de missões, garras pneumáticas/motorizadas e sensores giroscópicos.\n🏆 **Meta:** Desafio da Arena de Robótica no final do ciclo."
    )

    db.session.add_all([turma_a, turma_b, turma_c])
    db.session.commit()

    # 2. Criação das Medalhas / Conquistas Lego
    medalhas = [
        Medalha(
            codigo="primeiro_bloco",
            nome="Primeiro Bloco",
            descricao="Participou da primeira aula do projeto Lego com sucesso.",
            icone="🧱",
            cor="#E3000B",
            xp_bonus=15,
            tipo="presenca"
        ),
        Medalha(
            codigo="trabalho_equipe",
            nome="Espírito de Equipe",
            descricao="Demonstrou colaboração exemplar e apoio aos colegas de montagem.",
            icone="🤝",
            cor="#FFD700",
            xp_bonus=25,
            tipo="especial"
        ),
        Medalha(
            codigo="mestre_organizacao",
            nome="Mestre da Organização",
            descricao="Guardou e organizou todas as peças na caixa organizadora perfeitamente.",
            icone="📦",
            cor="#00852B",
            xp_bonus=20,
            tipo="especial"
        ),
        Medalha(
            codigo="primeiro_robo",
            nome="Criador de Robôs",
            descricao="Montou e programou seu primeiro mecanismo motorizado funcional.",
            icone="🤖",
            cor="#0055BF",
            xp_bonus=30,
            tipo="especial"
        ),
        Medalha(
            codigo="super_frequencia",
            nome="Frequência de Ouro",
            descricao="Alcançou sequência exemplar de presenças sem faltas.",
            icone="⭐",
            cor="#FF8800",
            xp_bonus=40,
            tipo="presenca"
        ),
        Medalha(
            codigo="mestre_supremo",
            nome="Mestre Construtor Lendário",
            descricao="Alcançou o nível máximo de dedicação e liderança no projeto.",
            icone="👑",
            cor="#9C27B0",
            xp_bonus=50,
            tipo="especial"
        )
    ]
    db.session.add_all(medalhas)
    db.session.commit()

    # 3. Alunos da Turma A
    alunos_a = [
        Aluno(nome="Lucas Silveira", turma_id=turma_a.id, equipe="Equipe Vermelha", avatar_tipo="lego-red", pontos_xp=80),
        Aluno(nome="Sofia Mendes", turma_id=turma_a.id, equipe="Equipe Amarela", avatar_tipo="lego-yellow", pontos_xp=95),
        Aluno(nome="Gabriel Costa", turma_id=turma_a.id, equipe="Equipe Vermelha", avatar_tipo="lego-blue", pontos_xp=60),
        Aluno(nome="Isabela Rocha", turma_id=turma_a.id, equipe="Equipe Amarela", avatar_tipo="lego-purple", pontos_xp=110),
        Aluno(nome="Enzo Henrique", turma_id=turma_a.id, equipe="Equipe Vermelha", avatar_tipo="lego-orange", pontos_xp=40),
        Aluno(nome="Mariana Lima", turma_id=turma_a.id, equipe="Equipe Amarela", avatar_tipo="lego-green", pontos_xp=75),
    ]

    # 4. Alunos da Turma B
    alunos_b = [
        Aluno(nome="Matheus Oliveira", turma_id=turma_b.id, equipe="RoboTech", avatar_tipo="lego-blue", pontos_xp=180),
        Aluno(nome="Beatriz Santos", turma_id=turma_b.id, equipe="CyberBlocks", avatar_tipo="lego-purple", pontos_xp=210),
        Aluno(nome="Pedro Alcantara", turma_id=turma_b.id, equipe="RoboTech", avatar_tipo="lego-ninja", pontos_xp=150),
        Aluno(nome="Helena Castro", turma_id=turma_b.id, equipe="CyberBlocks", avatar_tipo="lego-astronaut", pontos_xp=240),
        Aluno(nome="Rafael Martins", turma_id=turma_b.id, equipe="RoboTech", avatar_tipo="lego-yellow", pontos_xp=130),
        Aluno(nome="Camila Duarte", turma_id=turma_b.id, equipe="CyberBlocks", avatar_tipo="lego-red", pontos_xp=170),
    ]

    # 5. Alunos da Turma C
    alunos_c = [
        Aluno(nome="Arthur Ferreira", turma_id=turma_c.id, equipe="Mestres Alfa", avatar_tipo="lego-astronaut", pontos_xp=380),
        Aluno(nome="Larissa Neves", turma_id=turma_c.id, equipe="Mestres Beta", avatar_tipo="lego-ninja", pontos_xp=420),
        Aluno(nome="Thiago Barbosa", turma_id=turma_c.id, equipe="Mestres Alfa", avatar_tipo="lego-red", pontos_xp=320),
        Aluno(nome="Juliana Nogueira", turma_id=turma_c.id, equipe="Mestres Beta", avatar_tipo="lego-green", pontos_xp=360),
        Aluno(nome="Bernardo Ramos", turma_id=turma_c.id, equipe="Mestres Alfa", avatar_tipo="lego-orange", pontos_xp=290),
        Aluno(nome="Alice Monteiro", turma_id=turma_c.id, equipe="Mestres Beta", avatar_tipo="lego-purple", pontos_xp=510),
    ]

    todos_alunos = alunos_a + alunos_b + alunos_c
    db.session.add_all(todos_alunos)
    db.session.commit()

    # 6. Atribui algumas medalhas de exemplo
    med_primeiro_bloco = Medalha.query.filter_by(codigo="primeiro_bloco").first()
    med_trabalho_equipe = Medalha.query.filter_by(codigo="trabalho_equipe").first()
    med_robo = Medalha.query.filter_by(codigo="primeiro_robo").first()
    med_mestre = Medalha.query.filter_by(codigo="mestre_supremo").first()

    for a in todos_alunos:
        db.session.add(ConquistaAluno(aluno_id=a.id, medalha_id=med_primeiro_bloco.id, data_conquista=a.created_at))

    if med_trabalho_equipe:
        db.session.add(ConquistaAluno(aluno_id=alunos_a[1].id, medalha_id=med_trabalho_equipe.id))
        db.session.add(ConquistaAluno(aluno_id=alunos_b[3].id, medalha_id=med_trabalho_equipe.id))
    
    if med_robo:
        db.session.add(ConquistaAluno(aluno_id=alunos_b[0].id, medalha_id=med_robo.id))
        db.session.add(ConquistaAluno(aluno_id=alunos_c[0].id, medalha_id=med_robo.id))
        db.session.add(ConquistaAluno(aluno_id=alunos_c[1].id, medalha_id=med_robo.id))

    if med_mestre:
        db.session.add(ConquistaAluno(aluno_id=alunos_c[5].id, medalha_id=med_mestre.id))

    # 7. Criar sessões de chamadas anteriores com Anotações Pedagógicas
    hoje = date.today()
    
    sessao_a = SessaoChamada(
        turma_id=turma_a.id,
        data=hoje - timedelta(days=2),
        topico="Introdução a Alavancas e Roldanas Lego",
        observacoes="Primeira oficina prática de montagem básica. As equipes compreenderam bem a vantagem mecânica.",
        proxima_aula="Montagem da catapulta Lego e medição de alcance com régua métrica."
    )
    db.session.add(sessao_a)
    db.session.commit()

    for idx, aluno in enumerate(alunos_a):
        status = 'presente' if idx != 4 else 'falta'
        db.session.add(RegistroPresenca(
            sessao_id=sessao_a.id,
            aluno_id=aluno.id,
            status=status,
            pontos_ganhos=10 if status == 'presente' else 0,
            pontos_bonus=5 if idx == 1 else 0,
            motivo_bonus="Destaque de cooperação na mesa de peças" if idx == 1 else ""
        ))

    sessao_b = SessaoChamada(
        turma_id=turma_b.id,
        data=hoje - timedelta(days=1),
        topico="Montagem de Chassi Motorizado com Sensor Ultrassônico",
        observacoes="Construção dos carros autônomos. Equipe CyberBlocks precisou de apoio no loop de distância (< 15cm).",
        proxima_aula="Programar rota com giros de 90° e sinalizador sonoro com buzzer."
    )
    db.session.add(sessao_b)
    db.session.commit()

    for idx, aluno in enumerate(alunos_b):
        status = 'presente' if idx != 2 else 'justificada'
        db.session.add(RegistroPresenca(
            sessao_id=sessao_b.id,
            aluno_id=aluno.id,
            status=status,
            justificativa="Atestado médico informado pelos pais" if status == 'justificada' else "",
            pontos_ganhos=10 if status == 'presente' else 0,
            pontos_bonus=5 if idx == 3 else 0,
            motivo_bonus="Ajudou outra equipe a calibrar sensores" if idx == 3 else ""
        ))

    # 8. Diário de Bordo e Anotações Avulsas
    diarios = [
        DiarioBordo(
            turma_id=turma_a.id,
            data=hoje - timedelta(days=2),
            titulo="Avaliação do Kit BricQ Motion",
            conteudo="Os alunos demonstraram facilidade na montagem dos carrinhos de propulsão a elástico. Manter foco em segurança com elásticos.",
            categoria="Anotação Pedagógica"
        ),
        DiarioBordo(
            turma_id=turma_b.id,
            data=hoje - timedelta(days=1),
            titulo="Bateria dos Hubs Spike Prime",
            conteudo="Lembrar de colocar os Hubs 3 e 4 para carregar antes da aula de quinta-feira.",
            categoria="Recado / Material"
        ),
        DiarioBordo(
            turma_id=turma_c.id,
            data=hoje,
            titulo="Planejamento do Desafio de Robótica",
            conteudo="Equipes Alfa e Beta já definiram as estratégias de resgate de blocos com sensores giroscópicos. Projeto em excelente andamento.",
            categoria="Desafio Lego"
        )
    ]
    db.session.add_all(diarios)
    db.session.commit()

    print("Banco de dados Lego com anotações populado com sucesso!")
