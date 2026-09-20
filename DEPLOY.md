# Como colocar o Vendas Aeroduto online (Render)

Você já tem o Firestore funcionando — falta só hospedar o Flask em algum
lugar que fique no ar 24h. O caminho mais simples pra isso, sem precisar
mexer em linha de comando de nuvem, é o [Render](https://render.com)
(tem plano gratuito).

## 1. Colocar o código no GitHub

O Render puxa o deploy direto de um repositório Git.

1. Crie uma conta em [github.com](https://github.com) se ainda não tiver.
2. Crie um repositório novo (pode ser privado).
3. Suba todos os arquivos do projeto **exceto** `credenciais_firebase.json`
   — esse arquivo nunca deve ir para o Git. Crie um arquivo chamado
   `.gitignore` na raiz do projeto com este conteúdo:

   ```
   credenciais_firebase.json
   __pycache__/
   *.pyc
   ```

   Depois:

   ```bash
   git init
   git add .
   git commit -m "Vendas Aeroduto"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
   git push -u origin main
   ```

## 2. Criar o serviço no Render

1. Entre em [dashboard.render.com](https://dashboard.render.com) e crie uma conta (dá pra usar login do GitHub).
2. Clique em **New +** → **Web Service**.
3. Escolha o repositório que você acabou de criar.
4. Preencha:
   - **Name**: `vendas-aeroduto` (ou o nome que quiser)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app3:app`
   - **Instance Type**: Free
5. Ainda não clique em criar — primeiro configure os dois itens abaixo.

## 3. Configurar a credencial do Firebase como "Secret File"

1. Na mesma tela de criação do serviço, procure a seção **Secret Files**.
2. Clique em **Add Secret File**.
3. Em **Filename**, coloque: `credenciais_firebase.json`
4. Em **Contents**, cole o conteúdo inteiro do seu arquivo de credenciais (abra ele num editor de texto e copie tudo).
5. O Render vai deixar esse arquivo disponível em `/etc/secrets/credenciais_firebase.json` dentro do servidor.

## 4. Configurar as variáveis de ambiente

Ainda na tela de criação, na seção **Environment Variables**, adicione:

| Key | Value |
|---|---|
| `FIREBASE_CREDENCIAIS` | `/etc/secrets/credenciais_firebase.json` |
| `FLASK_SECRET_KEY` | qualquer texto longo e aleatório (ex: gere um em [randomkeygen.com](https://randomkeygen.com)) |

## 5. Deploy

Clique em **Create Web Service**. O Render vai instalar as dependências e
subir o servidor automaticamente — acompanhe pela aba **Logs**. Quando
terminar, ele mostra um link tipo `https://vendas-aeroduto.onrender.com`
— esse é o endereço que você compartilha com as pessoas autorizadas.

## Observações

- **Plano gratuito "dorme"**: se ninguém acessar por um tempo, o Render
  desliga o serviço, e a próxima pessoa que abrir o link espera uns 30-60
  segundos enquanto ele liga de novo. Isso é normal no plano free — se
  incomodar, dá pra migrar pro plano pago mais barato deles.
- **Toda vez que você editar o código**, é só rodar `git push` de novo —
  o Render redeploya sozinho.
- **Para adicionar/trocar usuários** depois do deploy, edite o
  `USUARIOS` em `app3.py`, dê `git push` de novo.
