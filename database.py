import os
import sqlite3
from datetime import date, timedelta
from sqlalchemy import text
from models import db, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo

def init_db(app):
    with app.app_context():
        db.create_all()
        migrar_colunas(app)
        seed_database()

def migrar_colunas(app):
    try:
        if 'sqlite' in db.engine.url.drivername:
            with db.engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(turmas)")).fetchall()
                colunas_turmas = [r[1] for r in res]
                if 'anotacoes' not in colunas_turmas:
                    conn.execute(text("ALTER TABLE turmas ADD COLUMN anotacoes TEXT DEFAULT ''"))
                    conn.commit()

                res_sess = conn.execute(text("PRAGMA table_info(sessoes_chamada)")).fetchall()
                colunas_sess = [r[1] for r in res_sess]
                if 'proxima_aula' not in colunas_sess:
                    conn.execute(text("ALTER TABLE sessoes_chamada ADD COLUMN proxima_aula TEXT DEFAULT ''"))
                    conn.commit()
    except Exception as e:
        print(f"Aviso de migracao: {e}")

def seed_database():
    if Turma.query.first():
        return

    print("Inicializando banco de dados com os alunos do Colégio Alfa COC...")

    # 1. Criação das 3 Turmas
    turma_a = Turma(
        nome="Colégio Alfa COC - Turma 1",
        codigo="ALFA-01",
        descricao="Oficina de Robótica e Montagem Lego - Colégio Alfa COC",
        horario="Segundas e Quartas, 14:00 - 15:30",
        cor_tema="#E3000B",
        icone="robot",
        anotacoes="📌 **Colégio Alfa COC**\nEquipe 1: 9 alunos\nEquipe 2: 9 alunos\n🔧 Montagem & Programação definidos para os desafios."
    )

    turma_b = Turma(
        nome="Colégio Alfa COC - Turma 2",
        codigo="ALFA-02",
        descricao="Mecanismos avançados, motores, sensores e lógica de automação.",
        horario="Terças e Quintas, 14:00 - 15:30",
        cor_tema="#0055BF",
        icone="cube",
        anotacoes="📌 **Colégio Alfa COC** - Turma 2"
    )

    turma_c = Turma(
        nome="Colégio Alfa COC - Turma 3",
        codigo="ALFA-03",
        descricao="Projetos complexos, desafios FLL/robótica e desafios em equipe.",
        horario="Sextas-feiras, 14:00 - 17:00",
        cor_tema="#00852B",
        icone="rocket",
        anotacoes="📌 **Colégio Alfa COC** - Turma 3"
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

    # 3. Alunos do Colégio Alfa COC (Equipe 1 e Equipe 2)
    alunos_turma_1 = [
        # Equipe 01
        Aluno(nome="Maria Eduarda Rocha Campos Silva", turma_id=turma_a.id, equipe="Equipe 01", avatar_tipo="lego-red", pontos_xp=40),
        Aluno(nome="Ana Carolina Zampiroli Ferreira", turma_id=turma_a.id, equipe="Equipe 01", avatar_tipo="lego-yellow", pontos_xp=40),
        Aluno(nome="Bianca Oliveira Alberton", turma_id=turma_a.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=60),
        Aluno(nome="Ester Rosa de Melo", turma_id=turma_a.id, equipe="Equipe 01", avatar_tipo="lego-purple", pontos_xp=40),
        Aluno(nome="Kaique G. Pereira Primo", turma_id=turma_a.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-ninja", pontos_xp=60),
        Aluno(nome="Larissa Santos Vieira", turma_id=turma_a.id, equipe="Equipe 01", avatar_tipo="lego-green", pontos_xp=40),
        Aluno(nome="Maria Antônia Naves Costa Pereira", turma_id=turma_a.id, equipe="Equipe 01", avatar_tipo="lego-orange", pontos_xp=40),
        Aluno(nome="Maria Emília Mundim Pena", turma_id=turma_a.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=60),
        Aluno(nome="Pedro Miguel de Alcantara Lima Dias", turma_id=turma_a.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=60),
        
        # Equipe 02
        Aluno(nome="Julia Kinach Rodrigues Vieira", turma_id=turma_a.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=40),
        Aluno(nome="João Arthur Caixeta F. Silva", turma_id=turma_a.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=60),
        Aluno(nome="João Matheus Caixeta F. Silva", turma_id=turma_a.id, equipe="Equipe 02", avatar_tipo="lego-ninja", pontos_xp=40),
        Aluno(nome="Laura Machado Sousa", turma_id=turma_a.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-purple", pontos_xp=60),
        Aluno(nome="Luísa Soares de Oliveira", turma_id=turma_a.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-green", pontos_xp=60),
        Aluno(nome="Manuela de Sousa F. Dumont", turma_id=turma_a.id, equipe="Equipe 02", avatar_tipo="lego-orange", pontos_xp=40),
        Aluno(nome="Maria Luiza Santos", turma_id=turma_a.id, equipe="Equipe 02", avatar_tipo="lego-red", pontos_xp=40),
        Aluno(nome="Maria Tereza Fernandes Caetano", turma_id=turma_a.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=40),
        Aluno(nome="Maria Cecília", turma_id=turma_a.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=60),
    ]

    db.session.add_all(alunos_turma_1)
    db.session.commit()

    # 4. Medalhas iniciais
    med_primeiro_bloco = Medalha.query.filter_by(codigo="primeiro_bloco").first()
    med_robo = Medalha.query.filter_by(codigo="primeiro_robo").first()

    for a in alunos_turma_1:
        if med_primeiro_bloco:
            db.session.add(ConquistaAluno(aluno_id=a.id, medalha_id=med_primeiro_bloco.id, data_conquista=a.created_at))
        if "Montagem" in a.equipe and med_robo:
            db.session.add(ConquistaAluno(aluno_id=a.id, medalha_id=med_robo.id))

    # 5. Diário de Bordo Inicial
    hoje = date.today()
    diario = DiarioBordo(
        turma_id=turma_a.id,
        data=hoje,
        titulo="Divisão das Equipes de Robótica - Colégio Alfa COC",
        conteudo="Equipes oficiais formadas:\n\n"
                 "🧱 **Equipe 01** (9 alunos):\n"
                 "- Montagem e Programação: Bianca, Maria Emília, Kaique, Pedro Miguel.\n"
                 "- Estrutura e Organização: Maria Eduarda, Ana Carolina, Ester, Larissa, Maria Antônia.\n\n"
                 "⚙️ **Equipe 02** (9 alunos):\n"
                 "- Montagem e Programação: Maria Cecília, Laura, Luísa, João Arthur.\n"
                 "- Estrutura e Organização: Julia, João Matheus, Manuela, Maria Luiza, Maria Tereza.",
        categoria="Desafio Lego"
    )
    db.session.add(diario)
    db.session.commit()

    print("Banco de dados com alunos do Colégio Alfa COC configurado!")
