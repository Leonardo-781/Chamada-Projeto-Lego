import unittest
from datetime import date, timedelta
from app import app, db
from models import Usuario, Turma, Aluno, SessaoChamada, RegistroPresenca, Medalha, ConquistaAluno, DiarioBordo, Atividade, EntregaAtividade, SlideAula, DuvidaAluno

class InstitutionalRoboticsSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            from database import seed_usuarios, seed_database, seed_atividades_e_materiais
            seed_usuarios()
            seed_database()
            seed_atividades_e_materiais()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_contas_institucionais_e_rbac(self):
        with app.app_context():
            # 1. Verificar se contas foram criadas
            admin = Usuario.query.filter_by(email="admin@montebot.ufu.br").first()
            prof_alfa = Usuario.query.filter_by(email="professor@alfacoc.com.br").first()
            
            self.assertIsNotNone(admin)
            self.assertTrue(admin.is_admin)
            self.assertIsNotNone(prof_alfa)
            self.assertTrue(prof_alfa.is_professor_escola)

            # 2. Login do Responsável (Admin Master)
            res_admin_login = self.client.post('/api/auth/login', json={
                'tipo': 'usuario',
                'email': 'admin@montebot.ufu.br',
                'senha': 'Admin@MonteBot2026'
            })
            self.assertEqual(res_admin_login.status_code, 200)
            self.assertIn('/painel-admin', res_admin_login.get_json()['redirect'])

            # 3. Teste de acesso do Admin à chamada
            res_chamada = self.client.get('/chamada')
            self.assertEqual(res_chamada.status_code, 200)
            print("[OK] Teste RBAC: Responsável pelas Aulas (Admin Master UFU) autenticado com sucesso!")

    def test_professor_escola_readonly(self):
        with app.app_context():
            # 1. Login do Professor da Escola
            res_login = self.client.post('/api/auth/login', json={
                'tipo': 'usuario',
                'email': 'professor@alfacoc.com.br',
                'senha': 'Professor@Alfa2026'
            })
            self.assertEqual(res_login.status_code, 200)
            self.assertIn('/painel-escola', res_login.get_json()['redirect'])

            # 2. Acesso ao Painel da Escola
            res_painel = self.client.get('/painel-escola')
            self.assertEqual(res_painel.status_code, 200)

            # 3. Tentativa de salvar chamada bloqueada para Professor da Escola
            res_bloqueio = self.client.post('/api/chamada/salvar', json={'turma_id': 1, 'data': '2026-08-31', 'registros': []})
            self.assertEqual(res_bloqueio.status_code, 403)
            print("[OK] Teste RBAC: Professor da Escola autenticado no Painel e restrito de salvar chamadas (Read-Only validado)!")

    def test_aluno_login_e_submissao(self):
        with app.app_context():
            aluno = Aluno.query.first()
            
            # 1. Login do Aluno
            res_aluno_login = self.client.post('/api/auth/login', json={
                'tipo': 'aluno',
                'aluno_id': aluno.id,
                'pin': '1234'
            })
            self.assertEqual(res_aluno_login.status_code, 200)
            self.assertIn('/portal-aluno', res_aluno_login.get_json()['redirect'])

            # 2. Acesso ao Portal do Aluno
            res_portal = self.client.get('/portal-aluno')
            self.assertEqual(res_portal.status_code, 200)
            self.assertIn(aluno.nome.encode('utf-8'), res_portal.data)

            # 3. Submeter Robô
            atividade = Atividade.query.first()
            res_submissao = self.client.post('/api/atividades/entregar', json={
                'atividade_id': atividade.id,
                'aluno_id': aluno.id,
                'link_foto_video': 'https://drive.google.com/teste-robo',
                'descricao_solucao': 'Montamos o chassis com tração diferencial e sensor de cor.'
            })
            self.assertEqual(res_submissao.status_code, 200)
            print(f"[OK] Teste Aluno: Login do aluno {aluno.nome}, acesso ao portal e submissao de projeto validados!")

    def test_admin_avaliacao_e_credito_xp(self):
        with app.app_context():
            # Login como Admin
            self.client.post('/api/auth/login', json={
                'tipo': 'usuario',
                'email': 'admin@montebot.ufu.br',
                'senha': 'Admin@MonteBot2026'
            })

            aluno = Aluno.query.first()
            atividade = Atividade.query.first()
            xp_inicial = aluno.pontos_xp

            entrega = EntregaAtividade(
                atividade_id=atividade.id,
                aluno_id=aluno.id,
                descricao_solucao="Protótipo concluído",
                status="pendente"
            )
            db.session.add(entrega)
            db.session.commit()

            # Avaliar e Conceder +50 XP
            res_aval = self.client.post(f'/api/entregas/{entrega.id}/avaliar', json={
                'status': 'aprovado',
                'xp_concedido': 50,
                'feedback_professor': 'Excelente precisão nos eixos e fixação dos motores.'
            })
            self.assertEqual(res_aval.status_code, 200)

            aluno_atualizado = db.session.get(Aluno, aluno.id)
            self.assertEqual(aluno_atualizado.pontos_xp, xp_inicial + 50)
            print("[OK] Teste Master: Avaliação de entrega de robô e crédito de XP validados!")

    def test_todas_as_rotas_principais(self):
        with app.app_context():
            # Login Admin para testar todas as rotas
            self.client.post('/api/auth/login', json={
                'tipo': 'usuario',
                'email': 'admin@montebot.ufu.br',
                'senha': 'Admin@MonteBot2026'
            })
            rotas = [
                '/',
                '/login',
                '/painel-admin',
                '/painel-escola',
                '/portal-aluno',
                '/chamada',
                '/atividades',
                '/slides',
                '/duvidas',
                '/anotacoes',
                '/alunos',
                '/gamificacao',
                '/historico',
                '/exportar-csv'
            ]
            for r in rotas:
                res = self.client.get(r)
                self.assertIn(res.status_code, [200, 302], f"Falha na rota {r}")
            print(f"[OK] Teste Geral: Todas as {len(rotas)} rotas institucionais validadas com sucesso!")

if __name__ == '__main__':
    unittest.main()
