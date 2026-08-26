import sys
import unittest
from datetime import date
from app import app, db
from models import Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo

class LegoSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            from database import seed_database
            seed_database()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_tres_turmas_e_anotacoes(self):
        with app.app_context():
            turmas = Turma.query.all()
            self.assertEqual(len(turmas), 3)
            # Verifica anotação da Turma A
            self.assertTrue(len(turmas[0].anotacoes) > 0)
            print("[OK] Verificacao: 3 Turmas Lego e anotacoes fixas validadas!")

    def test_diario_bordo(self):
        with app.app_context():
            turma = Turma.query.first()
            res = self.client.post('/api/diario', json={
                'turma_id': turma.id,
                'data': date.today().strftime('%Y-%m-%d'),
                'categoria': 'Anotacao Pedagogica',
                'titulo': 'Teste Diario',
                'conteudo': 'Conteudo do diario de teste'
            })
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.get_json()['success'])
            print("[OK] Verificacao: Criacao de nota no Diario de Bordo validada!")

    def test_salvar_chamada_com_planejamento(self):
        with app.app_context():
            turma = Turma.query.first()
            aluno = turma.alunos[0]
            xp_inicial = aluno.pontos_xp
            
            res = self.client.post('/api/chamada/salvar', json={
                'turma_id': turma.id,
                'data': date.today().strftime('%Y-%m-%d'),
                'topico': 'Teste de Robotica com Notas',
                'observacoes': 'Equipe colaborou bastante',
                'proxima_aula': 'Calibrar motores',
                'registros': [
                    {'aluno_id': aluno.id, 'status': 'presente', 'justificativa': '', 'pontos_bonus': 5, 'motivo_bonus': 'Destaque'}
                ]
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            
            aluno_atualizado = db.session.get(Aluno, aluno.id)
            self.assertEqual(aluno_atualizado.pontos_xp, xp_inicial + 15)
            print(f"[OK] Verificacao: Chamada e notas pedagógicas salvas (+15 XP para {aluno.nome})!")

    def test_rotas_web(self):
        rotas = ['/', '/chamada', '/anotacoes', '/alunos', '/gamificacao', '/historico', '/exportar-csv']
        for r in rotas:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Falha na rota {r}")
        print("[OK] Verificacao: Todas as 7 rotas Web respondendo com status 200!")

if __name__ == '__main__':
    unittest.main()
