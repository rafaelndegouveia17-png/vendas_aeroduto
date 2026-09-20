import os
from datetime import date
from functools import wraps

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

from armazenamento import Armazenamento, estado_completo

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "troque-esta-chave-em-producao")

# Troque a senha abaixo e/ou adicione mais usuários.
# Use gerar_senha.py para criar o hash de uma nova senha:
#   python gerar_senha.py "minha-senha-nova"
USUARIOS = {
    "rafael": generate_password_hash("troque-esta-senha"),
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


try:
    armazenamento = Armazenamento(db=obter_db())
except Exception:
    # Sem credenciais configuradas ainda -- as rotas abaixo avisam o usuário
    # em vez de quebrar o servidor inteiro. Configure credenciais_firebase.json
    # e reinicie para ativar o Firebase de verdade.
    armazenamento = None


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


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        hash_armazenado = USUARIOS.get(usuario)
        if hash_armazenado and check_password_hash(hash_armazenado, senha):
            session["usuario"] = usuario
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
    return render_template("index5.html", estado=estado, usuario=session.get("usuario"))


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
@login_obrigatorio_api
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
@login_obrigatorio_api
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
@login_obrigatorio_api
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
    return jsonify(estado_completo(armazenamento, ano, mes))


@app.route("/editar-meta-ano", methods=["POST"])
@login_obrigatorio_api
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
@login_obrigatorio_api
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