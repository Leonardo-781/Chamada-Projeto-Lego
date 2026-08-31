import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from app import app, db
from models import Turma, Aluno, Medalha, Atividade, SlideAula, DuvidaAluno

key_file = 'sistema-lego-firebase-adminsdk-fbsvc-756ef080a3.json'

if not os.path.exists(key_file):
    print(f"Erro: Arquivo de chave {key_file} nao encontrado!")
    exit(1)

print(f"Iniciando conexao com o Firebase Firestore usando {key_file}...")

cred = credentials.Certificate(key_file)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db_fire = firestore.client()
print("Conectado ao Cloud Firestore com sucesso!")

with app.app_context():
    turmas = Turma.query.all()
    alunos = Aluno.query.all()
    medalhas = Medalha.query.all()
    atividades = Atividade.query.all()
    slides = SlideAula.query.all()
    duvidas = DuvidaAluno.query.all()

    print(f"\nSincronizando {len(turmas)} Turmas com o Firestore...")
    for t in turmas:
        doc = db_fire.collection('turmas').document(str(t.id))
        doc.set(t.to_dict())
        print(f"  [Turma OK] #{t.id} {t.nome}")

    print(f"\nSincronizando {len(alunos)} Alunos do Colegio Alfa COC com o Firestore...")
    for a in alunos:
        doc = db_fire.collection('alunos').document(str(a.id))
        doc.set(a.to_dict())
        print(f"  [Aluno OK] #{a.id} {a.nome} ({a.equipe}) - PIN: {a.pin_acesso or '1234'}")

    print(f"\nSincronizando {len(medalhas)} Medalhas Lego...")
    for m in medalhas:
        db_fire.collection('medalhas').document(str(m.id)).set(m.to_dict())

    print(f"\nSincronizando {len(atividades)} Desafios Lego...")
    for at in atividades:
        db_fire.collection('atividades').document(str(at.id)).set(at.to_dict())

    print(f"\nSincronizando {len(slides)} Slides e Materiais...")
    for s in slides:
        db_fire.collection('slides').document(str(s.id)).set(s.to_dict())

    print(f"\nSincronizando {len(duvidas)} Duvidas no Forum...")
    for d in duvidas:
        db_fire.collection('duvidas').document(str(d.id)).set(d.to_dict())

print("\n" + "="*60)
print("TODOS OS DADOS FORAM MIGRADOS COM SUCESSO PARA O FIREBASE FIRESTORE!")
print("="*60)
