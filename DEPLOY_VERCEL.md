# 🚀 Guia de Deploy no Vercel + Banco de Dados em Nuvem

Como o **Vercel** opera em arquitetura *Serverless* (sem disco rígido fixo), arquivos SQLite locais são reiniciados a cada requisição. Para que seus dados (chamadas, XP, anotações) fiquem **salvos permanentemente para sempre**, precisamos de um banco de dados gratuito na nuvem.

---

## 🛠️ Passo 1: Criar um Banco de Dados Gratuito em Nuvem

Você pode usar qualquer serviço PostgreSQL gratuito. As 2 opções mais rápidas e recomendadas são:

### Opção A: **Neon.tech** (Recomendado - 100% Grátis, 1 minuto)
1. Acesse [https://neon.tech](https://neon.tech) e crie uma conta gratuita com seu GitHub ou Google.
2. Crie um projeto chamado `lego-attendance`.
3. Copie a **Connection String** (URL de conexão), parecida com:
   `postgresql://usuario:senha@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`

### Opção B: **Supabase** (100% Grátis)
1. Acesse [https://supabase.com](https://supabase.com) e crie um novo projeto.
2. Vá em **Project Settings** ➔ **Database** ➔ **Connection URI**.
3. Copie o link URI do banco PostgreSQL.

---

## ☁️ Passo 2: Fazer o Deploy no Vercel

1. Suba este projeto para o seu **GitHub** (repositório público ou privado).
2. Acesse o [Vercel Dashboard](https://vercel.com/dashboard) e clique em **"Add New..." ➔ "Project"**.
3. Selecione o repositório do projeto Lego.
4. Na seção **Environment Variables** (Variáveis de Ambiente), adicione:
   - **Nome:** `DATABASE_URL`
   - **Valor:** `Sua_URL_de_conexao_do_Neon_ou_Supabase`
5. Clique em **"Deploy"**! 🎉

---

## ⚡ Como o Sistema Funciona:
- **No seu Computador (Local):** Se a variável `DATABASE_URL` não for informada, o sistema usa automaticamente o arquivo SQLite local (`lego_chamada.db`).
- **No Vercel (Produção):** O sistema se conecta diretamente ao seu banco PostgreSQL na nuvem, criando as tabelas e as 3 turmas automaticamente na primeira execução!
