import os
import json
import glob
import firebase_admin
from firebase_admin import credentials, firestore

_firestore_db = None

def get_firebase_db():
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db

    # 1. Verifica variável de ambiente no Vercel (conteúdo JSON em string ou caminho de arquivo)
    firebase_env = os.environ.get('FIREBASE_CREDENTIALS') or os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    
    cred = None
    if firebase_env:
        try:
            # Tenta parsear como JSON direto
            key_dict = json.loads(firebase_env)
            cred = credentials.Certificate(key_dict)
        except Exception:
            if os.path.exists(firebase_env):
                cred = credentials.Certificate(firebase_env)

    # 2. Se não estiver no ambiente, procura o arquivo local .json do Firebase SDK
    if cred is None:
        possible_keys = glob.glob('*firebase*.json') + glob.glob('*adminsdk*.json') + ['serviceAccountKey.json']
        for key_path in possible_keys:
            if os.path.exists(key_path):
                print(f"[Firebase] Carregando credencial do arquivo local: {key_path}")
                cred = credentials.Certificate(key_path)
                break

    if cred is None:
        print("[Firebase] Aviso: Nenhuma credencial do Firebase encontrada. Usando modo offline/SQLAlchemy.")
        return None

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _firestore_db = firestore.client()
        print("[Firebase] Conectado com sucesso ao Cloud Firestore!")
        return _firestore_db
    except Exception as e:
        print(f"[Firebase] Erro ao conectar ao Firestore: {e}")
        return None


def export_all_to_firestore(turmas, alunos, medalhas, atividades, slides, duvidas):
    """
    Sincroniza todos os dados das turmas e alunos diretamente com o Firestore.
    """
    db_fire = get_firebase_db()
    if not db_fire:
        return False, "Firebase não inicializado"

    try:
        # 1. Turmas
        for t in turmas:
            doc_ref = db_fire.collection('turmas').document(str(t.id))
            doc_ref.set(t.to_dict())

        # 2. Alunos
        for a in alunos:
            doc_ref = db_fire.collection('alunos').document(str(a.id))
            doc_ref.set(a.to_dict())

        # 3. Medalhas
        for m in medalhas:
            doc_ref = db_fire.collection('medalhas').document(str(m.id))
            doc_ref.set(m.to_dict())

        # 4. Atividades
        for at in atividades:
            doc_ref = db_fire.collection('atividades').document(str(at.id))
            doc_ref.set(at.to_dict())

        # 5. Slides
        for s in slides:
            doc_ref = db_fire.collection('slides').document(str(s.id))
            doc_ref.set(s.to_dict())

        # 6. Dúvidas
        for d in duvidas:
            doc_ref = db_fire.collection('duvidas').document(str(d.id))
            doc_ref.set(d.to_dict())

        return True, "Sincronização com Cloud Firestore concluída!"
    except Exception as e:
        return False, f"Erro ao exportar para o Firestore: {e}"
