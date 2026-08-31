import os
import sqlite3
from datetime import date, timedelta
from sqlalchemy import text
from models import db, Usuario, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo, Atividade, EntregaAtividade, SlideAula, DuvidaAluno

def init_db(app):
    with app.app_context():
        db.create_all()
        migrar_colunas(app)
        seed_usuarios()
        seed_database()
        seed_atividades_e_materiais()

def migrar_colunas(app):
    try:
        driver = getattr(db.engine.url, 'drivername', '')
        if 'sqlite' in driver:
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

                res_alunos = conn.execute(text("PRAGMA table_info(alunos)")).fetchall()
                colunas_alunos = [r[1] for r in res_alunos]
                if 'pin_acesso' not in colunas_alunos:
                    conn.execute(text("ALTER TABLE alunos ADD COLUMN pin_acesso TEXT DEFAULT '1234'"))
                    conn.commit()
        else:
            # PostgreSQL / Supabase
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE turmas ADD COLUMN IF NOT EXISTS anotacoes TEXT DEFAULT ''"))
                conn.execute(text("ALTER TABLE sessoes_chamada ADD COLUMN IF NOT EXISTS proxima_aula TEXT DEFAULT ''"))
                conn.execute(text("ALTER TABLE alunos ADD COLUMN IF NOT EXISTS pin_acesso VARCHAR(10) DEFAULT '1234'"))
                conn.commit()
    except Exception as e:
        print(f"Aviso de migracao: {e}")

def seed_usuarios():
    # Verifica se já existem usuários cadastrados
    if Usuario.query.first():
        return

    print("Cadastrando contas institucionais (Responsáveis e Professores)...")

    # 1. Responsável pelas Aulas (Admin Master - UFU / FACOM / LINA / MONTE BOT)
    admin = Usuario(
        nome="Coordenação Monte Bot / UFU",
        email="admin@montebot.ufu.br",
        perfil="admin_responsavel",
        escola="UFU / LINA / Monte Bot"
    )
    admin.set_senha("Admin@MonteBot2026")

    # 2. Professor Colégio Alfa COC (Apenas Acompanhamento)
    prof_alfa = Usuario(
        nome="Professor(a) Colégio Alfa COC",
        email="professor@alfacoc.com.br",
        perfil="professor_escola",
        escola="Colégio Alfa COC"
    )
    prof_alfa.set_senha("Professor@Alfa2026")

    # 3. Professor Melo Viana (Apenas Acompanhamento)
    prof_melo = Usuario(
        nome="Professor(a) Melo Viana",
        email="professor@meloviana.com.br",
        perfil="professor_escola",
        escola="Melo Viana"
    )
    prof_melo.set_senha("Professor@Melo2026")

    db.session.add_all([admin, prof_alfa, prof_melo])
    db.session.commit()
    print("Contas institucionais criadas com sucesso!")

def seed_database():
    if Turma.query.first():
        return

    print("Inicializando turmas e alunos oficiais...")

    # 1. As 3 Turmas Oficiais do Projeto
    turma_1 = Turma(
        nome="Alfa COC - Equipe 01",
        codigo="ALFA-01",
        descricao="Oficina de Robótica e Mecanismos - Colégio Alfa COC (Equipe 01)",
        horario="Segundas e Quartas, 14:00 - 15:30",
        cor_tema="#0284C7",
        icone="robot",
        anotacoes="📌 **Projeto Monte Bot / LINA / UFU**\nEquipe 01 do Colégio Alfa COC.\n🔧 Montagem & Programação: Bianca, Maria Emília, Kaique, Pedro Miguel."
    )

    turma_2 = Turma(
        nome="Alfa COC - Equipe 02",
        codigo="ALFA-02",
        descricao="Oficina de Robótica e Mecanismos - Colégio Alfa COC (Equipe 02)",
        horario="Terças e Quintas, 14:00 - 15:30",
        cor_tema="#2563EB",
        icone="cpu",
        anotacoes="📌 **Projeto Monte Bot / LINA / UFU**\nEquipe 02 do Colégio Alfa COC.\n🔧 Montagem & Programação: Maria Cecília, Laura, Luísa, João Arthur."
    )

    turma_3 = Turma(
        nome="Melo Viana - Robótica Lego",
        codigo="MELO-VIANA",
        descricao="Laboratório de Robótica Educacional - Escola Melo Viana",
        horario="Sextas-feiras, 14:00 - 17:00",
        cor_tema="#059669",
        icone="rocket",
        anotacoes="📌 **Projeto Monte Bot / LINA / UFU**\nEquipe do Melo Viana."
    )

    db.session.add_all([turma_1, turma_2, turma_3])
    db.session.commit()

    # 2. Medalhas Institucionais
    medalhas = [
        Medalha(
            codigo="primeiro_bloco",
            nome="Primeiro Mecanismo",
            descricao="Concluiu a montagem do primeiro protótipo com sucesso.",
            icone="🧱",
            cor="#0284C7",
            xp_bonus=15,
            tipo="presenca"
        ),
        Medalha(
            codigo="trabalho_equipe",
            nome="Espírito de Equipe & Liderança",
            descricao="Demonstrou colaboração técnica exemplar na bancada de testes.",
            icone="🤝",
            cor="#F59E0B",
            xp_bonus=25,
            tipo="especial"
        ),
        Medalha(
            codigo="mestre_organizacao",
            nome="Organização de Bancada",
            descricao="Manteve os kits de peças, sensores e motores impecavelmente organizados.",
            icone="📦",
            cor="#059669",
            xp_bonus=20,
            tipo="especial"
        ),
        Medalha(
            codigo="primeiro_robo",
            nome="Engenharia de Automação",
            descricao="Programou com precisão sensores e motores angulares em circuito autônomo.",
            icone="🤖",
            cor="#2563EB",
            xp_bonus=30,
            tipo="especial"
        ),
        Medalha(
            codigo="super_frequencia",
            nome="Assiduidade Exemplar",
            descricao="Alcançou sequência de presenças sem faltas no ciclo de oficinas.",
            icone="⭐",
            cor="#D97706",
            xp_bonus=40,
            tipo="presenca"
        ),
        Medalha(
            codigo="mestre_supremo",
            nome="Mestre em Robótica & IA",
            descricao="Excelência em resolução de problemas de engenharia e montagem.",
            icone="👑",
            cor="#7C3AED",
            xp_bonus=50,
            tipo="especial"
        )
    ]
    db.session.add_all(medalhas)
    db.session.commit()

    # 3. Alunos da Turma 1 (Alfa COC - Equipe 01)
    alunos_t1 = [
        Aluno(nome="MARIA EDUARDA ROCHA CAMPOS SILVA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-blue", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="ANA CAROLINA ZAMPIROLI FERREIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-yellow", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="BIANCA OLIVEIRA ALBERTON", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="ESTER ROSA DE MELO", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-purple", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="KAIQUE G. PEREIRA PRIMO", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-ninja", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="LARISSA SANTOS VIEIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-green", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MARIA ANTÔNIA NAVES COSTA PEREIRA", turma_id=turma_1.id, equipe="Equipe 01", avatar_tipo="lego-orange", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MARIA EMÍLIA MUNDIM PENA", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="PEDRO MIGUEL DE ALCANTARA LIMA DIAS", turma_id=turma_1.id, equipe="Equipe 01 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0, pin_acesso="1234"),
    ]

    # 4. Alunos da Turma 2 (Alfa COC - Equipe 02)
    alunos_t2 = [
        Aluno(nome="JULIA KINACH RODRIGUES VIEIRA", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="JOÃO ARTHUR CAIXETA F. SILVA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-astronaut", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="JOÃO MATHEUS CAIXETA F. SILVA", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-ninja", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="LAURA MACHADO SOUSA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-purple", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="LUÍSA SOARES DE OLIVEIRA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-green", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MANUELA DE SOUSA F. DUMONT", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-orange", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MARIA LUIZA SANTOS", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-blue", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MARIA TEREZA FERNANDES CAETANO", turma_id=turma_2.id, equipe="Equipe 02", avatar_tipo="lego-yellow", pontos_xp=0, pin_acesso="1234"),
        Aluno(nome="MARIA CECÍLIA", turma_id=turma_2.id, equipe="Equipe 02 (Montagem & Prog.)", avatar_tipo="lego-blue", pontos_xp=0, pin_acesso="1234"),
    ]

    db.session.add_all(alunos_t1 + alunos_t2)
    db.session.commit()

    # 5. Diário de Bordo Inicial
    hoje = date.today()
    diario = DiarioBordo(
        turma_id=turma_1.id,
        data=hoje,
        titulo="Início do Ciclo de Oficinas STEM - UFU / LINA / Monte Bot",
        conteudo="Estruturação das turmas e bancadas de robótica:\n"
                 "- Alfa COC - Equipe 01: Foco em tração e sensores de luminosidade.\n"
                 "- Alfa COC - Equipe 02: Foco em garras motorizadas e controle giroscópico.\n"
                 "- Melo Viana: Laboratório aberto para novos cadastros.",
        categoria="Anotação Pedagógica",
        autor="Coordenação UFU / LINA"
    )
    db.session.add(diario)
    db.session.commit()

    print("Banco de dados institucional inicializado!")


def seed_atividades_e_materiais():
    if Atividade.query.first():
        return

    print("Inicializando Desafios e Slides Institucionais...")
    hoje = date.today()

    atividades = [
        Atividade(
            turma_id=None,
            titulo="Desafio 01: Seguidor de Linha em Alta Precisão",
            descricao="Projetar e calibrar a base motriz com dois motores angulares e sensor de cor/reflexão para percorrer o circuito sem desvios.",
            kit_lego="Lego SPIKE Prime",
            xp_recompensa=50,
            data_limite=hoje + timedelta(days=14),
            link_material="https://education.lego.com/pt-br/lessons",
            status="ativo"
        ),
        Atividade(
            turma_id=None,
            titulo="Desafio 02: Garra Mecânica Articulada com Redução",
            descricao="Desenvolver mecanismo de garra utilizando trem de engrenagens 8T e 24T para transporte seguro de módulos.",
            kit_lego="Lego SPIKE Prime",
            xp_recompensa=60,
            data_limite=hoje + timedelta(days=21),
            link_material="https://education.lego.com/pt-br/lessons",
            status="ativo"
        ),
        Atividade(
            turma_id=None,
            titulo="Desafio 03: Veículo com Frenagem de Emergência por Ultrassom",
            descricao="Construção de robô autônomo com sensor de distância ultrassônico capaz de desacelerar suavemente a 15 cm do obstáculo.",
            kit_lego="Lego SPIKE Prime",
            xp_recompensa=70,
            data_limite=hoje + timedelta(days=28),
            link_material="https://education.lego.com/pt-br/lessons",
            status="ativo"
        )
    ]
    db.session.add_all(atividades)
    db.session.commit()

    slides = [
        SlideAula(
            turma_id=None,
            titulo="Aula 01: Arquitetura de Hardware e Hub SPIKE Prime",
            descricao="Componentes de controle, portas digitais, giroscópio de 6 eixos e comunicação via Bluetooth.",
            numero_aula=1,
            link_slide="https://docs.google.com/presentation",
            tipo="slides"
        ),
        SlideAula(
            turma_id=None,
            titulo="Aula 02: Física Aplicada a Mecanismos e Engrenagens",
            descricao="Torque, velocidade angular, relações de transmissão e sustentação de eixos paralelos.",
            numero_aula=2,
            link_slide="https://education.lego.com",
            tipo="manual_montagem"
        ),
        SlideAula(
            turma_id=None,
            titulo="Aula 03: Lógica Algorítmica e Estruturas de Decisão",
            descricao="Programação por blocos e Python: estruturas condicionais e leitura de telemetria em tempo real.",
            numero_aula=3,
            link_slide="https://education.lego.com",
            tipo="apostila"
        )
    ]
    db.session.add_all(slides)
    db.session.commit()
    print("Desafios e Slides cadastrados com sucesso!")
