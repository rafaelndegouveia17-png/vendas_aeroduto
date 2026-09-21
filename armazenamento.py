from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

metas = {
    "mensal": [
        {"titulo": f"Vendedor {i + 1}", "meta": 50000, "atual": 0, "concluido": "não"}
        for i in range(4)
    ],
    "anual": {
        "titulo": "Meta anual",
        "meta": 1200000,
        "entradas": [],
    },
}


def calcular_anual():
    total = sum(e["valor"] for e in metas["anual"]["entradas"])
    concluido = "sim" if total >= metas["anual"]["meta"] else "não"
    return total, concluido


def estado_anual_json():
    atual, concluido = calcular_anual()
    return {
        "titulo": metas["anual"]["titulo"],
        "meta": metas["anual"]["meta"],
        "atual": atual,
        "concluido": concluido,
        "entradas": metas["anual"]["entradas"],
    }


@app.route("/")
def pagina():
    atual, concluido = calcular_anual()
    return render_template(
        "index5.html",
        mensal=metas["mensal"],
        anual_titulo=metas["anual"]["titulo"],
        anual_meta=metas["anual"]["meta"],
        anual_atual=atual,
        anual_concluido=concluido,
        anual_entradas=metas["anual"]["entradas"],
    )


@app.route("/alterar-mensal", methods=["POST"])
def alterar_mensal():
    dados = request.get_json(silent=True) or {}
    indice = dados.get("indice")

    if not isinstance(indice, int) or not (0 <= indice < len(metas["mensal"])):
        return jsonify({"erro": "Selecione um velocímetro válido."}), 400

    item = metas["mensal"][indice]

    if "titulo" in dados:
        titulo = str(dados["titulo"]).strip()
        if titulo == "":
            return jsonify({"erro": "O subtítulo não pode ficar vazio."}), 400
        item["titulo"] = titulo[:40]

    try:
        if "atual" in dados:
            item["atual"] = int(dados["atual"])
        if "meta" in dados:
            item["meta"] = int(dados["meta"])
    except (TypeError, ValueError):
        return jsonify({"erro": "Informe valores inteiros válidos."}), 400

    if item["atual"] < 0 or item["meta"] < 0:
        return jsonify({"erro": "Os valores não podem ser negativos."}), 400

    item["concluido"] = "sim" if item["atual"] >= item["meta"] else "não"

    return jsonify({
        "indice": indice,
        "titulo": item["titulo"],
        "atual": item["atual"],
        "meta": item["meta"],
        "concluido": item["concluido"],
    })


@app.route("/alterar-anual", methods=["POST"])
def alterar_anual():
    dados = request.get_json(silent=True) or {}
    tipo = dados.get("tipo")

    if tipo == "titulo":
        titulo = str(dados.get("valor", "")).strip()
        if titulo == "":
            return jsonify({"erro": "O subtítulo não pode ficar vazio."}), 400
        metas["anual"]["titulo"] = titulo[:40]

    elif tipo == "meta":
        try:
            nova_meta = int(dados.get("valor"))
        except (TypeError, ValueError):
            return jsonify({"erro": "Informe um valor inteiro válido."}), 400
        if nova_meta < 0:
            return jsonify({"erro": "A meta não pode ser negativa."}), 400
        metas["anual"]["meta"] = nova_meta

    elif tipo == "adicionar":
        rotulo = str(dados.get("rotulo", "")).strip()
        if rotulo == "":
            rotulo = f"Entrada {len(metas['anual']['entradas']) + 1}"
        try:
            valor = int(dados.get("valor", 0))
        except (TypeError, ValueError):
            return jsonify({"erro": "Informe um valor inteiro válido."}), 400
        if valor < 0:
            return jsonify({"erro": "O valor não pode ser negativo."}), 400
        metas["anual"]["entradas"].append({"rotulo": rotulo[:40], "valor": valor})

    elif tipo == "editar":
        indice = dados.get("indice")
        if not isinstance(indice, int) or not (0 <= indice < len(metas["anual"]["entradas"])):
            return jsonify({"erro": "Selecione uma entrada válida."}), 400
        entrada = metas["anual"]["entradas"][indice]

        if "rotulo" in dados:
            rotulo = str(dados["rotulo"]).strip()
            if rotulo == "":
                return jsonify({"erro": "O rótulo não pode ficar vazio."}), 400
            entrada["rotulo"] = rotulo[:40]

        if "valor" in dados:
            try:
                novo_valor = int(dados["valor"])
            except (TypeError, ValueError):
                return jsonify({"erro": "Informe um valor inteiro válido."}), 400
            if novo_valor < 0:
                return jsonify({"erro": "O valor não pode ser negativo."}), 400
            entrada["valor"] = novo_valor

    elif tipo == "remover":
        indice = dados.get("indice")
        if not isinstance(indice, int) or not (0 <= indice < len(metas["anual"]["entradas"])):
            return jsonify({"erro": "Selecione uma entrada válida."}), 400
        metas["anual"]["entradas"].pop(indice)

    else:
        return jsonify({"erro": "Ação inválida."}), 400

    return jsonify(estado_anual_json())


app.run(debug=True)
