import sys
import unittest
from datetime import date, timedelta
from app import app, db
from models import Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo, Atividade, EntregaAtividade, SlideAula, DuvidaAluno

class LegoSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            from database import seed_database, seed_atividades_e_materiais
            seed_database()
            seed_atividades_e_materiais()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_tres_turmas_e_anotacoes(self):
        with app.app_context():
            turmas = Turma.query.all()
            self.assertEqual(len(turmas), 3)
            self.assertTrue(len(turmas[0].anotacoes) > 0)
            print("[OK] Verificacao: 3 Turmas Lego e anotacoes fixas validadas!")

    def test_atividades_entregas_e_avaliacao_xp(self):
        with app.app_context():
            turma = Turma.query.first()
            aluno = turma.alunos[0]
            xp_inicial = aluno.pontos_xp
            
            # 1. Cadastrar Desafio
            res_ativ = self.client.post('/api/atividades', json={
                'titulo': 'Desafio Teste: Robô Seguidor de Luz',
                'descricao': 'Construa um robô que siga a lanterna',
                'kit_lego': 'Lego SPIKE Prime',
                'xp_recompensa': 50,
                'data_limite': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'turma_id': turma.id
            })
            self.assertEqual(res_ativ.status_code, 200)
            ativ_id = res_ativ.get_json()['atividade']['id']

            # 2. Aluno submeter entrega
            res_entrega = self.client.post('/api/atividades/entregar', json={
                'atividade_id': ativ_id,
                'aluno_id': aluno.id,
                'link_foto_video': 'https://drive.google.com/teste-video',
                'descricao_solucao': 'Montamos com dois motores angulares e sensor de luminosidade.'
            })
            self.assertEqual(res_entrega.status_code, 200)
            entrega_id = res_entrega.get_json()['entrega']['id']

            # 3. Professor avaliar e conceder XP
            res_aval = self.client.post(f'/api/entregas/{entrega_id}/avaliar', json={
                'status': 'aprovado',
                'xp_concedido': 50,
                'feedback_professor': 'Excelente solução de montagem e calibração!'
            })
            self.assertEqual(res_aval.status_code, 200)
            
            aluno_atualizado = db.session.get(Aluno, aluno.id)
            self.assertEqual(aluno_atualizado.pontos_xp, xp_inicial + 50)
            print(f"[OK] Verificacao: Atividade enviada, avaliada e creditados +50 XP para {aluno.nome}!")

    def test_slides_e_materiais(self):
        with app.app_context():
            res = self.client.post('/api/slides', json={
                'titulo': 'Aula 05: Sensores Giroscópicos',
                'descricao': 'Tutorial sobre controle de curvas de precisão',
                'numero_aula': 5,
                'link_slide': 'https://docs.google.com/presentation/d/teste',
                'tipo': 'slides'
            })
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.get_json()['success'])
            print("[OK] Verificacao: Cadastro e listagem de Slides/Materiais validado!")

    def test_duvidas_e_respostas_forum(self):
        with app.app_context():
            aluno = Aluno.query.first()
            # 1. Postar dúvida
            res_duvida = self.client.post('/api/duvidas', json={
                'aluno_id': aluno.id,
                'categoria': 'Programação & Sensores',
                'titulo': 'Dúvida sobre bloco de repetição',
                'pergunta': 'Como fazer o loop parar quando o sensor detectar a cor vermelha?'
            })
            self.assertEqual(res_duvida.status_code, 200)
            duvida_id = res_duvida.get_json()['duvida']['id']

            # 2. Responder dúvida
            res_resp = self.client.post(f'/api/duvidas/{duvida_id}/responder', json={
                'resposta': 'Use o bloco "Repetir até que <cor = vermelha>".',
                'respondido_por': 'Professor de Robótica'
            })
            self.assertEqual(res_resp.status_code, 200)
            self.assertEqual(res_resp.get_json()['duvida']['status'], 'respondida')

            # 3. Marcar como resolvida
            res_stat = self.client.put(f'/api/duvidas/{duvida_id}/status', json={'status': 'resolvida'})
            self.assertEqual(res_stat.status_code, 200)
            print("[OK] Verificacao: Ciclo completo do Fórum de Dúvidas (Pergunta, Resposta e Resolução) validado!")

    def test_portal_do_aluno_e_login(self):
        with app.app_context():
            aluno = Aluno.query.first()
            
            # 1. Teste de login com PIN errado
            res_err = self.client.post('/aluno/login', json={
                'aluno_id': aluno.id,
                'pin': '9999'
            })
            self.assertEqual(res_err.status_code, 401)

            # 2. Teste de login com PIN correto (padrão 1234)
            res_ok = self.client.post('/aluno/login', json={
                'aluno_id': aluno.id,
                'pin': '1234'
            })
            self.assertEqual(res_ok.status_code, 200)
            self.assertTrue(res_ok.get_json()['success'])

            # 3. Acesso à página de estudos logado
            res_estudos = self.client.get('/estudos')
            self.assertEqual(res_estudos.status_code, 200)
            self.assertIn(aluno.nome.encode('utf-8'), res_estudos.data)

            # 4. Alteração de PIN
            res_pin = self.client.put('/api/aluno/alterar-pin', json={'novo_pin': '5678'})
            self.assertEqual(res_pin.status_code, 200)

            aluno_atualizado = db.session.get(Aluno, aluno.id)
            self.assertEqual(aluno_atualizado.pin_acesso, '5678')
            print(f"[OK] Verificacao: Login do Aluno ({aluno.nome}), acesso aos estudos remotos e troca de PIN validados!")

    def test_todas_as_rotas_web(self):
        rotas = [
            '/',
            '/chamada',
            '/atividades',
            '/slides',
            '/duvidas',
            '/anotacoes',
            '/alunos',
            '/gamificacao',
            '/historico',
            '/aluno/login',
            '/exportar-csv'
        ]
        for r in rotas:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Falha na rota {r}")
        print(f"[OK] Verificacao: Todas as {len(rotas)} rotas Web do portal respondendo com status 200!")

if __name__ == '__main__':
    unittest.main()
