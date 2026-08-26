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

    print("Inicializando banco de dados com Alfa COC e Melo Viana...")

    # 1. Criação das 3 Turmas Oficiais
    turma_1 = Turma(
        nome="Alfa COC - Equipe 01",
        codigo="ALFA-01",
        descricao="Robótica Lego - Alfa COC (Equipe 1)",
        horario="Horário da Oficina",
        cor_tema="#E3000B",
        icone="robot",
        anotacoes="📌 **Alfa COC - Equipe 01**\nMontagem & Programação: Bianca, Maria Emília, Kaique, Pedro Miguel."
    )

    turma_2 = Turma(
        nome="Alfa COC - Equipe 02",
        codigo="ALFA-02",
        descricao="Robótica Lego - Alfa COC (Equipe 2)",
        horario="Horário da Oficina",
        cor_tema="#0055BF",
        icone="cube",
        anotacoes="📌 **Alfa COC - Equipe 02**\nMontagem & Programação: Maria Cecília, Laura, Luísa, João Arthur."
    )

    turma_3 = Turma(
        nome="Melo Viana - Robótica Lego",
        codigo="MELO-VIANA",
        descricao="Oficina de Robótica e Montagem Lego - Melo Viana",
        horario="Horário da Oficina",
        cor_tema="#00852B",
        icone="rocket",
        anotacoes="📌 **Melo Viana**\nEquipe de Robótica Lego do Melo Viana."
    )

    db.session.add_all([turma_1, turma_2, turma_3])
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

    # 3. Alunos da Turma 1 (Alfa COC - Equipe 01)
    alunos_t1 = [
        Aluno(nome="MARIA EDUARDA ROCHA CAMPOS SILVA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-red", pontos_xp=0),
        Aluno(nome="ANA CAROLINA ZAMPIROLI FERREIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-yellow", pontos_xp=0),
        Aluno(nome="BIANCA OLIVEIRA ALBERTON", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0),
        Aluno(nome="ESTER ROSA DE MELO", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-purple", pontos_xp=0),
        Aluno(nome="KAIQUE G. PEREIRA PRIMO", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-ninja", pontos_xp=0),
        Aluno(nome="LARISSA SANTOS VIEIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-green", pontos_xp=0),
        Aluno(nome="MARIA ANTÔNIA NAVES COSTA PEREIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-orange", pontos_xp=0),
        Aluno(nome="MARIA EMÍLIA MUNDIM PENA", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=0),
        Aluno(nome="PEDRO MIGUEL DE ALCANTARA LIMA DIAS", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0),
    ]

    # 4. Alunos da Turma 2 (Alfa COC - Equipe 02)
    alunos_t2 = [
        Aluno(nome="JULIA KINACH RODRIGUES VIEIRA", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=0),
        Aluno(nome="JOÃO ARTHUR CAIXETA F. SILVA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=0),
        Aluno(nome="JOÃO MATHEUS CAIXETA F. SILVA", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-ninja", pontos_xp=0),
        Aluno(nome="LAURA MACHADO SOUSA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-purple", pontos_xp=0),
        Aluno(nome="LUÍSA SOARES DE OLIVEIRA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-green", pontos_xp=0),
        Aluno(nome="MANUELA DE SOUSA F. DUMONT", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-orange", pontos_xp=0),
        Aluno(nome="MARIA LUIZA SANTOS", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-red", pontos_xp=0),
        Aluno(nome="MARIA TEREZA FERNANDES CAETANO", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=0),
        Aluno(nome="MARIA CECÍLIA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0),
    ]

    db.session.add_all(alunos_t1 + alunos_t2)
    db.session.commit()

    # 5. Conquistas
    med_primeiro = Medalha.query.filter_by(codigo="primeiro_bloco").first()
    med_robo = Medalha.query.filter_by(codigo="primeiro_robo").first()

    for a in (alunos_t1 + alunos_t2):
        if med_primeiro:
            db.session.add(ConquistaAluno(aluno_id=a.id, medalha_id=med_primeiro.id))
        if "Montagem" in a.equipe and med_robo:
            db.session.add(ConquistaAluno(aluno_id=a.id, medalha_id=med_robo.id))

    # 6. Diário de Bordo
    hoje = date.today()
    diario = DiarioBordo(
        turma_id=turma_1.id,
        data=hoje,
        titulo="Início das Atividades Lego - Alfa COC & Melo Viana",
        conteudo="Configuração das 3 turmas:\n"
                 "- Alfa COC - Equipe 01 (9 alunos)\n"
                 "- Alfa COC - Equipe 02 (9 alunos)\n"
                 "- Melo Viana (Pronta para cadastro dos alunos)",
        categoria="Desafio Lego"
    )
    db.session.add(diario)
    db.session.commit()

    print("Banco de dados com Alfa COC e Melo Viana configurado!")
