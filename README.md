# 🧱 Sistema de Chamada & Gamificação Lego (3 Turmas)

Sistema completo de controle de presença e frequência escolar desenvolvido especialmente para projetos de **Robótica e Montagem com LEGO**, contendo **backend em Python Flask + SQLite / PostgreSQL (Supabase)**, interface moderna e **sistema de gamificação por Tijolos de XP, Níveis de Construtor, Medalhas de Conquistas e Diário Pedagógico**.

---

## 🚀 Como Executar Localmente

### 1. Inicialização Rápida (Windows)
Basta dar um duplo clique no arquivo:
```
executar.bat
```

### 2. Ou via Terminal / PowerShell
```bash
pip install -r requirements.txt
python app.py
```

Após iniciar, abra seu navegador em:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## ☁️ Deploy no Vercel + Supabase

Para colocar o sistema online na nuvem 24h:
1. Conecte seu repositório no **[Vercel](https://vercel.com)**.
2. Adicione a variável de ambiente `DATABASE_URL` com sua URL de conexão PostgreSQL do **Supabase**.
3. Consulte o arquivo [`DEPLOY_VERCEL.md`](./DEPLOY_VERCEL.md) para o passo a passo completo.

---

## 🌟 Principais Funcionalidades

### 1. 🏫 As 3 Turmas Pré-Configuradas
- **Turma A - Construtores Júnior** (🧱 Vermelho Lego): Iniciação ao mundo Lego, estruturas básicas e engrenagens.
- **Turma B - Robótica & Mecanismos** (⚙️ Azul Lego): Mecanismos motorizados, sensores e lógica.
- **Turma C - Mestres Construtores** (🚀 Verde Lego): Projetos avançados, desafios e robôs autônomos.

### 2. 📋 Chamada Interativa em 1 Clique
- Botões diretos para cada aluno:
  - **Presente (Verde)**: Atribui automaticamente **+10 XP** de presença.
  - **Falta (Vermelho)**: Registra falta (0 XP).
  - **Justificada (Amarelo)**: Permite registrar o motivo e concede **+2 XP** por responsabilidade.
- Botão **"Marcar Todos Presentes"** para agilizar dias de aula cheia.
- Botões de **Bônus Especial de XP** (+5 Organização de Peças, +5 Trabalho em Equipe, +10 Robô Funcional).
- Chuva de Confetti comemorativa e feedback instantâneo.

### 3. 📝 Mural de Notas & Diário Pedagógico
- **Mural Fixo das Turmas**: Registro permanente de kits em uso, regras e metas.
- **Diário de Aula**: Registro de temas, dificuldades das equipes e planejamento para a próxima aula.

### 4. 🏆 Gamificação Lego & Níveis de Construtor
- **Nível 1 - Aprendiz de Blocos** (🧱 0 a 49 XP)
- **Nível 2 - Construtor Ágil** (⚙️ 50 a 149 XP)
- **Nível 3 - Engenheiro Robótico** (🤖 150 a 299 XP)
- **Nível 4 - Mestre da Criação** (🚀 300 a 499 XP)
- **Nível 5 - Mestre Construtor Lendário** (👑 500+ XP)

### 5. 🎖️ Medalhas e Conquistas
- Conceda medalhas de destaque como *Primeiro Bloco*, *Espírito de Equipe*, *Mestre da Organização*, *Criador de Robôs* e *Frequência de Ouro*.

### 6. 👥 Gerenciamento de Alunos & Avatares
- Cadastro com avatares estilizados de minifiguras Lego (Ninja, Astronauta, Mago, Robô, Piloto, etc.).
- Definição de equipes de montagem e controle individual de XP e assiduidade.

### 7. 📊 Histórico e Exportação
- Consulta de chamadas anteriores com filtros por data e turma.
- Exportação completa da frequência dos alunos para planilhas **Excel / CSV**.
