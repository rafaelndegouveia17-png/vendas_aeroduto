import os
from datetime import date
from functools import wraps

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

from armazenamento import Armazenamento, estado_completo
from notificacoes import Notificador

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")

# Troque as senhas e/ou adicione mais usuários.
# "papel" pode ser "admin" (pode editar) ou "usuario" (só visualiza).
# Use gerar_senha.py para criar o hash de uma nova senha:
#   python gerar_senha.py "minha-senha-nova"
USUARIOS = {
    "rafael": {"senha": generate_password_hash("troque-esta-senha"), "papel": "admin"},
    "consulta": {"senha": generate_password_hash("troque-esta-tambem"), "papel": "usuario"},
}


def obter_db():
    """Inicializa o cliente do Firestore usando o arquivo de credenciais do Firebase.

    Veja as instruções de configuração no README para gerar
    credenciais_firebase.json a partir do console do Firebase.
    """
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        caminho_credenciais = os.environ.get("FIREBASE_CREDENCIAIS", "credenciais_firebase.json")
        cred = credentials.Certificate(caminho_credenciais)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def obter_notificador():
    """Configura o envio de SMS/WhatsApp via Twilio a partir de variáveis de ambiente.

    Se as variáveis não estiverem definidas, o notificador fica inativo e
    simplesmente não envia nada (sem quebrar o app). Veja o README para a
    lista completa de variáveis.
    """
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    numero_origem = os.environ.get("TWILIO_NUMERO_ORIGEM", "")
    canal = os.environ.get("TWILIO_CANAL", "sms")
    destinatarios = [n.strip() for n in os.environ.get("NUMEROS_NOTIFICACAO", "").split(",") if n.strip()]

    cliente = None
    if sid and token:
        try:
            from twilio.rest import Client
            cliente = Client(sid, token)
        except Exception:
            cliente = None

    return Notificador(cliente=cliente, numero_origem=numero_origem, destinatarios=destinatarios, canal=canal)


try:
    armazenamento = Armazenamento(db=obter_db())
except Exception:
    # Sem credenciais configuradas ainda -- as rotas abaixo avisam o usuário
    # em vez de quebrar o servidor inteiro. Configure credenciais_firebase.json
    # e reinicie para ativar o Firebase de verdade.
    armazenamento = None

notificador = obter_notificador()


def login_obrigatorio(func):
    @wraps(func)
    def decorado(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorado


def login_obrigatorio_api(func):
    @wraps(func)
    def decorado(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"erro": "Sessão expirada. Faça login novamente."}), 401
        if armazenamento is None:
            return jsonify({"erro": "Firebase não configurado no servidor."}), 500
        return func(*args, **kwargs)
    return decorado


def admin_obrigatorio_api(func):
    @wraps(func)
    def decorado(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"erro": "Sessão expirada. Faça login novamente."}), 401
        if session.get("papel") != "admin":
            return jsonify({"erro": "Apenas administradores podem fazer essa alteração."}), 403
        if armazenamento is None:
            return jsonify({"erro": "Firebase não configurado no servidor."}), 500
        return func(*args, **kwargs)
    return decorado


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        registro = USUARIOS.get(usuario)
        if registro and check_password_hash(registro["senha"], senha):
            session["usuario"] = usuario
            session["papel"] = registro["papel"]
            return redirect(url_for("pagina"))
        erro = "Usuário ou senha inválidos."
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def pagina():
    if armazenamento is None:
        return (
            "Firebase não configurado. Adicione credenciais_firebase.json "
            "na pasta do projeto e reinicie o servidor.",
            500,
        )
    hoje = date.today()
    estado = estado_completo(armazenamento, hoje.year, hoje.month)
    return render_template(
        "index5.html",
        estado=estado,
        usuario=session.get("usuario"),
        is_admin=session.get("papel") == "admin",
    )


@app.route("/carregar-mes", methods=["POST"])
@login_obrigatorio_api
def carregar_mes():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe ano e mês válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    return jsonify(estado_completo(armazenamento, ano, mes))


@app.route("/editar-meta-mes", methods=["POST"])
@admin_obrigatorio_api
def editar_meta_mes():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
        nova_meta = int(dados["meta"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe valores válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    if nova_meta < 0:
        return jsonify({"erro": "A meta não pode ser negativa."}), 400
    armazenamento.definir_meta_mes(ano, mes, nova_meta)
    return jsonify(estado_completo(armazenamento, ano, mes))


@app.route("/editar-nome-velocimetro", methods=["POST"])
@admin_obrigatorio_api
def editar_nome_velocimetro():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
        indice = int(dados["indice"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe valores válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    if not (0 <= indice <= 2):
        return jsonify({"erro": "Selecione um velocímetro válido."}), 400
    nome = str(dados.get("nome", "")).strip()
    if nome == "":
        return jsonify({"erro": "O nome não pode ficar vazio."}), 400
    armazenamento.definir_nome_velocimetro(ano, mes, indice, nome[:40])
    return jsonify(estado_completo(armazenamento, ano, mes))


@app.route("/adicionar-entrada", methods=["POST"])
@admin_obrigatorio_api
def adicionar_entrada():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
        indice = int(dados["indice"])
        valor = int(dados["valor"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe valores válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    if not (0 <= indice <= 2):
        return jsonify({"erro": "Selecione um velocímetro válido."}), 400
    if valor < 0:
        return jsonify({"erro": "O valor não pode ser negativo."}), 400
    cliente = str(dados.get("cliente", "")).strip()
    if cliente == "":
        return jsonify({"erro": "Informe o nome do cliente."}), 400

    armazenamento.adicionar_entrada(ano, mes, indice, cliente[:60], valor)
    estado = estado_completo(armazenamento, ano, mes)

    try:
        nome_velocimetro = estado["velocimetros"][indice]["nome"]
        notificador.notificar_nova_entrada(nome_velocimetro, cliente[:60], valor, mes, ano)
    except Exception as erro:
        # nunca deixa uma falha de notificação derrubar a resposta da API
        print(f"[notificacoes] erro inesperado ao notificar: {erro}")

    return jsonify(estado)


@app.route("/editar-meta-ano", methods=["POST"])
@admin_obrigatorio_api
def editar_meta_ano():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
        nova_meta = int(dados["meta"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe valores válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    if nova_meta < 0:
        return jsonify({"erro": "A meta não pode ser negativa."}), 400
    armazenamento.definir_meta_ano(ano, nova_meta)
    return jsonify(estado_completo(armazenamento, ano, mes))


@app.route("/remover-entrada", methods=["POST"])
@admin_obrigatorio_api
def remover_entrada():
    dados = request.get_json(silent=True) or {}
    try:
        ano = int(dados["ano"])
        mes = int(dados["mes"])
        indice = int(dados["indice"])
        indice_entrada = int(dados["indice_entrada"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe valores válidos."}), 400
    if not (1 <= mes <= 12):
        return jsonify({"erro": "Mês inválido."}), 400
    if not (0 <= indice <= 2):
        return jsonify({"erro": "Selecione um velocímetro válido."}), 400

    mes_dados = armazenamento.obter_mes(ano, mes)
    entradas = mes_dados["gauges"][indice]["entradas"]
    if not (0 <= indice_entrada < len(entradas)):
        return jsonify({"erro": "Selecione uma entrada válida."}), 400

    armazenamento.remover_entrada(ano, mes, indice, indice_entrada)
    return jsonify(estado_completo(armazenamento, ano, mes))


if __name__ == "__main__":
    app.run(debug=True)
